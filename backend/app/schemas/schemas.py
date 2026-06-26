"""
Pydantic v2 request / response schemas for all phases.
Merged from GitHub scaffold and User's Phase A-D implementation.
"""
import uuid
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator

# ── Phase A — Classify ────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    prompt: str = Field(..., min_length=10, max_length=4000)

class ClassifyResponse(BaseModel):
    session_id: uuid.UUID | None = None
    design_type: Literal["HLD", "LLD"] | None = None
    system_name: str | None = None
    confidence: float | None = None
    reasoning: str | None = None
    # From GitHub
    type: Literal["HLD", "LLD"] | None = None
    suggested_correction: Literal["HLD", "LLD"] | None = None

# ── Phase B — MCQ ─────────────────────────────────────────────────────────────

VALID_DESIGN_TYPES = {"HLD", "LLD"}

MCQ_FIELDS = Literal[
    "scale", "dau", "read_write_ratio", "availability",
    "consistency", "latency_target", "data_model_preference",
    "api_style", "architecture_approach", "scalability_priority",
    "trade_off_priority", "functional_reqs", "out_of_scope",
    "user_actors", "bottleneck_focus",
]

class MCQOption(BaseModel):
    id: str
    label: str
    value: str | None = None  # User's code has value, GitHub doesn't

class MCQCategory(BaseModel):
    id: str
    label: str
    question: str
    type: Literal["single_select", "multi_select"]
    options: list[MCQOption]
    allow_free_text: bool = False
    free_text_placeholder: str = ""

class MCQQuestion(BaseModel):
    id: str
    field: str
    question: str
    hint: str | None = None
    multi_select: bool = False
    options: list[MCQOption]

class MCQTemplate(BaseModel):
    design_type: Literal["hld", "lld"]
    categories: list[MCQCategory]

class MCQResponse(BaseModel):
    session_id: uuid.UUID
    design_type: str
    questions: list[MCQQuestion]

class MCQSubmitRequest(BaseModel):
    answers: dict[str, Any]

    @field_validator("answers")
    @classmethod
    def answers_not_empty(cls, v: dict) -> dict:
        if not v:
            raise ValueError("answers must not be empty")
        return v

class MCQSubmitResponse(BaseModel):
    session_id: uuid.UUID
    context_json: dict[str, Any]
    ready_for_retrieval: bool

# ── Session Context (MCQ answers object) ──────────────────────────────────────

class SessionContext(BaseModel):
    system_name: str | None = None
    functional_reqs: list[str] = []
    out_of_scope: list[str] = []
    user_actors: list[str] = []
    read_write_ratio: str | None = None
    scale: str | None = None
    dau: str | None = None
    availability: str | None = None
    consistency: str | None = None
    latency_target: str | None = None
    request_size_category: str | None = None
    data_model_preference: str | None = None
    api_style: str | None = None
    architecture_approach: str | None = None
    bottleneck_focus: list[str] = []
    scalability_priority: str | None = None
    trade_off_priority: str | None = None

# ── Session ───────────────────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)
    design_type: Literal["HLD", "LLD"]
    context: SessionContext

class CreateSessionResponse(BaseModel):
    session_id: uuid.UUID
    retrieve_url: str
    stream_url: str
    status: str

class SessionResponse(BaseModel):
    id: uuid.UUID
    prompt: str
    design_type: str | None
    system_name: str | None
    context_json: dict[str, Any]
    status: str
    created_at: str
    completed_at: str | None

# ── Phase C — Retrieval ───────────────────────────────────────────────────────

class RagChunk(BaseModel):
    id: str
    source: str
    section: str
    text: str
    score: float

class RetrievalResponse(BaseModel):
    session_id: uuid.UUID
    query: str
    chunks: list[RagChunk]
    max_score: float
    used_web_fallback: bool
    famous_design_matched: str | None

# ── Phase D — Generation ──────────────────────────────────────────────────────

class GenerationStatusResponse(BaseModel):
    session_id: uuid.UUID
    status: str
    architecture: dict | None = None
    capacity_and_data: dict | None = None
    api_and_stack: dict | None = None
    error: str | None = None

# ── Famous Design ─────────────────────────────────────────────────────────────

class FamousDesignResponse(BaseModel):
    system: str
    title: str
    last_updated: str
    diagram: dict[str, Any]
    sections: dict[str, Any]
    key_insights: list[str]
    sources: list[str]

# ── SSE Event ─────────────────────────────────────────────────────────────────

class SSEEvent(BaseModel):
    section: str
    status: Literal["started", "complete", "error", "done"]
    payload: dict[str, Any] | None = None
    tokens_used: int = 0
    cached: bool = False
    duration_ms: int = 0
    error: str | None = None

# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    focus_section: str | None = None