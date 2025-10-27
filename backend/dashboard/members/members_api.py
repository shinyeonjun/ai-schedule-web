from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Dict, Any
import os
from supabase import create_client, Client
from ..auth.auth_service import verify_token

# Supabase 클라이언트 설정 (MUFI 프로젝트)
supabase_url = os.getenv("SUPABASE_URL", "https://znvwtoozdcnaqpuzbnhu.supabase.co")
supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd0b296ZGNuYXFwdXpibmh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ2Mjk0MjQsImV4cCI6MjA3MDIwNTQyNH0.UdqqsxqdUoPtPNyQSRfEjKL6cg90dUDNuzsancxIYR0")
supabase: Client = create_client(supabase_url, supabase_key)

router = APIRouter(prefix="/api/members", tags=["인원 관리"])

# JWT 토큰 검증
security = HTTPBearer()

@router.get("/mufi-users")
async def get_mufi_users(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    MUFI에 등록된 모든 사용자를 조회합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        
        print(f"👥 MUFI 사용자 목록 조회 시작")
        print(f"👤 요청자: {user_data.get('email', 'unknown')}")
        
        # public.users 테이블에서 사용자 목록 조회
        result = supabase.table('users').select('*').execute()
        
        print(f"🔍 데이터베이스에서 가져온 원본 데이터: {result.data}")
        
        if result.data:
            # 사용자 데이터 정리
            users = []
            for user in result.data:
                print(f"👤 원본 사용자 데이터: {user}")
                user_info = {
                    'id': user.get('id'),
                    'email': user.get('email'),
                    'name': user.get('name'),
                    'created_at': user.get('created_at'),
                    'last_login_at': user.get('last_login_at'),
                    'is_active': True,  # 기본값
                    'role': 'user',  # 기본값
                    'picture': user.get('picture')
                }
                print(f"📝 정리된 사용자 정보: {user_info}")
                users.append(user_info)
            
            # 생성일 기준 내림차순 정렬 (최신순)
            users.sort(key=lambda x: x['created_at'], reverse=True)
            
            print(f"✅ MUFI 사용자 목록 조회 완료: {len(users)}명")
            
            return {
                "success": True,
                "message": f"MUFI 사용자 {len(users)}명을 조회했습니다.",
                "data": {
                    "users": users,
                    "total_users": len(users)
                },
                "user": user_data
            }
        else:
            print(f"📭 등록된 사용자가 없습니다.")
            return {
                "success": True,
                "message": "등록된 사용자가 없습니다.",
                "data": {
                    "users": [],
                    "total_users": 0
                },
                "user": user_data
            }
            
    except Exception as e:
        print(f"❌ MUFI 사용자 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/external-contacts")
async def get_external_contacts(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    외부 인원 목록을 조회합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"👥 외부 인원 목록 조회 시작")
        print(f"👤 요청자: {user_data.get('email', 'unknown')}")
        
        # 외부 인원 테이블에서 조회 (사용자별로 관리)
        try:
            # user_id 변환 준비
            query_user_id_int = None
            try:
                if isinstance(user_id, str) and user_id.isdigit():
                    query_user_id_int = int(user_id)
                elif isinstance(user_id, int):
                    query_user_id_int = user_id
            except:
                query_user_id_int = None

            contacts = []
            # external_personnel 테이블에서 조회
            if query_user_id_int is not None:
                res_personnel = supabase.table('external_personnel').select('*').eq('user_id', query_user_id_int).execute()
                if res_personnel.data:
                    for c in res_personnel.data:
                        contacts.append({
                            'id': c.get('id'),
                            'name': c.get('name'),
                            'email': c.get('email'),
                            'created_at': c.get('created_at'),
                            'phone': c.get('phone'),
                            'company': c.get('company'),
                            'position': c.get('position'),
                            'notes': c.get('notes')
                        })

            # 응답 구성
            if contacts:
                contacts = sorted(contacts, key=lambda x: x.get('created_at', ''), reverse=True)
                print(f"✅ 외부 인원 목록 조회 완료: {len(contacts)}명")
                return {
                    "success": True,
                    "message": f"외부 인원 {len(contacts)}명을 조회했습니다.",
                    "data": {
                        "contacts": contacts,
                        "total_contacts": len(contacts)
                    },
                    "user": user_data
                }
            else:
                print(f"📭 등록된 외부 인원이 없습니다.")
                return {
                    "success": True,
                    "message": "등록된 외부 인원이 없습니다.",
                    "data": {
                        "contacts": [],
                        "total_contacts": 0
                    },
                    "user": user_data
                }
        except Exception as qe:
            # 테이블 미존재 등 스키마 이슈는 빈 목록으로 처리 (프론트 사용성 우선)
            err_msg = str(qe)
            print(f"⚠️ 외부 인원 조회 예외 처리: {err_msg}")
            if 'does not exist' in err_msg or 'relation' in err_msg:
                return {
                    "success": True,
                    "message": "외부 인원 테이블이 아직 구성되지 않았습니다.",
                    "data": {
                        "contacts": [],
                        "total_contacts": 0
                    },
                    "user": user_data
                }
            # 기타 예외는 기존 로직으로 500 처리
            raise
            
    except Exception as e:
        print(f"❌ 외부 인원 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"외부 인원 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/user/{user_id}")
async def delete_user(
    user_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    MUFI 사용자를 삭제합니다. (관리자만 가능)
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        
        print(f"🗑️ MUFI 사용자 삭제 시작")
        print(f"👤 요청자: {user_data.get('email', 'unknown')}")
        print(f"🆔 삭제 대상 사용자 ID: {user_id}")
        
        # 관리자 권한 확인 (간단한 체크)
        if user_data.get('role') != 'admin':
            raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
        
        # 사용자 삭제
        result = supabase.table('users').delete().eq('id', user_id).execute()
        
        deleted_count = len(result.data) if result.data else 0
        
        if deleted_count > 0:
            print(f"✅ MUFI 사용자 삭제 완료: {deleted_count}명")
            return {
                "success": True,
                "message": "사용자가 성공적으로 삭제되었습니다.",
                "data": {
                    "deleted_count": deleted_count,
                    "user_id": user_id
                },
                "user": user_data
            }
        else:
            print(f"❌ 삭제할 사용자를 찾을 수 없습니다.")
            raise HTTPException(status_code=404, detail="삭제할 사용자를 찾을 수 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ MUFI 사용자 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"사용자 삭제 중 오류가 발생했습니다: {str(e)}")

@router.post("/external-contacts")
async def add_external_contact(
    contact_data: dict,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    외부 인원을 추가합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        # user_id를 integer로 변환
        query_user_id_int = None
        try:
            if isinstance(user_id, str) and user_id.isdigit():
                query_user_id_int = int(user_id)
            elif isinstance(user_id, int):
                query_user_id_int = user_id
        except:
            raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID입니다.")
        
        if query_user_id_int is None:
            raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID입니다.")
        
        print(f"👥 외부 인원 추가 시작")
        print(f"👤 요청자: {user_data.get('email', 'unknown')}")
        print(f"📝 추가할 인원 정보: {contact_data}")
        
        # 필수 필드 확인
        if not contact_data.get('name'):
            raise HTTPException(status_code=400, detail="이름은 필수 입력 항목입니다.")
        
        if not contact_data.get('email'):
            raise HTTPException(status_code=400, detail="이메일은 필수 입력 항목입니다.")
        
        # 외부 인원 추가
        insert_data = {
            'user_id': query_user_id_int,
            'name': contact_data.get('name'),
            'email': contact_data.get('email'),
            'phone': contact_data.get('phone'),
            'company': contact_data.get('company'),
            'position': contact_data.get('position'),
            'notes': contact_data.get('notes')
        }
        
        result = supabase.table('external_personnel').insert(insert_data).execute()
        
        if result.data:
            print(f"✅ 외부 인원 추가 완료: {result.data[0]}")
            return {
                "success": True,
                "message": "외부 인원이 성공적으로 추가되었습니다.",
                "data": {
                    "contact": result.data[0]
                },
                "user": user_data
            }
        else:
            raise HTTPException(status_code=500, detail="외부 인원 추가에 실패했습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 외부 인원 추가 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"외부 인원 추가 중 오류가 발생했습니다: {str(e)}")

@router.delete("/contact/{contact_id}")
async def delete_contact(
    contact_id: str,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    외부 인원을 삭제합니다.
    """
    try:
        # 토큰 검증
        user_data = verify_token(credentials.credentials)
        user_id = user_data.get('sub', user_data.get('email', 'unknown'))
        
        print(f"🗑️ 외부 인원 삭제 시작")
        print(f"👤 요청자: {user_data.get('email', 'unknown')}")
        print(f"🆔 삭제 대상 인원 ID: {contact_id}")
        
        # 외부 인원 삭제 (사용자 소유 확인)
        # user_id를 integer로 변환
        query_user_id_int = None
        try:
            if isinstance(user_id, str) and user_id.isdigit():
                query_user_id_int = int(user_id)
            elif isinstance(user_id, int):
                query_user_id_int = user_id
        except:
            raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID입니다.")
        
        if query_user_id_int is None:
            raise HTTPException(status_code=400, detail="유효하지 않은 사용자 ID입니다.")
        
        result = supabase.table('external_personnel').delete().eq('id', contact_id).eq('user_id', query_user_id_int).execute()
        
        deleted_count = len(result.data) if result.data else 0
        
        if deleted_count > 0:
            print(f"✅ 외부 인원 삭제 완료: {deleted_count}명")
            return {
                "success": True,
                "message": "외부 인원이 성공적으로 삭제되었습니다.",
                "data": {
                    "deleted_count": deleted_count,
                    "contact_id": contact_id
                },
                "user": user_data
            }
        else:
            print(f"❌ 삭제할 외부 인원을 찾을 수 없습니다.")
            raise HTTPException(status_code=404, detail="삭제할 외부 인원을 찾을 수 없습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 외부 인원 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"외부 인원 삭제 중 오류가 발생했습니다: {str(e)}")

@router.get("/health")
async def members_health_check():
    """
    인원 관리 서비스 상태 확인
    """
    return {
        "status": "healthy",
        "service": "members-management"
    }
