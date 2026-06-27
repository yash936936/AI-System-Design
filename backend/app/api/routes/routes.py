import time
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import (
    CreateSessionRequest, CreateSessionResponse, SessionResponse, GenerationStatusResponse,
)
from app.services.session import create_session, get_session, session_to_response
from app.services.generation import get_generation_status, cancel_generation

router = APIRouter(prefix="/api", tags=["Sessions"])

@router.post("/sessions", response_model=CreateSessionResponse, status_code=202)
async def create_new_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
):
    session = await create_session(db, request)
    return CreateSessionResponse(
        session_id=session.id,
        retrieve_url=f"/api/sessions/{session.id}/retrieve",
        stream_url=f"/api/sessions/{session.id}/stream",
        status=session.status,
        created_at=int(session.created_at.timestamp() * 1000),
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

# These two were called by frontend/src/lib/api.ts (getGenerationStatus,
# cancelGeneration) but had no matching backend route at all — every call
# 404'd. They aren't wired into any UI component yet, but are needed so the
# existing client code doesn't break if/when it's used.
@router.get("/sessions/{session_id}/generation/status", response_model=GenerationStatusResponse)
async def generation_status(session_id: UUID, db: AsyncSession = Depends(get_db)):
    status = await get_generation_status(db, session_id)
    if not status:
        raise HTTPException(status_code=404, detail="Session not found")
    return status

@router.post("/sessions/{session_id}/generation/cancel", status_code=204)
async def generation_cancel(session_id: UUID, db: AsyncSession = Depends(get_db)):
    ok = await cancel_generation(db, session_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Session not found")
    return None