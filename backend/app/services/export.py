from uuid import UUID
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Export
from app.schemas.schemas import ExportRequest, ExportResponse
from app.services.session import get_session

def _naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

async def create_export(db: AsyncSession, session_id: UUID, request: ExportRequest) -> ExportResponse:
    session = await get_session(db, session_id)
    if not session: 
        raise ValueError("Session not found")
    
    expires_at = _naive_utcnow() + timedelta(days=7)
    
    export = Export(
        session_id=session_id, 
        user_id=session.user_id, 
        format=request.format,
        sections=request.sections, 
        download_url=f"https://mock-r2-url.com/exports/{session_id}.{request.format}",
        storage_key=f"exports/{session_id}.{request.format}", 
        size_bytes=1024, 
        expires_at=expires_at
    )
    db.add(export)
    await db.flush()
    await db.refresh(export)
    
    # FIX: Commit the transaction so the export record is saved
    await db.commit()
    
    return ExportResponse(
        id=export.id, session_id=export.session_id, format=export.format,
        sections=export.sections, download_url=export.download_url,
        expires_at=export.expires_at, created_at=export.created_at
    )

async def get_export(db: AsyncSession, export_id: UUID) -> ExportResponse | None:
    result = await db.execute(select(Export).where(Export.id == export_id))
    export = result.scalar_one_or_none()
    if not export: 
        return None
        
    return ExportResponse(
        id=export.id, session_id=export.session_id, format=export.format,
        sections=export.sections, download_url=export.download_url,
        expires_at=export.expires_at, created_at=export.created_at
    )