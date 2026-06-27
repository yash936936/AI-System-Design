from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import (
    CreateSessionRequest, CreateSessionResponse,
    SessionResponse,
)
from app.services.session import create_session, get_session, session_to_response, _to_epoch_ms

router = APIRouter(prefix="/api", tags=["Sessions"])

@router.get("/health")
async def health():
    return {"status": "ok", "stage": 1}

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
        created_at=_to_epoch_ms(session.created_at)
    )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_by_id(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return await session_to_response(db, session)