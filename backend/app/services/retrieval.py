import asyncio
import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.gemini import gemini_embed
from app.schemas.schemas import RetrievalResponse, RagChunk
from app.db.models import RagRetrieval, FamousDesign
from app.services.session import get_session
from app.services.vector_store import get_famous_designs_collection

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Famous systems catalog ───────────────────────────────────────────────────
# Previously this module kept a hardcoded `_FAMOUS_SYSTEMS` dict (twitter /
# netflix / uber only) and matched it against the query with a plain
# substring check. Famous-design records now live in the `famous_designs`
# SQL table (see db/models.py — populated by scripts/ingest_famous_designs.py)
# for the structured GET /api/famous routes below, and in the Chroma
# `famous_designs` collection (same ingest script) for the semantic-search
# fast path inside retrieve_context(). Run the ingest script before relying
# on either — both list_famous_systems() and the vector search degrade
# gracefully (empty list / no famous match) if it hasn't been run yet.

async def list_famous_systems(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(FamousDesign))
    rows = result.scalars().all()
    return [_design_to_dict(r) for r in rows]

async def get_famous_system(db: AsyncSession, slug: str) -> dict | None:
    result = await db.execute(
        select(FamousDesign).where(FamousDesign.system_name == slug.lower().strip())
    )
    row = result.scalar_one_or_none()
    return _design_to_dict(row) if row else None

def _design_to_dict(row: FamousDesign) -> dict:
    return {
        "system_name": row.system_name,
        "title": row.title,
        "diagram_json": row.diagram_json or {},
        "canonical_json": row.canonical_json or {},
        "key_insights": row.key_insights or [],
        "sources": row.sources or [],
        "last_updated": row.last_updated,
    }

# ── Vector search ─────────────────────────────────────────────────────────────

_FAMOUS_MATCH_THRESHOLD = 0.55  # cosine similarity below this isn't a confident match

async def _search_famous_designs(query: str) -> tuple[RagChunk | None, str | None]:
    """Embed `query` and search the Chroma `famous_designs` collection for
    a matching famous system. Returns (chunk, system_name) or (None, None)
    if nothing confident was found (empty collection, low score, or any
    failure along the way — this must never be allowed to break retrieval
    for everyone just because a vector lookup had a bad day)."""
    if not settings.gemini_api_key:
        logger.info("GEMINI_API_KEY not set — skipping vector search for famous designs")
        return None, None

    try:
        embedding = await gemini_embed(query, task_type="retrieval_query")
        collection = get_famous_designs_collection()

        loop = asyncio.get_running_loop()
        count = await loop.run_in_executor(None, collection.count)
        if count == 0:
            logger.info("famous_designs collection is empty — run scripts/ingest_famous_designs.py")
            return None, None

        results = await loop.run_in_executor(
            None,
            lambda: collection.query(
                query_embeddings=[embedding],
                n_results=1,
                include=["documents", "metadatas", "distances"],
            ),
        )
    except Exception as e:
        logger.warning("Famous-design vector search failed, continuing without it: %s", e)
        return None, None

    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]
    if not docs:
        return None, None

    score = round(1.0 - float(distances[0]), 4)  # cosine distance -> similarity
    if score < _FAMOUS_MATCH_THRESHOLD:
        logger.info("Best famous-design match scored %.3f, below threshold — ignoring", score)
        return None, None

    system_name = metas[0].get("system", "")
    chunk = RagChunk(
        id=f"famous_{system_name}",
        source="famous_designs",
        section="architecture",
        text=str(docs[0])[:1000],
        score=score,
    )
    return chunk, system_name

# ── Retrieval (Phase C) ──────────────────────────────────────────────────────────
async def retrieve_context(db: AsyncSession, session_id: UUID) -> RetrievalResponse:
    session = await get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")

    query = f"{session.prompt} {session.system_name or ''}"
    chunks: list[RagChunk] = []
    max_score = 0.0

    famous_chunk, famous_match = await _search_famous_designs(query)
    if famous_chunk:
        chunks.append(famous_chunk)
        max_score = famous_chunk.score

    if not chunks:
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
    await db.commit()

    return RetrievalResponse(
        session_id=session_id, query=query, chunks=chunks,
        max_score=max_score, used_web_fallback=False, famous_design_matched=famous_match
    )
