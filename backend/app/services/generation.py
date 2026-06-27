"""
Generation Service (Phase D)
=============================
Generates 5 sections via Gemini with batching strategy:
  D1 (Architecture) → 1 solo call
  D2+D3 (Capacity+DataModel) → 1 batched call
  D4+D5 (API+Stack) → 1 batched call
Total: 3 Gemini calls
"""
import logging
from typing import AsyncGenerator, Any, Dict
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.gemini import gemini_generate
from app.db.models import GenerationOutput

logger = logging.getLogger(__name__)


# ── System Prompts ────────────────────────────────────────────────────────────

ARCH_SYSTEM_PROMPT = """You are a senior system architect. Generate a component graph as JSON.

Output schema:
{
  "components": [
    {
      "id": "snake_case_id",
      "name": "Human Readable Name",
      "type": "frontend|backend|database|queue|cache|cdn|auth|storage|third_party|ai",
      "description": "One sentence description",
      "responsibilities": ["resp1", "resp2"],
      "connections": ["other_component_id1", "other_component_id2"]
    }
  ]
}

Rules:
- 8-15 components depending on system complexity
- Every component must have at least one connection
- Use standard naming: api_gateway, auth_service, user_service, etc.
- Include load balancers, caches, CDNs, message queues where appropriate
"""


CAPACITY_SYSTEM_PROMPT = """You are a capacity planning expert. Generate capacity estimates.

Output schema:
{
  "capacity": {
    "dau": 50000000,
    "peak_read_qps": 69444,
    "peak_write_qps": 5787,
    "daily_storage_gb": 50,
    "five_year_storage_tb": 91,
    "bandwidth_gbps": 0.46,
    "cache_dataset_gb": 200,
    "formulas": {
      "peak_read_qps": "50M DAU × 100 reads/day × 1.2 peak / 86400s = 69,444 QPS"
    }
  }
}

Rules:
- Use the DAU from context to calculate all metrics
- Show formulas for transparency
- Use standard assumptions: 86400s/day, 1.2x peak factor
"""


DATA_MODEL_SYSTEM_PROMPT = """You are a database architect. Generate the data model.

Output schema:
{
  "data_model": {
    "decision": "SQL|NoSQL|Hybrid",
    "rationale": "Why this choice based on context",
    "entities": [
      {
        "name": "table_name",
        "columns": [
          {"name": "col", "type": "TYPE", "primary": true, "indexed": true}
        ],
        "sharding_key": "col_name or null",
        "access_patterns": ["pattern1", "pattern2"]
      }
    ]
  }
}
"""


API_SYSTEM_PROMPT = """You are an API architect. Generate the API design.

Output schema:
{
  "api_design": {
    "style": "REST|GraphQL|gRPC",
    "auth": "JWT Bearer|OAuth2|API Key",
    "endpoints": [
      {
        "method": "GET|POST|PUT|DELETE",
        "path": "/v1/resource",
        "description": "What it does",
        "query_params": {"param": "type"},
        "response": {"field": "type"},
        "rate_limit": "100 req/min per user"
      }
    ]
  }
}
"""


STACK_SYSTEM_PROMPT = """You are a tech stack advisor. Generate layer-by-layer recommendations.

Output schema:
{
  "stack": {
    "layers": [
      {
        "layer": "database|cache|queue|frontend|backend|cdn|auth|monitoring",
        "primary": "Technology Name",
        "alternatives": ["Alt1", "Alt2"],
        "rationale": "Why this choice based on context",
        "trade_off": "What you're giving up"
      }
    ]
  }
}

Rules:
- Every choice must reference specific requirements
- No generic recommendations — tie everything to context
- Include managed vs self-hosted trade-offs
"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _build_context_block(context: Dict[str, Any]) -> str:
    """Convert context dict to readable prompt block."""
    lines = []
    for key, value in context.items():
        if value and value != [] and value != {} and value is not None:
            readable_key = key.replace("_", " ").title()
            if isinstance(value, list):
                lines.append(f"- {readable_key}: {', '.join(str(v) for v in value)}")
            else:
                lines.append(f"- {readable_key}: {value}")
    return "\n".join(lines) if lines else "No specific context provided."


def _build_prompt(context: Dict[str, Any], design_type: str, sections: list[str]) -> str:
    """Build the full prompt for generation."""
    context_block = _build_context_block(context)
    section_list = "\n".join(f"  - {s}" for s in sections)
    
    return f"""Design Type: {design_type}

User Requirements:
{context_block}

Generate the following sections as a single JSON object:
{section_list}

Each section should be a top-level key in the JSON output.
Be specific, reference the context, and avoid generic answers.
"""


# ── Section Generators ────────────────────────────────────────────────────────

async def _generate_architecture(
    context: Dict[str, Any], design_type: str
) -> Dict[str, Any]:
    """D1 — Architecture diagram (solo call, largest output)."""
    prompt = _build_prompt(context, design_type, ["architecture"])
    
    result = await gemini_generate(
        prompt=prompt,
        system_prompt=ARCH_SYSTEM_PROMPT,
        json_mode=True,
        use_cache=True,
    )
    
    parsed = result["parsed"] or {}
    
    # Normalize: Gemini might return {"components": [...]} or {"architecture": {"components": [...]}}
    if "components" not in parsed:
        if "architecture" in parsed and isinstance(parsed["architecture"], dict):
            parsed = parsed["architecture"]
        else:
            parsed = {"components": []}
    
    return {
        "payload": parsed,
        "tokens_used": result["tokens_in"] + result["tokens_out"],
        "duration_ms": result["duration_ms"],
        "cached": result["cached"],
    }


async def _generate_capacity_and_data_model(
    context: Dict[str, Any], design_type: str
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """D2+D3 — Batched call for capacity and data model."""
    prompt = _build_prompt(context, design_type, ["capacity", "data_model"])
    
    result = await gemini_generate(
        prompt=prompt,
        system_prompt=f"{CAPACITY_SYSTEM_PROMPT}\n\n{DATA_MODEL_SYSTEM_PROMPT}",
        json_mode=True,
        use_cache=True,
    )
    
    parsed = result["parsed"] or {}
    tokens = result["tokens_in"] + result["tokens_out"]
    duration = result["duration_ms"]
    
    # Extract capacity
    capacity_payload = parsed.get("capacity", {})
    if not capacity_payload and "capacity" not in parsed:
        capacity_payload = parsed  # Fallback
    
    # Extract data model
    data_model_payload = parsed.get("data_model", {})
    if not data_model_payload and "data_model" not in parsed:
        data_model_payload = {}
    
    return (
        {
            "payload": capacity_payload,
            "tokens_used": tokens // 2,
            "duration_ms": duration // 2,
            "cached": result["cached"],
        },
        {
            "payload": data_model_payload,
            "tokens_used": tokens // 2,
            "duration_ms": duration // 2,
            "cached": result["cached"],
        },
    )


async def _generate_api_and_stack(
    context: Dict[str, Any], design_type: str
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """D4+D5 — Batched call for API design and tech stack."""
    prompt = _build_prompt(context, design_type, ["api_design", "stack"])
    
    result = await gemini_generate(
        prompt=prompt,
        system_prompt=f"{API_SYSTEM_PROMPT}\n\n{STACK_SYSTEM_PROMPT}",
        json_mode=True,
        use_cache=True,
    )
    
    parsed = result["parsed"] or {}
    tokens = result["tokens_in"] + result["tokens_out"]
    duration = result["duration_ms"]
    
    api_payload = parsed.get("api_design", {})
    stack_payload = parsed.get("stack", {})
    
    return (
        {
            "payload": api_payload,
            "tokens_used": tokens // 2,
            "duration_ms": duration // 2,
            "cached": result["cached"],
        },
        {
            "payload": stack_payload,
            "tokens_used": tokens // 2,
            "duration_ms": duration // 2,
            "cached": result["cached"],
        },
    )


# ── Main Streaming Generator ──────────────────────────────────────────────────

async def stream_generation(
    session_id: str,
    context: Dict[str, Any],
    design_type: str,
    db: AsyncSession,
) -> AsyncGenerator[Dict[str, Any], None]:
    """
    Main generation pipeline. Yields events for each section.
    
    Event flow:
    1. Create GenerationOutput rows (status=pending)
    2. Stream D1 (architecture) — solo call
    3. Stream D2+D3 (capacity+data_model) — batched
    4. Stream D4+D5 (api_design+stack) — batched
    5. Yield done event
    """
    
    # Create output rows for tracking
    sections = ["architecture", "capacity", "data_model", "api_design", "stack"]
    output_rows = {}
    
    for section in sections:
        output = GenerationOutput(
            session_id=session_id,
            section=section,
            status="pending",
        )
        db.add(output)
        output_rows[section] = output
    
    await db.flush()
    
    # ── D1: Architecture (solo call) ──────────────────────────────────────
    yield {"section": "architecture", "status": "started"}
    
    try:
        result = await _generate_architecture(context, design_type)
        yield {
            "section": "architecture",
            "status": "complete",
            "payload": result["payload"],
            "tokens_used": result["tokens_used"],
            "duration_ms": result["duration_ms"],
            "cached": result["cached"],
        }
        
        # Update DB
        output_rows["architecture"].status = "complete"
        output_rows["architecture"].payload_json = result["payload"]
        output_rows["architecture"].tokens_used = result["tokens_used"]
        output_rows["architecture"].duration_ms = result["duration_ms"]
        output_rows["architecture"].cached = result["cached"]
        await db.flush()
        
    except Exception as e:
        logger.error(f"Architecture generation failed: {e}")
        yield {"section": "architecture", "status": "error", "error": str(e)}
        output_rows["architecture"].status = "error"
        await db.flush()
    
    # ── D2+D3: Capacity + Data Model (batched) ────────────────────────────
    yield {"section": "capacity", "status": "started"}
    yield {"section": "data_model", "status": "started"}
    
    try:
        cap_result, dm_result = await _generate_capacity_and_data_model(
            context, design_type
        )
        
        yield {
            "section": "capacity",
            "status": "complete",
            "payload": cap_result["payload"],
            "tokens_used": cap_result["tokens_used"],
            "duration_ms": cap_result["duration_ms"],
            "cached": cap_result["cached"],
        }
        yield {
            "section": "data_model",
            "status": "complete",
            "payload": dm_result["payload"],
            "tokens_used": dm_result["tokens_used"],
            "duration_ms": dm_result["duration_ms"],
            "cached": dm_result["cached"],
        }
        
        # Update DB
        output_rows["capacity"].status = "complete"
        output_rows["capacity"].payload_json = cap_result["payload"]
        output_rows["capacity"].tokens_used = cap_result["tokens_used"]
        output_rows["capacity"].duration_ms = cap_result["duration_ms"]
        output_rows["capacity"].cached = cap_result["cached"]
        
        output_rows["data_model"].status = "complete"
        output_rows["data_model"].payload_json = dm_result["payload"]
        output_rows["data_model"].tokens_used = dm_result["tokens_used"]
        output_rows["data_model"].duration_ms = dm_result["duration_ms"]
        output_rows["data_model"].cached = dm_result["cached"]
        
        await db.flush()
        
    except Exception as e:
        logger.error(f"Capacity/DataModel generation failed: {e}")
        yield {"section": "capacity", "status": "error", "error": str(e)}
        yield {"section": "data_model", "status": "error", "error": str(e)}
        output_rows["capacity"].status = "error"
        output_rows["data_model"].status = "error"
        await db.flush()
    
    # ── D4+D5: API Design + Stack (batched) ───────────────────────────────
    yield {"section": "api_design", "status": "started"}
    yield {"section": "stack", "status": "started"}
    
    try:
        api_result, stack_result = await _generate_api_and_stack(
            context, design_type
        )
        
        yield {
            "section": "api_design",
            "status": "complete",
            "payload": api_result["payload"],
            "tokens_used": api_result["tokens_used"],
            "duration_ms": api_result["duration_ms"],
            "cached": api_result["cached"],
        }
        yield {
            "section": "stack",
            "status": "complete",
            "payload": stack_result["payload"],
            "tokens_used": stack_result["tokens_used"],
            "duration_ms": stack_result["duration_ms"],
            "cached": stack_result["cached"],
        }
        
        # Update DB
        output_rows["api_design"].status = "complete"
        output_rows["api_design"].payload_json = api_result["payload"]
        output_rows["api_design"].tokens_used = api_result["tokens_used"]
        output_rows["api_design"].duration_ms = api_result["duration_ms"]
        output_rows["api_design"].cached = api_result["cached"]
        
        output_rows["stack"].status = "complete"
        output_rows["stack"].payload_json = stack_result["payload"]
        output_rows["stack"].tokens_used = stack_result["tokens_used"]
        output_rows["stack"].duration_ms = stack_result["duration_ms"]
        output_rows["stack"].cached = stack_result["cached"]
        
        await db.flush()
        
    except Exception as e:
        logger.error(f"API/Stack generation failed: {e}")
        yield {"section": "api_design", "status": "error", "error": str(e)}
        yield {"section": "stack", "status": "error", "error": str(e)}
        output_rows["api_design"].status = "error"
        output_rows["stack"].status = "error"
        await db.flush()
    
    await db.commit()
    
    # ── Done ──────────────────────────────────────────────────────────────
    yield {"section": "done", "status": "done"}