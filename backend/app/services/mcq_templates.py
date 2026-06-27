from app.schemas.schemas import MCQTemplate, MCQCategory, MCQOption

# NOTE: the previous version of this file returned a quiz-style
# `questions: [{question, options: string[], correct_answer}]` shape.
# The frontend (MCQChipGroup.tsx, useStore.ts) expects `MCQTemplate.categories`,
# where each category has `options: {id, label}[]`, a `type` of
# 'single_select' | 'multi_select', and `allow_free_text`. This rewrite
# matches that contract exactly, and uses category ids that line up with
# `SessionContext` field names so the answers can be merged directly into
# session context on the frontend (functional_reqs, dau, read_write_ratio,
# consistency, availability, data_model_preference, api_style, latency_target).

def _hld_categories() -> list[MCQCategory]:
    return [
        MCQCategory(
            id="functional_reqs", label="Functional Requirements",
            question="Which core features does your system need to support?",
            type="multi_select", allow_free_text=True,
            free_text_placeholder="Add a feature...",
            options=[
                MCQOption(id="auth", label="User auth & profiles"),
                MCQOption(id="realtime_feed", label="Real-time feeds / notifications"),
                MCQOption(id="media_storage", label="Media upload & storage"),
                MCQOption(id="search", label="Search & discovery"),
                MCQOption(id="messaging", label="Messaging / chat"),
                MCQOption(id="payments", label="Payments & transactions"),
            ],
        ),
        MCQCategory(
            id="dau", label="Scale",
            question="What is the expected DAU (Daily Active Users)?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="10k", label="< 10K"),
                MCQOption(id="100k", label="10K – 100K"),
                MCQOption(id="1m", label="100K – 1M"),
                MCQOption(id="10m", label="1M – 10M"),
                MCQOption(id="100m", label="10M+"),
            ],
        ),
        MCQCategory(
            id="read_write_ratio", label="Read/Write Ratio",
            question="What is the expected read-to-write ratio?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="write_heavy", label="Write-heavy"),
                MCQOption(id="balanced", label="Balanced"),
                MCQOption(id="read_heavy", label="Read-heavy (10:1)"),
                MCQOption(id="very_read_heavy", label="Very read-heavy (100:1+)"),
            ],
        ),
        MCQCategory(
            id="consistency", label="Consistency",
            question="What consistency model is acceptable?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="strong", label="Strong"),
                MCQOption(id="eventual", label="Eventual"),
            ],
        ),
        MCQCategory(
            id="availability", label="Availability",
            question="What availability target should the system meet?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="99", label="99% ('two nines')"),
                MCQOption(id="99.9", label="99.9% ('three nines')"),
                MCQOption(id="99.99", label="99.99% ('four nines')"),
                MCQOption(id="99.999", label="99.999% ('five nines')"),
            ],
        ),
        MCQCategory(
            id="data_model_preference", label="Data Model",
            question="What data model fits best?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="sql", label="Relational (SQL)"),
                MCQOption(id="nosql", label="NoSQL"),
                MCQOption(id="hybrid", label="Hybrid"),
            ],
        ),
        MCQCategory(
            id="api_style", label="API Style",
            question="What API style will external clients consume?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="rest", label="REST"),
                MCQOption(id="graphql", label="GraphQL"),
                MCQOption(id="grpc", label="gRPC"),
            ],
        ),
    ]

def _lld_categories() -> list[MCQCategory]:
    return [
        MCQCategory(
            id="functional_reqs", label="Operations",
            question="Which operations must this component expose?",
            type="multi_select", allow_free_text=True,
            free_text_placeholder="Add an operation...",
            options=[
                MCQOption(id="create", label="Create / write"),
                MCQOption(id="read", label="Read / lookup"),
                MCQOption(id="update", label="Update / patch"),
                MCQOption(id="delete", label="Delete / expire"),
            ],
        ),
        MCQCategory(
            id="latency_target", label="Latency",
            question="What is the p99 latency budget?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="1ms", label="< 1ms"),
                MCQOption(id="10ms", label="< 10ms"),
                MCQOption(id="50ms", label="< 50ms"),
                MCQOption(id="200ms", label="< 200ms"),
            ],
        ),
        MCQCategory(
            id="data_model_preference", label="Data Structure",
            question="What is the primary data structure this component manages?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="sql", label="Relational tables"),
                MCQOption(id="kv", label="Key-value"),
                MCQOption(id="document", label="Documents"),
            ],
        ),
        MCQCategory(
            id="consistency", label="Concurrency",
            question="How should concurrent access be handled?",
            type="single_select", allow_free_text=False,
            options=[
                MCQOption(id="strong", label="Strict locking / strong consistency"),
                MCQOption(id="eventual", label="Lock-free / eventual consistency"),
            ],
        ),
    ]

def get_mcq_template(design_type: str) -> MCQTemplate:
    dt = design_type.upper()
    if dt == "HLD":
        return MCQTemplate(design_type="HLD", categories=_hld_categories())
    elif dt == "LLD":
        return MCQTemplate(design_type="LLD", categories=_lld_categories())
    return MCQTemplate(design_type=dt, categories=[])