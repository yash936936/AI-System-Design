"""
Gemini API client.
Includes both the google.generativeai SDK implementation (from GitHub)
and the httpx implementation (from User).
"""

import asyncio
import hashlib
import json
import time
import logging
from typing import Any

import httpx
import google.generativeai as genai
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# ── SDK Implementation (GitHub) ───────────────────────────────────────────────
genai.configure(api_key=settings.gemini_api_key)

_rpm_semaphore = asyncio.Semaphore(settings.gemini_max_rpm)
_rpm_window_start: float = time.monotonic()
_rpm_call_count: int = 0

_response_cache: dict[str, tuple[Any, float]] = {}
_CACHE_TTL_SECONDS = 86400

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

def gemini_embed_sdk(text: str) -> list[float]:
    result = asyncio.get_event_loop().run_in_executor(
        None,
        lambda: genai.embed_content(
            model=settings.gemini_embed_model,
            content=text,
            task_type="retrieval_query",
        )
    )
    return result["embedding"]

# ── HTTPX Implementation (User) ───────────────────────────────────────────────
_sem = asyncio.Semaphore(getattr(settings, "gemini_rpm_limit", getattr(settings, "gemini_max_rpm", 5)))

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"
EMBED_MODEL = "models/gemini-embedding-001"
GEN_MODEL = "models/gemini-2.5-pro"

def _headers() -> dict:
    return {"Content-Type": "application/json"}

def _key_param() -> dict:
    return {"key": settings.gemini_api_key}

class GeminiRateLimitError(Exception):
    pass

class GeminiError(Exception):
    pass

@retry(
    retry=retry_if_exception_type(GeminiRateLimitError),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(4),
)
async def gemini_embed(text: str) -> list[float]:
    async with _sem:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{GEMINI_BASE}/{EMBED_MODEL}:embedContent",
                params=_key_param(),
                headers=_headers(),
                json={
                    "model": EMBED_MODEL,
                    "content": {"parts": [{"text": text}]},
                },
            )
        if resp.status_code == 429:
            raise GeminiRateLimitError("Gemini rate limit hit")
        if resp.status_code != 200:
            raise GeminiError(f"Embed failed: {resp.status_code} {resp.text}")
        return resp.json()["embedding"]["values"]

@retry(
    retry=retry_if_exception_type(GeminiRateLimitError),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(4),
)
async def gemini_generate_json(
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 8192,
) -> dict[str, Any]:
    async with _sem:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{GEMINI_BASE}/{GEN_MODEL}:generateContent",
                params=_key_param(),
                headers=_headers(),
                json={
                    "system_instruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "responseMimeType": "application/json",
                        "maxOutputTokens": max_tokens,
                        "temperature": 0.2,
                    },
                },
            )
    if resp.status_code == 429:
        raise GeminiRateLimitError("Gemini rate limit hit")
    if resp.status_code != 200:
        raise GeminiError(f"Generation failed: {resp.status_code} {resp.text}")

    raw = resp.json()
    try:
        text = raw["candidates"][0]["content"]["parts"][0]["text"]
        text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        return json.loads(text)
    except (KeyError, json.JSONDecodeError) as e:
        raise GeminiError(f"Failed to parse Gemini JSON response: {e}\nRaw: {raw}") from e