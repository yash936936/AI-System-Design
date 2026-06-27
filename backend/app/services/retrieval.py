"""
Retrieval Service (Phase C)
============================
Retrieves reference designs from DB with in-memory caching.
Fast keyword-based relevance scoring.
"""
import logging
from typing import List, Dict, Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import FamousSystem

logger = logging.getLogger(__name__)


# ─── In-Memory Cache ──────────────────────────────────────────────────────────

_systems_cache: Dict[str, Dict[str, Any]] = {}
_systems_list_cache: List[Dict[str, Any]] = []
_cache_loaded: bool = False


async def load_systems_to_cache(db: AsyncSession) -> int:
    """
    Load all famous systems from DB into in-memory cache.
    Call once on startup for fast retrieval.
    
    Returns:
        Number of systems loaded
    """
    global _systems_cache, _systems_list_cache, _cache_loaded
    
    logger.info("📦 Loading famous systems into cache...")
    
    result = await db.execute(select(FamousSystem))
    systems = result.scalars().all()
    
    _systems_cache = {}
    _systems_list_cache = []
    
    for system in systems:
        system_dict = {
            "id": system.id,
            "name": system.name,
            "slug": system.slug,
            "description": system.description,
            "design_type": system.design_type,
            "key_components": system.key_components or [],
            "architecture_summary": system.architecture_summary,
            "tags": system.tags or [],
            "reference_url": system.reference_url,
        }
        _systems_cache[system.slug] = system_dict
        _systems_list_cache.append(system_dict)
    
    _cache_loaded = True
    logger.info(f"✅ Cached {len(_systems_cache)} famous systems")
    return len(_systems_cache)


def _ensure_cache_loaded() -> None:
    """Ensure cache is loaded (lazy load if needed)."""
    if not _cache_loaded:
        logger.warning("⚠️ Cache not loaded - retrieval may be slow")


def refresh_cache() -> None:
    """Clear cache to force reload on next access."""
    global _systems_cache, _systems_list_cache, _cache_loaded
    _systems_cache = {}
    _systems_list_cache = []
    _cache_loaded = False
    logger.info("🔄 Cache cleared")


# ─── Retrieval Functions ──────────────────────────────────────────────────────

def retrieve_designs(context: Dict[str, Any], prompt: str) -> List[Dict[str, Any]]:
    """
    Retrieve relevant reference designs based on context and prompt.
    Uses in-memory cache for O(1) lookups and fast scoring.
    
    Args:
        context: User requirements context
        prompt: Original user prompt
        
    Returns:
        List of up to 5 most relevant designs, sorted by score
    """
    _ensure_cache_loaded()
    
    if not _systems_list_cache:
        logger.warning("No systems in cache")
        return []
    
    prompt_lower = prompt.lower()
    
    # Combine all context text
    context_text = " ".join([
        str(v) for v in context.values()
        if v is not None and v != [] and v != {}
    ]).lower()
    
    combined_text = f"{prompt_lower} {context_text}"
    
    # Score each system
    scored_systems = []
    for system in _systems_list_cache:
        score = _calculate_relevance_score(system, combined_text)
        if score > 0.05:  # Lower threshold for more matches
            scored_systems.append({
                "id": system["id"],
                "name": system["name"],
                "type": system["design_type"],
                "score": round(score, 2),
                "components": system["key_components"],
                "source": system.get("reference_url"),
                "summary": system.get("architecture_summary"),
            })
    
    # Sort by score descending
    scored_systems.sort(key=lambda x: x["score"], reverse=True)
    
    # Return top 5
    logger.info(f"Retrieved {len(scored_systems[:5])} relevant designs from {len(_systems_list_cache)} total")
    return scored_systems[:5]


def _calculate_relevance_score(system: Dict[str, Any], text: str) -> float:
    """
    Calculate relevance score for a system.
    Returns float between 0.0 and 1.0.
    """
    score = 0.0
    
    # Check tags (highest weight)
    tags = system.get("tags", [])
    for tag in tags:
        if tag.lower() in text:
            score += 0.25
    
    # Check name (high weight)
    if system["name"].lower() in text:
        score += 0.4
    
    # Check slug
    if system["slug"].lower() in text:
        score += 0.3
    
    # Check description keywords (medium weight)
    desc_words = system.get("description", "").lower().split()
    matched_words = 0
    for word in desc_words:
        # Only count words > 4 chars to avoid noise
        if len(word) > 4 and word in text:
            matched_words += 1
    
    if desc_words:
        score += (matched_words / len(desc_words)) * 0.3
    
    # Check key components (lower weight)
    components = system.get("key_components", [])
    for comp in components:
        comp_lower = comp.lower()
        if comp_lower in text or any(word in text for word in comp_lower.split() if len(word) > 5):
            score += 0.05
    
    return min(score, 1.0)


def get_famous_system(slug: str) -> Optional[Dict[str, Any]]:
    """
    Get a specific famous system by slug.
    Uses in-memory cache for O(1) lookup.
    """
    _ensure_cache_loaded()
    return _systems_cache.get(slug)


def list_famous_systems() -> List[Dict[str, Any]]:
    """
    List all famous systems.
    Uses in-memory cache for fast retrieval.
    """
    _ensure_cache_loaded()
    return _systems_list_cache.copy()


def search_famous_systems(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search famous systems by query string.
    Returns top N matches sorted by relevance.
    """
    _ensure_cache_loaded()
    
    query_lower = query.lower()
    scored = []
    
    for system in _systems_list_cache:
        score = 0.0
        
        # Exact slug match
        if system["slug"] == query_lower:
            score = 1.0
        # Name contains query
        elif query_lower in system["name"].lower():
            score = 0.8
        # Description contains query
        elif query_lower in system.get("description", "").lower():
            score = 0.5
        # Tag match
        elif any(query_lower in tag.lower() for tag in system.get("tags", [])):
            score = 0.6
        
        if score > 0:
            scored.append((score, system))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    return [s[1] for s in scored[:limit]]


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics for monitoring."""
    return {
        "loaded": _cache_loaded,
        "total_systems": len(_systems_cache),
        "slugs": list(_systems_cache.keys()),
    }