"""
Configuration management for MUFI application
"""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings"""
    
    # Database
    supabase_url: str
    supabase_anon_key: str
    supabase_service_key: str
    
    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "https://colobus-blues.ts.net:8000/auth/google/callback"
    
    # OpenAI
    openai_api_key: str
    
    # JWT
    jwt_secret_key: str = "your-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440
    
    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True
    
    # Logging
    log_level: str = "INFO"
    
    # CORS
    cors_origins: list = ["*"]  # 모든 도메인 허용 (개발용)
    
    # File Upload
    upload_dir: str = "uploads"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".txt", ".docx", ".pdf"]
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings() 