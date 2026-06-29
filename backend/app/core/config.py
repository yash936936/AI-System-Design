import os
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # App
    app_name: str = "SysDesign AI"
    debug: bool = True
    database_url: str = "sqlite+aiosqlite:///./sysdesign.db"

    # Gemini (Reads GEMINI_API_KEY from .env automatically)
    gemini_api_key: str = ""
    gemini_max_rpm: int = 14
    gemini_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "models/embedding-001"

    # RAG / Chroma
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    # Local on-disk path for chromadb.PersistentClient — no external Chroma
    # server is required. chroma_host/chroma_port are reserved for a future
    # HttpClient-based deployment but are currently unused.
    chroma_persist_dir: str = "./chroma_data"

    # Web search fallback (SerpAPI) — optional.
    # FIX: was missing entirely; retrieval_service.py referenced settings.serpapi_key
    # which caused AttributeError at runtime whenever vector scores fell below
    # FALLBACK_THRESHOLD (0.6). Now defined here so the attribute always exists;
    # an empty string means the web fallback is silently skipped (safe default).
    serpapi_key: str = ""

    # Auth — shared secret between Next.js bridge and FastAPI token verifier.
    # Must match INTERNAL_AUTH_SECRET in the frontend .env.local.
    internal_auth_secret: str = "dev-secret-change-me"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False
    )


_settings = Settings()


def get_settings() -> Settings:
    return _settings
