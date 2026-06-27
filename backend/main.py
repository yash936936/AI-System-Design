from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import classify, mcq, retrieval, generation, export
from app.api.routes.routes import router as session_router
from app.db.session import init_db

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

app.include_router(classify.router)
app.include_router(mcq.router)
app.include_router(retrieval.router)
app.include_router(generation.router)
app.include_router(export.router)
app.include_router(session_router)

@app.get("/health")
async def health():
    return {"status": "ok"}