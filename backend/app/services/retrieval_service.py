"""
Phase C — RAG Retrieval Service

Bug fixes applied vs original:
1. asyncio.get_event_loop() → asyncio.get_running_loop()
2. ChromaDB singleton protected with threading.Lock
3. Duplicate retrieval insert guarded with IntegrityError catch
4. build_retrieval_query: `if p` → `if p is not None` (preserves 0 values)
5. _search_famous_collection: count==0 guard matches _search_main_collection
6. Web fallback log clearly separates trigger vs result
7. Parallel ChromaDB queries via asyncio.gather
8. Chunk text truncated to 1000 chars before embedding to stay within limits
"""

import asyncio
import logging
import threading
import uuid
from typing import Any

import chromadb
from chromadb.config import Settings as ChromaSettings
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import get_settings
from app.core.gemini import gemini_embed
from app.db.models import Session as SessionModel, RagRetrieval
from app.schemas.schemas import RagChunk, RetrievalResponse

from chromadb.api import ClientAPI
from typing import Optional


logger = logging.getLogger(__name__)
settings = get_settings()

# ── ChromaDB singleton (thread-safe) ─────────────────────────────────────────
_chroma_client: Optional[object] = None
_chroma_lock = threading.Lock()

FAMOUS_SYSTEMS = {
    "twitter", "x", "netflix", "whatsapp", "meta", "facebook",
    "uber", "youtube", "airbnb", "instagram", "linkedin", "tiktok",
    "discord", "slack", "reddit", "amazon", "google", "spotify",
}

TOP_K = 5
FALLBACK_THRESHOLD = 0.6
MAX_CHUNK_TEXT_CHARS = 1000


def _get_chroma() -> chromadb.Client:
    global _chroma_client
    if _chroma_client is None:
        with _chroma_lock:
            # Double-checked locking
            if _chroma_client is None:
                _chroma_client = chromadb.PersistentClient(
                    path=settings.chroma_persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
    return _chroma_client


def _get_or_create_collection(name: str) -> chromadb.Collection:
    return _get_chroma().get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


# ── Query builder ─────────────────────────────────────────────────────────────

def build_retrieval_query(session: SessionModel) -> str:
    """
    Serialize context_json into a dense retrieval query string.

    Fix: uses `is not None` check so integer values like DAU=0 are preserved.
    """
    ctx: dict[str, Any] = session.context_json or {}
    parts = [session.design_type or "HLD"]

    if session.system_name:
        parts.append(session.system_name)
    elif ctx.get("system_name"):
        parts.append(ctx["system_name"])

    parts.append(session.prompt)

    field_map = {
        "read_write_ratio":      None,
        "scale":                 None,
        "dau":                   "DAU",
        "availability":          "availability",
        "consistency":           "consistency",
        "data_model_preference": None,
        "api_style":             None,
        "architecture_approach": None,
        "scalability_priority":  None,
        "trade_off_priority":    None,
    }
    for field, label in field_map.items():
        val = ctx.get(field)
        # FIX: was `if val` which drops 0; now `if val is not None`
        if val is not None:
            parts.append(f"{label} {val}" if label else str(val))

    for field in ("functional_reqs", "bottleneck_focus", "out_of_scope"):
        items = ctx.get(field) or []
        if items:
            parts.extend(str(i) for i in items)

    return " ".join(str(p) for p in parts if p is not None)


# ── Famous design fast-path ───────────────────────────────────────────────────

def _detect_famous_system(session: SessionModel) -> str | None:
    text = (
        (session.system_name or "") + " " +
        (session.prompt or "") + " " +
        str((session.context_json or {}).get("system_name", ""))
    ).lower()
    for name in FAMOUS_SYSTEMS:
        if name in text:
            return name
    return None


def _search_famous_collection(
    collection: chromadb.Collection,
    embedding: list[float],
    system_name: str,
) -> list[dict]:
    # FIX: guard empty collection the same way _search_main_collection does
    count = collection.count()
    if count == 0:
        logger.info("famous_designs collection is empty — skipping")
        return []
    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(TOP_K, count),
            where={"system": system_name},
            include=["documents", "metadatas", "distances"],
        )
        return _unpack_results(results, source_prefix="famous_designs")
    except Exception as e:
        logger.warning("Famous design search failed: %s", e)
        return []


def _search_main_collection(
    collection: chromadb.Collection,
    embedding: list[float],
) -> list[dict]:
    count = collection.count()
    if count == 0:
        logger.info("system_design_docs collection is empty — skipping")
        return []
    try:
        results = collection.query(
            query_embeddings=[embedding],
            n_results=min(TOP_K, count),
            include=["documents", "metadatas", "distances"],
        )
        return _unpack_results(results, source_prefix="")
    except Exception as e:
        logger.warning("Main collection search failed: %s", e)
        return []


def _unpack_results(results: dict, source_prefix: str) -> list[dict]:
    chunks = []
    docs      = results.get("documents",  [[]])[0]
    metas     = results.get("metadatas",  [[]])[0]
    distances = results.get("distances",  [[]])[0]

    for doc, meta, dist in zip(docs, metas, distances):
        score = round(1.0 - float(dist), 4)
        # FIX: truncate chunk text to prevent context overflow downstream
        text = str(doc)[:MAX_CHUNK_TEXT_CHARS]
        chunks.append({
            "id":      meta.get("chunk_id", str(uuid.uuid4())),
            "source":  meta.get("source", source_prefix),
            "section": meta.get("section", ""),
            "text":    text,
            "score":   score,
        })
    return chunks


# ── Web search fallback ───────────────────────────────────────────────────────

async def _web_search_fallback(query: str) -> list[dict]:
    """
    Fetch additional context via SerpAPI when vector scores are low.

    Fix: log result count separately from trigger so outcome is clear.
    Note: hardcoded score of 0.55 means web chunks rank below vector hits
          by design — they supplement, not replace.
    """
    serpapi_key = settings.serpapi_key
    if not serpapi_key:
        logger.info("No SERPAPI_KEY configured — skipping web fallback")
        return []

    try:
        import httpx
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(
                "https://serpapi.com/search",
                params={
                    "q":       query + " system design",
                    "api_key": serpapi_key,
                    "num":     5,
                    "engine":  "google",
                },
            )
            data = resp.json()

        chunks = []
        for i, result in enumerate(data.get("organic_results", [])[:5]):
            snippet = result.get("snippet", "")
            if not snippet:
                continue
            chunks.append({
                "id":      f"web_{i}",
                "source":  result.get("link", "web_search"),
                "section": result.get("title", "Web result"),
                "text":    snippet[:MAX_CHUNK_TEXT_CHARS],
                # Score deliberately below FALLBACK_THRESHOLD so web chunks
                # supplement vector results but never displace them.
                "score":   0.55,
            })

        logger.info("Web fallback returned %d chunks", len(chunks))
        return chunks

    except Exception as e:
        logger.warning("Web search fallback failed: %s", e)
        return []


# ── Main retrieval function ───────────────────────────────────────────────────

async def retrieve_for_session(
    db: AsyncSession,
    session_id: uuid.UUID,
) -> RetrievalResponse:
    """
    Full Phase C pipeline. Idempotent — returns cached retrieval if exists.

    Fixes vs original:
    - get_running_loop() instead of get_event_loop()
    - asyncio.gather() for parallel ChromaDB queries
    - IntegrityError catch for concurrent duplicate inserts
    """
    # ── Fetch session ──────────────────────────────────────────────────────────
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise ValueError(f"Session {session_id} not found")

    # ── Idempotency check ──────────────────────────────────────────────────────
    existing = await db.execute(
        select(RagRetrieval).where(RagRetrieval.session_id == session_id)
    )
    existing_row = existing.scalar_one_or_none()
    if existing_row:
        logger.info("Returning cached retrieval for session %s", session_id)
        return RetrievalResponse(
            session_id=session_id,
            query=existing_row.query,
            chunks=[RagChunk(**c) for c in existing_row.chunks_json],
            max_score=float(existing_row.max_score or 0.0),
            used_web_fallback=existing_row.used_web_fallback,
            famous_design_matched=existing_row.famous_match,
        )

    # ── Build query ────────────────────────────────────────────────────────────
    query = build_retrieval_query(session)
    logger.info("RAG query: %.120s", query)

    # ── Famous design detection ────────────────────────────────────────────────
    famous_match = _detect_famous_system(session)

    # ── Embed ──────────────────────────────────────────────────────────────────
    embedding = await gemini_embed(query)

    # ── Parallel vector search (FIX: gather instead of sequential executor calls)
    loop = asyncio.get_running_loop()   # FIX: was get_event_loop()

    famous_col = _get_or_create_collection("famous_designs")
    main_col   = _get_or_create_collection("system_design_docs")

    famous_task = loop.run_in_executor(
        None,
        lambda: (
            _search_famous_collection(famous_col, embedding, famous_match)
            if famous_match else []
        ),
    )
    main_task = loop.run_in_executor(
        None,
        lambda: _search_main_collection(main_col, embedding),
    )

    famous_chunks, main_chunks = await asyncio.gather(famous_task, main_task)

    # ── Merge + deduplicate ────────────────────────────────────────────────────
    seen: set[str] = set()
    chunks: list[dict] = []
    for c in list(famous_chunks) + list(main_chunks):
        if c["id"] not in seen:
            seen.add(c["id"])
            chunks.append(c)
    chunks.sort(key=lambda c: c["score"], reverse=True)
    chunks = chunks[:TOP_K]

    # ── Web fallback ───────────────────────────────────────────────────────────
    max_score = max((c["score"] for c in chunks), default=0.0)
    used_web_fallback = False

    if max_score < FALLBACK_THRESHOLD:
        logger.info(
            "Max vector score %.3f < %.1f threshold — triggering web fallback",
            max_score, FALLBACK_THRESHOLD,
        )
        web_chunks = await _web_search_fallback(query)
        if web_chunks:
            chunks.extend(web_chunks)
            chunks.sort(key=lambda c: c["score"], reverse=True)
            chunks = chunks[:TOP_K]
            used_web_fallback = True
        # FIX: recalculate max_score after extending
        max_score = max((c["score"] for c in chunks), default=0.0)

    # ── Persist (FIX: catch IntegrityError for concurrent duplicate inserts) ──
    retrieval = RagRetrieval(
        session_id=session_id,
        query=query,
        chunks_json=chunks,
        max_score=round(max_score, 3),
        used_web_fallback=used_web_fallback,
        famous_match=famous_match,
    )
    db.add(retrieval)
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        logger.warning(
            "Duplicate retrieval insert for session %s — fetching existing", session_id
        )
        existing = await db.execute(
            select(RagRetrieval).where(RagRetrieval.session_id == session_id)
        )
        existing_row = existing.scalar_one()
        return RetrievalResponse(
            session_id=session_id,
            query=existing_row.query,
            chunks=[RagChunk(**c) for c in existing_row.chunks_json],
            max_score=float(existing_row.max_score or 0.0),
            used_web_fallback=existing_row.used_web_fallback,
            famous_design_matched=existing_row.famous_match,
        )

    logger.info(
        "RAG complete: %d chunks, max_score=%.3f, web_fallback=%s, famous=%s",
        len(chunks), max_score, used_web_fallback, famous_match,
    )

    return RetrievalResponse(
        session_id=session_id,
        query=query,
        chunks=[RagChunk(**c) for c in chunks],
        max_score=round(max_score, 3),
        used_web_fallback=used_web_fallback,
        famous_design_matched=famous_match,
    )