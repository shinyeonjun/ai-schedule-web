"""
MUFI 알림 서비스
일정 공유, 초대, 응답 등에 대한 알림 관리
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from supabase import create_client, Client
import os
import json
import logging
from uuid import uuid4

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "https://ktcksionzsybzzpziird.supabase.co")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0Y2tzaW9uenN5Ynp6cHppaXJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEyNjAzNTgsImV4cCI6MjA2NjgzNjM1OH0.WcoHArimjWJe6nIcpRFAbECsbCvGnVUEKTvXKg0XgHM")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase 환경 변수가 설정되지 않았습니다.")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    async def create_share_invitation_notification(
        self,
        to_user_id: str,
        from_user_id: str,
        from_user_name: str,
        schedule_id: str,
        schedule_title: str,
        message: Optional[str] = None
    ) -> bool:
        """일정 공유 초대 알림 생성"""
        try:
            notification_data = {
                "id": str(uuid4()),
                "user_id": to_user_id,
                "type": "schedule_invite",
                "title": "일정 초대",
                "message": f"{from_user_name}님이 \"{schedule_title}\"에 초대했습니다.",
                "data": {
                    "schedule_id": schedule_id,
                    "from_user_id": from_user_id,
                    "from_user_name": from_user_name,
                    "schedule_title": schedule_title,
                    "invitation_message": message
                },
                "is_read": False,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table("notifications").insert(notification_data).execute()
            
            logger.info(f"✅ 일정 초대 알림 생성 완료: {to_user_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ 일정 초대 알림 생성 오류: {str(e)}")
            return False
    
    async def create_share_response_notification(
        self,
        to_user_id: str,
        from_user_id: str,
        from_user_name: str,
        schedule_id: str,
        schedule_title: str,
        action: str
    ) -> bool:
        """일정 공유 응답 알림 생성"""
        try:
            action_text = "수락" if action == "accept" else "거절"
            notification_type = f"schedule_{action}ed"
            
            notification_data = {
                "id": str(uuid4()),
                "user_id": to_user_id,
                "type": notification_type,
                "title": f"일정 {action_text}됨",
                "message": f"{from_user_name}님이 \"{schedule_title}\" 일정을 {action_text}했습니다.",
                "data": {
                    "schedule_id": schedule_id,
                    "from_user_id": from_user_id,
                    "from_user_name": from_user_name,
                    "schedule_title": schedule_title,
                    "action": action
                },
                "is_read": False,
                "created_at": datetime.now().isoformat()
            }
            
            result = self.client.table("notifications").insert(notification_data).execute()
            
            logger.info(f"✅ 일정 응답 알림 생성 완료: {to_user_id}, action: {action}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ 일정 응답 알림 생성 오류: {str(e)}")
            return False
    
    def get_user_notifications(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """사용자의 알림 목록 조회"""
        try:
            result = self.client.table("notifications").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
            
            logger.info(f"✅ 사용자 알림 조회 완료: {user_id}, count: {len(result.data)}")
            return result.data
            
        except Exception as e:
            logger.error(f"❌ 사용자 알림 조회 오류: {str(e)}")
            return []
    
    def mark_notification_as_read(self, notification_id: str) -> bool:
        """알림을 읽음으로 표시"""
        try:
            result = self.client.table("notifications").update({
                "is_read": True,
                "read_at": datetime.now().isoformat()
            }).eq("id", notification_id).execute()
            
            logger.info(f"✅ 알림 읽음 처리 완료: {notification_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ 알림 읽음 처리 오류: {str(e)}")
            return False
    
    def mark_all_notifications_as_read(self, user_id: str) -> bool:
        """사용자의 모든 알림을 읽음으로 표시"""
        try:
            result = self.client.table("notifications").update({
                "is_read": True,
                "read_at": datetime.now().isoformat()
            }).eq("user_id", user_id).eq("is_read", False).execute()
            
            logger.info(f"✅ 모든 알림 읽음 처리 완료: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 모든 알림 읽음 처리 오류: {str(e)}")
            return False
    
    def get_unread_count(self, user_id: str) -> int:
        """읽지 않은 알림 개수 조회"""
        try:
            result = self.client.table("notifications").select("id", count="exact").eq("user_id", user_id).eq("is_read", False).execute()
            
            count = result.count if result.count is not None else 0
            logger.info(f"✅ 읽지 않은 알림 개수 조회 완료: {user_id}, count: {count}")
            return count
            
        except Exception as e:
            logger.error(f"❌ 읽지 않은 알림 개수 조회 오류: {str(e)}")
            return 0
    
    def delete_notification(self, notification_id: str) -> bool:
        """알림 삭제"""
        try:
            result = self.client.table("notifications").delete().eq("id", notification_id).execute()
            
            logger.info(f"✅ 알림 삭제 완료: {notification_id}")
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"❌ 알림 삭제 오류: {str(e)}")
            return False