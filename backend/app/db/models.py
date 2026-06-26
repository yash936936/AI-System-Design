"""
SQLAlchemy ORM models.
Fixed relationship conflicts between one-to-one and one-to-many relationships.
"""
import uuid
from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, SmallInteger,
    Numeric, DateTime, Date, ForeignKey, ARRAY, UniqueConstraint, Index,
    Float,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.sql import func

class Base(AsyncAttrs, DeclarativeBase):
    pass

# ── GitHub Models ─────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(Text, nullable=False, unique=True)
    name = Column(Text)
    avatar_url = Column(Text)
    plan = Column(String(20), nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("Session", back_populates="user")

class GeminiUsage(Base):
    __tablename__ = "gemini_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date = Column(Date, nullable=False)
    model = Column(Text, nullable=False)
    total_calls = Column(Integer, nullable=False, default=0)
    tokens_in = Column(Integer, nullable=False, default=0)
    tokens_out = Column(Integer, nullable=False, default=0)
    cached_calls = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("date", "model", name="uq_gemini_usage_date_model"),
        Index("idx_gemini_usage_date_model", "date", "model"),
    )

class FamousDesign(Base):
    __tablename__ = "famous_designs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    system_name = Column(Text, nullable=False, unique=True)
    title = Column(Text, nullable=False)
    canonical_json = Column(JSONB, nullable=False, default=dict)
    diagram_json = Column(JSONB, nullable=False, default=dict)
    key_insights = Column(ARRAY(Text), nullable=False, default=list)
    sources = Column(ARRAY(Text), nullable=False, default=list)
    last_updated = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (Index("idx_famous_designs_name", "system_name"),)

class Export(Base):
    __tablename__ = "exports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    format = Column(String(20), nullable=False)
    sections = Column(ARRAY(Text), nullable=False)
    download_url = Column(Text, nullable=False)
    storage_key = Column(Text, nullable=False)
    size_bytes = Column(Integer)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # FIX: Add back_populates to link with Session
    session = relationship("Session", back_populates="exports")

    __table_args__ = (
        Index("idx_exports_session", "session_id"),
        Index("idx_exports_expires", "expires_at"),
    )

# ── User Models ───────────────────────────────────────────────────────────────

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    design_type: Mapped[str | None] = mapped_column(String(16))   # HLD | LLD
    system_name: Mapped[str | None] = mapped_column(String(128))
    context_json: Mapped[dict | None] = mapped_column(JSONB)
    mcq_answers: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    is_public: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user = relationship("User", back_populates="sessions")
    
    # FIX: Keep only ONE relationship with RagRetrieval
    # Use one-to-many (rag_retrievals) and remove the one-to-one (retrieval)
    # Or mark one as viewonly to avoid conflict
    retrieval: Mapped["RagRetrieval | None"] = relationship(
        back_populates="session", uselist=False, overlaps="rag_retrievals"
    )
    
    generation: Mapped["Generation | None"] = relationship(
        back_populates="session", uselist=False
    )
    
    # FIX: Add overlaps parameter to avoid conflict with 'retrieval'
    rag_retrievals = relationship("RagRetrieval", back_populates="session", 
                                  cascade="all, delete-orphan", overlaps="retrieval")
    generation_outputs = relationship("GenerationOutput", back_populates="session", cascade="all, delete-orphan")
    
    # FIX: Add exports relationship to match Export.session
    exports = relationship("Export", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_created", "created_at"),
    )

class RagRetrieval(Base):
    __tablename__ = "rag_retrievals"
    __table_args__ = (
        UniqueConstraint("session_id", name="uq_retrieval_session"),
        Index("idx_rag_session", "session_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    query: Mapped[str] = mapped_column(Text, nullable=False)
    chunks_json: Mapped[list] = mapped_column(JSONB, default=list)
    max_score: Mapped[float | None] = mapped_column(Float)
    used_web_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    famous_match: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="rag_retrievals")

class Generation(Base):
    __tablename__ = "generations"
    __table_args__ = (UniqueConstraint("session_id", name="uq_generation_session"),)

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False
    )
    architecture: Mapped[dict | None] = mapped_column(JSONB)
    capacity_and_data: Mapped[dict | None] = mapped_column(JSONB)
    api_and_stack: Mapped[dict | None] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    session: Mapped["Session"] = relationship(back_populates="generation")

class GenerationOutput(Base):
    __tablename__ = "generation_outputs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    section = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    payload_url = Column(Text)
    tokens_used = Column(Integer, default=0)
    cached = Column(Boolean, nullable=False, default=False)
    duration_ms = Column(Integer, default=0)
    error_msg = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    session = relationship("Session", back_populates="generation_outputs")

    __table_args__ = (
        UniqueConstraint("session_id", "section", name="uq_gen_output_session_section"),
        Index("idx_gen_outputs_session", "session_id"),
    )