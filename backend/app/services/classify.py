import logging
from typing import Dict, Any
from app.core.gemini import gemini_generate

logger = logging.getLogger(__name__)

PROMPT = """You are a system design interviewer classifier.
Determine if a prompt requires HLD (Architecture, Scale) or LLD (Data structures, Algorithms).
Respond with JSON: {"type": "HLD"|"LLD", "confidence": 0.0-1.0, "reasoning": "...", "keywords": []}"""

async def classify_prompt(prompt: str) -> Dict[str, Any]:
    result = await gemini_generate(prompt=prompt, system_prompt=PROMPT, json_mode=True)
    parsed = result["parsed"]
    if not isinstance(parsed, dict) or "type" not in parsed:
        return {"type": "HLD", "confidence": 0.6, "reasoning": "Fallback", "keywords": []}
    return {
        "type": parsed["type"] if parsed["type"] in ("HLD", "LLD") else "HLD",
        "confidence": float(parsed.get("confidence", 0.7)),
        "reasoning": parsed.get("reasoning", "Default"),
        "keywords": parsed.get("keywords", []),
    }