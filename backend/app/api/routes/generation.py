"""
Phase D — Generation route.

Triggers all three generation sections in parallel (asyncio.gather),
persists results to the Generation table, and returns the full output.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
import asyncio

from app.core.gemini import gemini_generate_json, GeminiError
from app.db.models import Generation, Session as SessionModel, RagRetrieval
from app.db.session import get_db
from app.schemas.schemas import GenerationStatusResponse
from app.services.prompts import (
    ARCH_SYSTEM, arch_user_prompt,
    CAPACITY_DATA_SYSTEM, capacity_data_user_prompt,
    API_STACK_SYSTEM, api_stack_user_prompt,
    format_context,
)

router = APIRouter(prefix="/api", tags=["Phase D — Generation"])


async def _run_section(
    system_prompt: str,
    user_prompt: str,
) -> dict:
    """Call Gemini for one section. Returns dict or raises GeminiError."""
    return await gemini_generate_json(system_prompt, user_prompt)


@router.post(
    "/sessions/{session_id}/generate",
    response_model=GenerationStatusResponse,
    status_code=201,
)
async def generate(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> GenerationStatusResponse:
    # ── Load session ───────────────────────────────────────────────────────────
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.status not in ("mcq_complete", "retrieved"):
        raise HTTPException(
            status_code=409,
            detail=f"Session status is {session.status!r}. Must be 'mcq_complete' or 'retrieved'.",
        )

    # ── Load retrieval chunks ─────────────────────────────────────────────────
    ret_result = await db.execute(
        select(RagRetrieval).where(RagRetrieval.session_id == session_id)
    )
    retrieval = ret_result.scalar_one_or_none()
    chunks = retrieval.chunks_json if retrieval else []

    ctx = session.context_json or {}
    context_block = format_context(
        ctx=ctx,
        prompt=session.prompt,
        design_type=session.design_type or "HLD",
        chunks=chunks,
    )

    # ── Run all three sections in parallel ────────────────────────────────────
    arch_task     = _run_section(ARCH_SYSTEM,         arch_user_prompt(context_block, session.design_type or "HLD"))
    cap_data_task = _run_section(CAPACITY_DATA_SYSTEM, capacity_data_user_prompt(context_block))
    api_stack_task = _run_section(API_STACK_SYSTEM,    api_stack_user_prompt(context_block))

    results = await asyncio.gather(
        arch_task, cap_data_task, api_stack_task,
        return_exceptions=True,
    )

    arch_result, cap_data_result, api_stack_result = results

    errors = []
    for label, r in [("architecture", arch_result), ("capacity_and_data", cap_data_result), ("api_and_stack", api_stack_result)]:
        if isinstance(r, Exception):
            errors.append(f"{label}: {r}")

    # ── Persist ───────────────────────────────────────────────────────────────
    gen = Generation(
        session_id=session_id,
        architecture=arch_result     if not isinstance(arch_result, Exception)     else None,
        capacity_and_data=cap_data_result if not isinstance(cap_data_result, Exception) else None,
        api_and_stack=api_stack_result if not isinstance(api_stack_result, Exception) else None,
        status="complete" if not errors else "partial",
        error="; ".join(errors) if errors else None,
    )
    db.add(gen)
    try:
        session.status = "complete" if not errors else "partial"
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Generation already exists for this session.")

    return GenerationStatusResponse(
        session_id=session_id,
        status=gen.status,
        architecture=gen.architecture,
        capacity_and_data=gen.capacity_and_data,
        api_and_stack=gen.api_and_stack,
        error=gen.error,
    )