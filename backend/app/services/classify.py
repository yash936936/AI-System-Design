import logging
from app.core.gemini import gemini_generate
from app.schemas.schemas import ClassifyResponse

logger = logging.getLogger(__name__)

def _opposite(design_type: str) -> str:
    return "LLD" if design_type == "HLD" else "HLD"

async def classify_prompt(prompt: str) -> ClassifyResponse:
    system_prompt = """You are an expert system design interviewer. Classify the user's prompt
    into 'HLD' (High-Level Design) or 'LLD' (Low-Level Design). There is no 'unknown' option —
    always pick the closer of the two, even if the prompt is ambiguous, and reflect that
    ambiguity with a lower confidence score instead.
    Output ONLY a JSON object with keys: "type" ("HLD" or "LLD"), "confidence" (float 0.0-1.0),
    "reasoning" (string), and "keywords" (list of strings that influenced the decision)."""

    try:
        result = await gemini_generate(prompt=prompt, system_prompt=system_prompt, json_mode=True)
        parsed = result.get("parsed")
        if parsed:
            design_type = str(parsed.get("type", "HLD")).upper()
            if design_type not in ("HLD", "LLD"):
                design_type = "HLD"
            return ClassifyResponse(
                type=design_type,
                confidence=float(parsed.get("confidence", 0.5)),
                reasoning=parsed.get("reasoning", "LLM parsed successfully"),
                suggested_correction=_opposite(design_type),
                keywords=parsed.get("keywords") or None,
            )
    except Exception as e:
        logger.error(f"Classification failed, falling back to heuristic: {e}")

    # Heuristic fallback (used if Gemini call/parsing fails, e.g. no API key set)
    prompt_lower = prompt.lower()
    lld_signals = ["class", "data structure", "algorithm", "concurrency", "thread", "rate limiter"]
    hld_signals = ["architecture", "scale", "design a system", "design twitter", "design uber", "design "]

    if any(s in prompt_lower for s in lld_signals):
        design_type, confidence, reasoning = "LLD", 0.7, "Heuristic fallback: detected component/implementation-level keywords"
    elif any(s in prompt_lower for s in hld_signals):
        design_type, confidence, reasoning = "HLD", 0.7, "Heuristic fallback: detected system/architecture-level keywords"
    else:
        design_type, confidence, reasoning = "HLD", 0.5, "Heuristic fallback: defaulted to HLD, no strong signal found"

    return ClassifyResponse(
        type=design_type,
        confidence=confidence,
        reasoning=reasoning,
        suggested_correction=_opposite(design_type),
    )