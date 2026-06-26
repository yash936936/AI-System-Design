from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import (
    MCQResponse,
    MCQSubmitRequest,
    MCQSubmitResponse,
    VALID_DESIGN_TYPES,
)
from app.services.mcq import get_mcq, submit_mcq

router = APIRouter(prefix="/api", tags=["Phase B — MCQ"])


@router.get(
    "/sessions/{session_id}/mcq/{design_type}",
    response_model=MCQResponse,
)
async def get_questions(
    session_id: UUID,
    design_type: str = Path(..., description="HLD or LLD"),
    db: AsyncSession = Depends(get_db),
) -> MCQResponse:
    # FIX: validate design_type at route level before hitting the service
    design_type = design_type.upper()
    if design_type not in VALID_DESIGN_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"design_type must be one of {sorted(VALID_DESIGN_TYPES)}",
        )
    try:
        return await get_mcq(db, session_id, design_type)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/sessions/{session_id}/mcq",
    response_model=MCQSubmitResponse,
    status_code=200,
)
async def submit_answers(
    session_id: UUID,
    req: MCQSubmitRequest,
    db: AsyncSession = Depends(get_db),
) -> MCQSubmitResponse:
    try:
        return await submit_mcq(db, session_id, req)
    except ValueError as e:
        status = 409 if "status" in str(e) else 404
        raise HTTPException(status_code=status, detail=str(e))