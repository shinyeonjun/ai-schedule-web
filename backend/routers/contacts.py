"""
Contacts API Router
외부 연락처 관리 기능을 제공합니다.
"""
import logging
from typing import Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from supabase import create_client
from config.config import settings
from core.dependencies import get_current_user_optional

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contacts", tags=["Contacts"])

# Pydantic 모델들
class ContactCreate(BaseModel):
    name: str
    email: EmailStr
    company: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    category: Optional[str] = "general"
    notes: Optional[str] = None
    is_favorite: Optional[bool] = False

class ContactUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None
    is_favorite: Optional[bool] = None

class ContactResponse(BaseModel):
    id: str
    name: str
    email: str
    company: Optional[str] = None
    position: Optional[str] = None
    phone: Optional[str] = None
    category: str = "general"
    notes: Optional[str] = None
    is_favorite: bool = False
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ContactsListResponse(BaseModel):
    contacts: List[ContactResponse]
    total_count: int
    page: int
    limit: int

@router.get("/", response_model=ContactsListResponse)
async def get_contacts_list(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, email, or company"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    연락처 목록 조회
    """
    try:
        print(f"📇 [INFO] 연락처 목록 조회 요청")
        print(f"📇 페이지: {page}, 제한: {limit}, 검색: {search}, 카테고리: {category}, 즐겨찾기: {is_favorite}")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 페이지네이션 계산
        offset = (page - 1) * limit
        
        # contacts 테이블에서 연락처 목록 조회
        query = supabase.table("contacts").select("*")
        
        # 검색 조건 추가
        if search:
            search_term = f"%{search}%"
            query = query.or_(f"name.ilike.{search_term},email.ilike.{search_term},company.ilike.{search_term}")
        
        # 카테고리 필터
        if category:
            query = query.eq("category", category)
        
        # 즐겨찾기 필터
        if is_favorite is not None:
            query = query.eq("is_favorite", is_favorite)
        
        # 전체 개수 조회 (필터 조건 포함)
        count_query = supabase.table("contacts").select("id", count="exact")
        if search:
            search_term = f"%{search}%"
            count_query = count_query.or_(f"name.ilike.{search_term},email.ilike.{search_term},company.ilike.{search_term}")
        if category:
            count_query = count_query.eq("category", category)
        if is_favorite is not None:
            count_query = count_query.eq("is_favorite", is_favorite)
        
        count_result = count_query.execute()
        total_count = count_result.count if count_result.count else 0
        
        # 페이지네이션 적용하여 실제 데이터 조회 (즐겨찾기 우선, 이름 순)
        query = query.order("is_favorite", desc=True).order("name", desc=False).range(offset, offset + limit - 1)
        result = query.execute()
        
        contacts = result.data if result.data else []
        
        print(f"📇 조회된 연락처 수: {len(contacts)}")
        print(f"📇 전체 연락처 수: {total_count}")
        
        # 응답 데이터 변환
        contact_responses = []
        for contact in contacts:
            contact_responses.append(ContactResponse(
                id=str(contact.get('id', '')),
                name=contact.get('name', ''),
                email=contact.get('email', ''),
                company=contact.get('company'),
                position=contact.get('position'),
                phone=contact.get('phone'),
                category=contact.get('category', 'general'),
                notes=contact.get('notes'),
                is_favorite=contact.get('is_favorite', False),
                created_by=str(contact.get('created_by', '')) if contact.get('created_by') else None,
                created_at=contact.get('created_at'),
                updated_at=contact.get('updated_at')
            ))
        
        return ContactsListResponse(
            contacts=contact_responses,
            total_count=total_count,
            page=page,
            limit=limit
        )
        
    except Exception as e:
        print(f"❌ [ERROR] 연락처 목록 조회 실패: {str(e)}")
        logger.error(f"Error fetching contacts list: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연락처 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/", response_model=ContactResponse)
async def create_contact(
    contact: ContactCreate,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    새 연락처 추가
    """
    try:
        print(f"📇 [INFO] 새 연락처 추가: {contact.name} ({contact.email})")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 이메일 중복 체크
        existing = supabase.table("contacts").select("id").eq("email", contact.email).execute()
        if existing.data and len(existing.data) > 0:
            raise HTTPException(status_code=400, detail="이미 등록된 이메일 주소입니다.")
        
        # 연락처 데이터 준비
        contact_data = {
            "name": contact.name,
            "email": contact.email,
            "company": contact.company,
            "position": contact.position,
            "phone": contact.phone,
            "category": contact.category or "general",
            "notes": contact.notes,
            "is_favorite": contact.is_favorite or False,
            "created_by": current_user.get('id') if current_user else None
        }
        
        # 연락처 추가
        result = supabase.table("contacts").insert(contact_data).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=500, detail="연락처 추가에 실패했습니다.")
        
        created_contact = result.data[0]
        print(f"✅ [DEBUG] 연락처 추가 성공: {created_contact['id']}")
        
        return ContactResponse(
            id=str(created_contact.get('id', '')),
            name=created_contact.get('name', ''),
            email=created_contact.get('email', ''),
            company=created_contact.get('company'),
            position=created_contact.get('position'),
            phone=created_contact.get('phone'),
            category=created_contact.get('category', 'general'),
            notes=created_contact.get('notes'),
            is_favorite=created_contact.get('is_favorite', False),
            created_by=str(created_contact.get('created_by', '')) if created_contact.get('created_by') else None,
            created_at=created_contact.get('created_at'),
            updated_at=created_contact.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ERROR] 연락처 추가 실패: {str(e)}")
        logger.error(f"Error creating contact: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연락처 추가 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(
    contact_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    특정 연락처 상세 정보 조회
    """
    try:
        print(f"📇 [INFO] 연락처 상세 조회: {contact_id}")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # contacts 테이블에서 특정 연락처 조회
        result = supabase.table("contacts").select("*").eq("id", contact_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail="연락처를 찾을 수 없습니다")
        
        contact = result.data[0]
        print(f"✅ [DEBUG] 연락처 조회 성공: {contact['email']}")
        
        return ContactResponse(
            id=str(contact.get('id', '')),
            name=contact.get('name', ''),
            email=contact.get('email', ''),
            company=contact.get('company'),
            position=contact.get('position'),
            phone=contact.get('phone'),
            category=contact.get('category', 'general'),
            notes=contact.get('notes'),
            is_favorite=contact.get('is_favorite', False),
            created_by=str(contact.get('created_by', '')) if contact.get('created_by') else None,
            created_at=contact.get('created_at'),
            updated_at=contact.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ERROR] 연락처 상세 조회 실패: {str(e)}")
        logger.error(f"Error fetching contact details: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연락처 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: str,
    contact_update: ContactUpdate,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    연락처 정보 수정
    """
    try:
        print(f"📇 [INFO] 연락처 수정: {contact_id}")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 기존 연락처 확인
        existing = supabase.table("contacts").select("*").eq("id", contact_id).execute()
        if not existing.data or len(existing.data) == 0:
            raise HTTPException(status_code=404, detail="연락처를 찾을 수 없습니다")
        
        # 수정할 데이터만 추출
        update_data = {}
        if contact_update.name is not None:
            update_data["name"] = contact_update.name
        if contact_update.email is not None:
            # 이메일 중복 체크 (현재 연락처 제외)
            email_check = supabase.table("contacts").select("id").eq("email", contact_update.email).neq("id", contact_id).execute()
            if email_check.data and len(email_check.data) > 0:
                raise HTTPException(status_code=400, detail="이미 등록된 이메일 주소입니다.")
            update_data["email"] = contact_update.email
        if contact_update.company is not None:
            update_data["company"] = contact_update.company
        if contact_update.position is not None:
            update_data["position"] = contact_update.position
        if contact_update.phone is not None:
            update_data["phone"] = contact_update.phone
        if contact_update.category is not None:
            update_data["category"] = contact_update.category
        if contact_update.notes is not None:
            update_data["notes"] = contact_update.notes
        if contact_update.is_favorite is not None:
            update_data["is_favorite"] = contact_update.is_favorite
        
        if not update_data:
            raise HTTPException(status_code=400, detail="수정할 데이터가 없습니다")
        
        # 연락처 수정
        result = supabase.table("contacts").update(update_data).eq("id", contact_id).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=500, detail="연락처 수정에 실패했습니다")
        
        updated_contact = result.data[0]
        print(f"✅ [DEBUG] 연락처 수정 성공: {updated_contact['id']}")
        
        return ContactResponse(
            id=str(updated_contact.get('id', '')),
            name=updated_contact.get('name', ''),
            email=updated_contact.get('email', ''),
            company=updated_contact.get('company'),
            position=updated_contact.get('position'),
            phone=updated_contact.get('phone'),
            category=updated_contact.get('category', 'general'),
            notes=updated_contact.get('notes'),
            is_favorite=updated_contact.get('is_favorite', False),
            created_by=str(updated_contact.get('created_by', '')) if updated_contact.get('created_by') else None,
            created_at=updated_contact.get('created_at'),
            updated_at=updated_contact.get('updated_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ERROR] 연락처 수정 실패: {str(e)}")
        logger.error(f"Error updating contact: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연락처 수정 중 오류가 발생했습니다: {str(e)}"
        )

@router.delete("/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    연락처 삭제
    """
    try:
        print(f"📇 [INFO] 연락처 삭제: {contact_id}")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 기존 연락처 확인
        existing = supabase.table("contacts").select("id, name, email").eq("id", contact_id).execute()
        if not existing.data or len(existing.data) == 0:
            raise HTTPException(status_code=404, detail="연락처를 찾을 수 없습니다")
        
        contact_info = existing.data[0]
        
        # 연락처 삭제
        result = supabase.table("contacts").delete().eq("id", contact_id).execute()
        
        print(f"✅ [DEBUG] 연락처 삭제 성공: {contact_info['name']} ({contact_info['email']})")
        
        return JSONResponse(content={
            "message": f"연락처 '{contact_info['name']}'이(가) 성공적으로 삭제되었습니다",
            "deleted_contact": {
                "id": contact_id,
                "name": contact_info['name'],
                "email": contact_info['email']
            }
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ [ERROR] 연락처 삭제 실패: {str(e)}")
        logger.error(f"Error deleting contact: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"연락처 삭제 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/categories/list")
async def get_contact_categories(
    current_user: Optional[Dict] = Depends(get_current_user_optional)
):
    """
    연락처 카테고리 목록 조회
    """
    try:
        print(f"📇 [INFO] 연락처 카테고리 목록 조회")
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 사용 중인 카테고리 목록 조회
        result = supabase.table("contacts").select("category").execute()
        
        categories = set()
        if result.data:
            for contact in result.data:
                if contact.get('category'):
                    categories.add(contact.get('category'))
        
        # 기본 카테고리 추가
        default_categories = ["general", "client", "partner", "vendor", "internal"]
        categories.update(default_categories)
        
        categories_list = sorted(list(categories))
        print(f"📇 사용 중인 카테고리: {categories_list}")
        
        return JSONResponse(content={
            "categories": categories_list,
            "total_count": len(categories_list)
        })
        
    except Exception as e:
        print(f"❌ [ERROR] 카테고리 목록 조회 실패: {str(e)}")
        logger.error(f"Error fetching contact categories: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"카테고리 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )