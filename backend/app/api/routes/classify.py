from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.schemas import ClassifyRequest, ClassifyResponse
from app.services.classify import classify_prompt

router = APIRouter(prefix="/api", tags=["Phase A — Classify"])


@router.post("/classify", response_model=ClassifyResponse, status_code=201)
async def classify(
    req: ClassifyRequest,
    db: AsyncSession = Depends(get_db),
) -> ClassifyResponse:
    try:
        return await classify_prompt(db, req)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))