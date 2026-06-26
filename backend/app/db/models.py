"""
SQLAlchemy ORM models matching db-schema.md exactly.
Uses async engine via asyncpg.
"""
from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, SmallInteger,
    Numeric, DateTime, Date, ForeignKey, ARRAY, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email      = Column(Text, nullable=False, unique=True)
    name       = Column(Text)
    avatar_url = Column(Text)
    plan       = Column(String(20), nullable=False, default="free")
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    sessions = relationship("Session", back_populates="user")


class Session(Base):
    __tablename__ = "sessions"

    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id       = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    prompt        = Column(Text, nullable=False)
    design_type   = Column(String(10))               # 'HLD' | 'LLD'
    system_name   = Column(Text)
    context_json  = Column(JSONB, nullable=False, default=dict)
    status        = Column(String(20), nullable=False, default="clarifying")
    is_public     = Column(Boolean, nullable=False, default=False)
    created_at    = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at  = Column(DateTime(timezone=True))

    user              = relationship("User", back_populates="sessions")
    rag_retrievals    = relationship("RagRetrieval", back_populates="session", cascade="all, delete-orphan")
    generation_outputs = relationship("GenerationOutput", back_populates="session", cascade="all, delete-orphan")
    exports           = relationship("Export", back_populates="session", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_sessions_user_id", "user_id"),
        Index("idx_sessions_status", "status"),
        Index("idx_sessions_created", "created_at"),
    )


class RagRetrieval(Base):
    __tablename__ = "rag_retrievals"

    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id        = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    query             = Column(Text, nullable=False)
    chunks_json       = Column(JSONB, nullable=False, default=list)
    max_score         = Column(Numeric(4, 3))
    used_web_fallback = Column(Boolean, nullable=False, default=False)
    famous_match      = Column(Text)
    created_at        = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    session = relationship("Session", back_populates="rag_retrievals")

    __table_args__ = (Index("idx_rag_session", "session_id"),)


class GenerationOutput(Base):
    __tablename__ = "generation_outputs"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id  = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    section     = Column(String(30), nullable=False)
    status      = Column(String(20), nullable=False, default="pending")
    payload_url = Column(Text)
    tokens_used = Column(Integer, default=0)
    cached      = Column(Boolean, nullable=False, default=False)
    duration_ms = Column(Integer, default=0)
    error_msg   = Column(Text)
    created_at  = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    session = relationship("Session", back_populates="generation_outputs")

    __table_args__ = (
        UniqueConstraint("session_id", "section", name="uq_gen_output_session_section"),
        Index("idx_gen_outputs_session", "session_id"),
    )


class GeminiUsage(Base):
    __tablename__ = "gemini_usage"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    date         = Column(Date, nullable=False)
    model        = Column(Text, nullable=False)
    total_calls  = Column(Integer, nullable=False, default=0)
    tokens_in    = Column(Integer, nullable=False, default=0)
    tokens_out   = Column(Integer, nullable=False, default=0)
    cached_calls = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("date", "model", name="uq_gemini_usage_date_model"),
        Index("idx_gemini_usage_date_model", "date", "model"),
    )


class FamousDesign(Base):
    __tablename__ = "famous_designs"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    system_name    = Column(Text, nullable=False, unique=True)
    title          = Column(Text, nullable=False)
    canonical_json = Column(JSONB, nullable=False, default=dict)
    diagram_json   = Column(JSONB, nullable=False, default=dict)
    key_insights   = Column(ARRAY(Text), nullable=False, default=list)
    sources        = Column(ARRAY(Text), nullable=False, default=list)
    last_updated   = Column(Date, nullable=False)
    created_at     = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    __table_args__ = (Index("idx_famous_designs_name", "system_name"),)


class Export(Base):
    __tablename__ = "exports"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id   = Column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    user_id      = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    format       = Column(String(20), nullable=False)
    sections     = Column(ARRAY(Text), nullable=False)
    download_url = Column(Text, nullable=False)
    storage_key  = Column(Text, nullable=False)
    size_bytes   = Column(Integer)
    expires_at   = Column(DateTime(timezone=True), nullable=False)
    created_at   = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    session = relationship("Session", back_populates="exports")

    __table_args__ = (
        Index("idx_exports_session", "session_id"),
        Index("idx_exports_expires", "expires_at"),
    )
