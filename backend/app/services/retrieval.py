import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.schemas import RetrievalResponse, RagChunk
from app.db.models import RagRetrieval
from app.services.session import get_session

logger = logging.getLogger(__name__)

async def retrieve_context(db: AsyncSession, session_id: UUID) -> RetrievalResponse:
    session = await get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")
    
    query = f"{session.prompt} {session.system_name or ''}"
    chunks = []
    max_score = 0.0
    famous_match = None
    
    famous_systems = ["twitter", "uber", "netflix", "whatsapp", "instagram"]
    if any(fs in query.lower() for fs in famous_systems):
        famous_match = next(fs for fs in famous_systems if fs in query.lower())
        chunks.append(RagChunk(
            id="famous_1", source="famous_designs", section="architecture",
            text=f"Canonical architecture for {famous_match}.", score=0.95
        ))
        max_score = 0.95
    else:
        chunks.append(RagChunk(
            id="mock_1", source="knowledge_base", section="general",
            text="General system design principles.", score=0.75
        ))
        max_score = 0.75
        
    db_retrieval = RagRetrieval(
        session_id=session_id, query=query,
        chunks_json=[c.model_dump() for c in chunks],
        max_score=max_score, used_web_fallback=False, famous_match=famous_match
    )
    db.add(db_retrieval)
    await db.flush()
    
    session.status = "retrieving"
    await db.flush()
    
    # FIX: Commit the transaction so the data is actually saved to PostgreSQL
    await db.commit()

    return RetrievalResponse(
        session_id=session_id, query=query, chunks=chunks,
        max_score=max_score, used_web_fallback=False, famous_design_matched=famous_match
    )