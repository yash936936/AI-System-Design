from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ClassifyRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=2000)

class ClassifyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    type: str
    confidence: float
    reasoning: str
    suggested_correction: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)

class MCQOption(BaseModel):
    id: str
    label: str
    description: Optional[str] = None
    recommended: bool = False

class MCQCategory(BaseModel):
    id: str
    label: str
    question: str
    type: str
    options: List[MCQOption]
    allow_free_text: bool = False
    free_text_placeholder: str = ""

class MCQTemplate(BaseModel):
    design_type: str
    categories: List[MCQCategory]
    version: str = "1.0"

class SessionContext(BaseModel):
    system_name: Optional[str] = None
    functional_reqs: List[str] = Field(default_factory=list)
    out_of_scope: List[str] = Field(default_factory=list)
    user_actors: List[str] = Field(default_factory=list)
    read_write_ratio: Optional[str] = None
    scale: Optional[str] = None
    dau: Optional[str] = None
    availability: Optional[str] = None
    consistency: Optional[str] = None
    latency_target: Optional[str] = None
    request_size_category: Optional[str] = None
    data_model_preference: Optional[str] = None
    api_style: Optional[str] = None
    architecture_approach: Optional[str] = None
    bottleneck_focus: List[str] = Field(default_factory=list)
    scalability_priority: Optional[str] = None
    trade_off_priority: Optional[str] = None
    custom_requirements: Optional[Dict[str, str]] = None

class CreateSessionRequest(BaseModel):
    prompt: str
    design_type: str
    context: SessionContext

class RetrievedDesign(BaseModel):
    id: str
    name: str
    type: str
    score: float
    components: List[str] = Field(default_factory=list)
    source: Optional[str] = None
    summary: Optional[str] = None

class CreateSessionResponse(BaseModel):
    session_id: str
    retrieve_url: str
    stream_url: str
    status: str
    design_type: str
    retrieved_designs: List[RetrievedDesign] = Field(default_factory=list)
    created_at: float

class FamousSystemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    slug: str
    description: str
    design_type: str
    key_components: List[str] = Field(default_factory=list)
    architecture_summary: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

class SectionOutput(BaseModel):
    section: str
    status: str
    payload: Optional[Dict[str, Any]] = None
    tokens_used: Optional[int] = None
    duration_ms: Optional[int] = None
    cached: bool = False

class SessionResponse(BaseModel):
    session_id: str
    prompt: str
    design_type: str
    status: str
    context: Dict[str, Any]
    sections: Dict[str, SectionOutput] = Field(default_factory=dict)
    created_at: float
    completed_at: Optional[float] = None
    total_tokens: int = 0
    total_duration_ms: int = 0

class GenerationStatusResponse(BaseModel):
    session_id: str
    session_status: str
    sections: Dict[str, Dict[str, Any]]
    total_tokens: int = 0
    total_duration_ms: int = 0