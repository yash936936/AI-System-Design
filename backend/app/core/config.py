from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "models/gemini-embedding-001"
    gemini_max_rpm: int = 5
    gemini_max_rpd: int = 18

    # Database
    database_url: str
    database_url_sync: str = ""

    # Redis
    redis_url: str = "redis://localhost:6379"

    # App
    app_env: str = "development"
    secret_key: str = "dev-secret-change-in-prod"
    allowed_origins: str = "http://localhost:3000"

    # ChromaDB
    chroma_persist_dir: str = "./data/chroma"

    # Web search
    serpapi_key: str = ""

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]

    class Config:
        env_file = ".env"
        extra = "ignore"


@lru_cache
def get_settings() -> Settings:
    return Settings()
