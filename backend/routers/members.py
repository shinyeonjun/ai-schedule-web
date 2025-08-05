"""
Members/Users routes for user management
"""
from fastapi import APIRouter, HTTPException, status, Depends, Form
from typing import Dict, Any, List
from services.database_service import DatabaseService
from core.dependencies import get_current_user, get_current_user_optional
from supabase import create_client
from config.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["members"])
db_service = DatabaseService()


@router.get("/profile")
async def get_user_profile(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get current user profile"""
    try:
        user_data = db_service.get_user_by_id(current_user["user_id"])
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "user_id": user_data["id"],
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "created_at": user_data.get("created_at"),
            "last_login_at": user_data.get("last_login_at")
        }
        
    except Exception as e:
        logger.error(f"Error getting user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )


@router.put("/profile")
async def update_user_profile(
    name: str = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update current user profile"""
    try:
        update_data = {}
        if name:
            update_data["name"] = name
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data to update"
            )
        
        updated_user = db_service.update_user(
            user_id=current_user["user_id"],
            data=update_data
        )
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "user_id": updated_user["id"],
                "email": updated_user["email"],
                "name": updated_user["name"],
                "picture": updated_user.get("picture")
            }
        }
        
    except Exception as e:
        logger.error(f"Error updating user profile: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.get("/search")
async def search_members(
    query: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Search for members by name or email"""
    try:
        if len(query) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query must be at least 2 characters long"
            )
        
        # This would be implemented in database_service
        # For now, return empty list
        results = []
        
        return {
            "members": results,
            "total": len(results)
        }
        
    except Exception as e:
        logger.error(f"Error searching members: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.delete("/account")
async def delete_user_account(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Delete current user account"""
    try:
        # This would delete all user data
        # For now, just return success message
        logger.info(f"Account deletion requested for user: {current_user['user_id']}")
        
        return {"message": "Account deletion requested"}
        
    except Exception as e:
        logger.error(f"Error deleting user account: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.get("/list")
async def get_all_users():
    """Get all registered users for member management"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # users 테이블에서 모든 사용자 정보 조회
        result = supabase.table("users").select(
            "id, email, name, picture, created_at, last_login_at"
        ).eq("is_active", True).order("created_at", desc=True).execute()
        
        if not result.data:
            return {"users": [], "total_count": 0}
        
        users = []
        for user in result.data:
            users.append({
                "id": user.get("id"),
                "email": user.get("email"),
                "name": user.get("name"),
                "picture": user.get("picture"),
                "created_at": user.get("created_at"),
                "last_login_at": user.get("last_login_at")
            })
        
        return {"users": users, "total_count": len(users)}
        
    except Exception as e:
        logger.error(f"Error getting users list: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )


@router.get("/contacts")
async def get_contacts(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get external contacts for current user"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 현재 사용자의 연락처만 조회
        result = supabase.table("contacts").select(
            "id, name, email, position, company, phone, created_at"
        ).eq("created_by", current_user["user_id"]).order("created_at", desc=True).execute()
        
        if not result.data:
            return {"contacts": [], "total_count": 0}
        
        return {"contacts": result.data, "total_count": len(result.data)}
        
    except Exception as e:
        logger.error(f"Error getting contacts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contacts: {str(e)}"
        )


@router.post("/contacts")
async def create_contact(
    name: str = Form(...),
    email: str = Form(...),
    position: str = Form(None),
    company: str = Form(None),
    phone: str = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create new external contact"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        contact_data = {
            "name": name,
            "email": email,
            "position": position,
            "company": company,
            "phone": phone,
            "created_by": current_user["user_id"],
            "category": "external"
        }
        
        result = supabase.table("contacts").insert(contact_data).execute()
        
        if result.data:
            return {"success": True, "contact": result.data[0]}
        else:
            raise Exception("Failed to create contact")
            
    except Exception as e:
        logger.error(f"Error creating contact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create contact: {str(e)}"
        )


@router.put("/contacts/{contact_id}")
async def update_contact(
    contact_id: str,
    name: str = Form(None),
    email: str = Form(None),
    position: str = Form(None),
    company: str = Form(None),
    phone: str = Form(None),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update external contact"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 본인이 생성한 연락처인지 확인
        existing = supabase.table("contacts").select("id").eq("id", contact_id).eq(
            "created_by", current_user["user_id"]
        ).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        update_data = {}
        if name is not None:
            update_data["name"] = name
        if email is not None:
            update_data["email"] = email
        if position is not None:
            update_data["position"] = position
        if company is not None:
            update_data["company"] = company
        if phone is not None:
            update_data["phone"] = phone
            
        if not update_data:
            raise HTTPException(status_code=400, detail="No data to update")
        
        result = supabase.table("contacts").update(update_data).eq("id", contact_id).execute()
        
        if result.data:
            return {"success": True, "contact": result.data[0]}
        else:
            raise Exception("Failed to update contact")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating contact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact: {str(e)}"
        )


@router.delete("/contacts/{contact_id}")
async def delete_contact(
    contact_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete external contact"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # 본인이 생성한 연락처인지 확인
        existing = supabase.table("contacts").select("id").eq("id", contact_id).eq(
            "created_by", current_user["user_id"]
        ).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Contact not found")
        
        result = supabase.table("contacts").delete().eq("id", contact_id).execute()
        
        return {"success": True, "message": "Contact deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting contact: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete contact: {str(e)}"
        )


@router.get("/all-people")
async def get_all_people(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all MUFI users and external contacts for email dropdown"""
    try:
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # MUFI 사용자 조회
        users_result = supabase.table("users").select(
            "id, email, name, picture"
        ).eq("is_active", True).order("name").execute()
        
        # 현재 사용자의 외부 연락처 조회
        contacts_result = supabase.table("contacts").select(
            "id, name, email, position, company"
        ).eq("created_by", current_user["user_id"]).order("name").execute()
        
        people = []
        
        # MUFI 사용자 추가
        if users_result.data:
            for user in users_result.data:
                people.append({
                    "id": user.get("id"),
                    "name": user.get("name"),
                    "email": user.get("email"),
                    "picture": user.get("picture"),
                    "type": "mufi_user",
                    "display_name": user.get("name") or user.get("email"),
                    "subtitle": "MUFI 사용자"
                })
        
        # 외부 연락처 추가
        if contacts_result.data:
            for contact in contacts_result.data:
                subtitle = []
                if contact.get("position"):
                    subtitle.append(contact.get("position"))
                if contact.get("company"):
                    subtitle.append(contact.get("company"))
                
                people.append({
                    "id": contact.get("id"),
                    "name": contact.get("name"),
                    "email": contact.get("email"),
                    "position": contact.get("position"),
                    "company": contact.get("company"),
                    "type": "external_contact",
                    "display_name": contact.get("name") or contact.get("email"),
                    "subtitle": " · ".join(subtitle) if subtitle else "외부 인원"
                })
        
        # 이름순으로 정렬
        people.sort(key=lambda x: x["display_name"].lower())
        
        return {"people": people, "total_count": len(people)}
        
    except Exception as e:
        logger.error(f"Error getting all people: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get all people: {str(e)}"
        ) 