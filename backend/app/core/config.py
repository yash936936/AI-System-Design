import os
from functools import lru_cache
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = Field(default="SysDesign AI")
    DEBUG: bool = Field(default=True)
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///./sysdesign.db")
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = Field(default="gemini-2.5-flash")
    CORS_ORIGINS: List[str] = Field(default=["http://localhost:3000"])
    
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True, extra="ignore"
    )

@lru_cache()
def get_settings() -> Settings:
    return Settings()

settings = get_settings()