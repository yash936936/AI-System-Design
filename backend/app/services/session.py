from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Session
from app.schemas.schemas import CreateSessionRequest, SessionResponse

async def create_session(db: AsyncSession, request: CreateSessionRequest) -> Session:
    db_session = Session(
        prompt=request.prompt,
        system_name=request.system_name,
        design_type=request.design_type,
        context_json={},  # Explicitly pass empty dict for JSONB column
        status="queued"
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_session(db: AsyncSession, session_id: UUID) -> Session | None:
    # session_id is already a native UUID object, no need to cast to string
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()

async def update_session_status(db: AsyncSession, session_id: UUID, status: str):
    session = await get_session(db, session_id)
    if session:
        session.status = status
        await db.commit()

def session_to_response(session: Session) -> SessionResponse:
    return SessionResponse(
        id=session.id, # Pydantic automatically handles native UUID objects
        prompt=session.prompt,
        system_name=session.system_name,
        design_type=session.design_type,
        status=session.status,
        created_at=session.created_at
    )