from fastapi import APIRouter, HTTPException, Depends, Request, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
from supabase import create_client, Client
from ..auth.auth_service import verify_token
from datetime import datetime, timedelta
import uuid

# Supabase 클라이언트 설정
supabase_url = os.getenv("SUPABASE_URL", "https://znvwtoozdcnaqpuzbnhu.supabase.co")
supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd0b296ZGNuYXFwdXpibmh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ2Mjk0MjQsImV4cCI6MjA3MDIwNTQyNH0.UdqqsxqdUoPtPNyQSRfEjKL6cg90dUDNuzsancxIYR0")
supabase: Client = create_client(supabase_url, supabase_key)

router = APIRouter(prefix="/api/groups", tags=["그룹 관리"])

# JWT 토큰 검증
security = HTTPBearer()

# 요청 모델
class CreateGroupRequest(BaseModel):
    group_name: str
    description: Optional[str] = None

class JoinGroupRequest(BaseModel):
    token: str

class ShareScheduleRequest(BaseModel):
    schedule_id: str
    group_ids: List[int]

# 사용자 ID 가져오기 헬퍼
def get_user_id_from_token(credentials: HTTPAuthorizationCredentials) -> int:
    """토큰에서 사용자 ID를 가져옵니다."""
    user_data = verify_token(credentials.credentials)
    email = user_data.get('email', user_data.get('sub', ''))
    
    # users 테이블에서 사용자 ID 찾기
    user_result = supabase.table('users').select('id').eq('email', email).execute()
    if not user_result.data:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
    
    return user_result.data[0]['id']

@router.post("/")
async def create_group(
    request: CreateGroupRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """그룹을 생성합니다."""
    try:
        user_id = get_user_id_from_token(credentials)
        
        # 그룹 생성
        group_result = supabase.table('group').insert({
            'admin_id': user_id,
            'group_name': request.group_name,
            'description': request.description
        }).execute()
        
        if not group_result.data:
            raise HTTPException(status_code=500, detail="그룹 생성에 실패했습니다.")
        
        group_id = group_result.data[0]['id']
        
        # 그룹 소유자로 멤버 추가
        supabase.table('group_members').insert({
            'group_id': group_id,
            'users_id': user_id,
            'role': 'owner'
        }).execute()
        
        return {
            "success": True,
            "message": "그룹이 성공적으로 생성되었습니다.",
            "data": {
                "group_id": group_id,
                "group_name": request.group_name
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 그룹 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"그룹 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/")
async def get_my_groups(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """사용자가 속한 그룹 목록을 조회합니다."""
    try:
        user_id = get_user_id_from_token(credentials)
        
        # 사용자가 속한 그룹 멤버십 조회
        members_result = supabase.table('group_members').select(
            'group_id, role, join_at'
        ).eq('users_id', user_id).execute()
        
        groups = []
        for member in members_result.data:
            group_id = member['group_id']
            
            # 그룹 정보 조회
            group_result = supabase.table('group').select('*').eq('id', group_id).execute()
            if not group_result.data:
                continue
                
            group_info = group_result.data[0]
            
            # 그룹 멤버 수 조회
            member_count_result = supabase.table('group_members').select('id').eq('group_id', group_id).execute()
            member_count = len(member_count_result.data) if member_count_result.data else 0
            
            # 그룹 일정 수 조회
            schedule_count_result = supabase.table('group_schedules').select('id').eq('group_id', group_id).execute()
            schedule_count = len(schedule_count_result.data) if schedule_count_result.data else 0
            
            # 그룹 멤버 목록 조회 (최대 5명)
            members_list_result = supabase.table('group_members').select(
                'users_id, role'
            ).eq('group_id', group_id).limit(5).execute()
            
            members = []
            for m in members_list_result.data:
                user_id_member = m['users_id']
                # 사용자 정보 조회
                user_result = supabase.table('users').select('id, name, email, picture').eq('id', user_id_member).execute()
                if user_result.data:
                    user_info = user_result.data[0]
                    members.append({
                        'id': user_info.get('id'),
                        'name': user_info.get('name'),
                        'email': user_info.get('email'),
                        'picture': user_info.get('picture')
                    })
            
            groups.append({
                'id': group_info['id'],
                'group_name': group_info['group_name'],
                'description': group_info.get('description'),
                'admin_id': group_info['admin_id'],
                'role': member['role'],
                'member_count': member_count,
                'schedule_count': schedule_count,
                'members': members,
                'created_at': group_info.get('created_at')
            })
        
        return {
            "success": True,
            "data": {
                "groups": groups
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 그룹 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"그룹 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/{group_id}/invite")
async def create_invite_link(
    group_id: int,
    http_request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """그룹 초대 링크를 생성합니다."""
    try:
        user_id = get_user_id_from_token(credentials)
        
        # 그룹 존재 확인 및 권한 확인
        group_result = supabase.table('group').select('*').eq('id', group_id).execute()
        if not group_result.data:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        
        # 사용자가 그룹 멤버인지 확인
        member_result = supabase.table('group_members').select('role').eq('group_id', group_id).eq('users_id', user_id).execute()
        if not member_result.data:
            raise HTTPException(status_code=403, detail="그룹 멤버만 초대 링크를 생성할 수 있습니다.")
        
        member_role = member_result.data[0]['role']
        if member_role not in ['owner', 'admin']:
            raise HTTPException(status_code=403, detail="그룹 관리자만 초대 링크를 생성할 수 있습니다.")
        
        # 만료 기간 설정 (기본값 7일)
        expires_in_days = 7
        try:
            request_body = await http_request.json()
            print(f"📥 요청 본문: {request_body}")
            if request_body and 'expires_in_days' in request_body:
                expires_in_days = int(request_body['expires_in_days'])
                print(f"📅 선택한 만료 기간: {expires_in_days}일")
                # 유효한 값인지 확인 (1~365일)
                if expires_in_days < 1 or expires_in_days > 365:
                    print(f"⚠️ 유효하지 않은 만료 기간: {expires_in_days}일, 기본값 7일 사용")
                    expires_in_days = 7
        except Exception as e:
            print(f"⚠️ 만료 기간 파싱 오류: {e}, 기본값 7일 사용")
            pass  # 요청 본문이 없거나 파싱 실패 시 기본값 사용
        
        print(f"✅ 최종 만료 기간: {expires_in_days}일")
        
        # 초대 토큰 생성 (UUID)
        invite_token = str(uuid.uuid4())
        
        # 만료 시간 설정
        expired_at = datetime.now() + timedelta(days=expires_in_days)
        
        # 초대 URL 생성
        base_url = os.getenv("BASE_URL", "http://localhost:8000")
        invite_url = f"{base_url}/invite/{invite_token}"
        
        # 초대 링크 생성 (URL 포함)
        invite_result = supabase.table('invite').insert({
            'user_id': user_id,
            'group_id': group_id,
            'token': invite_token,
            'url': invite_url,
            'invited_status': 'pending',
            'expired_at': expired_at.isoformat()
        }).execute()
        
        if not invite_result.data:
            raise HTTPException(status_code=500, detail="초대 링크 생성에 실패했습니다.")
        
        return {
            "success": True,
            "message": "초대 링크가 생성되었습니다.",
            "data": {
                "invite_token": invite_token,
                "invite_url": invite_url,
                "expired_at": expired_at.isoformat()
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 초대 링크 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"초대 링크 생성 중 오류가 발생했습니다: {str(e)}")

@router.get("/invite/{token}/preview")
async def get_invite_preview(token: str):
    """초대 토큰의 미리보기 정보를 조회합니다 (인증 불필요)."""
    try:
        # 초대 정보 조회
        invite_result = supabase.table('invite').select(
            'id, group_id, token, invited_status, expired_at, created_at'
        ).eq('token', token).execute()
        
        if not invite_result.data:
            raise HTTPException(status_code=404, detail="유효하지 않은 초대 링크입니다.")
        
        invite_data = invite_result.data[0]
        group_id = invite_data['group_id']
        
        # 만료 확인
        if invite_data.get('expired_at'):
            expired_at = datetime.fromisoformat(invite_data['expired_at'].replace('Z', '+00:00'))
            if datetime.now(expired_at.tzinfo) > expired_at:
                raise HTTPException(status_code=410, detail="만료된 초대 링크입니다.")
        
        # 상태 확인
        if invite_data['invited_status'] != 'pending':
            status_messages = {
                'accepted': '이미 수락된 초대 링크입니다.',
                'declined': '거절된 초대 링크입니다.',
                'expired': '만료된 초대 링크입니다.',
                'cancelled': '취소된 초대 링크입니다.'
            }
            raise HTTPException(status_code=410, detail=status_messages.get(invite_data['invited_status'], '유효하지 않은 초대 링크입니다.'))
        
        # 그룹 정보 조회
        group_result = supabase.table('group').select('*').eq('id', group_id).execute()
        if not group_result.data:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        
        group_info = group_result.data[0]
        
        # 그룹 멤버 목록 조회
        members_list_result = supabase.table('group_members').select(
            'users_id, role'
        ).eq('group_id', group_id).execute()
        
        members = []
        for member in members_list_result.data:
            user_id_member = member['users_id']
            # 사용자 정보 조회
            user_result = supabase.table('users').select('id, name, email, picture').eq('id', user_id_member).execute()
            if user_result.data:
                user_info = user_result.data[0]
                members.append({
                    'id': user_info.get('id'),
                    'name': user_info.get('name'),
                    'email': user_info.get('email'),
                    'picture': user_info.get('picture'),
                    'role': member.get('role')
                })
        
        # 그룹 소유자 정보 조회
        admin_result = supabase.table('users').select('id, name, email, picture').eq('id', group_info['admin_id']).execute()
        admin_info = admin_result.data[0] if admin_result.data else None
        
        return {
            "success": True,
            "data": {
                "group": {
                    "id": group_info['id'],
                    "group_name": group_info['group_name'],
                    "description": group_info.get('description'),
                    "admin": admin_info,
                    "member_count": len(members),
                    "created_at": group_info.get('created_at')
                },
                "members": members,
                "invite": {
                    "token": token,
                    "expired_at": invite_data.get('expired_at')
                }
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 초대 미리보기 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"초대 미리보기 조회 중 오류가 발생했습니다: {str(e)}")

@router.post("/invite/{token}/join")
async def join_group(
    token: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """초대 토큰을 사용하여 그룹에 참가합니다."""
    try:
        user_id = get_user_id_from_token(credentials)
        
        # 초대 정보 조회
        invite_result = supabase.table('invite').select(
            'id, group_id, token, invited_status, expired_at'
        ).eq('token', token).execute()
        
        if not invite_result.data:
            raise HTTPException(status_code=404, detail="유효하지 않은 초대 링크입니다.")
        
        invite_data = invite_result.data[0]
        group_id = invite_data['group_id']
        
        # 만료 확인
        if invite_data.get('expired_at'):
            expired_at = datetime.fromisoformat(invite_data['expired_at'].replace('Z', '+00:00'))
            if datetime.now(expired_at.tzinfo) > expired_at:
                raise HTTPException(status_code=410, detail="만료된 초대 링크입니다.")
        
        # 상태 확인
        if invite_data['invited_status'] != 'pending':
            status_messages = {
                'accepted': '이미 수락된 초대 링크입니다.',
                'declined': '거절된 초대 링크입니다.',
                'expired': '만료된 초대 링크입니다.',
                'cancelled': '취소된 초대 링크입니다.'
            }
            raise HTTPException(status_code=410, detail=status_messages.get(invite_data['invited_status'], '유효하지 않은 초대 링크입니다.'))
        
        # 이미 그룹 멤버인지 확인
        existing_member = supabase.table('group_members').select('id').eq('group_id', group_id).eq('users_id', user_id).execute()
        if existing_member.data:
            raise HTTPException(status_code=400, detail="이미 그룹 멤버입니다.")
        
        # 그룹 멤버로 추가
        member_result = supabase.table('group_members').insert({
            'group_id': group_id,
            'users_id': user_id,
            'role': 'member'
        }).execute()
        
        if not member_result.data:
            raise HTTPException(status_code=500, detail="그룹 참가에 실패했습니다.")
        
        # 초대 상태 업데이트
        supabase.table('invite').update({
            'invited_status': 'accepted',
            'invited_user_id': user_id
        }).eq('id', invite_data['id']).execute()
        
        # 그룹 정보 조회
        group_result = supabase.table('group').select('*').eq('id', group_id).execute()
        group_info = group_result.data[0] if group_result.data else None
        
        return {
            "success": True,
            "message": "그룹에 성공적으로 참가했습니다.",
            "data": {
                "group_id": group_id,
                "group_name": group_info['group_name'] if group_info else None
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 그룹 참가 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"그룹 참가 중 오류가 발생했습니다: {str(e)}")

@router.post("/schedules/share")
async def share_schedule_to_groups(
    request: ShareScheduleRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """일정을 여러 그룹에 공유합니다."""
    print(f"📤 일정 공유 요청 수신: schedule_id={request.schedule_id}, group_ids={request.group_ids}")
    print(f"📤 요청 경로: /api/groups/schedules/share")
    try:
        user_id = get_user_id_from_token(credentials)
        
        # 일정 존재 확인 및 소유자 확인
        schedule_result = supabase.table('schedules').select('*').eq('id', request.schedule_id).execute()
        if not schedule_result.data:
            raise HTTPException(status_code=404, detail="일정을 찾을 수 없습니다.")
        
        schedule = schedule_result.data[0]
        if schedule['user_id'] != user_id:
            raise HTTPException(status_code=403, detail="본인의 일정만 공유할 수 있습니다.")
        
        shared_groups = []
        already_shared_groups = []
        failed_groups = []
        
        # 각 그룹에 일정 공유
        for group_id in request.group_ids:
            try:
                # 그룹 존재 확인
                group_result = supabase.table('group').select('*').eq('id', group_id).execute()
                if not group_result.data:
                    failed_groups.append({'group_id': group_id, 'reason': '그룹을 찾을 수 없습니다.'})
                    continue
                
                # 사용자가 그룹 멤버인지 확인
                member_result = supabase.table('group_members').select('id').eq('group_id', group_id).eq('users_id', user_id).execute()
                if not member_result.data:
                    failed_groups.append({'group_id': group_id, 'reason': '그룹 멤버가 아닙니다.'})
                    continue
                
                # 이미 공유된 일정인지 확인
                existing_result = supabase.table('group_schedules').select('id').eq('group_id', group_id).eq('schedules_id', request.schedule_id).execute()
                print(f"🔍 그룹 {group_id}의 기존 공유 확인: {existing_result.data}")
                if existing_result.data:
                    print(f"✅ 그룹 {group_id}는 이미 공유된 그룹으로 추가")
                    already_shared_groups.append(group_id)
                    continue
                
                # 그룹에 일정 공유
                share_result = supabase.table('group_schedules').insert({
                    'group_id': group_id,
                    'schedules_id': request.schedule_id,
                    'shared_by': user_id
                }).execute()
                
                if share_result.data:
                    shared_groups.append(group_id)
                else:
                    failed_groups.append({'group_id': group_id, 'reason': '공유 실패'})
                    
            except Exception as e:
                failed_groups.append({'group_id': group_id, 'reason': str(e)})
        
        print(f"📊 공유 결과 요약:")
        print(f"  - 새로 공유된 그룹: {len(shared_groups)}개 - {shared_groups}")
        print(f"  - 이미 공유된 그룹: {len(already_shared_groups)}개 - {already_shared_groups}")
        print(f"  - 실패한 그룹: {len(failed_groups)}개 - {failed_groups}")
        
        response_data = {
            "success": True,
            "message": f"{len(shared_groups)}개 그룹에 일정이 공유되었습니다.",
            "data": {
                "shared_groups": shared_groups,
                "already_shared_groups": already_shared_groups,
                "failed_groups": failed_groups
            }
        }
        
        print(f"📤 응답 데이터: {response_data}")
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 일정 공유 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"일정 공유 중 오류가 발생했습니다: {str(e)}")

@router.get("/{group_id}/schedules")
async def get_group_schedules(
    group_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """그룹에 공유된 일정 목록을 조회합니다."""
    try:
        user_id = get_user_id_from_token(credentials)
        
        # 그룹 존재 확인
        group_result = supabase.table('group').select('*').eq('id', group_id).execute()
        if not group_result.data:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        
        # 사용자가 그룹 멤버인지 확인
        member_result = supabase.table('group_members').select('id').eq('group_id', group_id).eq('users_id', user_id).execute()
        if not member_result.data:
            raise HTTPException(status_code=403, detail="그룹 멤버만 일정을 조회할 수 있습니다.")
        
        # 그룹에 공유된 일정 조회
        group_schedules_result = supabase.table('group_schedules').select(
            'id, schedules_id, shared_by, created_at'
        ).eq('group_id', group_id).execute()
        
        schedules = []
        for gs in group_schedules_result.data:
            schedule_id = gs.get('schedules_id')
            if not schedule_id:
                continue
                
            # 일정 정보 직접 조회
            schedule_result = supabase.table('schedules').select('*').eq('id', schedule_id).execute()
            if not schedule_result.data:
                continue
                
            schedule_info = schedule_result.data[0]
            
            # 공유한 사용자 정보 조회
            shared_by_user_result = supabase.table('users').select('id, name, email, picture').eq('id', gs['shared_by']).execute()
            shared_by_user = shared_by_user_result.data[0] if shared_by_user_result.data else None
            
            schedules.append({
                'id': schedule_info.get('id'),
                'title': schedule_info.get('title'),
                'description': schedule_info.get('description'),
                'location': schedule_info.get('location'),
                'start_datetime': schedule_info.get('start_datetime'),
                'end_datetime': schedule_info.get('end_datetime'),
                'participants': schedule_info.get('participants', []),
                'shared_by': shared_by_user,
                'shared_at': gs.get('created_at'),
                'group_schedule_id': gs.get('id'),  # 그룹 일정 삭제용 ID
                'group_id': group_id
            })
        
        return {
            "success": True,
            "data": {
                "schedules": schedules
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 그룹 일정 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"그룹 일정 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/schedules/{group_schedule_id}")
async def remove_schedule_from_group(
    group_schedule_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """그룹에서 일정을 제거합니다 (원본 일정은 유지)."""
    try:
        user_id = get_user_id_from_token(credentials)
        
        # 그룹 일정 정보 조회
        group_schedule_result = supabase.table('group_schedules').select(
            'id, group_id, schedules_id, shared_by'
        ).eq('id', group_schedule_id).execute()
        
        if not group_schedule_result.data:
            raise HTTPException(status_code=404, detail="공유 일정을 찾을 수 없습니다.")
        
        group_schedule = group_schedule_result.data[0]
        group_id = group_schedule['group_id']
        
        # 그룹 멤버인지 확인
        member_result = supabase.table('group_members').select('role').eq('group_id', group_id).eq('users_id', user_id).execute()
        if not member_result.data:
            raise HTTPException(status_code=403, detail="그룹 멤버만 일정을 제거할 수 있습니다.")
        
        # 그룹에서 일정 제거 (group_schedules에서만 삭제)
        delete_result = supabase.table('group_schedules').delete().eq('id', group_schedule_id).execute()
        
        return {
            "success": True,
            "message": "그룹에서 일정이 제거되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 그룹 일정 제거 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"그룹 일정 제거 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{group_id}/leave")
async def leave_group(
    group_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """그룹에서 탈퇴합니다."""
    try:
        user_id = get_user_id_from_token(credentials)
        
        print(f"👋 그룹 탈퇴 시작: 그룹 ID={group_id}, 사용자 ID={user_id}")
        
        # 그룹 존재 확인
        group_result = supabase.table('group').select('*').eq('id', group_id).execute()
        if not group_result.data:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        
        group_info = group_result.data[0]
        
        # 그룹 멤버인지 확인
        member_result = supabase.table('group_members').select('role').eq('group_id', group_id).eq('users_id', user_id).execute()
        if not member_result.data:
            raise HTTPException(status_code=403, detail="그룹 멤버가 아닙니다.")
        
        member_role = member_result.data[0]['role']
        
        # 소유자는 탈퇴할 수 없음 (삭제만 가능)
        if member_role == 'owner':
            raise HTTPException(status_code=400, detail="그룹 소유자는 탈퇴할 수 없습니다. 그룹을 삭제해주세요.")
        
        # 그룹에서 멤버 제거
        delete_result = supabase.table('group_members').delete().eq('group_id', group_id).eq('users_id', user_id).execute()
        
        print(f"✅ 그룹 탈퇴 완료: 그룹 ID={group_id}, 사용자 ID={user_id}")
        
        return {
            "success": True,
            "message": f"{group_info['group_name']} 그룹에서 탈퇴했습니다.",
            "data": {
                "group_id": group_id,
                "group_name": group_info['group_name']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 그룹 탈퇴 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"그룹 탈퇴 중 오류가 발생했습니다: {str(e)}")

@router.delete("/{group_id}")
async def delete_group(
    group_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """그룹을 삭제합니다 (소유자만 가능)."""
    try:
        user_id = get_user_id_from_token(credentials)
        
        print(f"🗑️ 그룹 삭제 시작: 그룹 ID={group_id}, 사용자 ID={user_id}")
        
        # 그룹 존재 확인
        group_result = supabase.table('group').select('*').eq('id', group_id).execute()
        if not group_result.data:
            raise HTTPException(status_code=404, detail="그룹을 찾을 수 없습니다.")
        
        group_info = group_result.data[0]
        
        # 그룹 소유자인지 확인
        member_result = supabase.table('group_members').select('role').eq('group_id', group_id).eq('users_id', user_id).execute()
        if not member_result.data:
            raise HTTPException(status_code=403, detail="그룹 멤버가 아닙니다.")
        
        member_role = member_result.data[0]['role']
        if member_role != 'owner':
            raise HTTPException(status_code=403, detail="그룹 소유자만 그룹을 삭제할 수 있습니다.")
        
        # 관련 데이터 삭제 (순서 중요)
        # 1. 그룹 일정 삭제
        supabase.table('group_schedules').delete().eq('group_id', group_id).execute()
        
        # 2. 초대 링크 삭제
        supabase.table('invite').delete().eq('group_id', group_id).execute()
        
        # 3. 그룹 멤버 삭제
        supabase.table('group_members').delete().eq('group_id', group_id).execute()
        
        # 4. 그룹 삭제
        delete_result = supabase.table('group').delete().eq('id', group_id).execute()
        
        print(f"✅ 그룹 삭제 완료: 그룹 ID={group_id}, 그룹명={group_info['group_name']}")
        
        return {
            "success": True,
            "message": f"{group_info['group_name']} 그룹이 삭제되었습니다.",
            "data": {
                "group_id": group_id,
                "group_name": group_info['group_name']
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 그룹 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"그룹 삭제 중 오류가 발생했습니다: {str(e)}")

