from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import (
    ClassifyRequest, ClassifyResponse,
    MCQTemplate,
    CreateSessionRequest, CreateSessionResponse,
    SessionResponse,
)
from app.services.classify import classify_prompt
from app.services.mcq_templates import get_mcq_template
from app.services.session import create_session, get_session, session_to_response

router = APIRouter(prefix="/api")


# ── Health ─────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "stage": 1}


# ── Phase A: Classify ──────────────────────────────────────────────────────────

@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    """
    Classify a prompt as LLD or HLD.
    1 Gemini call. Result is cached for 24h.
    """
    return await classify_prompt(request.prompt)


# ── Phase B: MCQ Templates ────────────────────────────────────────────────────

@router.get("/mcq/{design_type}", response_model=MCQTemplate)
async def get_mcq(design_type: str):
    """
    Return the static MCQ question set for HLD or LLD.
    Zero Gemini calls — pure static data.
    """
    if design_type.lower() not in ("hld", "lld"):
        raise HTTPException(status_code=422, detail="design_type must be 'hld' or 'lld'")
    return get_mcq_template(design_type)


# ── Session: Create ───────────────────────────────────────────────────────────

@router.post("/sessions", response_model=CreateSessionResponse, status_code=202)
async def create_new_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Create a session after MCQ is complete.
    Returns session_id + URLs for retrieval and streaming (Stage 3+).
    """
    session = await create_session(db, request)
    return CreateSessionResponse(
        session_id=session.id,
        retrieve_url=f"/api/sessions/{session.id}/retrieve",
        stream_url=f"/api/sessions/{session.id}/stream",
        status="queued",
    )


# ── Session: Get ──────────────────────────────────────────────────────────────

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_by_id(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_to_response(session)


# ── Placeholder routes (activated in later stages) ────────────────────────────

@router.get("/sessions/{session_id}/retrieve")
async def retrieve_placeholder(session_id: UUID):
    """Stage 3 — RAG retrieval. Not yet implemented."""
    return {"message": "RAG retrieval activates in Stage 3", "session_id": str(session_id)}


@router.get("/sessions/{session_id}/stream")
async def stream_placeholder(session_id: UUID):
    """Stage 4 — Generation SSE stream. Not yet implemented."""
    return {"message": "Generation pipeline activates in Stage 4", "session_id": str(session_id)}


@router.get("/famous/{system_name}")
async def famous_placeholder(system_name: str):
    """Stage 3 — Famous designs. Not yet implemented."""
    return {"message": "Famous designs activate in Stage 3", "system": system_name}
