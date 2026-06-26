"""
Gemini client with:
- asyncio.Semaphore to enforce max 14 RPM (free tier = 15 RPM, 1 buffer)
- JSON mode via response_mime_type
- Usage logging per call
- Simple in-memory response cache (keyed on sha256 of model+prompt)
"""
import asyncio
import hashlib
import json
import time
import logging
from typing import Any

import google.generativeai as genai
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── Initialise SDK ─────────────────────────────────────────────────────────────
genai.configure(api_key=settings.gemini_api_key)

# ── Rate limit: 14 concurrent calls per 60s window ────────────────────────────
_rpm_semaphore = asyncio.Semaphore(settings.gemini_max_rpm)
_rpm_window_start: float = time.monotonic()
_rpm_call_count: int = 0

# ── Simple in-memory cache (replace with Redis in Stage 4) ────────────────────
_response_cache: dict[str, tuple[Any, float]] = {}
_CACHE_TTL_SECONDS = 86400  # 24 hours


def _cache_key(model: str, prompt: str) -> str:
    raw = f"{model}::{prompt}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _get_cached(key: str) -> Any | None:
    if key in _response_cache:
        value, ts = _response_cache[key]
        if time.monotonic() - ts < _CACHE_TTL_SECONDS:
            return value
        del _response_cache[key]
    return None


def _set_cached(key: str, value: Any) -> None:
    _response_cache[key] = (value, time.monotonic())


# ── Core call wrapper ──────────────────────────────────────────────────────────

async def gemini_generate(
    prompt: str,
    system_prompt: str = "",
    json_mode: bool = True,
    use_cache: bool = True,
) -> dict[str, Any]:
    """
    Call gemini-1.5-flash with optional JSON mode and rate limiting.

    Returns:
        {
            "text": str,
            "parsed": dict | None,  # only if json_mode=True
            "tokens_in": int,
            "tokens_out": int,
            "cached": bool,
        }
    """
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    cache_key = _cache_key(settings.gemini_model, full_prompt)

    if use_cache:
        cached = _get_cached(cache_key)
        if cached:
            logger.info("gemini_generate: cache hit")
            return {**cached, "cached": True}

    async with _rpm_semaphore:
        # Enforce 60-second window reset
        global _rpm_window_start, _rpm_call_count
        now = time.monotonic()
        if now - _rpm_window_start >= 60:
            _rpm_window_start = now
            _rpm_call_count = 0
        _rpm_call_count += 1

        generation_config = genai.GenerationConfig(
            response_mime_type="application/json" if json_mode else "text/plain",
        )

        model = genai.GenerativeModel(
            model_name=settings.gemini_model,
            generation_config=generation_config,
            system_instruction=system_prompt if system_prompt else None,
        )

        t0 = time.monotonic()
        response = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: model.generate_content(prompt)
        )
        duration_ms = int((time.monotonic() - t0) * 1000)

    raw_text = response.text
    tokens_in = response.usage_metadata.prompt_token_count
    tokens_out = response.usage_metadata.candidates_token_count

    logger.info(
        "gemini_generate: model=%s tokens_in=%d tokens_out=%d duration_ms=%d",
        settings.gemini_model, tokens_in, tokens_out, duration_ms
    )

    parsed = None
    if json_mode:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            # Strip markdown fences if model wrapped output
            clean = raw_text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
            parsed = json.loads(clean)

    result = {
        "text": raw_text,
        "parsed": parsed,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "duration_ms": duration_ms,
        "cached": False,
    }

    if use_cache:
        _set_cached(cache_key, result)

    return result


async def gemini_embed(text: str) -> list[float]:
    """
    Embed text using text-embedding-004.
    Returns a 768-dimensional float vector.
    """
    result = await asyncio.get_event_loop().run_in_executor(
        None,
        lambda: genai.embed_content(
            model=settings.gemini_embed_model,
            content=text,
            task_type="retrieval_query",
        )
    )
    return result["embedding"]
