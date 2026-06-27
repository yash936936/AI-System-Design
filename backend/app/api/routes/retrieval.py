"""
Phase C — Retrieval Route
==========================
POST /api/sessions
GET /api/sessions/{session_id}
"""
import logging
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.db.models import Session, GenerationOutput
from app.schemas.schemas import (
    CreateSessionRequest,
    CreateSessionResponse,
    SessionResponse,
    SectionOutput,
    ErrorResponse,
)
from app.services.retrieval import retrieve_designs

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Phase C — Retrieval"])


@router.post(
    "/sessions",
    response_model=CreateSessionResponse,
    responses={
        400: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Create a design session",
    description="Creates a new design session and retrieves relevant reference designs.",
)
async def create_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db),
) -> CreateSessionResponse:
    """
    Create a new design session.
    
    Steps:
    1. Create session record in DB
    2. Retrieve relevant reference designs
    3. Return session ID and URLs
    """
    try:
        # Create session
        session = Session(
            prompt=request.prompt,
            design_type=request.design_type,
            status="creating",
            context_json=request.context.model_dump(),
        )
        db.add(session)
        await db.flush()
        await db.commit()
        
        # Retrieve reference designs
        context_dict = request.context.model_dump()
        retrieved = retrieve_designs(context_dict, request.prompt)
        
        return CreateSessionResponse(
            session_id=session.id,
            retrieve_url=f"/api/sessions/{session.id}",
            stream_url=f"/api/sessions/{session.id}/stream",
            status=session.status,
            design_type=session.design_type,
            retrieved_designs=retrieved,
            created_at=time.time(),
        )
        
    except Exception as e:
        await db.rollback()
        logger.exception("Failed to create session")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "Failed to create session",
                "error_code": "SESSION_CREATE_FAILED",
                "detail": str(e),
            },
        )


@router.get(
    "/sessions/{session_id}",
    response_model=SessionResponse,
    responses={
        404: {"model": ErrorResponse},
    },
    summary="Get session details",
    description="Returns session details and all generated sections.",
)
async def get_session(
    session_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    """Get session details and generation results."""
    result = await db.execute(
        select(Session).where(Session.id == str(session_id))
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": f"Session not found: {session_id}",
                "error_code": "SESSION_NOT_FOUND",
            },
        )
    
    # Get outputs
    outputs_result = await db.execute(
        select(GenerationOutput).where(
            GenerationOutput.session_id == str(session_id)
        )
    )
    outputs = outputs_result.scalars().all()
    
    # Build sections dict
    sections = {}
    total_tokens = 0
    total_duration = 0
    
    for output in outputs:
        sections[output.section] = SectionOutput(
            section=output.section,
            status=output.status,
            payload=output.payload_json,
            tokens_used=output.tokens_used,
            duration_ms=output.duration_ms,
            cached=output.cached,
        )
        total_tokens += output.tokens_used or 0
        total_duration += output.duration_ms or 0
    
    return SessionResponse(
        session_id=session.id,
        prompt=session.prompt,
        design_type=session.design_type,
        status=session.status,
        context=session.context_json or {},
        sections=sections,
        created_at=session.created_at.timestamp() if session.created_at else time.time(),
        completed_at=session.completed_at.timestamp() if session.completed_at else None,
        total_tokens=total_tokens,
        total_duration_ms=total_duration,
    )