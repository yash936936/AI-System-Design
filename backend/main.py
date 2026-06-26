from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import classify, mcq, retrieval, generation
from app.api.routes.routes import router as gh_router  # Re-added safely

app = FastAPI(title="SysDesign AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the GitHub scaffold router (now safe, no duplicate /classify)
app.include_router(gh_router)

# Include Phase A-D routers
app.include_router(classify.router)
app.include_router(mcq.router)
app.include_router(retrieval.router)
app.include_router(generation.router)


@app.get("/health")
async def health():
    return {"status": "ok"}