from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/handyman_db"
    
    # OpenAI
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-4"
    
    # JWT
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    
    # Weather API
    WEATHER_API_KEY: Optional[str] = None
    WEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5/weather"
    
    # AWS S3
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET_NAME: Optional[str] = None
    
    # App
    APP_ENV: str = "development"
    DEBUG: bool = True
    
    # Geospatial
    DEFAULT_SEARCH_RADIUS_KM: float = 10.0  # Default radius for job matching
    
    # Pricing
    BASE_PRICE_PER_SQ_FT: float = 0.15
    SURGE_MULTIPLIER_MAX: float = 2.0
    
    # Job expiry
    JOB_EXPIRY_MINUTES: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
