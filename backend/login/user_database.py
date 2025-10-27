from supabase import create_client, Client
import os
from typing import Optional, Dict, Any
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# 환경 변수 로드 (.env 파일 사용)
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)

# Supabase 설정
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

print(f"환경 변수 파일 경로: {env_path}")
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_SERVICE_KEY: {SUPABASE_SERVICE_KEY}")

class UserDatabase:
    def __init__(self):
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            raise ValueError("Supabase 환경 변수가 설정되지 않았습니다.")
        self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    async def save_user(self, user_info: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 정보를 데이터베이스에 저장"""
        try:
            # 기존 사용자 확인
            existing_user = self.supabase.table("users").select("*").eq("google_id", user_info["id"]).execute()
            
            if existing_user.data:
                # 기존 사용자 업데이트
                user_data = {
                    "email": user_info["email"],
                    "name": user_info.get("name", ""),
                    "picture": user_info.get("picture", ""),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                result = self.supabase.table("users").update(user_data).eq("google_id", user_info["id"]).execute()
                return result.data[0] if result.data else None
            else:
                # 새 사용자 생성
                user_data = {
                    "google_id": user_info["id"],
                    "email": user_info["email"],
                    "name": user_info.get("name", ""),
                    "picture": user_info.get("picture", ""),
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                result = self.supabase.table("users").insert(user_data).execute()
                return result.data[0] if result.data else None
                
        except Exception as e:
            print(f"사용자 저장 실패: {str(e)}")
            return None
    
    async def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Google ID로 사용자 조회"""
        try:
            result = self.supabase.table("users").select("*").eq("google_id", google_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"사용자 조회 실패: {str(e)}")
            return None
    
    async def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """사용자 ID로 사용자 조회"""
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"사용자 조회 실패: {str(e)}")
            return None
    
    async def update_user_last_login(self, user_id: int) -> bool:
        """사용자 마지막 로그인 시간 업데이트"""
        try:
            user_data = {
                "last_login_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.supabase.table("users").update(user_data).eq("id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            print(f"마지막 로그인 업데이트 실패: {str(e)}")
            return False

# 전역 인스턴스
user_db = UserDatabase()
