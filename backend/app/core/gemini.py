import json
import time
import logging
from typing import Any
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
except ImportError:
    GEMINI_AVAILABLE = False

_cache: dict[str, dict] = {}

async def gemini_generate(prompt: str, system_prompt: str = "", json_mode: bool = True, use_cache: bool = True) -> dict[str, Any]:
    start_time = time.time()
    cache_key = f"{system_prompt[:100]}:{prompt[:200]}"
    
    if use_cache and cache_key in _cache:
        cached = _cache[cache_key].copy()
        cached["cached"] = True
        cached["duration_ms"] = 0
        return cached

    if not GEMINI_AVAILABLE or not settings.GEMINI_API_KEY:
        return _get_mock_response(prompt, start_time, cache_key, use_cache)

    try:
        model = genai.GenerativeModel(
            model_name=settings.GEMINI_MODEL,
            system_instruction=system_prompt if system_prompt else None,
        )
        gen_config = {"response_mime_type": "application/json"} if json_mode else {}
        response = model.generate_content(prompt, generation_config=gen_config)
        
        parsed = {}
        if response.text:
            try: parsed = json.loads(response.text)
            except json.JSONDecodeError: parsed = {"raw": response.text}
            
        tokens_in = getattr(response.usage_metadata, "prompt_token_count", 0) if hasattr(response, "usage_metadata") else 0
        tokens_out = getattr(response.usage_metadata, "candidates_token_count", 0) if hasattr(response, "usage_metadata") else 0
        
        result = {"parsed": parsed, "tokens_in": tokens_in, "tokens_out": tokens_out, "duration_ms": int((time.time() - start_time) * 1000), "cached": False}
        if use_cache: _cache[cache_key] = result.copy()
        return result
    except Exception as e:
        logger.exception("Gemini API failed")
        raise RuntimeError(f"Gemini generation failed: {str(e)}")

def _get_mock_response(prompt: str, start_time: float, cache_key: str, use_cache: bool) -> dict[str, Any]:
    p = prompt.lower()
    if "architecture" in p and "capacity" not in p:
        parsed = {"components": [{"id": "api_gateway", "name": "API Gateway", "type": "backend", "description": "Routes requests", "responsibilities": ["routing"], "connections": ["db"]}, {"id": "db", "name": "Database", "type": "database", "description": "Stores data", "responsibilities": ["persistence"], "connections": []}]}
    elif "capacity" in p:
        parsed = {"capacity": {"dau": 1000000, "peak_read_qps": 1000, "peak_write_qps": 100, "daily_storage_gb": 50, "five_year_storage_tb": 90, "bandwidth_gbps": 0.5, "cache_dataset_gb": 20, "formulas": {"peak_read_qps": "1M * 100 / 86400"}}, "data_model": {"decision": "SQL", "rationale": "ACID compliance needed", "entities": [{"name": "users", "columns": [{"name": "id", "type": "UUID", "primary": True}], "sharding_key": None, "access_patterns": ["Read by ID"]}]}}
    elif "api" in p:
        parsed = {"api_design": {"style": "REST", "auth": "JWT", "endpoints": [{"method": "GET", "path": "/v1/users", "description": "Get users", "response": {"users": "array"}}]}, "stack": {"layers": [{"layer": "database", "primary": "PostgreSQL", "alternatives": ["MySQL"], "rationale": "Relational data", "trade_off": "Harder to scale"}]}}
    else: parsed = {}
    
    result = {"parsed": parsed, "tokens_in": 100, "tokens_out": 50, "duration_ms": int((time.time() - start_time) * 1000), "cached": False}
    if use_cache: _cache[cache_key] = result.copy()
    return result