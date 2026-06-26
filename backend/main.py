from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all routers including the new Phase C routers
from app.api.routes import classify, mcq, retrieval, generation, famous
from app.api.routes.routes import router as gh_router

app = FastAPI(title="SysDesign AI", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Order matters! Specific routers first, generic placeholders last.
app.include_router(classify.router)
app.include_router(mcq.router)
app.include_router(retrieval.router) # Phase C
app.include_router(famous.router)   # Phase C
app.include_router(generation.router)
app.include_router(gh_router)       # Contains Stage 4+ placeholders

@app.get("/health")
async def health():
    return {"status": "ok"}