"""
MUFI Backend - Main FastAPI Application
Google OAuth 인증 및 사용자 관리 시스템
"""
import os
import urllib.parse
import json
from fastapi import FastAPI, HTTPException, status, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.security import HTTPBearer
from typing import Optional, Dict, Any
import httpx
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import configurations and services
from config.config import settings
from core.auth import create_jwt_token
from core.dependencies import get_current_user_optional
from services.database_service import DatabaseService
from services.auth_service import AuthService
from services.google_token_service import google_token_service

# FastAPI 앱 생성
app = FastAPI(
    title="MUFI API",
    description="AI-powered Meeting Analysis and Schedule Management System",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 초기화
db_service = DatabaseService()
auth_service = AuthService()

# 정적 파일 서빙 (프론트엔드)
app.mount("/css", StaticFiles(directory="../frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="../frontend/js"), name="js")

# 업로드 디렉토리 생성
os.makedirs("uploads", exist_ok=True)

# ==================== 인증 라우트 ====================

@app.get("/auth/google/login")
async def google_login():
    """Google OAuth 로그인 URL 생성"""
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.google_client_id}"
        "&response_type=code"
        "&scope=openid email profile https://www.googleapis.com/auth/calendar https://www.googleapis.com/auth/gmail.send"
        f"&redirect_uri={settings.google_redirect_uri}"
        "&access_type=offline"
        "&prompt=consent"
    )
    
    return {"auth_url": google_auth_url}


@app.get("/auth/google/callback")
async def google_callback(code: str):
    """Google OAuth 콜백 처리"""
    try:
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )
        
        # 1. Google에서 액세스 토큰 받기
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri
        }
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()
        
        access_token = token_info.get("access_token")
        if not access_token:
            raise ValueError("No access token received from Google")
        
        # 2. Google에서 사용자 정보 받기
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
        async with httpx.AsyncClient() as client:
            user_response = await client.get(user_info_url)
            user_response.raise_for_status()
            google_user_info = user_response.json()
        
        # 3. DB에서 사용자 찾기 또는 생성
        google_id = google_user_info.get("id")
        email = google_user_info.get("email")
        name = google_user_info.get("name")
        picture = google_user_info.get("picture")
        
        if not google_id or not email:
            raise ValueError("Missing required user information from Google")
        
        # 기존 사용자 확인 (google_id로)
        existing_user = db_service.get_user_by_google_id(google_id)
        
        if existing_user:
            # 기존 사용자 정보 업데이트
            user_record = db_service.update_user(
                user_id=existing_user["id"],
                data={
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "last_login_at": "now()"
                }
            )
            logger.info(f"Updated existing user: {user_record['id']}")
        else:
            # 새 사용자 생성
            user_record = db_service.create_user(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture
            )
            logger.info(f"Created new user: {user_record['id']}")
        
        # 4. JWT 토큰 생성
        jwt_token = create_jwt_token(
            user_id=user_record["id"],
            email=user_record["email"],
            name=user_record["name"]
        )
        
        # 5. Google Calendar 토큰 정보 준비
        google_credentials = {
            "access_token": access_token,
            "refresh_token": token_info.get("refresh_token"),
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "scopes": ["openid", "email", "profile", "https://www.googleapis.com/auth/calendar", "https://www.googleapis.com/auth/gmail.send"],
            "expires_in": token_info.get("expires_in", 3600)
        }
        
        # 6. Google 토큰을 DB에 저장 (비동기로 처리)
        try:
            stored_tokens = google_token_service.save_tokens(
                user_id=user_record["id"],
                token_data=google_credentials
            )
            logger.info(f"Google 토큰 DB 저장 성공 - User ID: {user_record['id']}")
        except Exception as token_error:
            logger.error(f"Google 토큰 DB 저장 실패: {token_error}")
            # 토큰 저장 실패해도 로그인은 계속 진행
        
        # 7. 대시보드로 리다이렉트 (토큰과 사용자 정보 포함)
        encoded_email = urllib.parse.quote(email)
        encoded_name = urllib.parse.quote(name)
        encoded_picture = urllib.parse.quote(picture) if picture else ""
        encoded_google_credentials = urllib.parse.quote(json.dumps(google_credentials))
        
        redirect_url = (
            f"/dashboard.html?"
            f"token={jwt_token}&"
            f"user_id={user_record['id']}&"
            f"email={encoded_email}&"
            f"name={encoded_name}&"
            f"picture={encoded_picture}&"
            f"google_credentials={encoded_google_credentials}"
        )
        
        return RedirectResponse(url=redirect_url)
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        return RedirectResponse(url=f"/login.html?error={urllib.parse.quote(str(e))}")


@app.get("/auth/status")
async def auth_status(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """현재 인증 상태 확인"""
    if current_user:
        return {
            "authenticated": True,
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "name": current_user["name"],
            "picture": current_user.get("picture")
        }
    else:
        return {
            "authenticated": False,
            "user_id": None,
            "email": None,
            "name": None,
            "picture": None
        }


# ==================== 페이지 라우트 ====================

@app.get("/")
async def root():
    """루트 페이지 - 인증 상태에 따라 리다이렉트"""
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>MUFI - Redirecting...</title>
        <script>
            // 토큰이 있으면 대시보드로, 없으면 로그인으로
            const token = localStorage.getItem('access_token');
            if (token) {
                window.location.href = '/dashboard.html';
            } else {
                window.location.href = '/login.html';
            }
        </script>
    </head>
    <body>
        <p>Redirecting...</p>
    </body>
    </html>
    """)


@app.get("/login.html")
async def login_page():
    """로그인 페이지"""
    return FileResponse("../frontend/login.html")


@app.get("/dashboard.html")
async def dashboard_page():
    """대시보드 페이지"""
    return FileResponse("../frontend/dashboard.html")


# ==================== API 라우트 ====================

# 라우터 추가
from routers import auth, analysis, schedules, members, email, google_calendar, gmail, schedule_share, notifications

app.include_router(auth.router, prefix="/api", tags=["auth"])
app.include_router(analysis.router, prefix="/api", tags=["analysis"])
app.include_router(schedules.router, prefix="/api", tags=["schedules"])
app.include_router(members.router, prefix="/api", tags=["members"])
app.include_router(email.router, prefix="/api", tags=["email"])
app.include_router(google_calendar.router, prefix="/api", tags=["google_calendar"])
app.include_router(gmail.router, tags=["gmail"])
app.include_router(schedule_share.router, prefix="/api/schedule-share", tags=["schedule_share"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])

@app.get("/health")
async def health_check():
    """건강 체크 엔드포인트"""
    return {"status": "healthy", "version": "1.0.0"}


# ==================== 서버 실행 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.debug
    ) 