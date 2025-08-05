"""
MUFI 알림 관리 라우터
알림 조회, 읽음 처리, 삭제 등의 기능 제공
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import logging

from core.dependencies import get_current_user
from services.notification_service import NotificationService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic 모델들
class MarkReadRequest(BaseModel):
    notification_id: Optional[str] = None  # None이면 모든 알림 읽음 처리

# 서비스 인스턴스
notification_service = NotificationService()

@router.get("/")
async def get_notifications(
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """사용자의 알림 목록 조회"""
    try:
        logger.info(f"📋 알림 목록 조회: user_id={current_user['user_id']}, limit={limit}")
        
        notifications = notification_service.get_user_notifications(
            current_user['user_id'], 
            limit
        )
        
        unread_count = notification_service.get_unread_count(current_user['user_id'])
        
        logger.info(f"✅ 알림 목록 조회 완료: {len(notifications)}개, 읽지 않음: {unread_count}개")
        
        return {
            "notifications": notifications,
            "total_count": len(notifications),
            "unread_count": unread_count
        }
        
    except Exception as e:
        logger.error(f"❌ 알림 목록 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/unread-count")
async def get_unread_count(
    current_user: Dict = Depends(get_current_user)
):
    """읽지 않은 알림 개수 조회"""
    try:
        logger.info(f"📊 읽지 않은 알림 개수 조회: user_id={current_user['user_id']}")
        
        unread_count = notification_service.get_unread_count(current_user['user_id'])
        
        logger.info(f"✅ 읽지 않은 알림 개수: {unread_count}개")
        
        return {
            "unread_count": unread_count
        }
        
    except Exception as e:
        logger.error(f"❌ 읽지 않은 알림 개수 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"읽지 않은 알림 개수 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/mark-read")
async def mark_notifications_read(
    request: MarkReadRequest,
    current_user: Dict = Depends(get_current_user)
):
    """알림을 읽음으로 표시"""
    try:
        if request.notification_id:
            logger.info(f"📖 특정 알림 읽음 처리: notification_id={request.notification_id}")
            
            success = notification_service.mark_notification_as_read(request.notification_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="알림을 찾을 수 없습니다."
                )
            
            logger.info(f"✅ 알림 읽음 처리 완료: {request.notification_id}")
            return {"message": "알림이 읽음으로 표시되었습니다."}
            
        else:
            logger.info(f"📖 모든 알림 읽음 처리: user_id={current_user['user_id']}")
            
            success = notification_service.mark_all_notifications_as_read(current_user['user_id'])
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="알림 읽음 처리에 실패했습니다."
                )
            
            logger.info(f"✅ 모든 알림 읽음 처리 완료")
            return {"message": "모든 알림이 읽음으로 표시되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 알림 읽음 처리 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 읽음 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """알림 삭제"""
    try:
        logger.info(f"🗑️ 알림 삭제: notification_id={notification_id}")
        
        # 알림이 현재 사용자의 것인지 먼저 확인
        notifications = notification_service.get_user_notifications(current_user['user_id'])
        notification_exists = any(n['id'] == notification_id for n in notifications)
        
        if not notification_exists:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="알림을 찾을 수 없거나 권한이 없습니다."
            )
        
        success = notification_service.delete_notification(notification_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="알림 삭제에 실패했습니다."
            )
        
        logger.info(f"✅ 알림 삭제 완료: {notification_id}")
        
        return {"message": "알림이 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 알림 삭제 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"알림 삭제 중 오류가 발생했습니다: {str(e)}"
        )