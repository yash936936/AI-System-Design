from fastapi import APIRouter
from app.schemas.schemas import ClassifyRequest, ClassifyResponse
from app.services.classify import classify_prompt

router = APIRouter(prefix="/api", tags=["Phase A: Classify"])

@router.post("/classify", response_model=ClassifyResponse)
async def classify(request: ClassifyRequest):
    return await classify_prompt(request.prompt)