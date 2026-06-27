from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.generation import generate_design_stream

router = APIRouter(prefix="/api", tags=["Phase D: Generation"])

@router.get("/sessions/{session_id}/stream")
async def stream_generation(session_id: UUID, db: AsyncSession = Depends(get_db)):
    try:
        return StreamingResponse(
            generate_design_stream(db, session_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))