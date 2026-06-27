from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Session, GenerationOutput
from app.schemas.schemas import CreateSessionRequest, SessionResponse, SectionResultSchema

def _to_epoch_ms(dt) -> int:
    return int(dt.timestamp() * 1000) if dt else 0

async def create_session(db: AsyncSession, request: CreateSessionRequest) -> Session:
    db_session = Session(
        prompt=request.prompt,
        design_type=request.design_type,  # already validated as "HLD"/"LLD" by the schema
        # FIX: the previous version always wrote `{}` here, silently discarding
        # whatever the caller sent. The frontend builds this from the user's
        # MCQ answers (see ChatPanel.handleGenerate / useStore.nextMcqCategory) —
        # dropping it meant every generated design ignored the user's requirements.
        context_json=request.context or {},
        status="creating",
    )
    db.add(db_session)
    await db.commit()
    await db.refresh(db_session)
    return db_session

async def get_session(db: AsyncSession, session_id: UUID) -> Session | None:
    result = await db.execute(select(Session).where(Session.id == session_id))
    return result.scalar_one_or_none()

async def update_session_status(db: AsyncSession, session_id: UUID, status: str):
    session = await get_session(db, session_id)
    if session:
        session.status = status
        await db.commit()

async def session_to_response(db: AsyncSession, session: Session) -> SessionResponse:
    """Builds the response for GET /api/sessions/{id}, matching the
    frontend's GetSessionResponse contract field-for-field."""
    result = await db.execute(
        select(GenerationOutput).where(GenerationOutput.session_id == session.id)
    )
    outputs = result.scalars().all()

    sections: dict[str, SectionResultSchema] = {}
    total_tokens = 0
    total_duration_ms = 0
    for o in outputs:
        sections[o.section] = SectionResultSchema(
            section=o.section,
            status=o.status,
            payload=o.payload_json,
            tokens_used=o.tokens_used,
            duration_ms=o.duration_ms,
            cached=bool(o.cached),
            error=o.error_msg,
        )
        total_tokens += o.tokens_used or 0
        total_duration_ms += o.duration_ms or 0

    return SessionResponse(
        session_id=session.id,
        status=session.status,
        design_type=session.design_type,
        context=session.context_json or {},
        sections=sections,
        created_at=_to_epoch_ms(session.created_at),
        completed_at=_to_epoch_ms(session.completed_at) if session.completed_at else None,
        total_tokens=total_tokens,
        total_duration_ms=total_duration_ms,
    )