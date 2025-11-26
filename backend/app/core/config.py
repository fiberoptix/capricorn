"""Application configuration"""
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    DATABASE_URL: str = "postgresql://capricorn:capricorn2025@postgres:5432/capricorn_db"
    
    # Redis
    REDIS_URL: str = "redis://redis:6379/0"
    
    # Security (for future auth implementation)
    SECRET_KEY: str = "capricorn-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Build
    BUILD_NUMBER: str = "1"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

settings = get_settings()

