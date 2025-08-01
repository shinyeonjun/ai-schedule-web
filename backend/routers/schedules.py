"""
Schedule management routes
"""
from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.responses import JSONResponse, FileResponse
from typing import Dict, Any, List, Optional
from services.database_service import DatabaseService
from services.ics_service import ICSService
from core.dependencies import get_current_user
from models.analysis import Schedule
from supabase import create_client
from config.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["schedules"])
db_service = DatabaseService()
ics_service = ICSService()


@router.get("/")
async def get_user_schedules(
    user_id: Optional[str] = Query(None, description="User ID"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get all schedules for user"""
    try:
        # 인증 비활성화 상태에서는 user_id를 Query 파라미터로 받음
        print(f"🔍 [DEBUG] 일정 조회 요청 - user_id: {user_id}")
        
        if not user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 페이지네이션 계산
        offset = (page - 1) * limit
        
        print(f"🔍 [DEBUG] 페이지네이션 - page: {page}, limit: {limit}, offset: {offset}")
        
        # 사용자의 일정 조회
        result = supabase.table("schedules")\
            .select("*")\
            .eq("user_id", user_id)\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        
        schedules = result.data if result.data else []
        print(f"🔍 [DEBUG] 조회된 일정 개수: {len(schedules)}")
        
        if schedules:
            print(f"🔍 [DEBUG] 첫 번째 일정: {schedules[0].get('title', 'N/A')}")
        
        # 총 개수 조회
        count_result = supabase.table("schedules")\
            .select("*", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        
        total = count_result.count if count_result.count else 0
        print(f"🔍 [DEBUG] 총 일정 개수: {total}")
        
        # 모든 사용자 ID 조회 (디버깅용)
        all_users_result = supabase.table("schedules")\
            .select("user_id")\
            .execute()
        
        unique_user_ids = list(set([item['user_id'] for item in all_users_result.data if all_users_result.data]))
        print(f"🔍 [DEBUG] DB에 있는 모든 user_id들: {unique_user_ids}")
        
        # file_id 기준으로 그룹화
        file_groups = {}
        for schedule in schedules:
            # file_id를 기준으로 그룹화 (같은 분석 파일의 모든 일정)
            file_id = schedule.get('file_id', 'unknown')
            analysis_id = schedule.get('analysis_id', 'unknown')
            
            print(f"🔍 [DEBUG] 일정 그룹화 - file_id: {file_id}, analysis_id: {analysis_id}, title: {schedule.get('title', '')}")
            
            if file_id not in file_groups:
                file_groups[file_id] = {
                    "file_id": file_id,
                    "analysis_id": analysis_id,  # 첫 번째 일정의 analysis_id 사용
                    "schedules": [],
                    "created_at": schedule.get('created_at'),
                    "source_name": analysis_id.split('_')[0] if '_' in analysis_id else analysis_id,
                    "schedule_count": 0
                }
            
            file_groups[file_id]["schedules"].append(schedule)
            file_groups[file_id]["schedule_count"] += 1
        
        # 리스트로 변환하고 최신순 정렬
        grouped_schedules = list(file_groups.values())
        grouped_schedules.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return {
            "success": True,
            "schedules": schedules,  # 기존 호환성
            "grouped_schedules": grouped_schedules,  # 새로운 그룹화 데이터
            "total": total,
            "groups_count": len(grouped_schedules),
            "page": page,
            "limit": limit,
            "pages": (total + limit - 1) // limit,
            "debug_info": {
                "requested_user_id": user_id,
                "found_schedules": len(schedules),
                "total_count": total,
                "groups_count": len(grouped_schedules),
                "all_user_ids_in_db": unique_user_ids
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting user schedules: {str(e)}")
        print(f"❌ [ERROR] 일정 조회 실패: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedules: {str(e)}"
        )


@router.post("/")
async def create_schedule(
    schedule: Schedule,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new schedule"""
    try:
        # This would save schedule to database
        logger.info(f"Creating schedule for user: {current_user['user_id']}")
        
        return {
            "message": "Schedule created successfully",
            "schedule": schedule.dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    schedule: Schedule,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing schedule"""
    try:
        # This would update schedule in database
        logger.info(f"Updating schedule {schedule_id} for user: {current_user['user_id']}")
        
        return {
            "message": "Schedule updated successfully",
            "schedule": schedule.dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schedule: {str(e)}"
        )


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a schedule"""
    try:
        # This would delete schedule from database
        logger.info(f"Deleting schedule {schedule_id} for user: {current_user['user_id']}")
        
        return {"message": "Schedule deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete schedule: {str(e)}"
        )


@router.get("/{schedule_id}/download-ics")
async def download_schedule_ics(schedule_id: str):
    """Download ICS file for a specific schedule"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 일정 조회
        result = supabase.table("schedules")\
            .select("*")\
            .eq("id", schedule_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        schedule = result.data[0]
        
        # ICS 파일 경로가 있으면 다운로드 URL 반환
        if schedule.get("ics_file_path"):
            public_url = supabase.storage.from_("schedules").get_public_url(schedule["ics_file_path"])
            return {"download_url": public_url}
        
        # ICS 파일이 없으면 새로 생성
        ics_content = ics_service.generate_ics_content([schedule], schedule["title"])
        
        return {
            "ics_content": ics_content,
            "filename": f"schedule_{schedule_id}.ics"
        }
        
    except Exception as e:
        logger.error(f"Error downloading schedule ICS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download ICS: {str(e)}"
        )


@router.post("/{schedule_id}/send-email")
async def send_schedule_email(
    schedule_id: str,
    email_data: Dict[str, Any]
):
    """Send schedule via email"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 일정 조회
        result = supabase.table("schedules")\
            .select("*")\
            .eq("id", schedule_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        schedule = result.data[0]
        
        # 이메일 발송 로직 (추후 이메일 서비스 연동)
        # 현재는 성공 응답만 반환
        
        return {
            "success": True,
            "message": f"일정 '{schedule['title']}'이(가) 이메일로 발송되었습니다.",
            "recipients": email_data.get("recipients", [])
        }
        
    except Exception as e:
        logger.error(f"Error sending schedule email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )


@router.post("/{schedule_id}/share")
async def share_schedule(
    schedule_id: str,
    share_data: Dict[str, Any]
):
    """Share schedule with others"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 일정 조회
        result = supabase.table("schedules")\
            .select("*")\
            .eq("id", schedule_id)\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Schedule not found")
        
        schedule = result.data[0]
        
        # 공유 링크 생성 (현재는 기본적인 공유 URL)
        share_url = f"/schedules/shared/{schedule_id}"
        
        # 공유 정보 업데이트
        share_info = {
            "shared_at": "now()",
            "shared_with": share_data.get("shared_with", []),
            "share_type": share_data.get("share_type", "link")
        }
        
        supabase.table("schedules")\
            .update({"share": share_info})\
            .eq("id", schedule_id)\
            .execute()
        
        return {
            "success": True,
            "share_url": share_url,
            "message": "일정이 공유되었습니다."
        }
        
    except Exception as e:
        logger.error(f"Error sharing schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share schedule: {str(e)}"
        ) 