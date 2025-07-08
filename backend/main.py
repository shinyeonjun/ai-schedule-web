from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from config import settings
from routers import analysis

# FastAPI 앱 생성
app = FastAPI(
    title="MUFI API",
    description="통화 내용 AI 분석 및 일정 관리 시스템",
    version="1.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (프론트엔드)
app.mount("/static", StaticFiles(directory="../frontend"), name="static")

# 라우터 등록
app.include_router(analysis.router, prefix="/api", tags=["analysis"])

# 업로드 디렉토리 생성
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

# 루트 경로에서 index.html 제공
@app.get("/")
async def read_root():
    return FileResponse("../frontend/dashboard.html")

# 건강 체크 엔드포인트
@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True) 