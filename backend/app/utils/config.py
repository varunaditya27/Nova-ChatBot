import os
from typing import Optional
from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    """Application settings."""
    
    # Application Settings
    environment: str = Field("development", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    # API Settings
    api_prefix: str = Field("/api", env="API_PREFIX")
    debug: bool = Field(False, env="DEBUG")
    
    # CORS Settings
    cors_origins: list[str] = Field(
        ["http://localhost:5173"],  # Vite dev server by default
        env="CORS_ORIGINS"
    )
    
    # Security
    secret_key: str = Field("your-secret-key-here", env="SECRET_KEY")
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Cache Settings
    redis_url: str = Field("redis://localhost:6379", env="REDIS_URL")
    cache_ttl: int = Field(300, env="CACHE_TTL")  # 5 minutes default
    cache_enabled: bool = Field(True, env="CACHE_ENABLED")

    class Config:
        env_file = os.getenv("ENV_FILE", ".env")
        env_file_encoding = "utf-8"
        case_sensitive = True
        
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == "cors_origins":
                return [origin.strip() for origin in raw_val.split(",") if origin.strip()]
            return cls.json_loads(raw_val)


def get_settings() -> Settings:
    """Get the application settings."""
    return Settings()


# Global settings instance
settings = get_settings()