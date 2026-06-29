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
from app.services.retrieval_service import retrieve_for_session

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
#
# BUG FIX (this was the actual broken wiring in the repo): this module used to
# contain its own, separate retrieve_context() implementation — one that:
#   1. Never checked for an existing RagRetrieval row first, so every GET to
#      /api/sessions/{id}/retrieve inserted a brand-new row. There was no
#      caching/idempotency on this path at all, despite app/services/
#      retrieval_service.py implementing exactly that (idempotency check,
#      SerpAPI web fallback, parallel search of BOTH Chroma collections).
#   2. Never called the SerpAPI web-search fallback — the code for it exists
#      in retrieval_service.py but was never invoked from anywhere, so it was
#      fully dead.
#   3. Only ever searched the `famous_designs` collection, never the main
#      `system_design_docs` collection.
#   4. Fell back to a hardcoded fake chunk ("General system design
#      principles.") whenever nothing was found, instead of real fallback
#      content.
#
# Fix: delegate to retrieve_for_session(), which already implements all of
# the above correctly. This file keeps list_famous_systems/get_famous_system
# (still used by app/api/routes/famous.py) plus _search_famous_designs as a
# small helper retained for any direct callers, but the route-facing entry
# point now actually uses the real pipeline.
async def retrieve_context(db: AsyncSession, session_id: UUID) -> RetrievalResponse:
    session = await get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")

    response = await retrieve_for_session(db, session_id)

    # Status tracking only (not load-bearing for downstream logic, but kept
    # consistent with the rest of the session lifecycle).
    if session.status not in ("generating", "complete"):
        session.status = "retrieving"
        await db.commit()

    return response