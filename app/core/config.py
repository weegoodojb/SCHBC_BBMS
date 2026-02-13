"""
Application Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    APP_NAME: str = "SCHBC BBMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # Changed to False for production
    
    # Database - Supabase (PostgreSQL)
    # Default connection string, can be overridden by environment variable
    DATABASE_URL: str = "postgresql://postgres.gzqtyjwoasbbgelylkix:rkP4z7EfunMSIMXC@aws-1-ap-southeast-2.pooler.supabase.com:5432/postgres"
    
    # Supabase (optional - for direct API access)
    SUPABASE_URL: str = "https://gzqtyjwoasbbgelylkix.supabase.co"
    SUPABASE_KEY: str = "sb_publishable_XypkjPMQoR9JR8Vv_bumEw_NC_MrCTn"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    class Config:
        env_file = ".env"


settings = Settings()
