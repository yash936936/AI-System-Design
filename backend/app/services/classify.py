"""
Phase A — Intent Classification.
Merged from GitHub and User implementations.
"""
from app.core.gemini import gemini_generate, gemini_generate_json
from app.schemas.schemas import ClassifyResponse

# ── GitHub Implementation ─────────────────────────────────────────────────────

SYSTEM_PROMPT_GH = """You are a system design expert. Your only job is to classify a user's prompt as either HLD (High-Level Design) or LLD (Low-Level Design).

HLD signals:
- "design X" where X is a product or system (Twitter, Uber, WhatsApp, Netflix)
- "architecture of", "system design for", "how does X work at scale"
- Focus on components, services, data flow, trade-offs at a system level

LLD signals:
- "implement X", "low-level design of", "deep dive into X component"
- "design the data structure for", "how would you code X"
- Focus on a single component's internals, algorithms, data structures, concurrency

Rules:
- If ambiguous, default to HLD
- Return ONLY valid JSON, no preamble, no markdown fences

Output schema:
{
 "type": "HLD" | "LLD",
 "confidence": float between 0 and 1,
 "reasoning": "one sentence explaining the classification",
 "suggested_correction": "LLD" if type is "HLD", else "HLD"
}"""

async def classify_prompt_gh(prompt: str) -> ClassifyResponse:
    result = await gemini_generate(
        prompt=f'Classify this prompt: "{prompt}"',
        system_prompt=SYSTEM_PROMPT_GH,
        json_mode=True,
        use_cache=True,
    )

    data = result["parsed"]
    return ClassifyResponse(
        session_id=None,  # GitHub version doesn't return session_id
        design_type=data["type"],
        system_name=None,
        confidence=float(data["confidence"]),
        reasoning=data["reasoning"],
        type=data["type"],
        suggested_correction=data["suggested_correction"],
    )

# ── User Implementation ───────────────────────────────────────────────────────

_CLASSIFY_SYSTEM = """You are a system design classification engine.
Output ONLY valid JSON — no preamble, no markdown fences.
Classify the user's prompt as either HLD (High Level Design) or LLD (Low Level Design).

HLD = overall distributed system architecture (multiple services, scaling, data flow)
LLD = deep dive into a single component or service (class design, algorithm, API internals)

Also extract the canonical system name if one is mentioned (e.g. "Twitter", "payment service").
"""

def _classify_user_prompt(prompt: str) -> str:
    return f"""Classify this system design prompt:

\"{prompt}\"

Output JSON:
{{
  "design_type": "HLD" | "LLD",
  "system_name": "string or null",
  "confidence": 0.0-1.0,
  "reasoning": "one sentence explanation"
}}"""

async def classify_prompt(db, req) -> ClassifyResponse:
    from app.db.models import Session as SessionModel
    raw = await gemini_generate_json(_CLASSIFY_SYSTEM, _classify_user_prompt(req.prompt))

    design_type = raw.get("design_type", "HLD")
    if design_type not in ("HLD", "LLD"):
        design_type = "HLD"

    system_name: str | None = raw.get("system_name") or None
    confidence = float(raw.get("confidence", 0.8))
    reasoning = str(raw.get("reasoning", ""))

    session = SessionModel(
        prompt=req.prompt,
        design_type=design_type,
        system_name=system_name,
        context_json={},
        status="classified",
    )
    db.add(session)
    await db.flush()

    return ClassifyResponse(
        session_id=session.id,
        design_type=design_type,
        system_name=system_name,
        confidence=confidence,
        reasoning=reasoning,
    )