"""
Phase A — Classification Route
================================
POST /api/classify
"""
import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.schemas import ClassifyRequest, ClassifyResponse, ErrorResponse
from app.services.classify import classify_prompt

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Phase A — Classification"])


@router.post(
    "/classify",
    response_model=ClassifyResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Classify a design prompt",
    description="Determines if a prompt requires HLD or LLD design approach.",
)
async def classify(request: ClassifyRequest) -> ClassifyResponse:
    """
    Classify a prompt as HLD or LLD.
    
    Uses Gemini AI to analyze the prompt and determine the design type.
    Returns classification result with confidence score and reasoning.
    """
    try:
        result = await classify_prompt(request.prompt)
        return ClassifyResponse(**result)
    except Exception as e:
        logger.exception("Classification failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Classification failed",
                "error_code": "CLASSIFICATION_FAILED",
                "detail": str(e),
            },
        )