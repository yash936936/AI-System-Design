"""
SysDesign AI — Backend (Stage 1)
FastAPI app entry point.
"""
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api.routes.routes import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SysDesign AI backend starting — Stage 1")
    logger.info("Environment: %s", settings.app_env)
    logger.info("Gemini model: %s", settings.gemini_model)
    yield
    logger.info("Backend shutting down")


app = FastAPI(
    title="SysDesign AI API",
    description="System design assistant powered by Gemini — Stage 1",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
async def root():
    return {
        "service": "SysDesign AI Backend",
        "stage": 1,
        "docs": "/docs",
        "health": "/api/health",
    }
