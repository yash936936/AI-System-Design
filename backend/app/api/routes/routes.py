from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import (
    CreateSessionRequest, CreateSessionResponse, SessionResponse,
)
from app.services.session import create_session, get_session, session_to_response

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
        status="queued",
    )

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_by_id(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_to_response(session)