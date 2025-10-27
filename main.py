from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

# OAuth 모듈 import (경로 수정)
from backend.login.oauth.google_auth import setup_google_oauth_routes

# 분석 API import
from backend.dashboard.analysis.analysis_api import router as analysis_router

# 일정 관리 API import
from backend.dashboard.schedules.schedules_api import router as schedules_router

# 인원 관리 API import
from backend.dashboard.members.members_api import router as members_router

# FastAPI 앱 생성
app = FastAPI(
    title="MUFI - AI 통화 분석 시스템",
    description="AI 기반 통화 내용 분석 및 일정 관리 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 개발 환경에서는 모든 origin 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙
app.mount("/css", StaticFiles(directory="frontend/css"), name="css")
app.mount("/js", StaticFiles(directory="frontend/js"), name="js")

# OAuth 라우트 설정
setup_google_oauth_routes(app)

# 분석 API 라우터 추가
app.include_router(analysis_router)

# 일정 관리 API 라우터 추가
app.include_router(schedules_router)

# 인원 관리 API 라우터 추가
app.include_router(members_router)

# 환경 변수 로드
from dotenv import load_dotenv
load_dotenv("backend/.env")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """루트 경로 - 로그인 페이지 반환"""
    return FileResponse("frontend/html/login.html")

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    """로그인 페이지"""
    return FileResponse("frontend/html/login.html")

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """대시보드 페이지"""
    return FileResponse("frontend/html/dashboard.html")

@app.get("/invite/{token}", response_class=HTMLResponse)
async def invite_preview_page(token: str):
    """초대 링크 미리보기 페이지"""
    return FileResponse("frontend/html/invite-preview.html")

@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    return {"status": "healthy", "service": "MUFI"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
