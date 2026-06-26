"""Initial schema — create all tables

Revision ID: 0001
Revises:
Create Date: 2026-06-26

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("plan", sa.String(20), nullable=False, server_default="free"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )

    # ── sessions ───────────────────────────────────────────────────────────────
    op.create_table(
        "sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("design_type", sa.String(10), nullable=True),
        sa.Column("system_name", sa.Text(), nullable=True),
        sa.Column("context_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("status", sa.String(20), nullable=False, server_default="clarifying"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_sessions_user_id", "sessions", ["user_id"])
    op.create_index("idx_sessions_status", "sessions", ["status"])
    op.create_index("idx_sessions_created", "sessions", ["created_at"])

    # ── rag_retrievals ─────────────────────────────────────────────────────────
    op.create_table(
        "rag_retrievals",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("chunks_json", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("max_score", sa.Numeric(4, 3), nullable=True),
        sa.Column("used_web_fallback", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("famous_match", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_rag_session", "rag_retrievals", ["session_id"])

    # ── generation_outputs ─────────────────────────────────────────────────────
    op.create_table(
        "generation_outputs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("section", sa.String(30), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("payload_url", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), server_default="0"),
        sa.Column("cached", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("duration_ms", sa.Integer(), server_default="0"),
        sa.Column("error_msg", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_gen_outputs_session", "generation_outputs", ["session_id"])
    op.create_unique_constraint(
        "uq_gen_output_session_section", "generation_outputs", ["session_id", "section"]
    )

    # ── gemini_usage ───────────────────────────────────────────────────────────
    op.create_table(
        "gemini_usage",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("model", sa.Text(), nullable=False),
        sa.Column("total_calls", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_in", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tokens_out", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cached_calls", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index("idx_gemini_usage_date_model", "gemini_usage", ["date", "model"])
    op.create_unique_constraint(
        "uq_gemini_usage_date_model", "gemini_usage", ["date", "model"]
    )

    # ── famous_designs ─────────────────────────────────────────────────────────
    op.create_table(
        "famous_designs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("system_name", sa.Text(), nullable=False, unique=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("canonical_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("diagram_json", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("key_insights", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("sources", postgresql.ARRAY(sa.Text()), nullable=False, server_default="{}"),
        sa.Column("last_updated", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_famous_designs_name", "famous_designs", ["system_name"])

    # ── exports ────────────────────────────────────────────────────────────────
    op.create_table(
        "exports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("format", sa.String(20), nullable=False),
        sa.Column("sections", postgresql.ARRAY(sa.Text()), nullable=False),
        sa.Column("download_url", sa.Text(), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("idx_exports_session", "exports", ["session_id"])
    op.create_index("idx_exports_expires", "exports", ["expires_at"])


def downgrade() -> None:
    op.drop_table("exports")
    op.drop_table("famous_designs")
    op.drop_table("gemini_usage")
    op.drop_table("generation_outputs")
    op.drop_table("rag_retrievals")
    op.drop_table("sessions")
    op.drop_table("users")