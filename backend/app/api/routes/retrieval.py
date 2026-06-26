from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.schemas.schemas import RetrievalResponse
from app.services.retrieval_service import retrieve_for_session

router = APIRouter(prefix="/api", tags=["Phase C — Retrieval"])

# DEBUG FIX: Changed from POST to GET to match api-spec.md
@router.get("/sessions/{session_id}/retrieve", response_model=RetrievalResponse)
async def retrieve(session_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return await retrieve_for_session(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))