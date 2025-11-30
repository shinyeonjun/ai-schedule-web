from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import httpx
import jwt
from datetime import datetime, timedelta
import os
from typing import Optional
import json
from backend.login.user_database import user_db
from backend.dashboard.auth.google_token_service import GoogleTokenService

# 환경 변수 로드
from dotenv import load_dotenv
from pathlib import Path

# .env 파일 경로 설정
env_path = Path(__file__).parent.parent.parent / ".env"
if not env_path.exists():
    env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_BASE_URL = os.getenv("GOOGLE_REDIRECT_BASE_URL")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# 디버깅: 환경 변수 확인
if not GOOGLE_CLIENT_ID or GOOGLE_CLIENT_ID == "your_google_client_id_here.apps.googleusercontent.com":
    print(f"⚠️ 경고: GOOGLE_CLIENT_ID가 설정되지 않았거나 플레이스홀더 값입니다.")
    print(f"현재 값: {GOOGLE_CLIENT_ID}")

class GoogleOAuth:
    def __init__(self):
        self.client_id = GOOGLE_CLIENT_ID
        self.client_secret = GOOGLE_CLIENT_SECRET
        self.redirect_base_url = GOOGLE_REDIRECT_BASE_URL
        self.jwt_secret = JWT_SECRET_KEY
        self.jwt_algorithm = JWT_ALGORITHM
        self.jwt_expire_minutes = JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        
    def get_google_auth_url(self) -> str:
        """구글 OAuth 인증 URL 생성"""
        params = {
            'client_id': self.client_id,
            'redirect_uri': f"{self.redirect_base_url}/oauth/google/callback",
            'response_type': 'code',
            'scope': 'openid email profile https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.send https://www.googleapis.com/auth/gmail.readonly',
            'access_type': 'offline',
            'prompt': 'consent'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"
    
    async def exchange_code_for_tokens(self, code: str) -> dict:
        """인증 코드를 액세스 토큰으로 교환"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': f"{self.redirect_base_url}/oauth/google/callback"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="토큰 교환 실패")
            
            return response.json()
    
    async def get_user_info(self, access_token: str) -> dict:
        """액세스 토큰으로 사용자 정보 가져오기"""
        userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        headers = {'Authorization': f'Bearer {access_token}'}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(userinfo_url, headers=headers)
            
            if response.status_code != 200:
                raise HTTPException(status_code=400, detail="사용자 정보 가져오기 실패")
            
            return response.json()
    
    def create_jwt_token(self, user_data: dict, db_user_id: int = None) -> str:
        """JWT 토큰 생성"""
        # DB 사용자 ID가 있으면 그것을 사용, 없으면 Google ID 사용
        user_id = str(db_user_id) if db_user_id is not None else user_data['id']
        
        payload = {
            'sub': user_id,
            'email': user_data['email'],
            'name': user_data.get('name', ''),
            'picture': user_data.get('picture', ''),
            'exp': datetime.utcnow() + timedelta(minutes=self.jwt_expire_minutes),
            'iat': datetime.utcnow()
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def verify_jwt_token(self, token: str) -> dict:
        """JWT 토큰 검증"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="토큰이 만료되었습니다")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"토큰 검증 실패: {str(e)}")

# OAuth 인스턴스 생성
google_oauth = GoogleOAuth()

# FastAPI 앱에 라우터 추가
def setup_google_oauth_routes(app: FastAPI):
    """구글 OAuth 라우트 설정"""
    
    @app.get("/oauth/google/login")
    async def google_login():
        """구글 로그인 URL 반환"""
        auth_url = google_oauth.get_google_auth_url()
        return {"auth_url": auth_url}
    
    @app.get("/oauth/google/auth-url")
    async def get_google_auth_url():
        """구글 인증 URL 반환 (Gmail 전송용)"""
        auth_url = google_oauth.get_google_auth_url()
        return {"auth_url": auth_url}
    
    @app.get("/oauth/google/callback")
    async def google_callback(code: str):
        """구글 OAuth 콜백 처리"""
        try:
            # 인증 코드를 토큰으로 교환
            tokens = await google_oauth.exchange_code_for_tokens(code)
            access_token = tokens['access_token']
            
            # 사용자 정보 가져오기
            user_info = await google_oauth.get_user_info(access_token)
            
            # Supabase users 테이블에 사용자 정보 저장
            saved_user = await user_db.save_user(user_info)
            
            if saved_user:
                # 마지막 로그인 시간 업데이트
                await user_db.update_user_last_login(saved_user['id'])
                
                # Google 토큰 저장
                await GoogleTokenService.save_google_tokens(saved_user['id'], tokens)
            
            # JWT 토큰 생성 (데이터베이스 사용자 ID 포함)
            jwt_token = google_oauth.create_jwt_token(user_info, saved_user['id'] if saved_user else None)
            
            # 프론트엔드로 리다이렉트 (토큰 포함)
            redirect_url = f"{GOOGLE_REDIRECT_BASE_URL}/dashboard?token={jwt_token}"
            return RedirectResponse(url=redirect_url)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"인증 실패: {str(e)}")
    
    @app.get("/oauth/verify")
    async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """JWT 토큰 검증"""
        try:
            payload = google_oauth.verify_jwt_token(credentials.credentials)
            return {"valid": True, "user": payload}
        except HTTPException as e:
            return {"valid": False, "error": e.detail}
        except Exception as e:
            return {"valid": False, "error": str(e)}
    
    @app.get("/oauth/user")
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """현재 사용자 정보 반환"""
        try:
            payload = google_oauth.verify_jwt_token(credentials.credentials)
            user_id = int(payload.get('sub'))
            
            # 데이터베이스에서 최신 사용자 정보 가져오기
            user_data = await user_db.get_user_by_id(user_id)
            
            if user_data:
                return {
                    'id': user_data['id'],
                    'email': user_data['email'],
                    'name': user_data['name'],
                    'picture': user_data.get('picture', '')
                }
            else:
                # DB에서 찾을 수 없으면 JWT 페이로드 반환
                return payload
                
        except Exception as e:
            raise HTTPException(status_code=401, detail=f"사용자 정보 조회 실패: {str(e)}")
