"""
Users API Router
사용자 관리 기능을 제공합니다.
"""
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from supabase import create_client
from config.config import settings
from core.dependencies import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/users", tags=["Users"])

# Pydantic 모델들
class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    picture: Optional[str] = None
    google_id: Optional[str] = None
    locale: Optional[str] = "ko"
    is_active: Optional[bool] = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login_at: Optional[str] = None

class UsersListResponse(BaseModel):
    users: List[UserResponse]
    total_count: int
    page: int
    limit: int

@router.get("/", response_model=UsersListResponse)
async def get_users_list(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    모든 사용자 목록 조회
    """
    try:
        print(f"👥 [INFO] 사용자 목록 조회 요청")
        print(f"👥 페이지: {page}, 제한: {limit}, 검색: {search}")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 페이지네이션 계산
        offset = (page - 1) * limit
        
        # users 테이블에서 사용자 목록 조회
        query = supabase.table("users").select("*")
        
        # 검색 조건 추가
        if search:
            search_term = f"%{search}%"
            query = query.or_(f"name.ilike.{search_term},email.ilike.{search_term}")
        
        # 전체 개수 조회 (검색 조건 포함)
        count_query = supabase.table("users").select("id", count="exact")
        if search:
            search_term = f"%{search}%"
            count_query = count_query.or_(f"name.ilike.{search_term},email.ilike.{search_term}")
        
        count_result = count_query.execute()
        total_count = count_result.count if count_result.count else 0
        
        # 페이지네이션 적용하여 실제 데이터 조회
        query = query.order("created_at", desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        users = result.data if result.data else []
        
        print(f"👥 조회된 사용자 수: {len(users)}")
        print(f"👥 전체 사용자 수: {total_count}")
        
        # 응답 데이터 변환
        user_responses = []
        for user in users:
            user_responses.append(UserResponse(
                id=str(user.get('id', '')),
                email=user.get('email', ''),
                name=user.get('name', ''),
                picture=user.get('picture'),
                google_id=user.get('google_id'),
                locale=user.get('locale', 'ko'),
                is_active=user.get('is_active', True),
                created_at=user.get('created_at'),
                updated_at=user.get('updated_at'),
                last_login_at=user.get('last_login_at')
            ))
        
        return UsersListResponse(
            users=user_responses,
            total_count=total_count,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        print(f"❌ [ERROR] 사용자 목록 조회 실패: {str(e)}")
        logger.error(f"Error fetching users list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{user_id}")
async def get_user_by_id(
    user_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    특정 사용자 상세 정보 조회
    """
    try:
        print(f"👤 [INFO] 사용자 상세 조회: {user_id}")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # users 테이블에서 특정 사용자 조회
        result = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다")
        
        user = result.data[0]
        print(f"✅ [DEBUG] 사용자 조회 성공: {user['email']}")
        
        # 사용자의 일정 수 조회
        schedules_result = supabase.table("schedules")\
            .select("id", count="exact")\
            .eq("user_id", user_id)\
            .execute()
        
        schedules_count = schedules_result.count if schedules_result.count else 0
        
        # 사용자 상세 정보 반환
        user_detail = {
            "id": str(user.get('id', '')),
            "email": user.get('email', ''),
            "name": user.get('name', ''),
            "picture": user.get('picture'),
            "google_id": user.get('google_id'),
            "locale": user.get('locale', 'ko'),
            "is_active": user.get('is_active', True),
            "created_at": user.get('created_at'),
            "updated_at": user.get('updated_at'),
            "last_login_at": user.get('last_login_at'),
            "schedules_count": schedules_count
        }
        
        return JSONResponse(content=user_detail)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ERROR] 사용자 상세 조회 실패: {str(e)}")
        logger.error(f"Error fetching user details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사용자 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/stats/summary")
async def get_users_stats(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    사용자 통계 정보 조회
    """
    try:
        print(f"📊 [INFO] 사용자 통계 조회")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # users 테이블에서 전체 사용자 수 조회
        total_users_result = supabase.table("users").select("id", count="exact").execute()
        total_users = total_users_result.count if total_users_result.count else 0
        
        # 활성 사용자 수 조회
        active_users_result = supabase.table("users").select("id", count="exact").eq("is_active", True).execute()
        active_users = active_users_result.count if active_users_result.count else 0
        
        # 전체 일정 수 조회
        schedules_result = supabase.table("schedules")\
            .select("id", count="exact")\
            .execute()
        total_schedules = schedules_result.count if schedules_result.count else 0
        
        stats = {
            "total_users": total_users,
            "active_users": active_users,
            "inactive_users": total_users - active_users,
            "total_schedules": total_schedules,
            "avg_schedules_per_user": round(total_schedules / total_users, 1) if total_users > 0 else 0
        }
        
        print(f"📊 통계 정보: {stats}")
        
        return JSONResponse(content=stats)
        
    except Exception as e:
        print(f"❌ [ERROR] 사용자 통계 조회 실패: {str(e)}")
        logger.error(f"Error fetching user stats: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"사용자 통계 조회 중 오류가 발생했습니다: {str(e)}"
        )