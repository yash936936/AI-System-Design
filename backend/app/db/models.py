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
    # FIX: retrieve_for_session() (app/services/retrieval_service.py) catches
    # IntegrityError to handle two concurrent requests racing to create the
    # first retrieval for the same session. The DB already enforces this via
    # the `uq_retrieval_session` unique constraint added in alembic migration
    # 26c51db01cbf_add_missing_columns_to_sessions.py — but the ORM model
    # itself never declared it, so SQLAlchemy didn't know about it and a
    # fresh `Base.metadata.create_all()` (e.g. via init_db(), which is what
    # actually runs the schema today — see app/db/session.py) silently
    # skipped creating the constraint, leaving the idempotency guard with
    # nothing to catch. Declaring it here keeps the model in sync with the
    # migration and makes create_all() create it too.
    __table_args__ = (UniqueConstraint('session_id', name='uq_retrieval_session'),)

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

# NOTE: these two models were referenced (but never defined) by two
# standalone maintenance scripts:
#   - app/services/seed_data.py            -> FamousSystem
#   - scripts/ingest_famous_designs.py     -> FamousDesign
# Both scripts would raise ImportError the moment they were actually run.
# Neither is imported by the live app at startup (the live RAG flow uses
# the in-memory mock catalog in services/retrieval.py instead — see the
# comment at the top of that file), so this was previously a silent,
# dormant bug rather than a startup crash. Adding the two models here
# matches each script's already-written field usage exactly; the scripts
# themselves were not changed.

class FamousSystem(Base):
    __tablename__ = "famous_systems"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    slug = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(String, nullable=True)
    design_type = Column(String(16), nullable=True)
    key_components = Column(JSON, default=list)
    architecture_summary = Column(String, nullable=True)
    tags = Column(JSON, default=list)
    reference_url = Column(String, nullable=True)
    created_at = Column(DateTime, default=_naive_utcnow)
    updated_at = Column(DateTime, default=_naive_utcnow, onupdate=_naive_utcnow)

class FamousDesign(Base):
    __tablename__ = "famous_designs"

    id = Column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_name = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String, nullable=True)
    diagram_json = Column(JSON, default=dict)
    canonical_json = Column(JSON, default=dict)
    key_insights = Column(JSON, default=list)
    sources = Column(JSON, default=list)
    last_updated = Column(DateTime, default=_naive_utcnow, nullable=False)