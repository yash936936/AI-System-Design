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
if settings.gemini_api_key:
    genai.configure(api_key=settings.gemini_api_key)
else:
    logger.warning("GEMINI_API_KEY is not set. Gemini calls will fail.")

# ── Rate limit: 14 concurrent calls per 60s window ────────────────────────────
_rpm_semaphore = asyncio.Semaphore(settings.gemini_max_rpm)
_rpm_window_start: float = time.monotonic()
_rpm_call_count: int = 0

# ── Simple in-memory cache ────────────────────────────────────────────────────
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
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    cache_key = _cache_key(settings.gemini_model, full_prompt)

    if use_cache:
        cached = _get_cached(cache_key)
        if cached:
            logger.info("gemini_generate: cache hit")
            return {**cached, "cached": True}

    async with _rpm_semaphore:
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
        try:
            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: model.generate_content(prompt)
            )
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise

        duration_ms = int((time.monotonic() - t0) * 1000)
        raw_text = response.text
        
        # Safe token extraction
        usage = getattr(response, 'usage_metadata', None)
        tokens_in = usage.prompt_token_count if usage else 0
        tokens_out = usage.candidates_token_count if usage else 0

        parsed = None
        if json_mode:
            try:
                parsed = json.loads(raw_text)
            except json.JSONDecodeError:
                clean = raw_text.strip()
                if clean.startswith("```json"): clean = clean[7:]
                elif clean.startswith("```"): clean = clean[3:]
                if clean.endswith("```"): clean = clean[:-3]
                clean = clean.strip()
                
                try:
                    parsed = json.loads(clean)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from Gemini: {e}\nRaw text: {raw_text}")
                    parsed = None

        result = {
            "text": raw_text,
            "parsed": parsed,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "duration_ms": duration_ms,
            "cached": False,
        }

        if use_cache and parsed is not None:
            _set_cached(cache_key, result)

        return result

async def gemini_embed(text: str, task_type: str = "retrieval_query") -> list[float]:
    """
    task_type: "retrieval_document" when embedding content going INTO the
    vector store (e.g. famous-design ingestion), "retrieval_query" when
    embedding a search query going against it — Gemini's embedding model
    is asymmetric and indexes/queries embedded with the matching task_type
    retrieve noticeably better than embedding everything the same way.
    """
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: genai.embed_content(
            model=settings.gemini_embed_model,
            content=text,
            task_type=task_type,
        )
    )
    return result["embedding"]