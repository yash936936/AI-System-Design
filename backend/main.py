import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import classify, mcq, retrieval, generation, famous
from app.api.routes.routes import router as gh_router
from app.core.config import settings
from app.db.session import init_db, close_db, async_session_maker
from app.services.seed_data import seed_famous_systems
from app.services.retrieval import load_systems_to_cache

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"🚀 Starting {settings.APP_NAME}...")
    await init_db()
    
    async with async_session_maker() as db:
        await seed_famous_systems(db)
        
    async with async_session_maker() as db:
        await load_systems_to_cache(db)
        
    logger.info("🎉 Application ready!")
    yield
    await close_db()

app = FastAPI(title=settings.APP_NAME, version="6.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(classify.router)
app.include_router(mcq.router)
app.include_router(famous.router)
app.include_router(retrieval.router)
app.include_router(generation.router)
app.include_router(gh_router)

@app.get("/health")
async def health():
    return {"status": "ok", "phase": "6", "version": "6.0.0"}