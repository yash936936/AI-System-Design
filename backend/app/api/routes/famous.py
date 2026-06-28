from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.services.retrieval import get_famous_system, list_famous_systems
from app.schemas.schemas import FamousDesignResponse

router = APIRouter(prefix="/api", tags=["Phase C — Famous Designs"])

@router.get("/famous", response_model=list[FamousDesignResponse])
async def get_all_famous_systems(db: AsyncSession = Depends(get_db)):
    """Return all famous system designs from the famous_designs table
    (populated via `python -m scripts.ingest_famous_designs`)."""
    systems = []
    for d in await list_famous_systems(db):
        systems.append(FamousDesignResponse(
            system=d.get("system_name", ""),
            title=d.get("title", ""),
            last_updated=str(d.get("last_updated", "")),
            diagram=d.get("diagram_json", {}),
            sections=d.get("canonical_json", {}),
            key_insights=d.get("key_insights", []),
            sources=d.get("sources", []),
        ))
    return systems

@router.get("/famous/{system_name}", response_model=FamousDesignResponse)
async def get_famous_design(system_name: str, db: AsyncSession = Depends(get_db)):
    """Return a specific famous system design from the famous_designs table."""
    design = await get_famous_system(db, system_name)

    if not design:
        raise HTTPException(status_code=404, detail=f"Design '{system_name}' not found")

    return FamousDesignResponse(
        system=design.get("system_name", ""),
        title=design.get("title", ""),
        last_updated=str(design.get("last_updated", "")),
        diagram=design.get("diagram_json", {}),
        sections=design.get("canonical_json", {}),
        key_insights=design.get("key_insights", []),
        sources=design.get("sources", []),
    )
