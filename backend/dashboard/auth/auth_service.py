import jwt
from fastapi import HTTPException
from datetime import datetime
import os
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

def verify_token(token: str) -> dict:
    """
    JWT 토큰을 검증하고 사용자 정보를 반환합니다.
    """
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"토큰 검증 실패: {str(e)}")
