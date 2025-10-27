from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List, Dict, Any
import os
import tempfile
from datetime import datetime
import uuid
from supabase import create_client, Client
from .gpt_service import gpt_service
from ..auth.auth_service import verify_token

# Supabase 클라이언트 설정 (MUFI 프로젝트)
supabase_url = os.getenv("SUPABASE_URL", "https://znvwtoozdcnaqpuzbnhu.supabase.co")
supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd0b296ZGNuYXFwdXpibmh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ2Mjk0MjQsImV4cCI6MjA3MDIwNTQyNH0.UdqqsxqdUoPtPNyQSRfEjKL6cg90dUDNuzsancxIYR0")
supabase: Client = create_client(supabase_url, supabase_key)

router = APIRouter(prefix="/api/analysis", tags=["통화 분석"])

# JWT 토큰 검증
security = HTTPBearer()

@router.post("/upload-file")
async def analyze_uploaded_file(
    file: UploadFile = File(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    업로드된 텍스트 파일을 분석합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        
        # 파일 확장자 검증
        if not file.filename.lower().endswith('.txt'):
            raise HTTPException(status_code=400, detail="텍스트 파일(.txt)만 업로드 가능합니다.")
        
        # 파일 크기 제한 (10MB)
        if file.size and file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="파일 크기는 10MB를 초과할 수 없습니다.")
        
        # 파일 내용 읽기
        content = await file.read()
        content_str = content.decode('utf-8')
        
        print(f"📁 파일 업로드 분석 시작")
        print(f"📄 파일명: {file.filename}")
        print(f"📏 파일 크기: {len(content)} bytes")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"📝 파일 내용 (처음 500자): {content_str[:500]}...")
        
        # GPT 분석 실행
        result = await gpt_service.analyze_call_content(content_str)
        
        print(f"✅ 분석 완료")
        print(f"📊 결과: {result}")
        
        return {
            "success": True,
            "message": "파일 분석이 완료되었습니다.",
            "data": result,
            "user": user_data
        }
        
    except Exception as e:
        print(f"❌ 파일 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/analyze-text")
async def analyze_text_content(
    content: str = Form(...),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    직접 입력된 텍스트를 분석합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        
        # 내용 검증
        if not content.strip():
            raise HTTPException(status_code=400, detail="분석할 내용을 입력해주세요.")
        
        print(f"📝 텍스트 분석 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"📝 입력 내용 (처음 500자): {content[:500]}...")
        
        # GPT 분석 실행
        result = await gpt_service.analyze_call_content(content)
        
        print(f"✅ 분석 완료")
        print(f"📊 결과: {result}")
        
        return {
            "success": True,
            "message": "텍스트 분석이 완료되었습니다.",
            "data": result,
            "user": user_data
        }
        
    except Exception as e:
        print(f"❌ 텍스트 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 중 오류가 발생했습니다: {str(e)}")

@router.put("/update-schedule")
async def update_schedule(
    schedule_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    분석된 일정을 수정합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        
        # 필수 필드 검증
        required_fields = ["type", "index", "field", "value"]
        for field in required_fields:
            if field not in schedule_data:
                raise HTTPException(status_code=400, detail=f"필수 필드가 누락되었습니다: {field}")
        
        schedule_type = schedule_data["type"]
        schedule_index = schedule_data["index"]
        field_name = schedule_data["field"]
        field_value = schedule_data["value"]
        
        # 필드 값 유효성 검사
        if not _validate_field_value(field_name, field_value):
            raise HTTPException(status_code=400, detail=f"잘못된 필드 값입니다: {field_name}")
        
        print(f"📝 일정 수정 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"📅 일정 타입: {schedule_type}")
        print(f"📅 일정 인덱스: {schedule_index}")
        print(f"📝 수정 필드: {field_name}")
        print(f"📝 수정 값: {field_value}")
        
        # 여기서 실제 데이터베이스 업데이트 로직을 구현할 수 있습니다
        # 현재는 성공 응답만 반환
        
        return {
            "success": True,
            "message": "일정이 성공적으로 수정되었습니다.",
            "data": {
                "type": schedule_type,
                "index": schedule_index,
                "field": field_name,
                "value": field_value
            },
            "user": user_data
        }
        
    except Exception as e:
        print(f"❌ 일정 수정 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 수정 중 오류가 발생했습니다: {str(e)}")

@router.post("/save-all-changes")
async def save_all_changes(
    schedules_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    모든 변경사항을 데이터베이스에 저장합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))  # Google ID 또는 이메일
        
        # 데이터 검증
        if "group" not in schedules_data and "personal" not in schedules_data:
            raise HTTPException(status_code=400, detail="일정 데이터가 누락되었습니다.")
        
        print(f"💾 모든 변경사항 저장 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"🆔 사용자 ID: {user_id}")
        print(f"📊 그룹 일정 개수: {len(schedules_data.get('group', []))}")
        print(f"📊 개인 일정 개수: {len(schedules_data.get('personal', []))}")
        
        # 분석 세션 ID 생성 (이번 저장 세션을 위한 고유 ID)
        analysis_session_id = str(uuid.uuid4())
        
        saved_schedules = []
        total_schedules = 0
        
        # analysis_source_name 가져오기
        analysis_source_name = schedules_data.get('analysis_source_name', '통화 분석')
        
        # 그룹 일정 저장
        for schedule in schedules_data.get('group', []):
            try:
                schedule_data = {
                    "user_id": user_id,
                    "analysis_session_id": analysis_session_id,
                    "analysis_source_name": analysis_source_name,
                    "title": schedule.get('title', ''),
                    "description": schedule.get('description', ''),
                    "location": schedule.get('location', ''),
                    "start_datetime": schedule.get('start_datetime'),
                    "end_datetime": schedule.get('end_datetime'),
                    "schedule_type": "group",
                    "participants": schedule.get('participants', [])
                }
                
                # Supabase에 저장
                result = supabase.table('schedules').insert(schedule_data).execute()
                saved_schedules.append(schedule_data)
                total_schedules += 1
                print(f"✅ 그룹 일정 저장 완료: {schedule_data['title']}")
                
            except Exception as e:
                print(f"❌ 그룹 일정 저장 실패: {str(e)}")
                raise HTTPException(status_code=500, detail=f"그룹 일정 저장 중 오류: {str(e)}")
        
        # 개인 일정 저장
        for schedule in schedules_data.get('personal', []):
            try:
                schedule_data = {
                    "user_id": user_id,
                    "analysis_session_id": analysis_session_id,
                    "analysis_source_name": analysis_source_name,
                    "title": schedule.get('title', ''),
                    "description": schedule.get('description', ''),
                    "location": schedule.get('location', ''),
                    "start_datetime": schedule.get('start_datetime'),
                    "end_datetime": schedule.get('end_datetime'),
                    "schedule_type": "personal",
                    "participants": schedule.get('participants', [])
                }
                
                # Supabase에 저장
                result = supabase.table('schedules').insert(schedule_data).execute()
                saved_schedules.append(schedule_data)
                total_schedules += 1
                print(f"✅ 개인 일정 저장 완료: {schedule_data['title']}")
                
            except Exception as e:
                print(f"❌ 개인 일정 저장 실패: {str(e)}")
                raise HTTPException(status_code=500, detail=f"개인 일정 저장 중 오류: {str(e)}")
        
        print(f"🎉 모든 일정 저장 완료! 총 {total_schedules}개 일정 저장됨")
        
        return {
            "success": True,
            "message": f"모든 변경사항이 성공적으로 저장되었습니다. (총 {total_schedules}개 일정)",
            "data": {
                "analysis_session_id": analysis_session_id,
                "total_schedules": total_schedules,
                "group_count": len(schedules_data.get('group', [])),
                "personal_count": len(schedules_data.get('personal', [])),
                "saved_schedules": saved_schedules
            },
            "user": user_data
        }
        
    except Exception as e:
        print(f"❌ 변경사항 저장 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"변경사항 저장 중 오류가 발생했습니다: {str(e)}")

@router.post("/export-calendar")
async def export_calendar(
    schedules_data: Dict[str, Any],
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    일정을 캘린더 파일로 내보냅니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        
        # 데이터 검증
        if "group" not in schedules_data and "personal" not in schedules_data:
            raise HTTPException(status_code=400, detail="일정 데이터가 누락되었습니다.")
        
        print(f"📅 캘린더 내보내기 시작")
        print(f"👤 사용자: {user_data.get('email', 'unknown')}")
        print(f"📊 총 일정 개수: {len(schedules_data.get('group', [])) + len(schedules_data.get('personal', []))}")
        
        # ICS 파일 생성 로직을 여기에 구현할 수 있습니다
        # 현재는 성공 응답만 반환
        
        return {
            "success": True,
            "message": "캘린더 파일이 성공적으로 생성되었습니다.",
            "data": {
                "file_url": "/api/analysis/download-calendar",  # 실제 다운로드 URL
                "total_schedules": len(schedules_data.get('group', [])) + len(schedules_data.get('personal', []))
            },
            "user": user_data
        }
        
    except Exception as e:
        print(f"❌ 캘린더 내보내기 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"캘린더 내보내기 중 오류가 발생했습니다: {str(e)}")

def _validate_field_value(field_name: str, field_value: Any) -> bool:
    """
    필드 값의 유효성을 검사합니다.
    """
    if field_name in ["title", "description", "location"]:
        return isinstance(field_value, str) and len(field_value.strip()) > 0
    elif field_name in ["start_datetime", "end_datetime"]:
        # 날짜 형식 검증 로직을 여기에 추가할 수 있습니다
        return isinstance(field_value, str) and len(field_value.strip()) > 0
    elif field_name == "participants":
        return isinstance(field_value, list) or (isinstance(field_value, str) and len(field_value.strip()) >= 0)
    else:
        return True

@router.get("/health")
async def analysis_health_check():
    """
    분석 서비스 상태 확인
    """
    return {
        "status": "healthy",
        "service": "call-analysis",
        "gpt_available": gpt_service.client is not None
    }
