from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import classify, mcq, retrieval, generation, export, famous
from app.api.routes.routes import router as session_router
from app.db.session import init_db

# Ensure static/exports directory exists before mounting
Path("static/exports").mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="SysDesign AI", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve generated export files
app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(classify.router)
app.include_router(mcq.router)
app.include_router(retrieval.router)
app.include_router(generation.router)
app.include_router(export.router)
app.include_router(famous.router)
app.include_router(session_router)


@app.get("/health")
async def health():
    return {"status": "ok"}