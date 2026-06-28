import asyncio
import sys
import os
import datetime
import json

# Add parent directory to path so the script can find the 'app' folder
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import select
from app.core.config import get_settings
from app.core.gemini import gemini_embed
from app.db.models import FamousDesign
from app.db.session import AsyncSessionLocal
from app.services.vector_store import get_famous_designs_collection

settings = get_settings()

FAMOUS_DESIGNS = [
    {
        "system_name": "netflix",
        "title": "Netflix Video Streaming Architecture",
        "diagram_json": {"nodes": ["CDN", "Open Connect", "Zuul Gateway"]},
        "canonical_json": {"sections": ["Video Processing", "Recommendation Engine"]},
        "key_insights": ["Uses AWS S3 for raw storage", "Open Connect for last-mile CDN"],
        "sources": ["netflixtechblog.com"]
    },
    {
        "system_name": "twitter",
        "title": "Twitter Timeline Architecture",
        "diagram_json": {"nodes": ["Fanout Service", "Redis", "Manhattan DB"]},
        "canonical_json": {"sections": ["Push vs Pull", "Graph Services"]},
        "key_insights": ["Push model for normal users", "Pull model for celebrities"],
        "sources": ["blog.twitter.com/engineering"]
    },
    {
        # Carried over from the hardcoded dict that previously lived in
        # services/retrieval.py — that dict is gone now that retrieval
        # queries the vector store below, so this entry has to live here
        # instead or "uber" queries would silently lose their famous-design
        # fast path.
        "system_name": "uber",
        "title": "Uber Ride Matching",
        "diagram_json": {"nodes": ["Location Service", "Geo-Sharded Dispatch", "Pricing Service", "Trip Service"]},
        "canonical_json": {"sections": ["Dispatch", "Pricing", "Trip Lifecycle"]},
        "key_insights": [
            "Geohashing / H3 grid for efficient driver-rider proximity search",
            "Separate, eventually-consistent pricing computation to avoid blocking dispatch",
        ],
        "sources": ["eng.uber.com"]
    },
]


def _build_document_text(design_data: dict) -> str:
    """Flatten a famous-design record into a single text blob for embedding.
    Used as both the embedding input and the document Chroma returns at
    query time, so it needs to carry the information retrieval.py's RAG
    step actually wants to surface (components + the curated insights)."""
    parts = [design_data["title"]]
    nodes = design_data.get("diagram_json", {}).get("nodes", [])
    if nodes:
        parts.append("Components: " + ", ".join(nodes))
    sections = design_data.get("canonical_json", {}).get("sections", [])
    if sections:
        parts.append("Sections: " + ", ".join(sections))
    parts.extend(design_data.get("key_insights", []))
    return "\n".join(parts)


async def _index_chroma(design_data: dict) -> None:
    """Embed + upsert one design into the `famous_designs` Chroma
    collection. `upsert` (not `add`) keyed by system_name makes this safe
    to re-run — reruns update the existing vector instead of erroring or
    duplicating it."""
    if not settings.gemini_api_key:
        print(f"  [skip-vector] No GEMINI_API_KEY set — '{design_data['system_name']}' "
              f"was saved to SQL but not indexed in ChromaDB.")
        return

    document = _build_document_text(design_data)
    try:
        embedding = await gemini_embed(document, task_type="retrieval_document")
    except Exception as e:
        print(f"  [skip-vector] Embedding failed for '{design_data['system_name']}': {e}")
        return

    collection = get_famous_designs_collection()
    collection.upsert(
        ids=[design_data["system_name"]],
        embeddings=[embedding],
        documents=[document],
        metadatas=[{
            "system": design_data["system_name"],
            "title": design_data["title"],
        }],
    )
    print(f"  [vector-ok] Indexed '{design_data['system_name']}' in ChromaDB "
          f"({settings.chroma_persist_dir})")


async def seed():
    async with AsyncSessionLocal() as db:
        try:
            for design_data in FAMOUS_DESIGNS:
                # Check if it already exists to prevent duplicates
                result = await db.execute(
                    select(FamousDesign).where(FamousDesign.system_name == design_data["system_name"])
                )
                exists = result.scalar_one_or_none()

                if not exists:
                    print(f"+ Adding {design_data['system_name']} to SQL...")

                    # Create the object
                    design = FamousDesign(**design_data)

                    # FIX: Explicitly set last_updated to avoid NotNullViolation
                    design.last_updated = datetime.datetime.now(datetime.timezone.utc)

                    db.add(design)
                else:
                    print(f"= {design_data['system_name']} already in SQL, skipping insert.")

            await db.commit()
            print("Famous designs seeded successfully to the database!")
        except Exception as e:
            await db.rollback()
            print(f"Error seeding database: {e}")
            raise

        # Vector indexing runs after the SQL commit above, and is its own
        # idempotent upsert — re-running this script always refreshes the
        # ChromaDB vectors even when the SQL rows already existed (e.g.
        # after wiping ./chroma_data but not the SQL database).
        print("\nIndexing famous designs into ChromaDB...")
        for design_data in FAMOUS_DESIGNS:
            await _index_chroma(design_data)
        print("\nDone.")


if __name__ == "__main__":
    asyncio.run(seed())
