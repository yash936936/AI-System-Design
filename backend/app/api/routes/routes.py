from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import (
    MCQTemplate,
    CreateSessionRequest, 
    CreateSessionResponse,
    SessionResponse,
)
from app.services.mcq_templates import get_mcq_template
from app.services.session import create_session, get_session, session_to_response

router = APIRouter(tags=["Misc"])
router = APIRouter(prefix="/api")

# ── Phase B: MCQ Templates ──────────────────────────────────────────────────
@router.get("/mcq/{design_type}", response_model=MCQTemplate)
async def get_mcq(design_type: str):
    """
    Phase B — Return static MCQ templates to gather initial requirements.
    Zero LLM calls — pure dictionary lookup.
    """
    template = get_mcq_template(design_type)
    if not template:
        raise HTTPException(
            status_code=404, 
            detail=f"MCQ template for '{design_type}' not found"
        )
    return template

# ── Session Management ───────────────────────────────────────────────────────
@router.post("/sessions", response_model=CreateSessionResponse, status_code=201)
async def create_new_session(
    request: CreateSessionRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new system design session after MCQ completion.
    """
    try:
        session = await create_session(db, request)
        
        # FIX: Construct the full response expected by the Pydantic schema
        return CreateSessionResponse(
            session_id=session.id,
            retrieve_url=f"/api/sessions/{session.id}/retrieve",
            stream_url=f"/api/sessions/{session.id}/stream",
            status=session.status  # e.g., 'clarifying' or 'classified'
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create session: {str(e)}")

@router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session_details(
    session_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve the current state and metadata of a session.
    """
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return session_to_response(session)

# ── Placeholder routes (Stage 4 & beyond) ────────────────────────────────────
@router.get("/sessions/{session_id}/stream")
async def stream_placeholder(session_id: UUID):
    """Stage 4 — Generation SSE stream. Not yet implemented."""
    return {
        "message": "Generation pipeline activates in Stage 4", 
        "session_id": str(session_id)
    }

@router.get("/api/placeholder/{stage}")
async def placeholder(stage: str):
    """Placeholder endpoint for future stages."""
    return {
        "stage": stage,
        "message": "This endpoint is a placeholder for Phase 5+",
        "status": "not_implemented",
    }