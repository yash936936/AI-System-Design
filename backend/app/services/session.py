"""
Session CRUD — creates and retrieves sessions from PostgreSQL.
In Stage 1, sessions are created after MCQ is complete.
"""
import json
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Session as SessionModel
from app.schemas.schemas import CreateSessionRequest, SessionResponse


async def create_session(
    db: AsyncSession,
    request: CreateSessionRequest,
    user_id: UUID | None = None,
) -> SessionModel:
    session = SessionModel(
        user_id=user_id,
        prompt=request.prompt,
        design_type=request.design_type,
        system_name=request.context.system_name,
        context_json=request.context.model_dump(exclude_none=False),
        status="clarifying",
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    return session


async def get_session(db: AsyncSession, session_id: UUID) -> SessionModel | None:
    result = await db.execute(select(SessionModel).where(SessionModel.id == session_id))
    return result.scalar_one_or_none()


async def update_session_status(db: AsyncSession, session_id: UUID, status: str) -> None:
    session = await get_session(db, session_id)
    if session:
        session.status = status
        if status == "complete":
            session.completed_at = datetime.utcnow()
        await db.flush()


def session_to_response(session: SessionModel) -> SessionResponse:
    return SessionResponse(
        id=session.id,
        prompt=session.prompt,
        design_type=session.design_type,
        system_name=session.system_name,
        context_json=session.context_json or {},
        status=session.status,
        created_at=session.created_at.isoformat(),
        completed_at=session.completed_at.isoformat() if session.completed_at else None,
    )
