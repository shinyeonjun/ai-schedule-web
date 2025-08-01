"""
Gmail API Router
Gmail을 통한 이메일 전송 기능을 제공합니다.
"""
import json
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from services.gmail_service import GmailService
from services.ics_service import ICSService
from services.database_service import DatabaseService
from core.dependencies import get_current_user_optional
from supabase import create_client
from config.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/gmail", tags=["Gmail"])

# 서비스 초기화
gmail_service = GmailService()
ics_service = ICSService()
db_service = DatabaseService()

# Pydantic 모델들
class SendScheduleEmailRequest(BaseModel):
    schedule_id: str
    to_emails: List[EmailStr]
    google_credentials: Dict
    message: Optional[str] = ""

class SendGroupEmailRequest(BaseModel):
    file_id: str
    to_emails: List[EmailStr]
    google_credentials: Dict
    message: Optional[str] = ""

class EmailResponse(BaseModel):
    success: bool
    message: str
    details: Optional[Dict] = None

@router.post("/send-schedule", response_model=EmailResponse)
async def send_schedule_email(
    request: SendScheduleEmailRequest,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    개별 일정을 이메일로 전송
    """
    try:
        print(f"📧 일정 이메일 전송 요청: schedule_id={request.schedule_id}")
        print(f"📧 수신자: {request.to_emails}")
        
        # Supabase 클라이언트 생성
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 일정 정보 조회
        result = supabase.table("schedules").select("*").eq("id", request.schedule_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
        
        schedule = result.data[0]
        
        # ICS 콘텐츠 생성
        ics_content = ics_service.generate_ics_content(
            schedules=[schedule],
            title=schedule.get('title', '일정')
        )
        
        # Gmail 서비스를 통해 이메일 전송
        email_result = await gmail_service.send_schedule_invitation(
            google_credentials=request.google_credentials,
            to_emails=request.to_emails,
            schedule_title=schedule.get('title', '일정'),
            schedule_description=schedule.get('description', ''),
            ics_content=ics_content,
            sender_name="MUFI"
        )
        
        if email_result["success"]:
            return EmailResponse(
                success=True,
                message=email_result["message"],
                details={
                    "schedule_title": schedule.get('title'),
                    "recipients": request.to_emails,
                    "sent_count": email_result["total_sent"]
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=email_result.get("error", "이메일 전송에 실패했습니다.")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 일정 이메일 전송 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"일정 이메일 전송 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/send-group", response_model=EmailResponse)
async def send_group_email(
    request: SendGroupEmailRequest,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    그룹 일정들을 이메일로 전송
    """
    try:
        print(f"📧 그룹 이메일 전송 요청: file_id={request.file_id}")
        print(f"📧 수신자: {request.to_emails}")
        
        # Supabase 클라이언트 생성
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 그룹 일정들 조회
        result = supabase.table("schedules").select("*").eq("file_id", request.file_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="해당 그룹의 일정을 찾을 수 없습니다.")
        
        schedules = result.data
        
        # 그룹명 생성 (첫 번째 일정의 analysis_id에서 추출)
        group_name = schedules[0].get('analysis_id', '일정 그룹').split('_')[0] if schedules else '일정 그룹'
        
        # 전체 그룹의 ICS 콘텐츠 생성
        ics_content = ics_service.generate_ics_content(
            schedules=schedules,
            title=f"{group_name} - 전체 일정"
        )
        
        # 그룹 설명 생성
        schedule_summary = []
        for i, schedule in enumerate(schedules, 1):
            schedule_summary.append(f"{i}. {schedule.get('title', '제목 없음')}")
        
        group_description = f"""
        {group_name}에서 추출된 전체 일정입니다.
        
        포함된 일정:
        {chr(10).join(schedule_summary)}
        
        {request.message if request.message else ''}
        """.strip()
        
        # Gmail 서비스를 통해 이메일 전송
        email_result = await gmail_service.send_schedule_invitation(
            google_credentials=request.google_credentials,
            to_emails=request.to_emails,
            schedule_title=f"{group_name} - 전체 일정 ({len(schedules)}개)",
            schedule_description=group_description,
            ics_content=ics_content,
            sender_name="MUFI"
        )
        
        if email_result["success"]:
            return EmailResponse(
                success=True,
                message=email_result["message"],
                details={
                    "group_name": group_name,
                    "schedule_count": len(schedules),
                    "recipients": request.to_emails,
                    "sent_count": email_result["total_sent"]
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=email_result.get("error", "이메일 전송에 실패했습니다.")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 그룹 이메일 전송 오류: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"그룹 이메일 전송 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/test-credentials")
async def test_gmail_credentials(
    access_token: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    Gmail 자격증명 테스트
    """
    try:
        import httpx
        
        # Gmail API 프로필 조회로 토큰 유효성 검사
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/profile",
                headers=headers,
                timeout=10
            )
            response.raise_for_status()
            profile = response.json()
        
        return {
            "success": True,
            "message": "Gmail 자격증명이 유효합니다.",
            "email": profile.get('emailAddress'),
            "messages_total": profile.get('messagesTotal'),
            "threads_total": profile.get('threadsTotal')
        }
        
    except httpx.HTTPError as e:
        if e.response and e.response.status_code == 401:
            return {
                "success": False,
                "error": "Gmail 자격증명이 만료되었습니다. 다시 로그인해주세요.",
                "error_code": "AUTH_EXPIRED"
            }
        else:
            return {
                "success": False,
                "error": f"Gmail 자격증명 테스트 실패: {str(e)}",
                "error_code": "TEST_FAILED"
            }
    except Exception as e:
        logger.error(f"❌ Gmail 자격증명 테스트 오류: {e}")
        return {
            "success": False,
            "error": f"자격증명 테스트 중 오류가 발생했습니다: {str(e)}",
            "error_code": "UNKNOWN_ERROR"
        }