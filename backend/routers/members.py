"""
Members/Users routes for user management
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
from services.database_service import DatabaseService
from core.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/members", tags=["members"])
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