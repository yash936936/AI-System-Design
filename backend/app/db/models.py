import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Integer, Float, ForeignKey, UniqueConstraint, JSON, Uuid
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

# Helper to generate naive UTC datetimes (works the same on SQLite & Postgres)
def _naive_utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)

# NOTE on portability:
# The previous version of this file imported UUID/JSONB from
# `sqlalchemy.dialects.postgresql`. Those types ONLY compile on a Postgres
# connection. Since `Settings.database_url` defaults to a SQLite URL,
# the app crashed on startup for anyone who hadn't already provisioned
# Postgres. `sqlalchemy.Uuid` and `sqlalchemy.JSON` are dialect-agnostic:
# they render as native UUID/JSONB on Postgres and as CHAR(32)/TEXT on
# SQLite, so the exact same models work in both environments. Swap back to
# `postgresql.JSONB`/`postgresql.UUID` later if you need Postgres-only
# features (GIN indexes on JSONB, etc).

class Session(Base):
    __tablename__ = "sessions"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(36), nullable=True, default="anonymous")
    prompt = Column(String, nullable=False)
    system_name = Column(String, nullable=True)
    design_type = Column(String, nullable=True)
    context_json = Column(JSON, default=dict)
    status = Column(String, default="creating")
    created_at = Column(DateTime, default=_naive_utcnow)
    completed_at = Column(DateTime, nullable=True)

    retrievals = relationship("RagRetrieval", back_populates="session", cascade="all, delete-orphan")
    generations = relationship("GenerationOutput", back_populates="session", cascade="all, delete-orphan")
    exports = relationship("Export", back_populates="session", cascade="all, delete-orphan")

class RagRetrieval(Base):
    __tablename__ = "rag_retrievals"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    query = Column(String)
    chunks_json = Column(JSON)
    max_score = Column(Float)
    used_web_fallback = Column(Integer, default=0)
    famous_match = Column(String, nullable=True)
    created_at = Column(DateTime, default=_naive_utcnow)

    session = relationship("Session", back_populates="retrievals")

class GenerationOutput(Base):
    __tablename__ = "generation_outputs"
    __table_args__ = (UniqueConstraint('session_id', 'section', name='uix_session_section'),)

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    section = Column(String)
    status = Column(String)
    payload_json = Column(JSON, nullable=True)
    tokens_used = Column(Integer, default=0)
    cached = Column(Integer, default=0)
    duration_ms = Column(Integer, default=0)
    error_msg = Column(String, nullable=True)
    created_at = Column(DateTime, default=_naive_utcnow)

    session = relationship("Session", back_populates="generations")

class Export(Base):
    __tablename__ = "exports"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(Uuid(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"))
    user_id = Column(String(36), nullable=True)
    format = Column(String)
    sections = Column(JSON)
    download_url = Column(String)
    storage_key = Column(String)
    size_bytes = Column(Integer)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=_naive_utcnow)

    session = relationship("Session", back_populates="exports")