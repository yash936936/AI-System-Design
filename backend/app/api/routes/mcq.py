from fastapi import APIRouter, HTTPException
from app.schemas.schemas import MCQTemplate
from app.services.mcq_templates import get_mcq_template

router = APIRouter(prefix="/api", tags=["Phase B: MCQ"])

@router.get("/mcq/{design_type}", response_model=MCQTemplate)
async def get_mcq(design_type: str):
    if design_type.lower() not in ("hld", "lld"):
        raise HTTPException(status_code=422, detail="design_type must be 'hld' or 'lld'")
    return get_mcq_template(design_type)