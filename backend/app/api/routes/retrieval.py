from pydantic import BaseModel, Field
from typing import Optional, Literal, Any, Union
from uuid import UUID
from datetime import datetime

VALID_DESIGN_TYPES = {"HLD", "LLD"}

# ── Phase A: Classify ──────────────────────────────────────────────────────────
class ClassifyRequest(BaseModel):
    prompt: str

class ClassifyResponse(BaseModel):
    # NOTE: must be UPPERCASE "HLD"/"LLD" — the frontend's DesignType union is
    # 'HLD' | 'LLD' and the store does a strict `result.type === "HLD"` check.
    type: Literal["HLD", "LLD"]
    confidence: float
    reasoning: str
    # The frontend's "Not right? Switch to X" button reads this directly and
    # passes it straight into setDesignType(correction) with no null-check,
    # so it must ALWAYS be populated (the opposite of `type`).
    suggested_correction: Literal["HLD", "LLD"]
    keywords: Optional[list[str]] = None

# ── Phase B: MCQ ───────────────────────────────────────────────────────────────
class MCQOption(BaseModel):
    id: str
    label: str
    description: Optional[str] = None
    recommended: Optional[bool] = None
    icon: Optional[str] = None

class MCQCategory(BaseModel):
    id: str
    label: str
    question: str
    type: Literal["single_select", "multi_select"]
    options: list[MCQOption]
    allow_free_text: bool = False
    free_text_placeholder: str = "Add your own..."
    required: bool = True
    help_text: Optional[str] = None
    defaults: Optional[list[str]] = None

class MCQTemplate(BaseModel):
    design_type: str
    categories: list[MCQCategory]
    version: str = "1.0"

# ── Session ────────────────────────────────────────────────────────────────────
class CreateSessionRequest(BaseModel):
    prompt: str
    design_type: Literal["HLD", "LLD"]
    context: dict[str, Any] = Field(default_factory=dict)

class CreateSessionResponse(BaseModel):
    session_id: UUID
    retrieve_url: str
    stream_url: str
    status: str
    created_at: int  # epoch ms — frontend expects a number, not an ISO string

class SectionResultSchema(BaseModel):
    section: str
    status: str
    payload: Optional[dict[str, Any]] = None
    tokens_used: Optional[int] = None
    duration_ms: Optional[int] = None
    cached: Optional[bool] = None
    error: Optional[str] = None

class SessionResponse(BaseModel):
    """Matches the frontend's GetSessionResponse contract field-for-field."""
    session_id: UUID
    status: str
    design_type: Optional[str] = None
    context: dict[str, Any] = Field(default_factory=dict)
    sections: dict[str, SectionResultSchema] = Field(default_factory=dict)
    created_at: int
    completed_at: Optional[int] = None
    total_tokens: Optional[int] = None
    total_duration_ms: Optional[int] = None

class GenerationStatusResponse(BaseModel):
    session_id: UUID
    session_status: str
    sections: dict[str, dict[str, Any]] = Field(default_factory=dict)
    total_tokens: int = 0
    total_duration_ms: int = 0

# ── Phase C: Retrieval ─────────────────────────────────────────────────────────
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

# ── Famous Systems ─────────────────────────────────────────────────────────────
class FamousSystemSchema(BaseModel):
    system_name: str
    title: str
    canonical_json: dict
    diagram_json: dict
    key_insights: list[str]
    sources: list[str]
    # Accept both datetime objects and ISO strings (the in-memory catalog
    # stores strings; a DB-backed catalog might store datetime).
    last_updated: Union[datetime, str]

    model_config = {"arbitrary_types_allowed": True}

class ErrorResponse(BaseModel):
    error: str
    error_code: Optional[str] = None

# ── Phase D: Generation / SSE ──────────────────────────────────────────────────
# Flexible envelope covering every member of the frontend's SSEEvent
# discriminated union (ping | heartbeat | section.start | section.done |
# section.error | pipeline.done | pipeline.error). `type` is the discriminator
# the frontend's openStream() switches on — every event MUST set it.
class SSEEvent(BaseModel):
    type: str
    timestamp: int
    session_id: Optional[str] = None   # str not UUID so it serialises cleanly
    message: Optional[str] = None
    section: Optional[str] = None
    status: Optional[str] = None
    payload: Optional[dict[str, Any]] = None
    tokens_used: Optional[int] = None
    duration_ms: Optional[int] = None
    cached: Optional[bool] = None
    total_tokens: Optional[int] = None
    total_duration_ms: Optional[int] = None
    error: Optional[str] = None
    error_code: Optional[str] = None

# ── Phase 6: Export (prepared, not wired into the UI yet) ─────────────────────
class ExportRequest(BaseModel):
    format: Literal["pdf", "md", "json"]
    sections: list[str] = ["architecture", "capacity", "data_model", "api_design", "stack"]

class ExportResponse(BaseModel):
    id: UUID
    session_id: UUID
    format: str
    sections: list[str]