"""
Google 토큰 관리 서비스
사용자별 Google OAuth 토큰의 저장, 갱신, 검증을 담당합니다.
Google-Auth 표준 라이브러리 사용
"""

import logging
import json
import httpx  # 기존 코드 호환성을 위해 유지
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from supabase import create_client, Client
from config.config import settings

# Google 표준 라이브러리 import
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)

class GoogleTokenService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.supabase_url,
            settings.supabase_service_key
        )
    
    def save_tokens(self, user_id: str, token_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자의 Google 토큰을 DB에 저장합니다.
        
        Args:
            user_id: 사용자 ID
            token_data: Google OAuth 토큰 정보
            
        Returns:
            저장된 토큰 정보
        """
        try:
            # 만료 시간 계산 (일반적으로 3600초)
            expires_in = token_data.get("expires_in", 3600)
            expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            token_record = {
                "user_id": user_id,
                "access_token": token_data.get("access_token"),
                "refresh_token": token_data.get("refresh_token"),
                "token_uri": token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "scopes": token_data.get("scopes", [
                    "openid", "email", "profile", 
                    "https://www.googleapis.com/auth/calendar",
                    "https://www.googleapis.com/auth/gmail.send"
                ]),
                "expires_at": expires_at.isoformat()
            }
            
            # UPSERT: 기존 토큰이 있으면 업데이트, 없으면 생성
            result = self.supabase.table("google_tokens").upsert(
                token_record,
                on_conflict="user_id"
            ).execute()
            
            if result.data:
                logger.info(f"Google 토큰 저장 성공 - User ID: {user_id}")
                return result.data[0]
            else:
                raise Exception("토큰 저장 실패")
                
        except Exception as e:
            logger.error(f"Google 토큰 저장 실패: {e}")
            raise e
    
    def get_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        사용자의 Google 토큰을 가져옵니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            토큰 정보 또는 None
        """
        try:
            result = self.supabase.table("google_tokens").select("*").eq(
                "user_id", user_id
            ).execute()
            
            if result.data and len(result.data) > 0:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"Google 토큰 조회 실패: {e}")
            return None
    
    def is_token_expired(self, token_data: Dict[str, Any]) -> bool:
        """
        토큰이 만료되었는지 확인합니다.
        
        Args:
            token_data: 토큰 정보
            
        Returns:
            만료 여부
        """
        try:
            if not token_data.get("expires_at"):
                logger.warning("토큰에 expires_at 정보가 없음")
                return True
                
            # UTC 시간으로 정규화
            expires_at_str = token_data["expires_at"]
            if expires_at_str.endswith("Z"):
                expires_at_str = expires_at_str.replace("Z", "+00:00")
            
            expires_at = datetime.fromisoformat(expires_at_str)
            
            # UTC 시간으로 현재 시간 가져오기
            if expires_at.tzinfo is not None:
                # expires_at이 timezone aware라면 UTC로 변환
                from datetime import timezone
                now = datetime.now(timezone.utc)
                if expires_at.tzinfo != timezone.utc:
                    expires_at = expires_at.astimezone(timezone.utc)
            else:
                # expires_at이 timezone naive라면 로컬 시간 사용
                now = datetime.now()
            
            # 5분 여유를 두고 만료 체크
            check_time = expires_at - timedelta(minutes=5)
            is_expired = now >= check_time
            
            logger.info(f"🕐 토큰 만료 체크: 현재={now}, 만료={expires_at}, 체크시간={check_time}, 만료됨={is_expired}")
            logger.info(f"🕐 시간대 정보: now_tz={now.tzinfo}, expires_tz={expires_at.tzinfo}")
            
            return is_expired
            
        except Exception as e:
            logger.error(f"토큰 만료 확인 실패: {e}")
            return True
    
    async def load_and_refresh_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Google 표준 라이브러리를 사용하여 토큰을 로드하고 자동 갱신합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            갱신된 토큰 정보 또는 None
        """
        try:
            # 1. DB에서 토큰 정보 가져오기
            token_data = self.get_tokens(user_id)
            if not token_data:
                logger.warning(f"🔄 토큰 데이터가 없음 - User ID: {user_id}")
                return None
            
            if not token_data.get("refresh_token"):
                logger.error(f"🔄 Refresh token이 없음 - User ID: {user_id}")
                logger.error(f"🔄 재인증이 필요합니다. offline access로 다시 승인받아야 합니다.")
                return None
            
            logger.info(f"🔄 Google 표준 라이브러리로 토큰 갱신 시작 - User ID: {user_id}")
            
            # 2. Google Credentials 객체 생성
            creds = Credentials(
                token=token_data.get("access_token"),
                refresh_token=token_data.get("refresh_token"),
                token_uri=token_data.get("token_uri", "https://oauth2.googleapis.com/token"),
                client_id=token_data.get("client_id"),
                client_secret=token_data.get("client_secret"),
                scopes=token_data.get("scopes", [])
            )
            
            logger.info(f"🔍 토큰 상태 체크: valid={creds.valid}, expired={creds.expired}")
            
            # 3. 토큰이 유효하지 않으면 자동 갱신
            if not creds.valid:
                logger.info(f"🔄 토큰이 무효하므로 자동 갱신 시도")
                creds.refresh(Request())
                logger.info(f"✅ Google 표준 라이브러리로 토큰 갱신 성공")
                
                # 4. 갱신된 토큰을 DB에 저장
                expiry_datetime = creds.expiry
                if expiry_datetime:
                    # timezone-aware datetime을 ISO string으로 변환
                    expires_at = expiry_datetime.isoformat()
                else:
                    # expiry가 없으면 기본값 (1시간)
                    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
                
                update_data = {
                    "access_token": creds.token,
                    "expires_at": expires_at
                }
                
                # 새로운 refresh token이 있다면 업데이트
                if creds.refresh_token and creds.refresh_token != token_data.get("refresh_token"):
                    update_data["refresh_token"] = creds.refresh_token
                    logger.info("🔄 새 refresh token으로 업데이트")
                
                logger.info(f"🔄 DB 업데이트: 새 만료시간={expires_at}")
                
                result = self.supabase.table("google_tokens").update(update_data).eq(
                    "user_id", user_id
                ).execute()
                
                if not result.data:
                    logger.error("🔄 DB 업데이트 실패")
                    return None
            else:
                logger.info(f"✅ 토큰이 여전히 유효함")
            
            # 5. 최종 토큰 정보 반환
            return {
                "access_token": creds.token,
                "refresh_token": creds.refresh_token,
                "token_uri": creds.token_uri,
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "scopes": creds.scopes,
                "expires_at": creds.expiry.isoformat() if creds.expiry else None
            }
                
        except Exception as e:
            logger.error(f"❌ Google 표준 라이브러리 토큰 갱신 실패: {e}")
            import traceback
            logger.error(f"❌ 상세 오류: {traceback.format_exc()}")
            return None

    async def refresh_access_token(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        호환성을 위한 래퍼 함수 - load_and_refresh_credentials 사용
        """
        return await self.load_and_refresh_credentials(user_id)
    
    async def get_valid_tokens(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        유효한 Google 토큰을 가져옵니다. 만료된 경우 자동으로 갱신합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            유효한 토큰 정보 또는 None
        """
        try:
            logger.info(f"🔍 유효한 Google 토큰 조회 시작 - User ID: {user_id}")
            
            # Google 표준 라이브러리를 사용한 토큰 로드 및 갱신
            valid_tokens = await self.load_and_refresh_credentials(user_id)
            
            if valid_tokens:
                logger.info(f"✅ 유효한 Google 토큰 확보 완료 - User ID: {user_id}")
                return valid_tokens
            else:
                logger.error(f"❌ 유효한 Google 토큰 확보 실패 - User ID: {user_id}")
                return None
                
        except Exception as e:
            logger.error(f"❌ 유효한 Google 토큰 조회 실패: {e}")
            return None
    
    def delete_tokens(self, user_id: str) -> bool:
        """
        사용자의 Google 토큰을 삭제합니다.
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            삭제 성공 여부
        """
        try:
            result = self.supabase.table("google_tokens").delete().eq(
                "user_id", user_id
            ).execute()
            
            logger.info(f"Google 토큰 삭제 성공 - User ID: {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Google 토큰 삭제 실패: {e}")
            return False
    
    async def test_token_validity(self, access_token: str) -> bool:
        """
        Access token의 유효성을 테스트합니다.
        
        Args:
            access_token: 테스트할 액세스 토큰
            
        Returns:
            토큰 유효성
        """
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.googleapis.com/oauth2/v1/tokeninfo?access_token={access_token}"
                )
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"토큰 유효성 테스트 실패: {e}")
            return False

# 전역 인스턴스
google_token_service = GoogleTokenService()