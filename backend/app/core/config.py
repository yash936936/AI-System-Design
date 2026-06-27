import os
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # App
    app_name: str = "SysDesign AI"
    debug: bool = True

    # Database — defaults to local SQLite for zero-config dev.
    # Override with a Postgres URL (postgresql+asyncpg://...) in .env for prod.
    database_url: str = "sqlite+aiosqlite:///./sysdesign.db"

    # Gemini (Reads GEMINI_API_KEY from .env automatically)
    gemini_api_key: str = ""
    gemini_max_rpm: int = 14
    gemini_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "models/embedding-001"

    # RAG / Chroma
    chroma_host: str = "localhost"
    chroma_port: int = 8000

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