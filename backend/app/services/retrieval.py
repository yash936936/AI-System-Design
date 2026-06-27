import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.schemas import RetrievalResponse, RagChunk
from app.db.models import RagRetrieval
from app.services.session import get_session

logger = logging.getLogger(__name__)

# ── Famous systems mock catalog ─────────────────────────────────────────────────
# `famous.py` imports `list_famous_systems` / `get_famous_system` from this
# module, but neither function existed here before — every call to
# GET /api/famous or /api/famous/{slug} raised an ImportError at import time,
# which means the whole app failed to start (main.py imports famous.py's
# router transitively). Defining them here (and registering the router in
# main.py — see below) fixes both the ImportError and the missing routes.
_FAMOUS_SYSTEMS: dict[str, dict] = {
    "twitter": {
        "system_name": "twitter", "title": "Twitter / X Timeline & Fan-out",
        "canonical_json": {
            "components": ["Tweet Service", "Fan-out Service", "Timeline Cache", "Graph Service"],
        },
        "diagram_json": {},
        "key_insights": [
            "Fan-out-on-write for most users; fan-out-on-read (pull) for celebrities with huge follower counts",
            "Redis-backed timeline cache to avoid recomputing feeds on every read",
        ],
        "sources": ["https://systeminterview.com/design-twitter.php"],
        "last_updated": "2024-01-01T00:00:00Z",
    },
    "netflix": {
        "system_name": "netflix", "title": "Netflix Video Streaming",
        "canonical_json": {
            "components": ["Open Connect CDN", "Encoding Pipeline", "Metadata Service", "Recommendation Service"],
        },
        "diagram_json": {},
        "key_insights": [
            "Open Connect: Netflix's own CDN, deployed inside ISP networks",
            "Pre-transcodes video into many bitrate/codec variants for adaptive streaming",
        ],
        "sources": ["https://netflixtechblog.com"],
        "last_updated": "2024-01-01T00:00:00Z",
    },
    "uber": {
        "system_name": "uber", "title": "Uber Ride Matching",
        "canonical_json": {
            "components": ["Location Service", "Geo-Sharded Dispatch", "Pricing Service", "Trip Service"],
        },
        "diagram_json": {},
        "key_insights": [
            "Geohashing / H3 grid for efficient driver-rider proximity search",
            "Separate, eventually-consistent pricing computation to avoid blocking dispatch",
        ],
        "sources": ["https://eng.uber.com"],
        "last_updated": "2024-01-01T00:00:00Z",
    },
}

def list_famous_systems() -> list[dict]:
    return list(_FAMOUS_SYSTEMS.values())

def get_famous_system(slug: str) -> dict | None:
    return _FAMOUS_SYSTEMS.get(slug.lower())

# ── Retrieval (Phase C) ──────────────────────────────────────────────────────────
async def retrieve_context(db: AsyncSession, session_id: UUID) -> RetrievalResponse:
    session = await get_session(db, session_id)
    if not session:
        raise ValueError("Session not found")

    query = f"{session.prompt} {session.system_name or ''}"
    chunks: list[RagChunk] = []
    max_score = 0.0
    famous_match = None

    query_lower = query.lower()
    for slug in _FAMOUS_SYSTEMS:
        if slug in query_lower:
            famous_match = slug
            chunks.append(RagChunk(
                id="famous_1", source="famous_designs", section="architecture",
                text=f"Canonical architecture for {famous_match}.", score=0.95
            ))
            max_score = 0.95
            break

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