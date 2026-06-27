from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import ExportRequest, ExportResponse
from app.services.export import create_export, get_export
from app.core.auth import get_current_user, get_optional_user, UserClaims

router = APIRouter(prefix="/api", tags=["Phase 6: Export"])


@router.post(
    "/sessions/{session_id}/export",
    response_model=ExportResponse,
    status_code=201,
)
async def export_session(
    session_id: UUID,
    request: ExportRequest,
    db: AsyncSession = Depends(get_db),
    user: UserClaims = Depends(get_current_user),
):
    """
    Generate an export file (md / json / pdf) for the given session.
    The caller must own the session (user_id must match).
    """
    try:
        return await create_export(db, session_id, request, owner_id=user.user_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))


@router.get("/exports/{export_id}", response_model=ExportResponse)
async def get_export_by_id(
    export_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: UserClaims = Depends(get_current_user),
):
    """
    Retrieve export metadata. Only the owning user can fetch their export.
    """
    export = await get_export(db, export_id)
    if not export:
        raise HTTPException(status_code=404, detail="Export not found")
    if export.user_id and export.user_id != user.user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return export