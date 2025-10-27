from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any
import os
from supabase import create_client, Client
from ..auth.auth_service import verify_token
from ..auth.google_token_service import GoogleTokenService
from .calendar import GoogleCalendarService
from .gmail_service import GmailService
import httpx
import json
from datetime import datetime, timedelta
import uuid

# Supabase 클라이언트 설정 (MUFI 프로젝트)
supabase_url = os.getenv("SUPABASE_URL", "https://znvwtoozdcnaqpuzbnhu.supabase.co")
supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd0b296ZGNuYXFwdXpibmh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ2Mjk0MjQsImV4cCI6MjA3MDIwNTQyNH0.UdqqsxqdUoPtPNyQSRfEjKL6cg90dUDNuzsancxIYR0")
supabase: Client = create_client(supabase_url, supabase_key)

# Google OAuth 설정
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

router = APIRouter(prefix="/api/schedules", tags=["일정 관리"])

# Gmail 전송 요청 모델
class GmailSendRequest(BaseModel):
    recipients: List[str]
    subject: str = "일정 안내"
    message: str = ""

# JWT 토큰 검증
security = HTTPBearer()

@router.get("/analysis-sessions")
async def get_analysis_sessions(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    사용자의 모든 분석 세션을 조회합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"📊 분석 세션 조회 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"🆔 사용자 ID: {user_id}")
        
        # 분석 세션별로 일정 조회
        result = supabase.table('schedules').select(
            'analysis_session_id, analysis_source_name, created_at'
        ).eq('user_id', user_id).execute()
        
        if result.data:
            # 중복 제거하여 고유한 분석 세션만 추출
            sessions = {}
            for schedule in result.data:
                session_id = schedule['analysis_session_id']
                if session_id not in sessions:
                    sessions[session_id] = {
                        'analysis_session_id': session_id,
                        'analysis_source_name': schedule['analysis_source_name'],
                        'created_at': schedule['created_at'],
                        'total_schedules': 0,
                        'group_count': 0,
                        'personal_count': 0
                    }
                sessions[session_id]['total_schedules'] += 1
            
            # 각 세션별 일정 개수 세기
            for session_id in sessions:
                session_result = supabase.table('schedules').select('schedule_type').eq('analysis_session_id', session_id).execute()
                for schedule in session_result.data:
                    if schedule['schedule_type'] == 'group':
                        sessions[session_id]['group_count'] += 1
                    elif schedule['schedule_type'] == 'personal':
                        sessions[session_id]['personal_count'] += 1
            
            sessions_list = list(sessions.values())
            sessions_list.sort(key=lambda x: x['created_at'], reverse=True)  # 최신순 정렬
            
            print(f"✅ 분석 세션 조회 완료: {len(sessions_list)}개 세션")
            
            return {
                "success": True,
                "message": f"분석 세션 {len(sessions_list)}개를 조회했습니다.",
                "data": {
                    "sessions": sessions_list,
                    "total_sessions": len(sessions_list)
                },
                "user": user_data
            }
        else:
            print(f"📭 분석 세션이 없습니다.")
            return {
                "success": True,
                "message": "저장된 분석 세션이 없습니다.",
                "data": {
                    "sessions": [],
                    "total_sessions": 0
                },
                "user": user_data
            }
            
    except Exception as e:
        print(f"❌ 분석 세션 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 세션 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/session/{analysis_session_id}")
async def get_schedules_by_session(
    analysis_session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    특정 분석 세션의 모든 일정을 조회합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"📅 일정 조회 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"🆔 사용자 ID: {user_id}")
        print(f"📊 분석 세션 ID: {analysis_session_id}")
        
        # 해당 세션의 모든 일정 조회
        result = supabase.table('schedules').select('*').eq('analysis_session_id', analysis_session_id).eq('user_id', user_id).execute()
        
        if result.data:
            # 그룹/개인 일정으로 분류
            group_schedules = []
            personal_schedules = []
            
            for schedule in result.data:
                schedule_data = {
                    'id': schedule['id'],
                    'title': schedule['title'],
                    'description': schedule['description'],
                    'location': schedule['location'],
                    'start_datetime': schedule['start_datetime'],
                    'end_datetime': schedule['end_datetime'],
                    'participants': schedule['participants'],
                    'schedule_type': schedule['schedule_type'],
                    'created_at': schedule['created_at']
                }
                
                if schedule['schedule_type'] == 'group':
                    group_schedules.append(schedule_data)
                else:
                    personal_schedules.append(schedule_data)
            
            # 세션 정보 조회
            session_info = supabase.table('schedules').select('analysis_source_name, created_at').eq('analysis_session_id', analysis_session_id).limit(1).execute()
            
            session_data = {
                'analysis_session_id': analysis_session_id,
                'analysis_source_name': session_info.data[0]['analysis_source_name'] if session_info.data else '통화 분석',
                'created_at': session_info.data[0]['created_at'] if session_info.data else None,
                'total_schedules': len(result.data),
                'group_count': len(group_schedules),
                'personal_count': len(personal_schedules)
            }
            
            print(f"✅ 일정 조회 완료: 그룹 {len(group_schedules)}개, 개인 {len(personal_schedules)}개")
            
            return {
                "success": True,
                "message": f"일정 {len(result.data)}개를 조회했습니다.",
                "data": {
                    "session": session_data,
                    "schedules": {
                        "group": group_schedules,
                        "personal": personal_schedules
                    }
                },
                "user": user_data
            }
        else:
            print(f"📭 해당 세션의 일정이 없습니다.")
            return {
                "success": True,
                "message": "해당 분석 세션의 일정이 없습니다.",
                "data": {
                    "session": None,
                    "schedules": {
                        "group": [],
                        "personal": []
                    }
                },
                "user": user_data
            }
            
    except Exception as e:
        print(f"❌ 일정 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/session/{analysis_session_id}")
async def delete_analysis_session(
    analysis_session_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    특정 분석 세션의 모든 일정을 삭제합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"🗑️ 분석 세션 삭제 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"🆔 사용자 ID: {user_id}")
        print(f"📊 분석 세션 ID: {analysis_session_id}")
        
        # 해당 세션의 모든 일정 삭제
        result = supabase.table('schedules').delete().eq('analysis_session_id', analysis_session_id).eq('user_id', user_id).execute()
        
        deleted_count = len(result.data) if result.data else 0
        
        print(f"✅ 분석 세션 삭제 완료: {deleted_count}개 일정 삭제됨")
        
        return {
            "success": True,
            "message": f"분석 세션이 성공적으로 삭제되었습니다. ({deleted_count}개 일정)",
            "data": {
                "deleted_count": deleted_count,
                "analysis_session_id": analysis_session_id
            },
            "user": user_data
        }
        
    except Exception as e:
        print(f"❌ 분석 세션 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 세션 삭제 중 오류가 발생했습니다: {str(e)}")

@router.put("/schedule/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    schedule_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    특정 일정을 수정합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"✏️ 일정 수정 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"🆔 사용자 ID: {user_id}")
        print(f"📅 일정 ID: {schedule_id}")
        print(f"📝 수정 데이터: {schedule_data}")
        
        # 수정 가능한 필드들만 허용
        allowed_fields = ['title', 'description', 'location', 'start_datetime', 'end_datetime', 'participants']
        update_data = {k: v for k, v in schedule_data.items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다.")
        
        # 해당 일정 수정 (사용자 소유 확인)
        result = supabase.table('schedules').update(update_data).eq('id', schedule_id).eq('user_id', user_id).execute()
        
        updated_count = len(result.data) if result.data else 0
        
        if updated_count > 0:
            print(f"✅ 일정 수정 완료: {updated_count}개 일정 수정됨")
            return {
                "success": True,
                "message": "일정이 성공적으로 수정되었습니다.",
                "data": {
                    "updated_count": updated_count,
                    "schedule_id": schedule_id,
                    "updated_fields": list(update_data.keys())
                },
                "user": user_data
            }
        else:
            print(f"❌ 일정을 찾을 수 없거나 수정 권한이 없습니다.")
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없거나 수정 권한이 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 일정 수정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 수정 중 오류가 발생했습니다: {str(e)}")

@router.put("/session/{session_id}/title")
async def update_session_title(
    session_id: str,
    title_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    분석 세션의 제목을 수정합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"✏️ 세션 제목 수정 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"🆔 사용자 ID: {user_id}")
        print(f"📅 세션 ID: {session_id}")
        print(f"📝 새 제목: {title_data.get('analysis_source_name')}")
        
        new_title = title_data.get('analysis_source_name')
        if not new_title or not new_title.strip():
            raise HTTPException(status_code=400, detail="제목을 입력해주세요.")
        
        # 해당 세션의 모든 일정의 analysis_source_name 업데이트 (사용자 소유 확인)
        result = supabase.table('schedules').update({
            'analysis_source_name': new_title.strip()
        }).eq('analysis_session_id', session_id).eq('user_id', user_id).execute()
        
        updated_count = len(result.data) if result.data else 0
        
        if updated_count > 0:
            print(f"✅ 세션 제목 수정 완료: {updated_count}개 일정의 제목 수정됨")
            return {
                "success": True,
                "message": "세션 제목이 성공적으로 수정되었습니다.",
                "data": {
                    "updated_count": updated_count,
                    "session_id": session_id,
                    "new_title": new_title.strip()
                },
                "user": user_data
            }
        else:
            print(f"❌ 세션을 찾을 수 없거나 수정 권한이 없습니다.")
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없거나 수정 권한이 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 세션 제목 수정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"세션 제목 수정 중 오류가 발생했습니다: {str(e)}")



@router.delete("/schedule/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    특정 일정을 삭제합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"🗑️ 일정 삭제 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"🆔 사용자 ID: {user_id}")
        print(f"📅 일정 ID: {schedule_id}")
        
        # 해당 일정 삭제 (사용자 소유 확인)
        result = supabase.table('schedules').delete().eq('id', schedule_id).eq('user_id', user_id).execute()
        
        deleted_count = len(result.data) if result.data else 0
        
        if deleted_count > 0:
            print(f"✅ 일정 삭제 완료: {deleted_count}개 일정 삭제됨")
            return {
                "success": True,
                "message": "일정이 성공적으로 삭제되었습니다.",
                "data": {
                    "deleted_count": deleted_count,
                    "schedule_id": schedule_id
                },
                "user": user_data
            }
        else:
            print(f"❌ 일정을 찾을 수 없거나 삭제 권한이 없습니다.")
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없거나 삭제 권한이 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 일정 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 삭제 중 오류가 발생했습니다: {str(e)}")

@router.post("/schedule/{schedule_id}/add-to-calendar")
async def add_schedule_to_calendar(
    schedule_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    특정 일정을 Google Calendar에 추가합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"📅 캘린더 추가 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"🆔 사용자 ID: {user_id}")
        print(f"📅 일정 ID: {schedule_id}")
        
        # 해당 일정 조회 (사용자 소유 확인)
        result = supabase.table('schedules').select('*').eq('id', schedule_id).eq('user_id', user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없거나 접근 권한이 없습니다.")
        
        schedule = result.data[0]
        
        # Google Calendar API를 사용하여 일정 추가
        print(f"🔍 Google Calendar API 호출 시작")
        calendar_event = await GoogleCalendarService.create_calendar_event(schedule, user_data)
        
        if calendar_event:
            print(f"✅ 캘린더 추가 완료: {calendar_event.get('id')}")
            
            return {
                "success": True,
                "message": "일정이 Google Calendar에 성공적으로 추가되었습니다.",
                "data": {
                    "schedule_id": schedule_id,
                    "calendar_event_id": calendar_event.get('id'),
                    "calendar_event_url": calendar_event.get('htmlLink'),
                    "added_at": datetime.utcnow().isoformat()
                },
                "user": user_data
            }
        else:
            print(f"❌ Google Calendar API 호출 실패")
            raise HTTPException(status_code=500, detail="Google Calendar에 일정 추가에 실패했습니다. 권한을 확인해주세요.")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 캘린더 추가 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캘린더 추가 중 오류가 발생했습니다: {str(e)}")



@router.get("/health")
async def schedules_health_check():
    """
    일정 관리 서비스 상태 확인
    """
    return {
        "status": "healthy",
        "service": "schedules-management"
    }

@router.get("/google-token-status")
async def check_google_token_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    사용자의 Google 토큰 상태 확인
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = int(user_data.get('sub'))
        
        # Google 토큰 상태 확인
        token_status = await GoogleTokenService.check_token_status(user_id)
        
        return {
            "success": True,
            "data": token_status,
            "user": user_data
        }
        
    except Exception as e:
        print(f"❌ Google 토큰 상태 확인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"토큰 상태 확인 중 오류가 발생했습니다: {str(e)}")

@router.post("/send-email")
async def send_email(
    email_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Gmail API를 사용하여 이메일 발송 (자동 토큰 갱신 포함)
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        # 이메일 데이터 추출
        to_email = email_data.get('to_email')
        subject = email_data.get('subject', 'MUFI 일정 안내')
        body = email_data.get('body', '')
        
        if not to_email or not body:
            raise HTTPException(status_code=400, detail="수신자 이메일과 내용을 입력해주세요.")
        
        print(f"📧 이메일 발송 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"📧 수신자: {to_email}")
        print(f"📝 제목: {subject}")
        
        # Gmail 서비스에서 자동으로 토큰 확인 및 갱신됨
        
        # Gmail 서비스 사용
        gmail_service = GmailService()
        result = gmail_service.send_email(
            user_id=user_id,
            to_email=to_email,
            subject=subject,
            body=body,
            is_html=True
        )
        
        if result['success']:
            print(f"✅ 이메일 발송 완료: {to_email}")
            return {
                "success": True,
                "message": result['message'],
                "data": {
                    "to_email": to_email,
                    "subject": subject,
                    "message_id": result.get('message_id'),
                    "sent_at": datetime.utcnow().isoformat()
                },
                "user": user_data
            }
        else:
            raise HTTPException(status_code=500, detail=result.get('error', '이메일 발송에 실패했습니다.'))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 이메일 발송 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"이메일 발송 중 오류가 발생했습니다: {str(e)}")

@router.post("/{schedule_id}/send-gmail")
async def send_schedule_gmail(
    schedule_id: str,
    email_request: GmailSendRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    특정 일정을 Gmail로 전송합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"📧 Gmail 일정 전송 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"📅 일정 ID: {schedule_id}")
        print(f"📧 수신자 수: {len(email_request.recipients)}")
        
        # 일정 데이터 조회
        result = supabase.table('schedules').select('*').eq('id', schedule_id).eq('user_id', user_id).execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
        
        schedule_data = result.data[0]
        print(f"📅 일정 정보: {schedule_data.get('title', '')}")
        
        # Gmail 서비스 사용 (ICS 첨부 포함)
        gmail_service = GmailService()
        result = gmail_service.send_schedule_email(
            user_id=user_id,
            schedule_data=schedule_data,
            recipients=email_request.recipients,
            subject=email_request.subject,
            extra_message=email_request.message
        )
        
        if result["success"]:
            print(f"✅ Gmail 일정 전송 성공")
            return {
                "success": True,
                "message": result["message"],
                "data": {
                    "schedule_id": schedule_id,
                    "recipients": email_request.recipients,
                    "subject": email_request.subject,
                    "results": result.get("results"),
                    "sent_at": datetime.utcnow().isoformat()
                },
                "user": user_data
            }
        else:
            print(f"❌ Gmail 일정 전송 실패: {result.get('error', '')}")
            raise HTTPException(status_code=500, detail=result.get("error", "Gmail 전송에 실패했습니다."))
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Gmail 일정 전송 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Gmail 전송 중 오류가 발생했습니다: {str(e)}")

@router.get("/gmail-auth-status")
async def check_gmail_auth_status(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Gmail 인증 상태를 확인합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"🔍 Gmail 인증 상태 확인")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        
        # Gmail 서비스 사용
        try:
            gmail_service = GmailService()
            auth_status = gmail_service.check_gmail_permissions(user_id)
            
            return {
                "success": True,
                "data": auth_status,
                "user": user_data
            }
        except Exception as gmail_error:
            # Gmail 권한이 없거나 토큰이 없는 경우
            return {
                "success": True,
                "data": {
                    "success": False,
                    "error": str(gmail_error)
                },
                "user": user_data
            }
        
    except Exception as e:
        print(f"❌ Gmail 인증 상태 확인 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"인증 상태 확인 중 오류가 발생했습니다: {str(e)}")