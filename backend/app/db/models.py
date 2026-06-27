import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

# Helper to generate naive UTC datetimes (Required for PostgreSQL TIMESTAMP WITHOUT TIME ZONE)
def _naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class Session(Base):
    __tablename__ = "sessions"

    # Use native PostgreSQL UUID type
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(36), nullable=True, default="anonymous")
    prompt = Column(String, nullable=False)
    system_name = Column(String, nullable=True)
    design_type = Column(String, nullable=True)
    context_json = Column(JSONB, default=dict)
    status = Column(String, default="queued")
    created_at = Column(DateTime, default=_naive_utcnow)

    retrievals = relationship("RagRetrieval", back_populates="session", cascade="all, delete-orphan")
    generations = relationship("GenerationOutput", back_populates="session", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="session", cascade="all, delete-orphan")

class RagRetrieval(Base):
    __tablename__ = "rag_retrievals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    query = Column(String)
    chunks_json = Column(JSONB)
    max_score = Column(Float)
    used_web_fallback = Column(Integer, default=0)
    famous_match = Column(String, nullable=True)
    created_at = Column(DateTime, default=_naive_utcnow)

    session = relationship("Session", back_populates="retrievals")

class GenerationOutput(Base):
    __tablename__ = "generation_outputs"
    __table_args__ = (UniqueConstraint('session_id', 'section', name='uix_session_section'),)

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    section = Column(String)
    status = Column(String)
    payload_json = Column(JSONB, nullable=True)
    tokens_used = Column(Integer, default=0)
    cached = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    error_msg = Column(String, nullable=True)
    created_at = Column(DateTime, default=_naive_utcnow)

    session = relationship("Session", back_populates="generations")

class Export(Base):
    __tablename__ = "exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    user_id = Column(String(36), nullable=True)
    format = Column(String)
    sections = Column(JSONB)
    download_url = Column(String)
    storage_key = Column(String)
    size_bytes = Column(Integer)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=_naive_utcnow)

    session = relationship("Session", back_populates="exports")