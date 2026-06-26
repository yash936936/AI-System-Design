"""
Gemini API client.
- SDK implementation (gemini_generate) — kept for potential future use
- HTTPX implementation (gemini_generate_json, gemini_embed) — actively used
- Real RPM + RPD enforcement (not cosmetic)
- Correct markdown-fence stripping via removeprefix/removesuffix
"""

import asyncio
import hashlib
import json
import time
import logging
from datetime import date
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


# =============================================================================
# ── SHARED: Real RPM + RPD enforcement ────────────────────────────────────────
# =============================================================================

class RateLimiter:
    """
    Thread-safe sliding-window RPM limiter + daily RPD counter.
    - acquire() blocks until a slot is available under BOTH limits.
    - Records each successful call for accounting.
    """

    def __init__(self, rpm: int, rpd: int):
        self.rpm = max(1, rpm)
        self.rpd = max(1, rpd)
        self._lock = asyncio.Lock()
        # Sliding window of call timestamps (monotonic seconds)
        self._rpm_timestamps: list[float] = []
        # Daily counter: (date, count)
        self._rpd_day: date = date.today()
        self._rpd_count: int = 0

    async def acquire(self) -> None:
        while True:
            async with self._lock:
                now_mono = time.monotonic()
                today = date.today()

                # Reset daily counter at midnight
                if today != self._rpd_day:
                    self._rpd_day = today
                    self._rpd_count = 0

                # Prune timestamps older than 60s
                cutoff = now_mono - 60.0
                self._rpm_timestamps = [
                    t for t in self._rpm_timestamps if t > cutoff
                ]

                rpm_ok = len(self._rpm_timestamps) < self.rpm
                rpd_ok = self._rpd_count < self.rpd

                if rpm_ok and rpd_ok:
                    # Reserve the slot
                    self._rpm_timestamps.append(now_mono)
                    self._rpd_count += 1
                    return

                # Calculate wait time
                if not rpm_ok:
                    # Wait until oldest timestamp in window expires
                    wait_secs = self._rpm_timestamps[0] - cutoff + 0.05
                else:
                    # RPD exhausted — wait until midnight
                    now = time.time()
                    tomorrow = time.mktime((today.year, today.month, today.day + 1,
                                            0, 0, 0, 0, 0, 0))
                    wait_secs = max(1.0, tomorrow - now)

            logger.warning(
                "Gemini rate limit reached (rpm_ok=%s, rpd_ok=%s) — sleeping %.2fs",
                rpm_ok, rpd_ok, wait_secs,
            )
            await asyncio.sleep(wait_secs)


# Single shared limiter for all Gemini calls
_limiter = RateLimiter(
    rpm=getattr(settings, "gemini_rpm_limit",
                getattr(settings, "gemini_max_rpm", 14)),
    rpd=getattr(settings, "gemini_max_rpd", 1800),
)


# =============================================================================
# ── SDK IMPLEMENTATION (kept, fixed) ──────────────────────────────────────────
# =============================================================================

genai.configure(api_key=settings.gemini_api_key)

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


def _strip_markdown_fences(text: str) -> str:
    """Correctly strip ```json / ``` fences using removeprefix/removesuffix."""
    t = text.strip()
    # Handle opening fence (```json or ```)
    if t.startswith("```"):
        first_nl = t.find("\n")
        if first_nl != -1:
            t = t[first_nl + 1:]
        else:
            t = t[3:]
    # Handle closing fence
    if t.endswith("```"):
        t = t[:-3]
    return t.strip()


async def gemini_generate(
    prompt: str,
    system_prompt: str = "",
    json_mode: bool = True,
    use_cache: bool = True,
) -> dict[str, Any]:
    """SDK-based generation. Respects settings.gemini_model. Enforces RPM/RPD."""
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
    cache_key = _cache_key(settings.gemini_model, full_prompt)

    if use_cache:
        cached = _get_cached(cache_key)
        if cached:
            logger.info("gemini_generate: cache hit")
            return {**cached, "cached": True}

    # Enforce real rate limits before calling
    await _limiter.acquire()

    generation_config = genai.GenerationConfig(
        response_mime_type="application/json" if json_mode else "text/plain",
    )

    model = genai.GenerativeModel(
        model_name=settings.gemini_model,  # FIX: now uses config, not hardcoded
        generation_config=generation_config,
        system_instruction=system_prompt if system_prompt else None,
    )

    t0 = time.monotonic()
    loop = asyncio.get_running_loop()
    response = await loop.run_in_executor(
        None,
        lambda: model.generate_content(prompt),
    )
    duration_ms = int((time.monotonic() - t0) * 1000)

    raw_text = response.text
    tokens_in = response.usage_metadata.prompt_token_count
    tokens_out = response.usage_metadata.candidates_token_count

    logger.info(
        "gemini_generate: model=%s tokens_in=%d tokens_out=%d duration_ms=%d",
        settings.gemini_model, tokens_in, tokens_out, duration_ms,
    )

    parsed = None
    if json_mode:
        try:
            parsed = json.loads(raw_text)
        except json.JSONDecodeError:
            # FIX: use proper fence stripping, not broken lstrip
            clean = _strip_markdown_fences(raw_text)
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


# =============================================================================
# ── HTTPX IMPLEMENTATION (actively used — fixed) ─────────────────────────────
# =============================================================================

GEMINI_BASE = "https://generativelanguage.googleapis.com/v1beta"


def _headers() -> dict:
    return {"Content-Type": "application/json"}


def _key_param() -> dict:
    return {"key": settings.gemini_api_key}


class GeminiRateLimitError(Exception):
    pass


class GeminiError(Exception):
    pass


class GeminiDailyLimitExceeded(Exception):
    """Raised when the daily RPD budget is exhausted."""
    pass


@retry(
    retry=retry_if_exception_type(GeminiRateLimitError),
    wait=wait_exponential(multiplier=2, min=4, max=30),
    stop=stop_after_attempt(4),
)
async def gemini_embed(text: str) -> list[float]:
    """Embed text. Uses settings.gemini_embed_model. Enforces RPM/RPD."""
    # Enforce real rate limits
    await _limiter.acquire()

    # FIX: use settings, not hardcoded
    embed_model = getattr(settings, "gemini_embed_model", "models/text-embedding-004")

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{GEMINI_BASE}/{embed_model}:embedContent",
            params=_key_param(),
            headers=_headers(),
            json={
                "model": embed_model,
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
    """
    Generate JSON via HTTPX. Uses settings.gemini_model. Enforces RPM/RPD.
    """
    # Enforce real rate limits
    await _limiter.acquire()

    # FIX: use settings, not hardcoded
    gen_model = getattr(settings, "gemini_model", "gemini-1.5-flash")
    # Google's HTTP API expects "models/" prefix
    if not gen_model.startswith("models/"):
        gen_model = f"models/{gen_model}"

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{GEMINI_BASE}/{gen_model}:generateContent",
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
        # FIX: use proper fence stripping (removeprefix/removesuffix),
        # not the broken lstrip("```json") which strips character sets
        text = _strip_markdown_fences(text)
        return json.loads(text)
    except (KeyError, json.JSONDecodeError) as e:
        raise GeminiError(f"Failed to parse Gemini JSON response: {e}\nRaw: {raw}") from e