import asyncio
import json
import logging
import time
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.gemini import gemini_generate
from app.db.models import GenerationOutput, Session as SessionModel
from app.services.session import get_session, update_session_status
from app.schemas.schemas import SSEEvent, GenerationStatusResponse

logger = logging.getLogger(__name__)
SECTIONS = ["architecture", "capacity", "data_model", "api_design", "stack"]

# Per-section JSON shape instructions — these line up with the frontend's
# ArchitectureData / CapacityData / DataModelData / ApiDesignData / StackData
# interfaces (frontend/src/types/index.ts) so the artifact panel can render
# the payload directly without any frontend-side reshaping.
SECTION_SCHEMAS = {
    "architecture": """Return JSON: {"components": [{"id": str, "name": str,
"type": one of ["frontend","backend","database","queue","cache","cdn","auth","storage","third_party","ai"],
"description": str, "connections": [str ids of other components]}],
"metadata": {"total_components": int, "total_connections": int}}""",
    "capacity": """Return JSON: {"dau": int, "peak_read_qps": int, "peak_write_qps": int,
"daily_storage_gb": number, "five_year_storage_tb": number, "bandwidth_gbps": number,
"cache_dataset_gb": number, "formulas": {"<calc name>": "<formula and explanation as text>"}}""",
    "data_model": """Return JSON: {"decision": one of ["SQL","NoSQL","Hybrid"], "rationale": str,
"entities": [{"name": str, "columns": [{"name": str, "type": str, "primary": bool, "indexed": bool}],
"sharding_key": str or null}], "notes": str}""",
    "api_design": """Return JSON: {"style": one of ["REST","GraphQL","gRPC","WebSocket"], "auth": str,
"endpoints": [{"method": one of ["GET","POST","PUT","DELETE","PATCH"], "path": str, "description": str,
"rate_limit": str or null}], "base_url": str or null, "version": str or null}""",
    "stack": """Return JSON: {"layers": [{"layer": str, "primary": str, "alternatives": [str],
"rationale": str, "trade_off": str or null}], "philosophy": str or null}""",
}

def _now_ms() -> int:
    return int(time.time() * 1000)

def _event(**kwargs) -> str:
    evt = SSEEvent(timestamp=_now_ms(), **kwargs)
    return f"data: {evt.model_dump_json(exclude_none=True)}\n\n"

async def generate_section(session: SessionModel, section: str) -> dict:
    schema_hint = SECTION_SCHEMAS.get(section, "Return a JSON object.")
    prompt = (
        f"Generate the '{section}' section for a {session.design_type or 'HLD'} design of: "
        f"{session.system_name or session.prompt}.\n"
        f"User-provided requirements/context: {json.dumps(session.context_json or {})}\n\n"
        f"{schema_hint}"
    )
    result = await gemini_generate(
        prompt=prompt,
        system_prompt="You are a system design expert. Output ONLY valid JSON matching the requested shape — no prose, no markdown fences.",
        json_mode=True,
    )
    payload = result.get("parsed") or {}
    return {
        "payload": payload,
        "tokens_used": result.get("tokens_in", 0) + result.get("tokens_out", 0),
        "cached": result.get("cached", False),
        "duration_ms": result.get("duration_ms", 0),
    }

async def generate_design_stream(db: AsyncSession, session_id: UUID):
    session = await get_session(db, session_id)
    if not session:
        yield _event(type="pipeline.error", error="Session not found", error_code="SESSION_NOT_FOUND")
        return

    yield _event(type="ping", session_id=session_id, message="Connected. Starting generation pipeline.")

    await update_session_status(db, session_id, "generating")

    total_tokens = 0
    total_duration_ms = 0

    for section in SECTIONS:
        # Cooperative cancellation: the cancel endpoint flips session.status
        # to "cancelled"; re-fetch and check before starting each section so
        # an in-flight stream can actually stop instead of running to completion.
        await db.refresh(session)
        if session.status == "cancelled":
            yield _event(type="pipeline.error", error="Generation cancelled by user", error_code="CANCELLED")
            return

        result = await db.execute(select(GenerationOutput).where(
            GenerationOutput.session_id == session_id, GenerationOutput.section == section
        ))
        gen_output = result.scalar_one_or_none()
        if not gen_output:
            gen_output = GenerationOutput(session_id=session_id, section=section, status="generating")
            db.add(gen_output)
        else:
            gen_output.status = "generating"
            gen_output.error_msg = None
        await db.flush()

        yield _event(type="section.start", section=section, status="started")

        try:
            result = await generate_section(session, section)
            gen_output.status = "complete"
            gen_output.payload_json = result["payload"]
            gen_output.tokens_used = result["tokens_used"]
            gen_output.cached = result["cached"]
            gen_output.duration_ms = result["duration_ms"]
            gen_output.error_msg = None
            await db.commit()

            total_tokens += result["tokens_used"]
            total_duration_ms += result["duration_ms"]

            yield _event(
                type="section.done", section=section, status="complete",
                payload=result["payload"], tokens_used=result["tokens_used"],
                duration_ms=result["duration_ms"], cached=result["cached"],
            )
        except Exception as e:
            logger.error(f"Section '{section}' generation failed: {e}")
            gen_output.status = "error"
            gen_output.error_msg = str(e)
            await db.commit()
            yield _event(type="section.error", section=section, status="error", error=str(e))
            # Keep going — one bad section shouldn't kill the whole pipeline.

        await asyncio.sleep(0.1)

    await update_session_status(db, session_id, "complete")
    yield _event(
        type="pipeline.done", section="done", status="done",
        total_tokens=total_tokens, total_duration_ms=total_duration_ms,
    )

async def get_generation_status(db: AsyncSession, session_id: UUID) -> GenerationStatusResponse | None:
    session = await get_session(db, session_id)
    if not session:
        return None

    result = await db.execute(select(GenerationOutput).where(GenerationOutput.session_id == session_id))
    outputs = result.scalars().all()

    sections: dict[str, dict] = {}
    total_tokens = 0
    total_duration_ms = 0
    for o in outputs:
        sections[o.section] = {
            "status": o.status,
            "tokens_used": o.tokens_used,
            "duration_ms": o.duration_ms,
            "cached": bool(o.cached),
        }
        total_tokens += o.tokens_used or 0
        total_duration_ms += o.duration_ms or 0

    return GenerationStatusResponse(
        session_id=session_id,
        session_status=session.status,
        sections=sections,
        total_tokens=total_tokens,
        total_duration_ms=total_duration_ms,
    )

async def cancel_generation(db: AsyncSession, session_id: UUID) -> bool:
    """Cooperative cancellation: flips status so the streaming generator's
    per-section check (`if session.status == "cancelled"`) stops it before
    the next section starts. Does not abort an in-flight Gemini call."""
    session = await get_session(db, session_id)
    if not session:
        return False
    session.status = "cancelled"
    await db.commit()
    return True