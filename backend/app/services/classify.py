"""
Phase A — Intent Classification.
Single Gemini call. Result cached for session lifetime.
"""
from app.core.gemini import gemini_generate
from app.schemas.schemas import ClassifyResponse

SYSTEM_PROMPT = """You are a system design expert. Your only job is to classify a user's prompt as either HLD (High-Level Design) or LLD (Low-Level Design).

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


async def classify_prompt(prompt: str) -> ClassifyResponse:
    result = await gemini_generate(
        prompt=f'Classify this prompt: "{prompt}"',
        system_prompt=SYSTEM_PROMPT,
        json_mode=True,
        use_cache=True,
    )

    data = result["parsed"]
    return ClassifyResponse(
        type=data["type"],
        confidence=float(data["confidence"]),
        reasoning=data["reasoning"],
        suggested_correction=data["suggested_correction"],
    )
