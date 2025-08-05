"""
MUFI 일정 공유 관리 라우터
일정 공유, 수락, 거절, 공유 목록 조회 등의 기능 제공
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, EmailStr
import uuid
from datetime import datetime
import json
import logging

from core.dependencies import get_current_user
from services.database_service import DatabaseService
from services.notification_service import NotificationService

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Pydantic 모델들
class ShareScheduleRequest(BaseModel):
    schedule_id: str
    share_with_emails: List[EmailStr]
    message: Optional[str] = None

class ShareActionRequest(BaseModel):
    schedule_id: str
    action: str  # "accept" or "reject"

class SharedUserInfo(BaseModel):
    email: str
    user_id: str
    shared_at: datetime
    status: str  # "invited", "accepted", "rejected"
    message: Optional[str] = None

# 서비스 인스턴스
database_service = DatabaseService()
notification_service = NotificationService()

@router.get("/users")
async def get_shareable_users(
    current_user_id: str
):
    """공유 가능한 사용자 목록 조회 (자신 제외)"""
    try:
        logger.info(f"👥 공유 가능한 사용자 목록 조회 - current_user_id: {current_user_id}")
        
        # 자신을 제외한 모든 활성 사용자 조회
        from supabase import create_client
        from config.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        result = supabase.table("users").select(
            "id, email, name, picture"
        ).eq("is_active", True).neq("id", current_user_id).order("name").execute()
        
        users = result.data if result.data else []
        logger.info(f"✅ 조회된 사용자 수: {len(users)}")
        
        return {"users": users}
        
    except Exception as e:
        logger.error(f"Error getting shareable users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"사용자 목록 조회 실패: {str(e)}"
        )

@router.post("/share")
async def share_schedule(
    request: ShareScheduleRequest,
    current_user_id: str = "5e462ae0-b67a-4f47-942f-81485142bb51"  # 테스트용 고정 ID
):
    """일정을 다른 사용자들과 공유"""
    try:
        logger.info(f"🔄 일정 공유 요청: schedule_id={request.schedule_id}, emails={request.share_with_emails}")
        
        # 1. 스케줄 존재 및 권한 확인
        schedule_data = database_service.get_schedule_by_id(request.schedule_id)
        logger.info(f"🔍 [DEBUG] schedule_data type: {type(schedule_data)}")
        logger.info(f"🔍 [DEBUG] schedule_data content: {schedule_data}")
        
        if not schedule_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="일정을 찾을 수 없습니다."
            )
        
        # 일정 소유자인지 확인 (스테이징 환경에서는 체크 생략)
        # if schedule_data.get('user_id') != current_user_id:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="이 일정을 공유할 권한이 없습니다."
        #     )
        
        # 2. 공유할 사용자들의 정보 조회
        shared_users = []
        for email in request.share_with_emails:
            # 이메일로 사용자 정보 조회
            user_info = database_service.get_user_by_email(email)
            logger.info(f"🔍 [DEBUG] user_info type: {type(user_info)}")
            logger.info(f"🔍 [DEBUG] user_info content: {user_info}")
            
            if not user_info:
                logger.warning(f"⚠️ 사용자를 찾을 수 없습니다: {email}")
                continue
                
            shared_user = {
                "email": email,
                "user_id": user_info['id'],
                "shared_at": datetime.now().isoformat(),
                "status": "invited",
                "message": request.message
            }
            shared_users.append(shared_user)
        
        if not shared_users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="공유할 수 있는 사용자가 없습니다."
            )
        
        # 3. 기존 share 데이터 가져오기 및 새로운 형식으로 변환
        # 3. 공유된 사용자들에게 바로 알림 전송 (원본 일정은 수정하지 않음)
        existing_emails = set()  # 중복 체크용 (단순화)
        
        # 6. 공유된 사용자들에게 알림 전송
        try:
            for shared_user in shared_users:
                if shared_user['email'] not in existing_emails:
                    logger.info(f"📤 알림 전송 중: {shared_user['email']}")
                    # 간단한 알림 시스템 (notifications 테이블에 직접 삽입)
                    from supabase import create_client
                    from config.config import settings
                    
                    supabase = create_client(settings.supabase_url, settings.supabase_service_key)
                    
                    notification_data = {
                        "user_id": shared_user['user_id'],
                        "type": "schedule_invite",
                        "title": f"일정 공유 초대",
                        "message": f"'{schedule_data.get('title', '제목 없음')}' 일정이 공유되었습니다.",
                        "data": {
                            "schedule_id": request.schedule_id,
                            "schedule_title": schedule_data.get('title', '제목 없음'),
                            "shared_by": current_user_id,
                            "action_type": "share_invite"
                        },
                        "is_read": False
                    }
                    
                    result = supabase.table("notifications").insert(notification_data).execute()
                    if result.data:
                        logger.info(f"✅ 알림 전송 성공: {shared_user['email']}")
                    else:
                        logger.error(f"❌ 알림 전송 실패: {shared_user['email']}")
        except Exception as e:
            logger.error(f"❌ 알림 전송 중 오류: {str(e)}")
        
        logger.info(f"✅ 일정 공유 완료: {len(shared_users)}명에게 공유")
        
        return {
            "message": "일정이 성공적으로 공유되었습니다.",
            "shared_count": len(shared_users),
            "shared_users": shared_users
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 일정 공유 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"일정 공유 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/respond")
async def respond_to_share(
    request: ShareActionRequest,
    current_user_id: str = Query(..., description="현재 사용자 ID")
):
    """공유된 일정에 대해 수락 또는 거절"""
    try:
        logger.info(f"🔄 공유 일정 응답: schedule_id={request.schedule_id}, action={request.action}")
        
        if request.action not in ["accept", "reject"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="올바르지 않은 액션입니다. 'accept' 또는 'reject'만 가능합니다."
            )
        
        # 1. 스케줄 조회
        schedule_data = database_service.get_schedule_by_id(request.schedule_id)
        if not schedule_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="일정을 찾을 수 없습니다."
            )
        
        # 2. 해당 일정이 존재하는지만 확인 (복잡한 권한 체크 제거)
        logger.info(f"✅ 일정 확인 완료: {schedule_data.get('title', '제목 없음')}")
        
        # 3. 수락일 때만 일정 복사하여 새로 생성
        if request.action == "accept":
            try:
                from supabase import create_client
                from config.config import settings
                import uuid
                
                supabase = create_client(settings.supabase_url, settings.supabase_service_key)
                
                # 중복 생성 방지: 이미 공유받은 일정이 있는지 확인
                existing_check = supabase.table("schedules").select("id").eq(
                    "user_id", current_user_id
                ).eq(
                    "share", True
                ).eq(
                    "analysis_id", schedule_data.get('analysis_id')
                ).eq(
                    "title", schedule_data.get('title')
                ).execute()
                
                if existing_check.data:
                    logger.info(f"⚠️ 이미 공유받은 일정이 존재함: {existing_check.data[0]['id']}")
                    # 기존 일정 ID 반환
                    existing_schedule_id = existing_check.data[0]['id']
                else:
                    # 새로운 일정 ID 생성
                    new_schedule_id = str(uuid.uuid4())
                    
                    # 원본 일정 데이터 복사
                    new_schedule = {
                        "id": new_schedule_id,
                        "user_id": current_user_id,  # 받은 사람의 ID로 변경
                        "analysis_id": schedule_data.get('analysis_id'),
                        "participants": schedule_data.get('participants'),
                        "title": schedule_data.get('title'),
                        "description": schedule_data.get('description'),
                        "location": schedule_data.get('location'),
                        "start_datetime": schedule_data.get('start_datetime'),
                        "end_datetime": schedule_data.get('end_datetime'),
                        "type": schedule_data.get('type'),
                        "ics_file_path": schedule_data.get('ics_file_path'),
                        "share": True,  # 공유받은 일정임을 표시
                        "file_id": schedule_data.get('file_id')
                    }
                    
                    # 새로운 일정 저장
                    result = supabase.table("schedules").insert(new_schedule).execute()
                    
                    if result.data:
                        logger.info(f"✅ 공유받은 일정을 새로운 일정으로 생성 완료: {new_schedule_id}")
                        
                        # 공유받은 사용자용 ICS 파일 생성 및 저장
                        try:
                            from services.ics_service import ICSService
                            
                            ics_service = ICSService()
                            
                            # 새로 생성된 일정 데이터로 ICS 생성
                            ics_result = await ics_service.generate_and_save_ics(
                                schedules=[new_schedule],
                                user_id=current_user_id,
                                title=f"공유받은 일정 - {new_schedule.get('title', '제목 없음')}",
                                analysis_id=new_schedule.get('analysis_id')
                            )
                            
                            if ics_result.get('success'):
                                # 생성된 ICS 파일 URL을 새 일정에 업데이트
                                supabase.table("schedules").update({
                                    "ics_file_path": ics_result.get('public_url')
                                }).eq("id", new_schedule_id).execute()
                                
                                logger.info(f"✅ 공유받은 일정용 ICS 파일 생성 완료: {ics_result.get('filename')}")
                            else:
                                logger.warning(f"⚠️ ICS 파일 생성 실패: {ics_result.get('error')}")
                                
                        except Exception as ics_error:
                            logger.error(f"❌ ICS 파일 생성 중 오류: {str(ics_error)}")
                            # ICS 생성 실패해도 일정 자체는 생성되었으므로 계속 진행
                    else:
                        raise Exception("일정 생성 실패")
                    
            except Exception as e:
                logger.error(f"❌ 공유받은 일정 생성 중 오류: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="공유받은 일정 생성에 실패했습니다."
                )
        else:
            # 거절일 때는 아무것도 저장하지 않음
            logger.info(f"⚠️ 거절된 일정은 저장하지 않음")
        
        # 5. 수락/거절한 알림 삭제
        try:
            from supabase import create_client
            from config.config import settings
            
            supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            
            # 해당 schedule_id와 관련된 알림 삭제
            delete_result = supabase.table("notifications").delete().eq(
                "user_id", current_user_id
            ).eq(
                "type", "schedule_invite"
            ).contains(
                "data", {"schedule_id": request.schedule_id}
            ).execute()
            
            if delete_result.data:
                logger.info(f"✅ 관련 알림 삭제 완료: {len(delete_result.data)}개")
            else:
                logger.warning(f"⚠️ 삭제할 알림을 찾지 못함")
                
        except Exception as e:
            logger.error(f"❌ 알림 삭제 중 오류: {str(e)}")
        
        # 6. 일정 소유자에게 알림 전송 (현재는 비활성화)
        # await notification_service.create_share_response_notification(
        #     to_user_id=schedule_data['user_id'],
        #     from_user_id=current_user_id,
        #     from_user_name="테스트 사용자",
        #     schedule_id=request.schedule_id,
        #     schedule_title=schedule_data['title'],
        #     action=request.action
        # )
        
        action_text = "수락" if request.action == "accept" else "거절"
        logger.info(f"✅ 공유 일정 {action_text} 완료")
        
        return {
            "message": f"일정을 {action_text}했습니다.",
            "action": request.action,
            "schedule_id": request.schedule_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 공유 응답 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"응답 처리 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/my-shared-schedules")
async def get_my_shared_schedules(
    user_id: str = Query(..., description="조회할 사용자 ID")
):
    """내가 공유받은 일정들 조회"""
    try:
        logger.info(f"📋 공유받은 일정 조회: user_id={user_id}")
        
        # 내가 공유받은 일정들 조회 (share = true인 일정들)
        try:
            from supabase import create_client
            from config.config import settings
            
            supabase = create_client(settings.supabase_url, settings.supabase_service_key)
            
            logger.info(f"🔍 [DEBUG] 공유 일정 조회 쿼리: user_id={user_id}, share=true")
            
            result = supabase.table("schedules").select("*").eq(
                "user_id", user_id
            ).eq(
                "share", True
            ).execute()
            
            shared_schedules = result.data
            logger.info(f"📋 공유받은 일정 조회 완료: {len(shared_schedules)}개")
            
            # 디버그: 조회된 일정들의 상세 정보 로깅
            for schedule in shared_schedules:
                logger.info(f"🔍 [DEBUG] 공유받은 일정: id={schedule.get('id')}, title={schedule.get('title')}, share={schedule.get('share')}")
            
        except Exception as e:
            logger.error(f"❌ 공유받은 일정 조회 중 오류: {str(e)}")
            shared_schedules = []
        
        # 응답 형태로 변환 (share = true인 일정들을 그대로 반환)
        result = []
        for schedule in shared_schedules:
            result.append({
                "id": schedule['id'],
                "title": schedule.get('title', '제목 없음'),
                "description": schedule.get('description', ''),
                "location": schedule.get('location', ''),
                "start_datetime": schedule.get('start_datetime'),
                "end_datetime": schedule.get('end_datetime'),
                "type": schedule.get('type', 'personal'),
                "participants": schedule.get('participants', []),
                "created_at": schedule.get('created_at'),
                "is_shared": True  # 공유받은 일정임을 표시
            })
        
        logger.info(f"✅ 공유받은 일정 조회 완료: {len(result)}개")
        
        return {
            "schedules": result,
            "count": len(result)
        }
        
    except Exception as e:
        logger.error(f"❌ 공유받은 일정 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공유받은 일정 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/schedule/{schedule_id}/shares")
async def get_schedule_shares(
    schedule_id: str,
    current_user_id: str = "5e462ae0-b67a-4f47-942f-81485142bb51"  # 테스트용 고정 ID
):
    """특정 일정의 공유 현황 조회"""
    try:
        logger.info(f"📋 일정 공유 현황 조회: schedule_id={schedule_id}")
        
        # 스케줄 조회 및 권한 확인
        schedule_data = database_service.get_schedule_by_id(schedule_id)
        if not schedule_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="일정을 찾을 수 없습니다."
            )
        
        # 일정 소유자이거나 공유받은 사용자인지 확인 (스테이징에서는 체크 생략)
        has_access = True  # 스테이징 환경에서는 모든 접근 허용
        # if schedule_data.get('user_id') == current_user_id:
        #     has_access = True
        # else:
        #     share_data = schedule_data.get('share') or []
        #     for shared_user in share_data:
        #         if shared_user.get('user_id') == current_user_id:
        #             has_access = True
        #             break
        
        # if not has_access:
        #     raise HTTPException(
        #         status_code=status.HTTP_403_FORBIDDEN,
        #         detail="이 일정에 대한 권한이 없습니다."
        #     )
        
        share_data = schedule_data.get('share') or []
        
        logger.info(f"✅ 일정 공유 현황 조회 완료: {len(share_data)}명 공유")
        
        return {
            "schedule_id": schedule_id,
            "title": schedule_data['title'],
            "owner_id": schedule_data['user_id'],
            "shares": share_data,
            "share_count": len(share_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ 일정 공유 현황 조회 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"공유 현황 조회 중 오류가 발생했습니다: {str(e)}"
        )