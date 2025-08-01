"""
Google Calendar 연동 API 라우터
OAuth 2.0을 통해 사용자의 Google Calendar에 ICS 파일을 자동으로 추가합니다.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import RedirectResponse, JSONResponse
from typing import Optional, Dict, Any
import logging

from services.google_calendar_service import GoogleCalendarService
from services.ics_service import ICSService
from supabase import create_client
from config.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# 서비스 인스턴스
google_calendar_service = GoogleCalendarService()
ics_service = ICSService()

@router.get("/auth/google")
async def google_auth(user_id: str = Query(..., description="사용자 ID")):
    """
    Google OAuth 인증을 시작합니다.
    
    Args:
        user_id: 사용자 ID
        
    Returns:
        Google OAuth 인증 페이지로 리다이렉트
    """
    try:
        auth_url = google_calendar_service.get_auth_url(user_id)
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Google 인증 URL 생성 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Google 인증 설정 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/auth/google/callback")
async def google_auth_callback(
    code: str = Query(..., description="Google 인증 코드"),
    state: str = Query(..., description="사용자 ID"),
    error: Optional[str] = Query(None, description="오류 메시지")
):
    """
    Google OAuth 콜백을 처리합니다.
    
    Args:
        code: Google에서 반환한 인증 코드
        state: 사용자 ID
        error: 오류 메시지 (선택사항)
        
    Returns:
        인증 결과 및 토큰 정보
    """
    try:
        if error:
            logger.error(f"Google 인증 오류: {error}")
            raise HTTPException(
                status_code=400,
                detail=f"Google 인증이 거부되었습니다: {error}"
            )
        
        # OAuth 콜백 처리
        result = google_calendar_service.handle_oauth_callback(code, state)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=400,
                detail=f"Google 인증 처리 실패: {result.get('error', '알 수 없는 오류')}"
            )
        
        # TODO: 여기서 토큰을 안전하게 저장 (예: 데이터베이스)
        # 현재는 임시로 세션이나 로컬 스토리지에 저장하도록 안내
        
        # 성공 페이지로 리다이렉트 (토큰 정보 포함)
        return RedirectResponse(
            url=f"http://localhost:8000/dashboard.html?google_auth=success&user_id={state}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth 콜백 처리 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"인증 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/calendar/add-schedule")
async def add_schedule_to_calendar(request: Dict[str, Any]):
    """
    ICS 파일을 Google Calendar에 추가합니다.
    
    Request Body:
        {
            "schedule_id": "string",  # 일정 ID
            "user_id": "string",      # 사용자 ID
            "google_credentials": {   # Google OAuth 토큰 정보
                "access_token": "string",
                "refresh_token": "string",
                ...
            },
            "calendar_id": "primary"  # 대상 캘린더 ID (선택사항)
        }
        
    Returns:
        캘린더 추가 결과
    """
    try:
        schedule_id = request.get('schedule_id')
        user_id = request.get('user_id')
        google_credentials = request.get('google_credentials')
        calendar_id = request.get('calendar_id', 'primary')
        
        if not all([schedule_id, user_id, google_credentials]):
            raise HTTPException(
                status_code=400,
                detail="schedule_id, user_id, google_credentials는 필수 항목입니다."
            )
        
        # 데이터베이스에서 일정 정보 조회
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        schedule_result = supabase.table("schedules")\
            .select("*")\
            .eq("id", schedule_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not schedule_result.data:
            raise HTTPException(
                status_code=404,
                detail="해당 일정을 찾을 수 없습니다."
            )
        
        schedule = schedule_result.data[0]
        
        # ICS 파일 경로에서 내용 가져오기
        ics_file_path = schedule.get('ics_file_path')
        if not ics_file_path:
            # ICS 파일이 없으면 일정 정보로 새로 생성
            logger.info(f"ICS 파일 없음, 일정 정보로 새로 생성: {schedule_id}")
            ics_content = ics_service.generate_ics_content([schedule], "MUFI 일정")
        else:
            # 스토리지에서 ICS 파일 다운로드
            try:
                # Supabase Storage에서 파일 다운로드
                # ics_file_path가 public URL이면 직접 사용
                if ics_file_path.startswith('http'):
                    import httpx
                    async with httpx.AsyncClient() as client:
                        response = await client.get(ics_file_path)
                        response.raise_for_status()
                        ics_content = response.text
                else:
                    # 상대 경로면 스토리지에서 다운로드
                    file_response = supabase.storage.from_("schedules").download(ics_file_path)
                    ics_content = file_response.decode('utf-8')
                    
            except Exception as download_error:
                logger.error(f"ICS 파일 다운로드 실패: {download_error}")
                # 실패 시 일정 정보로 새로 생성
                ics_content = ics_service.generate_ics_content([schedule], "MUFI 일정")
        
        # Google Calendar에 추가
        result = google_calendar_service.add_ics_to_calendar(
            credentials_data=google_credentials,
            ics_content=ics_content,
            calendar_id=calendar_id
        )
        
        if result.get('success'):
            logger.info(f"Google Calendar 추가 성공: {schedule_id}, 추가된 이벤트: {result.get('added_count', 0)}")
            return {
                "success": True,
                "message": f"Google Calendar에 {result.get('added_count', 0)}개 일정이 추가되었습니다.",
                "schedule_id": schedule_id,
                "calendar_id": calendar_id,
                "details": result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Google Calendar 추가 실패: {result.get('error', '알 수 없는 오류')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캘린더 추가 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"캘린더 추가 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/calendar/add-group")
async def add_group_to_calendar(request: Dict[str, Any]):
    """
    파일 그룹의 모든 일정을 Google Calendar에 추가합니다.
    
    Request Body:
        {
            "file_id": "string",      # 파일 ID (그룹 식별자)
            "user_id": "string",      # 사용자 ID
            "google_credentials": {   # Google OAuth 토큰 정보
                "access_token": "string",
                "refresh_token": "string",
                ...
            },
            "calendar_id": "primary"  # 대상 캘린더 ID (선택사항)
        }
        
    Returns:
        캘린더 추가 결과
    """
    try:
        file_id = request.get('file_id')
        user_id = request.get('user_id')
        google_credentials = request.get('google_credentials')
        calendar_id = request.get('calendar_id', 'primary')
        
        if not all([file_id, user_id, google_credentials]):
            raise HTTPException(
                status_code=400,
                detail="file_id, user_id, google_credentials는 필수 항목입니다."
            )
        
        # 데이터베이스에서 파일 그룹의 모든 일정 조회
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        schedules_result = supabase.table("schedules")\
            .select("*")\
            .eq("file_id", file_id)\
            .eq("user_id", user_id)\
            .execute()
        
        if not schedules_result.data:
            raise HTTPException(
                status_code=404,
                detail="해당 파일 그룹의 일정을 찾을 수 없습니다."
            )
        
        schedules = schedules_result.data
        
        # 그룹 전체를 위한 ICS 생성
        group_name = schedules[0].get('analysis_id', 'MUFI 일정').split('_')[0]
        ics_content = ics_service.generate_ics_content(schedules, f"MUFI - {group_name}")
        
        # Google Calendar에 추가
        result = google_calendar_service.add_ics_to_calendar(
            credentials_data=google_credentials,
            ics_content=ics_content,
            calendar_id=calendar_id
        )
        
        if result.get('success'):
            logger.info(f"Google Calendar 그룹 추가 성공: {file_id}, 추가된 이벤트: {result.get('added_count', 0)}")
            return {
                "success": True,
                "message": f"Google Calendar에 {result.get('added_count', 0)}개 일정이 추가되었습니다.",
                "file_id": file_id,
                "calendar_id": calendar_id,
                "total_schedules": len(schedules),
                "details": result
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Google Calendar 추가 실패: {result.get('error', '알 수 없는 오류')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캘린더 그룹 추가 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"캘린더 그룹 추가 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/calendar/list")
async def get_user_calendars(request: Dict[str, Any]):
    """
    사용자의 Google Calendar 목록을 가져옵니다.
    
    Request Body:
        {
            "google_credentials": {   # Google OAuth 토큰 정보
                "access_token": "string",
                "refresh_token": "string",
                ...
            }
        }
        
    Returns:
        캘린더 목록
    """
    try:
        google_credentials = request.get('google_credentials')
        
        if not google_credentials:
            raise HTTPException(
                status_code=400,
                detail="google_credentials는 필수 항목입니다."
            )
        
        # Google Calendar 목록 조회
        result = google_calendar_service.get_user_calendars(google_credentials)
        
        if result.get('success'):
            return {
                "success": True,
                "calendars": result.get('calendars', []),
                "total_count": result.get('total_count', 0)
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"캘린더 목록 조회 실패: {result.get('error', '알 수 없는 오류')}"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"캘린더 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"캘린더 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )