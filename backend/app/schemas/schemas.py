from __future__ import annotations
from typing import Any, Literal
from uuid import UUID
from pydantic import BaseModel, Field


# ── Classify ──────────────────────────────────────────────────────────────────

class ClassifyRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)


class ClassifyResponse(BaseModel):
    type: Literal["HLD", "LLD"]
    confidence: float
    reasoning: str
    suggested_correction: Literal["HLD", "LLD"]


# ── MCQ ───────────────────────────────────────────────────────────────────────

class MCQOption(BaseModel):
    id: str
    label: str


class MCQCategory(BaseModel):
    id: str
    label: str
    question: str
    type: Literal["single_select", "multi_select"]
    options: list[MCQOption]
    allow_free_text: bool = False
    free_text_placeholder: str = ""


class MCQTemplate(BaseModel):
    design_type: Literal["hld", "lld"]
    categories: list[MCQCategory]


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
    session_id: UUID
    retrieve_url: str
    stream_url: str
    status: str


class SessionResponse(BaseModel):
    id: UUID
    prompt: str
    design_type: str | None
    system_name: str | None
    context_json: dict[str, Any]
    status: str
    created_at: str
    completed_at: str | None


# ── RAG Chunk ─────────────────────────────────────────────────────────────────

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
    famous_design_matched: str | None


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
