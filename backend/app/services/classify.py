import logging
from app.core.gemini import gemini_generate
from app.schemas.schemas import ClassifyResponse

logger = logging.getLogger(__name__)

async def classify_prompt(prompt: str) -> ClassifyResponse:
    system_prompt = """You are an expert system design interviewer. Classify the user's prompt into 'hld' (High-Level Design), 'lld' (Low-Level Design), or 'unknown'.
    Output ONLY a JSON object with keys: "type", "confidence" (float 0.0-1.0), and "reasoning"."""
    
    try:
        result = await gemini_generate(prompt=prompt, system_prompt=system_prompt, json_mode=True)
        parsed = result.get("parsed")
        if parsed:
            return ClassifyResponse(
                type=parsed.get("type", "unknown"),
                confidence=float(parsed.get("confidence", 0.5)),
                reasoning=parsed.get("reasoning", "LLM parsed successfully")
            )
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        
    prompt_lower = prompt.lower()
    if "architecture" in prompt_lower or "scale" in prompt_lower:
        return ClassifyResponse(type="hld", confidence=0.8, reasoning="Heuristic fallback")
    elif "class" in prompt_lower or "api" in prompt_lower:
        return ClassifyResponse(type="lld", confidence=0.8, reasoning="Heuristic fallback")
        
    return ClassifyResponse(type="unknown", confidence=0.5, reasoning="Could not determine design type")