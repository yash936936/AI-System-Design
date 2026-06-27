from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import ExportRequest, ExportResponse
from app.services.export import create_export, get_export

router = APIRouter(prefix="/api", tags=["Phase 6: Export"])

@router.post("/sessions/{session_id}/export", response_model=ExportResponse, status_code=201)
async def export_session(session_id: UUID, request: ExportRequest, db: AsyncSession = Depends(get_db)):
    try: 
        return await create_export(db, session_id, request)
    except ValueError as e: 
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/exports/{export_id}", response_model=ExportResponse)
async def get_export_by_id(export_id: UUID, db: AsyncSession = Depends(get_db)):
    export = await get_export(db, export_id)
    if not export: 
        raise HTTPException(status_code=404, detail="Export not found")
    return export