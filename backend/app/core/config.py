from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Gemini
    gemini_api_key: str
    gemini_model: str = "gemini-2.5-flash"  # or "gemini-2.5-flash-lite", etc.
    gemini_embed_model: str = "models/text-embedding-004"
    
    # Rate limits will be auto-configured based on model below
    # These are fallbacks if model-specific limits aren't found
    gemini_max_rpm: int = 5  # default to Gemini 2.5 Flash
    gemini_max_rpd: int = 20  # default to Gemini 2.5 Flash
    
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
    
    def get_model_rate_limits(self) -> tuple[int, int]:
        """
        Returns (RPM, RPD) based on the configured model.
        Source: Google AI Studio rate limits dashboard.
        """
        model = self.gemini_model.lower()
        
        # Map model names to their rate limits
        limits = {
            "gemini-2.5-flash": (5, 20),
            "gemini-2.5-flash-lite": (10, 20),
            "gemini-2.5-flash-tts": (3, 10),
            "gemini-2.5-pro": (5, 20),  # assuming same as flash unless specified
            "gemini-2.0-flash-exp": (5, 20),  # fallback
        }
        
        # Try exact match first
        if model in limits:
            return limits[model]
        
        # Try partial matches
        for key, value in limits.items():
            if key in model or model in key:
                return value
        
        # Default fallback
        return (5, 20)
    
    class Config:
        env_file = ".env"
        extra = "ignore"

@lru_cache
def get_settings() -> Settings:
    return Settings()