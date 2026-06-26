"""
Phase B — MCQ routes.

NOTE — Two MCQ systems exist in this codebase:
  1. GET /api/mcq/{design_type}  (in mcq_templates.py / routes.py)
     - Static, DB-unaware template. Schema: MCQCategory / MCQTemplate.
     - Intended for frontend rendering of the question UI before a session exists.
  2. GET /api/sessions/{id}/mcq/{design_type}  (this file → services/mcq.py)
     - DB-aware, session-scoped. Schema: MCQQuestion / MCQResponse.
     - Used to fetch questions tied to an existing session and to submit answers.

These have DIFFERENT response shapes (categories vs questions, different option
fields). The frontend must call the correct endpoint for each stage of the flow.
Do NOT mix them up — doing so will cause runtime schema errors.
"""

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