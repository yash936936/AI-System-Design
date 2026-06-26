"""
Phase D — Generation prompt templates.

Bug fixes vs original:
1. format_context: str() cast + None filter on all list joins (no TypeError)
2. format_context: chunk text truncated to 800 chars (context limit safety)
3. SECTIONS kept in sync with actual generation keys
4. arch_user_prompt: LLD/HLD rule surfaced prominently, not buried
5. capacity_data_user_prompt: batch trade-off documented in comment
"""
from typing import Any

MAX_CHUNK_DISPLAY_CHARS = 800


# ── Shared context formatter ──────────────────────────────────────────────────

def format_context(
    ctx: dict[str, Any],
    prompt: str,
    design_type: str,
    chunks: list[dict],
) -> str:
    """
    Build the [CONTEXT] block injected into every generation prompt.

    Fix: all list joins use `str(x) for x in items if x is not None`
         to avoid TypeError when items contain non-strings or None.
    Fix: chunk text is truncated to MAX_CHUNK_DISPLAY_CHARS to prevent
         the assembled prompt from exceeding Gemini's context window.
    """
    def safe_join(items: list | None) -> str:
        if not items:
            return "none"
        return ", ".join(str(x) for x in items if x is not None)

    chunk_text = ""
    if chunks:
        chunk_text = "\n\n[RETRIEVED KNOWLEDGE]\n"
        for i, c in enumerate(chunks[:5], 1):
            text_preview = str(c.get("text", ""))[:MAX_CHUNK_DISPLAY_CHARS]
            chunk_text += (
                f"\n{i}. [{c.get('source', '')} — {c.get('section', '')}]"
                f" (score: {c.get('score', 0):.2f})\n{text_preview}\n"
            )

    return f"""[SESSION CONTEXT]
Design Type: {design_type}
Original Prompt: {prompt}
System Name: {ctx.get('system_name') or 'Unknown'}
Functional Requirements: {safe_join(ctx.get('functional_reqs'))}
Out of Scope: {safe_join(ctx.get('out_of_scope'))}
User Actors: {safe_join(ctx.get('user_actors'))}
Scale: {ctx.get('scale') or 'not specified'}
DAU: {ctx.get('dau') or 'not specified'}
Read/Write Ratio: {ctx.get('read_write_ratio') or 'not specified'}
Availability Target: {ctx.get('availability') or 'not specified'}
Consistency Model: {ctx.get('consistency') or 'not specified'}
Latency Target: {ctx.get('latency_target') or 'not specified'}
Data Model Preference: {ctx.get('data_model_preference') or 'not specified'}
API Style: {ctx.get('api_style') or 'not specified'}
Architecture Approach: {ctx.get('architecture_approach') or 'not specified'}
Bottleneck Focus: {safe_join(ctx.get('bottleneck_focus'))}
Scalability Priority: {ctx.get('scalability_priority') or 'not specified'}
Trade-off Priority: {ctx.get('trade_off_priority') or 'not specified'}
{chunk_text}"""


# ── D1 — Architecture ─────────────────────────────────────────────────────────

ARCH_SYSTEM = """You are a senior staff engineer generating system architecture designs.
Output ONLY valid JSON — no preamble, no markdown fences.
Base every decision on the SESSION CONTEXT provided.
Reference specific context values (DAU, consistency model, API style, etc.) in descriptions.
Never invent requirements not present in the context."""


def arch_user_prompt(context_block: str, design_type: str = "HLD") -> str:
    # FIX: design_type scope rule surfaced at top of prompt, not buried at bottom
    scope_rule = (
        "Focus on the full distributed system: all major services, data stores, "
        "CDN, queues, and client-facing gateways."
        if design_type == "HLD"
        else
        "Focus ONLY on the internal components of the single service being designed. "
        "Do not include unrelated external systems."
    )
    return f"""{context_block}

Scope rule for this {design_type}: {scope_rule}

Generate a complete architecture component graph.

Output JSON schema:
{{
  "components": [
    {{
      "id": "snake_case_id",
      "name": "Human Readable Name",
      "type": "client | gateway | backend | cache | queue | database | storage | cdn | external",
      "description": "What this component does — must reference a specific context value",
      "responsibilities": ["list", "of", "responsibilities"],
      "technology": "Specific named technology e.g. Redis 7, PostgreSQL 15, Nginx 1.25",
      "connections": ["ids", "of", "components", "this", "connects", "to"]
    }}
  ],
  "data_flows": [
    {{
      "from": "component_id",
      "to": "component_id",
      "label": "brief description of data/event flowing",
      "protocol": "HTTP | gRPC | WebSocket | TCP | async"
    }}
  ],
  "deployment_zones": [
    {{
      "zone": "CDN | Edge | App Tier | Data Tier | External",
      "components": ["component_ids_in_this_zone"]
    }}
  ],
  "key_design_decisions": [
    "Decision 1 — rationale referencing a specific context field value",
    "Decision 2 — rationale"
  ]
}}

Rules:
- HLD: 8-12 components covering the full system.
- LLD: 4-7 components covering the single service internals only.
- Every connection id must reference a valid component id in this response.
- technology must be a specific named product, never a generic term like 'NoSQL database'."""


# ── D2+D3 — Capacity + Data Model (batched) ───────────────────────────────────

CAPACITY_DATA_SYSTEM = """You are a senior systems engineer.
Output ONLY valid JSON — no preamble, no markdown fences.
All capacity numbers must be derived mathematically from the DAU/scale/read-write ratio in context.
Show your derivation formulas. Never invent numbers that cannot be derived from the context."""


def capacity_data_user_prompt(context_block: str) -> str:
    # NOTE: Capacity and data model are batched into one Gemini call to reduce
    # latency and cost. Trade-off: if the response is malformed, both sections
    # are lost. The generation orchestrator should handle this with a retry on
    # the full prompt rather than partial recovery.
    return f"""{context_block}

Generate capacity estimation AND data model in one JSON response.

Output JSON schema:
{{
  "capacity": {{
    "dau": <number — from context or estimated>,
    "peak_read_qps": <number>,
    "peak_write_qps": <number>,
    "daily_storage_gb": <number>,
    "five_year_storage_tb": <number>,
    "bandwidth_gbps": <number>,
    "cache_dataset_gb": <number>,
    "replication_factor": <number, typically 3>,
    "formulas": {{
      "peak_read_qps":    "e.g. DAU * avg_reads_per_day / 86400 * peak_multiplier",
      "peak_write_qps":   "formula string",
      "daily_storage_gb": "formula string",
      "bandwidth_gbps":   "formula string"
    }},
    "scaling_notes": "2-3 sentences on which numbers drive infrastructure decisions"
  }},
  "data_model": {{
    "decision": "SQL | NoSQL | Hybrid",
    "rationale": "1-2 sentences referencing specific context values that drove this choice",
    "primary_store": "Specific technology name and version",
    "secondary_stores": ["store name — what it holds"],
    "entities": [
      {{
        "name": "table_or_collection_name",
        "store": "which database",
        "columns": [
          {{
            "name": "col_name",
            "type": "SQL_TYPE or BSON_TYPE",
            "primary": true,
            "indexed": true,
            "nullable": false
          }}
        ],
        "sharding_key": "column name or null",
        "partition_strategy": "description or null",
        "access_patterns": ["pattern 1", "pattern 2"],
        "estimated_row_size_bytes": <number>
      }}
    ],
    "caching_strategy": "What gets cached, TTL, eviction policy, cache-aside vs write-through"
  }}
}}"""


# ── D4+D5 — API Design + Tech Stack (batched) ────────────────────────────────

API_STACK_SYSTEM = """You are a senior architect.
Output ONLY valid JSON — no preamble, no markdown fences.
Every technology choice must cite a specific context field value that justifies it.
Never give generic recommendations."""


def api_stack_user_prompt(context_block: str) -> str:
    # NOTE: API design and tech stack are batched. Same retry trade-off applies
    # as capacity_data — retry the full prompt on parse failure.
    return f"""{context_block}

Generate API design AND tech stack in one JSON response.

Output JSON schema:
{{
  "api_design": {{
    "style": "REST | GraphQL | gRPC | Event-driven",
    "auth": "JWT Bearer | API Key | OAuth2 | mTLS",
    "versioning": "URL path | Header | Query param",
    "rate_limiting": "strategy description e.g. token bucket per user, 100 req/min",
    "endpoints": [
      {{
        "method": "GET | POST | PUT | DELETE | PATCH",
        "path": "/v1/resource/{{id}}",
        "description": "what this endpoint does",
        "auth_required": true,
        "query_params": {{"param_name": "type and description"}},
        "request_body": {{"field": "type and description"}},
        "response": {{"field": "type and description"}},
        "rate_limit": "e.g. 100 req/min per user",
        "notes": "pagination strategy, caching headers, idempotency key etc."
      }}
    ],
    "error_handling": "Error response format, status codes used, retry guidance"
  }},
  "tech_stack": {{
    "layers": [
      {{
        "layer": "CDN | Load Balancer | API Gateway | Application | Cache | Message Queue | Database | Object Storage | Monitoring",
        "primary": "Specific technology + version",
        "alternatives": ["Alternative 1", "Alternative 2"],
        "rationale": "Why this choice — quote the specific context value that drove it",
        "trade_off": "What you give up vs the main alternative"
      }}
    ],
    "infrastructure": {{
      "deployment": "Kubernetes | ECS | Railway | Vercel | bare metal",
      "ci_cd": "GitHub Actions | CircleCI | etc.",
      "observability": ["Prometheus", "Grafana", "Jaeger"],
      "iac": "Terraform | Pulumi | CDK | none"
    }},
    "cost_estimate": "Rough monthly cost at the stated DAU/scale with per-service breakdown"
  }}
}}

Include 5-7 endpoints covering all functional_reqs from context.
Include 6-9 layers covering the full stack."""


# ── Section registry (kept in sync with Generation model columns) ─────────────

SECTIONS = ["architecture", "capacity_and_data", "api_and_stack"]

SECTION_LABELS = {
    "architecture":      "Architecture Diagram",
    "capacity_and_data": "Capacity & Data Model",
    "api_and_stack":     "API Design & Tech Stack",
}