from pydantic import BaseModel
from typing import Optional, Literal, Any
from uuid import UUID
from datetime import datetime

# ── Session ───────────────────────────────────────────────────────────────────
class CreateSessionRequest(BaseModel):
    prompt: str
    system_name: Optional[str] = None
    design_type: Optional[Literal["hld", "lld"]] = None

class CreateSessionResponse(BaseModel):
    session_id: UUID
    retrieve_url: str
    stream_url: str
    status: str

class SessionResponse(BaseModel):
    id: UUID
    prompt: str
    system_name: Optional[str] = None
    design_type: Optional[str] = None
    status: str
    created_at: datetime

# ── Phase A: Classify ─────────────────────────────────────────────────────────
class ClassifyRequest(BaseModel):
    prompt: str

class ClassifyResponse(BaseModel):
    type: Literal["hld", "lld", "unknown"]
    confidence: float
    reasoning: str

# ── Phase B: MCQ ──────────────────────────────────────────────────────────────
class MCQQuestion(BaseModel):
    question: str
    options: list[str]
    correct_answer: str

class MCQTemplate(BaseModel):
    design_type: str
    questions: list[MCQQuestion]

# ── Phase C: Retrieval ────────────────────────────────────────────────────────
class RagChunk(BaseModel):
    id: str
    source: str
    section: str
    text: str
    score: float

class RetrievalResponse(BaseModel):
    session_id: UUID
    query: str
    chunks: list[RagChunk]
    max_score: float
    used_web_fallback: bool
    famous_design_matched: Optional[str] = None

# ── Phase D: Generation ───────────────────────────────────────────────────────
class SSEEvent(BaseModel):
    section: str
    status: str
    payload: Optional[dict[str, Any]] = None
    tokens_used: int = 0
    cached: bool = False
    duration_ms: int = 0
    error: Optional[str] = None

# ── Phase 6: Export ───────────────────────────────────────────────────────────
class ExportRequest(BaseModel):
    format: Literal["pdf", "md", "json"]
    sections: list[str] = ["architecture", "capacity", "data_model", "api_design", "stack"]

class ExportResponse(BaseModel):
    id: UUID
    session_id: UUID
    format: str
    sections: list[str]
    download_url: str
    expires_at: datetime
    created_at: datetime