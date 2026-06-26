from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import FamousDesign
from app.schemas.schemas import FamousDesignResponse

router = APIRouter(prefix="/api", tags=["Phase C — Famous Designs"])

@router.get("/famous/{system_name}", response_model=FamousDesignResponse)
async def get_famous_design(system_name: str, db: AsyncSession = Depends(get_db)):
    system_name = system_name.lower().strip()
    result = await db.execute(select(FamousDesign).where(FamousDesign.system_name == system_name))
    design = result.scalar_one_or_none()
    
    if not design:
        raise HTTPException(status_code=404, detail=f"Design '{system_name}' not found")

    return FamousDesignResponse(
        system=design.system_name,
        title=design.title,
        last_updated=design.last_updated.isoformat(),
        diagram=design.diagram_json,
        sections=design.canonical_json,
        key_insights=design.key_insights,
        sources=design.sources,
    )