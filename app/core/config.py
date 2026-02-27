"""
Application Configuration
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "SCHBC BBMS"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database - Supabase (PostgreSQL)
    DATABASE_URL: str
    
    # Supabase (optional)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    # SMTP Settings (Gmail)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }


settings = Settings()
