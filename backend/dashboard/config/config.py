import os
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

class Settings:
    # OpenAI 설정
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = "gpt-4o-mini"
    openai_temperature: float = 0.7
    openai_max_tokens: int = 2000
    
    # JWT 설정
    jwt_secret_key: str = os.getenv("JWT_SECRET_KEY", "")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))
    
    # Supabase 설정
    supabase_url: str = os.getenv("SUPABASE_URL", "")
    supabase_service_key: str = os.getenv("SUPABASE_SERVICE_KEY", "")
    
    # 파일 업로드 설정
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".txt"]

settings = Settings()
