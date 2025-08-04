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
    subject: Optional[str] = ""
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
        print(f"📧 [DEBUG] Raw request received")
        print(f"📧 Request 타입: {type(request)}")
        
        # 개별 필드 안전하게 접근
        try:
            schedule_id = getattr(request, 'schedule_id', 'MISSING')
            to_emails = getattr(request, 'to_emails', 'MISSING') 
            subject = getattr(request, 'subject', 'MISSING')
            message = getattr(request, 'message', 'MISSING')
            google_credentials = getattr(request, 'google_credentials', 'MISSING')
            
            print(f"📧 Schedule ID: {schedule_id} (타입: {type(schedule_id)})")
            print(f"📧 수신자: {to_emails} (타입: {type(to_emails)})")
            print(f"📧 제목: {subject} (타입: {type(subject)})")
            print(f"📧 내용: {str(message)[:100] if message != 'MISSING' else 'MISSING'}...")
            print(f"📧 Google 인증: 있음={google_credentials != 'MISSING'}")
            
        except Exception as attr_error:
            print(f"📧 [ERROR] 속성 접근 오류: {attr_error}")
            
        print(f"📧 일정 이메일 전송 요청: schedule_id={request.schedule_id}")
        print(f"📧 수신자: {request.to_emails}")
        
        # Supabase 클라이언트 생성
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 일정 정보 조회
        result = supabase.table("schedules").select("*").eq("id", request.schedule_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
        
        schedule = result.data[0]
        
        # ICS 콘텐츠 가져오기 (캐시 → Storage 다운로드 → 새로 생성)
        ics_file_path = schedule.get('ics_file_path')
        
        print(f"🔍 [DEBUG] Raw ics_file_path: {ics_file_path}")
        
        if ics_file_path:
            # 캐시에서 먼저 확인
            if ics_file_path in gmail_service._ics_cache:
                print(f"🎯 캐시에서 ICS 파일 사용: {ics_file_path}")
                ics_content = gmail_service._ics_cache[ics_file_path]
            else:
                # URL에서 실제 파일 경로 추출
                if ics_file_path.startswith('http'):
                    # URL에서 파일 경로 부분만 추출 
                    # 예: https://xxx.supabase.co/storage/v1/object/public/schedules/users/xxx/file.ics
                    # → users/xxx/file.ics
                    parts = ics_file_path.split('/schedules/')
                    if len(parts) > 1:
                        storage_path = parts[1].split('?')[0]  # URL 파라미터 제거
                    else:
                        storage_path = ics_file_path
                else:
                    storage_path = ics_file_path
                
                print(f"📁 Storage에서 ICS 파일 다운로드")
                print(f"📁 원본 경로: {ics_file_path}")
                print(f"📁 Storage 경로: {storage_path}")
                
                try:
                    # Storage에서 ICS 파일 다운로드
                    file_response = supabase.storage.from_("schedules").download(storage_path)
                    ics_content = file_response.decode('utf-8')
                    # ICS 콘텐츠 확인
                    print(f"📄 ICS 콘텐츠 미리보기 (처음 200자):")
                    print(f"📄 {ics_content[:200]}...")
                    print(f"📄 ICS 콘텐츠 길이: {len(ics_content)} 문자")
                    
                    # 캐시에 저장 (스마트 캐시 관리)
                    gmail_service._manage_cache(ics_file_path, ics_content)
                    print(f"✅ Storage에서 ICS 파일 다운로드 및 캐시 저장 완료")
                except Exception as storage_error:
                    print(f"❌ Storage 다운로드 실패, 새로 생성: {storage_error}")
                    # Storage 다운로드 실패 시 새로 생성
                    ics_content = ics_service.generate_ics_content(
                        schedules=[schedule],
                        title=schedule.get('title', '일정')
                    )
        else:
            print(f"📝 ICS 파일 경로가 없어 새로 생성")
            # ICS 파일 경로가 없으면 새로 생성
            ics_content = ics_service.generate_ics_content(
                schedules=[schedule],
                title=schedule.get('title', '일정')
            )
        
        # 제목 설정 (사용자 입력 > 일정 제목 > 기본값)
        email_subject = request.subject or schedule.get('title', '일정')
        email_content = request.message or schedule.get('description', '')

        # Gmail 서비스를 통해 이메일 전송
        email_result = await gmail_service.send_schedule_invitation(
            google_credentials=request.google_credentials,
            to_emails=request.to_emails,
            schedule_title=email_subject,
            schedule_description=email_content,
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
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"❌ 일정 이메일 전송 오류: {e}")
        logger.error(f"❌ 상세 에러: {error_details}")
        print(f"❌ [ERROR] 일정 이메일 전송 상세 오류:\n{error_details}")
        
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