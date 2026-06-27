"""
Phase B — MCQ Route
====================
GET /api/mcq/{design_type}
"""
import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.schemas import MCQTemplate, ErrorResponse
from app.services.mcq_templates import get_template

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Phase B — MCQ"])


@router.get(
    "/mcq/{design_type}",
    response_model=MCQTemplate,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
    summary="Get MCQ template",
    description="Returns the MCQ template for a specific design type (HLD or LLD).",
)
async def get_mcq_template(design_type: str) -> MCQTemplate:
    """
    Get MCQ template for a design type.
    
    Args:
        design_type: 'hld' or 'lld' (case-insensitive)
        
    Returns:
        MCQ template with categories and questions
    """
    try:
        template = get_template(design_type.upper())
        return MCQTemplate(**template)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Invalid design type: {design_type}",
                "error_code": "INVALID_DESIGN_TYPE",
                "detail": str(e),
            },
        )
    except Exception as e:
        logger.exception("Failed to get MCQ template")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to get MCQ template",
                "error_code": "TEMPLATE_FETCH_FAILED",
                "detail": str(e),
            },
        )