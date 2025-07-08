#!/usr/bin/env python3
"""
MUFI 백엔드 서버 시작 스크립트
"""
import uvicorn
import os
from pathlib import Path

if __name__ == "__main__":
    # 현재 디렉토리를 백엔드 폴더로 설정
    os.chdir(Path(__file__).parent)
    
    print("🚀 MUFI 백엔드 서버를 시작합니다...")
    print("📁 프론트엔드: http://localhost:8000")
    print("📚 API 문서: http://localhost:8000/docs")
    print("🔧 OpenAPI: http://localhost:8000/redoc")
    print("❌ 종료하려면 Ctrl+C를 누르세요")
    print("-" * 50)
    
    # 서버 실행
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[".", "../frontend"],
        log_level="info"
    ) 