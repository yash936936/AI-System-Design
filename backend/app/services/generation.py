"""
Phase D — Generation Service
============================
Streams design sections over SSE.

Architecture:
  - 3 Gemini calls (batched):
      1. architecture         → ArchitectureData
      2. capacity_and_data    → CapacityData + DataModelData
      3. api_and_stack        → ApiDesignData + StackData
  - Each batch result is split and emitted as individual section.done events
    so the frontend's SECTION_TO_TAB map (architecture → diagram,
    capacity → capacity, data_model → data_model, api_design → api,
    stack → stack) receives the exact SectionId keys it expects.
  - Cooperative cancellation: checks session.status == "cancelled" before
    each batch call.
"""

import asyncio
import json
import logging
import time
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.gemini import gemini_generate
from app.db.models import GenerationOutput, Session as SessionModel
from app.schemas.schemas import SSEEvent, GenerationStatusResponse
from app.services.session import get_session, update_session_status
from app.services.prompts import (
    format_context,
    arch_user_prompt,
    capacity_data_user_prompt,
    api_stack_user_prompt,
    ARCH_SYSTEM,
    CAPACITY_DATA_SYSTEM,
    API_STACK_SYSTEM,
)

logger = logging.getLogger(__name__)

# ── Section IDs exactly as frontend SECTION_TO_TAB expects ──────────────────
# architecture  → ARTIFACT_TABS.DIAGRAM
# capacity      → ARTIFACT_TABS.CAPACITY
# data_model    → ARTIFACT_TABS.DATA_MODEL
# api_design    → ARTIFACT_TABS.API
# stack         → ARTIFACT_TABS.STACK
FRONTEND_SECTIONS = ["architecture", "capacity", "data_model", "api_design", "stack"]


def _now_ms() -> int:
    return int(time.time() * 1000)


def _event(**kwargs) -> str:
    evt = SSEEvent(timestamp=_now_ms(), **kwargs)
    return f"data: {evt.model_dump_json(exclude_none=True)}\n\n"


def _upsert_gen_output(outputs_by_section: dict, section: str, session_id: UUID) -> GenerationOutput:
    """Return existing GenerationOutput or create a new one."""
    if section in outputs_by_section:
        out = outputs_by_section[section]
        out.status = "generating"
        out.error_msg = None
        return out
    return GenerationOutput(session_id=session_id, section=section, status="generating")


async def _call_gemini_batch(
    system: str,
    user: str,
) -> dict:
    """Call Gemini and return the parsed JSON dict, or {} on failure."""
    result = await gemini_generate(
        prompt=user,
        system_prompt=system,
        json_mode=True,
    )
    return {
        "parsed": result.get("parsed") or {},
        "tokens_used": result.get("tokens_in", 0) + result.get("tokens_out", 0),
        "cached": result.get("cached", False),
        "duration_ms": result.get("duration_ms", 0),
    }


async def generate_design_stream(db: AsyncSession, session_id: UUID):
    """
    SSE generator.  Yields raw SSE text frames.

    Batch layout:
      Batch 1: architecture
      Batch 2: capacity + data_model   (capacity_and_data)
      Batch 3: api_design + stack      (api_and_stack)

    Each batch emits:
      section.start  for every section it covers
      section.done / section.error for every section it covers
    """
    session = await get_session(db, session_id)
    if not session:
        yield _event(type="pipeline.error", error="Session not found", error_code="SESSION_NOT_FOUND")
        return

    yield _event(type="ping", session_id=str(session_id), message="Connected. Starting generation pipeline.")

    await update_session_status(db, session_id, "generating")

    # Pre-load existing GenerationOutput rows (idempotency on restart)
    existing_result = await db.execute(
        select(GenerationOutput).where(GenerationOutput.session_id == session_id)
    )
    outputs_by_section: dict[str, GenerationOutput] = {
        o.section: o for o in existing_result.scalars().all()
    }

    # Build context block once — shared across all batches
    ctx = session.context_json or {}
    design_type = session.design_type or "HLD"

    # Retrieve RAG chunks if available (best-effort; empty list is fine)
    chunks: list[dict] = []
    try:
        from sqlalchemy import select as sa_select
        from app.db.models import RagRetrieval
        rag_result = await db.execute(
            sa_select(RagRetrieval).where(RagRetrieval.session_id == session_id)
        )
        rag_row = rag_result.scalar_one_or_none()
        if rag_row and rag_row.chunks_json:
            chunks = rag_row.chunks_json
    except Exception as e:
        logger.warning("Could not load RAG chunks: %s", e)

    context_block = format_context(
        ctx=ctx,
        prompt=session.prompt or "",
        design_type=design_type,
        chunks=chunks,
    )

    total_tokens = 0
    total_duration_ms = 0

    # ── BATCH 1: Architecture ────────────────────────────────────────────────
    await db.refresh(session)
    if session.status == "cancelled":
        yield _event(type="pipeline.error", error="Generation cancelled by user", error_code="CANCELLED")
        return

    batch1_sections = ["architecture"]
    for sec in batch1_sections:
        out = _upsert_gen_output(outputs_by_section, sec, session_id)
        if sec not in outputs_by_section:
            db.add(out)
            outputs_by_section[sec] = out
    await db.flush()

    yield _event(type="section.start", section="architecture", status="started")

    try:
        b1 = await _call_gemini_batch(
            system=ARCH_SYSTEM,
            user=arch_user_prompt(context_block, design_type),
        )
        arch_payload = b1["parsed"]

        out = outputs_by_section["architecture"]
        out.status = "complete"
        out.payload_json = arch_payload
        out.tokens_used = b1["tokens_used"]
        out.cached = b1["cached"]
        out.duration_ms = b1["duration_ms"]
        out.error_msg = None
        await db.commit()

        total_tokens += b1["tokens_used"]
        total_duration_ms += b1["duration_ms"]

        yield _event(
            type="section.done",
            section="architecture",
            status="complete",
            payload=arch_payload,
            tokens_used=b1["tokens_used"],
            duration_ms=b1["duration_ms"],
            cached=b1["cached"],
        )
    except Exception as e:
        logger.error("Architecture batch failed: %s", e)
        out = outputs_by_section["architecture"]
        out.status = "error"
        out.error_msg = str(e)
        await db.commit()
        yield _event(type="section.error", section="architecture", status="error", error=str(e))

    await asyncio.sleep(0.05)

    # ── BATCH 2: Capacity + Data Model ───────────────────────────────────────
    await db.refresh(session)
    if session.status == "cancelled":
        yield _event(type="pipeline.error", error="Generation cancelled by user", error_code="CANCELLED")
        return

    batch2_sections = ["capacity", "data_model"]
    for sec in batch2_sections:
        out = _upsert_gen_output(outputs_by_section, sec, session_id)
        if sec not in outputs_by_section:
            db.add(out)
            outputs_by_section[sec] = out
    await db.flush()

    yield _event(type="section.start", section="capacity", status="started")
    yield _event(type="section.start", section="data_model", status="started")

    try:
        b2 = await _call_gemini_batch(
            system=CAPACITY_DATA_SYSTEM,
            user=capacity_data_user_prompt(context_block),
        )
        b2_data = b2["parsed"]

        # The batch prompt returns {"capacity": {...}, "data_model": {...}}
        # Fall back gracefully if Gemini doesn't wrap in the expected keys
        cap_payload = b2_data.get("capacity") or b2_data
        dm_payload = b2_data.get("data_model") or {}

        for sec, payload in [("capacity", cap_payload), ("data_model", dm_payload)]:
            out = outputs_by_section[sec]
            out.status = "complete"
            out.payload_json = payload
            out.tokens_used = b2["tokens_used"] // 2  # split evenly
            out.cached = b2["cached"]
            out.duration_ms = b2["duration_ms"] // 2
            out.error_msg = None

        await db.commit()
        total_tokens += b2["tokens_used"]
        total_duration_ms += b2["duration_ms"]

        yield _event(
            type="section.done",
            section="capacity",
            status="complete",
            payload=cap_payload,
            tokens_used=b2["tokens_used"] // 2,
            duration_ms=b2["duration_ms"] // 2,
            cached=b2["cached"],
        )
        yield _event(
            type="section.done",
            section="data_model",
            status="complete",
            payload=dm_payload,
            tokens_used=b2["tokens_used"] // 2,
            duration_ms=b2["duration_ms"] // 2,
            cached=b2["cached"],
        )
    except Exception as e:
        logger.error("Capacity+DataModel batch failed: %s", e)
        for sec in batch2_sections:
            out = outputs_by_section[sec]
            out.status = "error"
            out.error_msg = str(e)
        await db.commit()
        for sec in batch2_sections:
            yield _event(type="section.error", section=sec, status="error", error=str(e))

    await asyncio.sleep(0.05)

    # ── BATCH 3: API Design + Tech Stack ────────────────────────────────────
    await db.refresh(session)
    if session.status == "cancelled":
        yield _event(type="pipeline.error", error="Generation cancelled by user", error_code="CANCELLED")
        return

    batch3_sections = ["api_design", "stack"]
    for sec in batch3_sections:
        out = _upsert_gen_output(outputs_by_section, sec, session_id)
        if sec not in outputs_by_section:
            db.add(out)
            outputs_by_section[sec] = out
    await db.flush()

    yield _event(type="section.start", section="api_design", status="started")
    yield _event(type="section.start", section="stack", status="started")

    try:
        b3 = await _call_gemini_batch(
            system=API_STACK_SYSTEM,
            user=api_stack_user_prompt(context_block),
        )
        b3_data = b3["parsed"]

        api_payload = b3_data.get("api_design") or b3_data
        stack_payload = b3_data.get("tech_stack") or {}

        # Normalise tech_stack → layers key the frontend expects
        if "layers" not in stack_payload and isinstance(stack_payload, dict):
            # If gemini returned the whole object at top level, wrap it
            stack_payload = {"layers": [], **stack_payload}

        for sec, payload in [("api_design", api_payload), ("stack", stack_payload)]:
            out = outputs_by_section[sec]
            out.status = "complete"
            out.payload_json = payload
            out.tokens_used = b3["tokens_used"] // 2
            out.cached = b3["cached"]
            out.duration_ms = b3["duration_ms"] // 2
            out.error_msg = None

        await db.commit()
        total_tokens += b3["tokens_used"]
        total_duration_ms += b3["duration_ms"]

        yield _event(
            type="section.done",
            section="api_design",
            status="complete",
            payload=api_payload,
            tokens_used=b3["tokens_used"] // 2,
            duration_ms=b3["duration_ms"] // 2,
            cached=b3["cached"],
        )
        yield _event(
            type="section.done",
            section="stack",
            status="complete",
            payload=stack_payload,
            tokens_used=b3["tokens_used"] // 2,
            duration_ms=b3["duration_ms"] // 2,
            cached=b3["cached"],
        )
    except Exception as e:
        logger.error("API+Stack batch failed: %s", e)
        for sec in batch3_sections:
            out = outputs_by_section[sec]
            out.status = "error"
            out.error_msg = str(e)
        await db.commit()
        for sec in batch3_sections:
            yield _event(type="section.error", section=sec, status="error", error=str(e))

    # ── Pipeline done ────────────────────────────────────────────────────────
    await update_session_status(db, session_id, "complete")
    yield _event(
        type="pipeline.done",
        section="done",
        status="done",
        total_tokens=total_tokens,
        total_duration_ms=total_duration_ms,
    )


async def get_generation_status(db: AsyncSession, session_id: UUID) -> GenerationStatusResponse | None:
    session = await get_session(db, session_id)
    if not session:
        return None

    result = await db.execute(
        select(GenerationOutput).where(GenerationOutput.session_id == session_id)
    )
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
    """Flip status to 'cancelled' — the stream generator checks this before each batch."""
    session = await get_session(db, session_id)
    if not session:
        return False
    session.status = "cancelled"
    await db.commit()
    return True