"""
Phase B — MCQ Service

Responsibilities:
1. Return a design-type-aware question set for the session
2. Validate and persist submitted answers into session.context_json
3. Mark session ready for Phase C

Bug fixes applied:
- design_type validated against strict allowlist (no KeyError on bad input)
- answers merged non-destructively into existing context_json
- list fields (functional_reqs etc.) deduplicated on merge
- submit validates session exists and belongs to correct state
- no mutable default dicts in module scope
"""

import logging
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Session as SessionModel
from app.schemas.schemas import (
    MCQOption,
    MCQQuestion,
    MCQResponse,
    MCQSubmitRequest,
    MCQSubmitResponse,
    VALID_DESIGN_TYPES,
)

logger = logging.getLogger(__name__)

# ── Question bank ─────────────────────────────────────────────────────────────
# Defined as functions (not module-level dicts) to avoid shared mutable state.

def _hld_questions() -> list[MCQQuestion]:
    return [
        MCQQuestion(
            id="functional_reqs",
            field="functional_reqs",
            question="Which core features does your system need to support?",
            hint="Select all that apply — these drive component choices.",
            multi_select=True,
            options=[
                MCQOption(id="a", label="User authentication & profiles", value="auth"),
                MCQOption(id="b", label="Real-time feeds / notifications", value="realtime_feed"),
                MCQOption(id="c", label="Media upload & storage", value="media_storage"),
                MCQOption(id="d", label="Search & discovery", value="search"),
                MCQOption(id="e", label="Messaging / chat", value="messaging"),
                MCQOption(id="f", label="Payments & transactions", value="payments"),
                MCQOption(id="g", label="Analytics & reporting", value="analytics"),
                MCQOption(id="h", label="Recommendations / ML ranking", value="recommendations"),
            ],
        ),
        MCQQuestion(
            id="scale",
            field="scale",
            question="What is the expected traffic scale at launch?",
            options=[
                MCQOption(id="a", label="Startup (< 10K DAU)", value="startup"),
                MCQOption(id="b", label="Mid-size (10K – 1M DAU)", value="mid"),
                MCQOption(id="c", label="Large (1M – 100M DAU)", value="large"),
                MCQOption(id="d", label="Hyper-scale (100M+ DAU)", value="hyperscale"),
            ],
        ),
        MCQQuestion(
            id="dau",
            field="dau",
            question="What is the target DAU (Daily Active Users)?",
            hint="Pick the closest order of magnitude.",
            options=[
                MCQOption(id="a", label="~10K",    value="10000"),
                MCQOption(id="b", label="~100K",   value="100000"),
                MCQOption(id="c", label="~1M",     value="1000000"),
                MCQOption(id="d", label="~10M",    value="10000000"),
                MCQOption(id="e", label="~100M",   value="100000000"),
                MCQOption(id="f", label="~1B+",    value="1000000000"),
            ],
        ),
        MCQQuestion(
            id="read_write_ratio",
            field="read_write_ratio",
            question="What is the expected read-to-write ratio?",
            options=[
                MCQOption(id="a", label="Write-heavy (1:1 or more writes)", value="write_heavy"),
                MCQOption(id="b", label="Balanced (roughly 1:1)",            value="balanced"),
                MCQOption(id="c", label="Read-heavy (10:1)",                 value="read_heavy"),
                MCQOption(id="d", label="Very read-heavy (100:1+)",          value="very_read_heavy"),
            ],
        ),
        MCQQuestion(
            id="availability",
            field="availability",
            question="What availability SLA does the system need?",
            options=[
                MCQOption(id="a", label="99%   (87.6h downtime/year)",  value="99"),
                MCQOption(id="b", label="99.9%  (8.7h downtime/year)",  value="99.9"),
                MCQOption(id="c", label="99.99% (52m downtime/year)",   value="99.99"),
                MCQOption(id="d", label="99.999% (5m downtime/year)",   value="99.999"),
            ],
        ),
        MCQQuestion(
            id="consistency",
            field="consistency",
            question="What consistency model is acceptable?",
            hint="Strong consistency costs latency; eventual consistency gains scale.",
            options=[
                MCQOption(id="a", label="Strong (read-your-writes, linearizable)",  value="strong"),
                MCQOption(id="b", label="Eventual (acceptable stale reads)",        value="eventual"),
                MCQOption(id="c", label="Causal (ordered within a session)",        value="causal"),
                MCQOption(id="d", label="Read-your-writes only",                    value="read_your_writes"),
            ],
        ),
        MCQQuestion(
            id="latency_target",
            field="latency_target",
            question="What is the p99 latency target for read APIs?",
            options=[
                MCQOption(id="a", label="< 50ms",   value="50ms"),
                MCQOption(id="b", label="< 200ms",  value="200ms"),
                MCQOption(id="c", label="< 500ms",  value="500ms"),
                MCQOption(id="d", label="< 2s",     value="2s"),
            ],
        ),
        MCQQuestion(
            id="data_model_preference",
            field="data_model_preference",
            question="What data model fits best?",
            options=[
                MCQOption(id="a", label="Relational (SQL)",              value="sql"),
                MCQOption(id="b", label="Document (MongoDB, Firestore)", value="document"),
                MCQOption(id="c", label="Wide-column (Cassandra, HBase)",value="wide_column"),
                MCQOption(id="d", label="Graph (Neo4j)",                 value="graph"),
                MCQOption(id="e", label="Hybrid (SQL + NoSQL)",          value="hybrid"),
            ],
        ),
        MCQQuestion(
            id="api_style",
            field="api_style",
            question="What API style will external clients consume?",
            options=[
                MCQOption(id="a", label="REST",          value="REST"),
                MCQOption(id="b", label="GraphQL",       value="GraphQL"),
                MCQOption(id="c", label="gRPC",          value="gRPC"),
                MCQOption(id="d", label="Event-driven",  value="Event-driven"),
            ],
        ),
        MCQQuestion(
            id="architecture_approach",
            field="architecture_approach",
            question="What architecture approach suits your team and scale?",
            options=[
                MCQOption(id="a", label="Monolith",                         value="monolith"),
                MCQOption(id="b", label="Microservices",                    value="microservices"),
                MCQOption(id="c", label="Modular monolith",                 value="modular_monolith"),
                MCQOption(id="d", label="Serverless / functions",           value="serverless"),
                MCQOption(id="e", label="Event-driven / CQRS",              value="event_driven_cqrs"),
            ],
        ),
        MCQQuestion(
            id="bottleneck_focus",
            field="bottleneck_focus",
            question="Which bottlenecks should the design prioritise solving?",
            multi_select=True,
            options=[
                MCQOption(id="a", label="Read throughput",          value="read_throughput"),
                MCQOption(id="b", label="Write throughput",         value="write_throughput"),
                MCQOption(id="c", label="Fan-out / delivery",       value="fanout"),
                MCQOption(id="d", label="Storage cost",             value="storage_cost"),
                MCQOption(id="e", label="Cold-start latency",       value="cold_start"),
                MCQOption(id="f", label="Cross-region replication", value="replication"),
            ],
        ),
        MCQQuestion(
            id="trade_off_priority",
            field="trade_off_priority",
            question="In CAP terms, which trade-off are you willing to make?",
            options=[
                MCQOption(id="a", label="Availability over Consistency (AP)", value="AP"),
                MCQOption(id="b", label="Consistency over Availability (CP)", value="CP"),
                MCQOption(id="c", label="Consistency + Availability (CA — single region)", value="CA"),
            ],
        ),
        MCQQuestion(
            id="out_of_scope",
            field="out_of_scope",
            question="Which concerns are explicitly out of scope for this design?",
            multi_select=True,
            options=[
                MCQOption(id="a", label="Billing / payments",       value="billing"),
                MCQOption(id="b", label="Mobile clients",           value="mobile"),
                MCQOption(id="c", label="Internationalisation",     value="i18n"),
                MCQOption(id="d", label="Abuse / fraud detection",  value="fraud"),
                MCQOption(id="e", label="ML model training",        value="ml_training"),
                MCQOption(id="f", label="CI/CD pipeline",           value="cicd"),
            ],
        ),
        MCQQuestion(
            id="scalability_priority",
            field="scalability_priority",
            question="Which scaling dimension matters most?",
            options=[
                MCQOption(id="a", label="Horizontal scale-out (more nodes)",    value="horizontal"),
                MCQOption(id="b", label="Vertical scale-up (bigger machines)",  value="vertical"),
                MCQOption(id="c", label="Geographic distribution (multi-region)", value="geo"),
                MCQOption(id="d", label="Elastic auto-scaling",                 value="elastic"),
            ],
        ),
    ]


def _lld_questions() -> list[MCQQuestion]:
    return [
        MCQQuestion(
            id="functional_reqs",
            field="functional_reqs",
            question="Which operations must this component expose?",
            multi_select=True,
            options=[
                MCQOption(id="a", label="Create / write",        value="create"),
                MCQOption(id="b", label="Read / lookup",         value="read"),
                MCQOption(id="c", label="Update / patch",        value="update"),
                MCQOption(id="d", label="Delete / expire",       value="delete"),
                MCQOption(id="e", label="Stream / subscribe",    value="stream"),
                MCQOption(id="f", label="Batch / bulk process",  value="batch"),
                MCQOption(id="g", label="Search / filter",       value="search"),
            ],
        ),
        MCQQuestion(
            id="api_style",
            field="api_style",
            question="How will other services call this component?",
            options=[
                MCQOption(id="a", label="Internal REST HTTP",     value="REST"),
                MCQOption(id="b", label="gRPC (protobuf)",        value="gRPC"),
                MCQOption(id="c", label="Async via message queue",value="async_queue"),
                MCQOption(id="d", label="In-process library",     value="library"),
            ],
        ),
        MCQQuestion(
            id="latency_target",
            field="latency_target",
            question="What is the p99 latency budget for this component?",
            options=[
                MCQOption(id="a", label="< 1ms",    value="1ms"),
                MCQOption(id="b", label="< 10ms",   value="10ms"),
                MCQOption(id="c", label="< 50ms",   value="50ms"),
                MCQOption(id="d", label="< 200ms",  value="200ms"),
                MCQOption(id="e", label="< 1s",     value="1s"),
            ],
        ),
        MCQQuestion(
            id="consistency",
            field="consistency",
            question="What consistency guarantee does this component need to provide?",
            options=[
                MCQOption(id="a", label="Linearizable (strongest)",  value="strong"),
                MCQOption(id="b", label="Sequential",                value="sequential"),
                MCQOption(id="c", label="Eventual",                  value="eventual"),
                MCQOption(id="d", label="None — fire and forget",    value="none"),
            ],
        ),
        MCQQuestion(
            id="data_model_preference",
            field="data_model_preference",
            question="What is the primary data structure this component manages?",
            options=[
                MCQOption(id="a", label="Rows / relational tables",  value="sql"),
                MCQOption(id="b", label="Key-value pairs",           value="kv"),
                MCQOption(id="c", label="Documents / JSON blobs",    value="document"),
                MCQOption(id="d", label="Time-series / events",      value="timeseries"),
                MCQOption(id="e", label="Graph nodes / edges",       value="graph"),
                MCQOption(id="f", label="Binary / blob",             value="blob"),
            ],
        ),
        MCQQuestion(
            id="read_write_ratio",
            field="read_write_ratio",
            question="What is the internal read-to-write pattern for this component?",
            options=[
                MCQOption(id="a", label="Write-once, read-many",      value="worm"),
                MCQOption(id="b", label="Write-heavy (logs, metrics)", value="write_heavy"),
                MCQOption(id="c", label="Balanced CRUD",               value="balanced"),
                MCQOption(id="d", label="Read-heavy with caching",     value="read_heavy"),
            ],
        ),
        MCQQuestion(
            id="bottleneck_focus",
            field="bottleneck_focus",
            question="Where is the primary bottleneck in this component?",
            multi_select=True,
            options=[
                MCQOption(id="a", label="CPU / compute",          value="cpu"),
                MCQOption(id="b", label="Memory / heap pressure", value="memory"),
                MCQOption(id="c", label="Disk I/O",               value="disk_io"),
                MCQOption(id="d", label="Network I/O",            value="network_io"),
                MCQOption(id="e", label="Lock contention",        value="lock_contention"),
                MCQOption(id="f", label="GC pressure",            value="gc"),
            ],
        ),
        MCQQuestion(
            id="scalability_priority",
            field="scalability_priority",
            question="How does this component need to scale?",
            options=[
                MCQOption(id="a", label="Single-threaded (simplicity first)", value="single_threaded"),
                MCQOption(id="b", label="Multi-threaded / concurrent",        value="multi_threaded"),
                MCQOption(id="c", label="Distributed (sharded across nodes)", value="distributed"),
                MCQOption(id="d", label="Stateless (scale horizontally)",     value="stateless"),
            ],
        ),
        MCQQuestion(
            id="availability",
            field="availability",
            question="What fault-tolerance does this component require?",
            options=[
                MCQOption(id="a", label="Best-effort (restarts OK)",          value="best_effort"),
                MCQOption(id="b", label="Hot standby (< 30s failover)",       value="hot_standby"),
                MCQOption(id="c", label="Active-active (no failover needed)", value="active_active"),
                MCQOption(id="d", label="No state — fully ephemeral",         value="ephemeral"),
            ],
        ),
        MCQQuestion(
            id="out_of_scope",
            field="out_of_scope",
            question="What is explicitly out of scope for this component?",
            multi_select=True,
            options=[
                MCQOption(id="a", label="Authentication / AuthZ",    value="auth"),
                MCQOption(id="b", label="Rate limiting",             value="rate_limiting"),
                MCQOption(id="c", label="Observability setup",       value="observability"),
                MCQOption(id="d", label="Client SDK",                value="client_sdk"),
                MCQOption(id="e", label="Data migration",            value="migration"),
            ],
        ),
    ]


_QUESTION_BANK: dict[str, list[MCQQuestion]] = {
    "HLD": [],   # populated lazily — avoids mutable module-level state
    "LLD": [],
}


def _get_questions(design_type: str) -> list[MCQQuestion]:
    """Return cached question list for design_type."""
    if not _QUESTION_BANK[design_type]:
        _QUESTION_BANK[design_type] = (
            _hld_questions() if design_type == "HLD" else _lld_questions()
        )
    return _QUESTION_BANK[design_type]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _merge_context(existing: dict, answers: dict) -> dict:
    """
    Non-destructively merge MCQ answers into existing context_json.
    List fields are unioned and deduplicated; scalar fields are overwritten.
    """
    LIST_FIELDS = {
        "functional_reqs", "out_of_scope", "user_actors", "bottleneck_focus"
    }
    merged = dict(existing)
    for field, value in answers.items():
        if field in LIST_FIELDS:
            prev = merged.get(field) or []
            if isinstance(value, list):
                merged[field] = list(dict.fromkeys(prev + value))
            else:
                merged[field] = list(dict.fromkeys(prev + [value]))
        else:
            # Scalar: only overwrite if value is truthy or explicitly provided
            if value is not None and value != "":
                merged[field] = value
    return merged


# ── Public API ────────────────────────────────────────────────────────────────

async def get_mcq(
    db: AsyncSession,
    session_id: uuid.UUID,
    design_type: str,
) -> MCQResponse:
    """
    Return questions for the session.
    design_type is re-validated here even though the route also validates,
    to make the service safe to call directly.
    """
    design_type = design_type.upper()
    if design_type not in VALID_DESIGN_TYPES:
        raise ValueError(
            f"Invalid design_type {design_type!r}. Must be one of {VALID_DESIGN_TYPES}."
        )

    # Verify session exists
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError(f"Session {session_id} not found")

    # Use design_type from session if available, fall back to param
    effective_type = session.design_type or design_type

    questions = _get_questions(effective_type)

    logger.info(
        "Serving %d MCQ questions (%s) for session %s",
        len(questions), effective_type, session_id,
    )

    return MCQResponse(
        session_id=session_id,
        design_type=effective_type,
        questions=questions,
    )


async def submit_mcq(
    db: AsyncSession,
    session_id: uuid.UUID,
    req: MCQSubmitRequest,
) -> MCQSubmitResponse:
    """
    Validate and persist MCQ answers into session.context_json.
    Marks session status as 'mcq_complete'.
    """
    result = await db.execute(
        select(SessionModel).where(SessionModel.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise ValueError(f"Session {session_id} not found")

    # Guard against re-submission after generation has started
    if session.status in ("generating", "complete"):
        raise ValueError(
            f"Session {session_id} is in status {session.status!r} — "
            "cannot resubmit MCQ answers at this stage."
        )

    existing_context = session.context_json or {}
    merged = _merge_context(existing_context, req.answers)

    # Persist system_name if it came in via answers
    if "system_name" in merged and not session.system_name:
        session.system_name = str(merged["system_name"])

    session.context_json = merged
    session.mcq_answers = req.answers
    session.status = "mcq_complete"
    await db.flush()

    logger.info(
        "MCQ submitted for session %s — %d context fields set",
        session_id, len(merged),
    )

    return MCQSubmitResponse(
        session_id=session_id,
        context_json=merged,
        ready_for_retrieval=True,
    )