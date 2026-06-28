"""
ChromaDB vector store — a single shared client + collection helper.

Used by:
  - scripts/ingest_famous_designs.py   (writes: embed + upsert famous designs)
  - app/services/retrieval.py          (reads: semantic search at RAG time)

Uses a local `PersistentClient` (no external Chroma server required) so the
vector store follows the same "zero-config dev" philosophy as the SQLite
`database_url` default in core/config.py — nothing in this repo documents a
Chroma server actually being run anywhere.
"""
import logging
import threading
from typing import Optional

import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FAMOUS_DESIGNS_COLLECTION = "famous_designs"

_client: Optional["chromadb.ClientAPI"] = None
_lock = threading.Lock()


def get_chroma_client() -> "chromadb.ClientAPI":
    """Thread-safe singleton — avoids re-opening the on-disk Chroma store
    (and the file-lock contention that comes with that) on every call."""
    global _client
    if _client is None:
        with _lock:
            if _client is None:  # double-checked locking
                _client = chromadb.PersistentClient(
                    path=settings.chroma_persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False),
                )
    return _client


def get_famous_designs_collection():
    return get_chroma_client().get_or_create_collection(
        name=FAMOUS_DESIGNS_COLLECTION,
        metadata={"hnsw:space": "cosine"},
    )
