"""
Phase C — Famous Systems Route
================================
GET /api/famous
GET /api/famous/{slug}
"""
import logging
from typing import List

from fastapi import APIRouter, HTTPException, status

from app.schemas.schemas import FamousSystemSchema, ErrorResponse
from app.services.retrieval import list_famous_systems, get_famous_system

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Phase C — Famous Systems"])


@router.get(
    "/famous",
    response_model=List[FamousSystemSchema],
    summary="List famous systems",
    description="Returns all famous system designs available as reference.",
)
async def list_famous() -> List[FamousSystemSchema]:
    """List all famous systems."""
    systems = list_famous_systems()
    return [FamousSystemSchema(**s) for s in systems]


@router.get(
    "/famous/{slug}",
    response_model=FamousSystemSchema,
    responses={
        404: {"model": ErrorResponse},
    },
    summary="Get famous system",
    description="Returns a specific famous system design by slug.",
)
async def get_famous(slug: str) -> FamousSystemSchema:
    """Get a specific famous system by slug."""
    system = get_famous_system(slug)
    if not system:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Famous system not found: {slug}",
                "error_code": "FAMOUS_NOT_FOUND",
            },
        )
    return FamousSystemSchema(**system)