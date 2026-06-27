import asyncio
import json
import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.gemini import gemini_generate
from app.db.models import GenerationOutput
from app.services.session import get_session, update_session_status
from app.schemas.schemas import SSEEvent

logger = logging.getLogger(__name__)
SECTIONS = ["architecture", "capacity", "data_model", "api_design", "stack"]

async def generate_section(session, section: str) -> SSEEvent:
    prompt = f"Generate the '{section}' section for: {session.system_name or session.prompt}. Context: {json.dumps(session.context_json)}"
    try:
        result = await gemini_generate(prompt=prompt, system_prompt="Output ONLY valid JSON.", json_mode=True)
        return SSEEvent(
            section=section, status="complete", payload=result.get("parsed", {}),
            tokens_used=result.get("tokens_in", 0) + result.get("tokens_out", 0),
            cached=result.get("cached", False), duration_ms=result.get("duration_ms", 0)
        )
    except Exception as e:
        return SSEEvent(section=section, status="error", error=str(e))

async def generate_design_stream(db: AsyncSession, session_id: UUID):
    session = await get_session(db, session_id)
    if not session: 
        raise ValueError("Session not found")
        
    await update_session_status(db, session_id, "generating")
    
    yield f"data: {json.dumps({'section': 'all', 'status': 'started'})}\n\n"
    
    for section in SECTIONS:
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
        
        yield f"data: {json.dumps({'section': section, 'status': 'started'})}\n\n"
        
        event = await generate_section(session, section)
        
        gen_output.status = event.status
        gen_output.tokens_used = event.tokens_used
        gen_output.cached = event.cached
        gen_output.duration_ms = event.duration_ms
        gen_output.error_msg = event.error
        await db.flush()
        
        yield f"data: {json.dumps(event.model_dump())}\n\n"
        await asyncio.sleep(0.5)
        
    await update_session_status(db, session_id, "complete")
    yield f"data: {json.dumps({'section': 'all', 'status': 'done'})}\n\n"