"""
Authentication routes for MUFI application
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, Optional
from services.auth_service import AuthService
from core.dependencies import get_current_user_optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = AuthService()


@router.get("/google/login")
async def google_login():
    """Get Google OAuth login URL"""
    from config.config import settings
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.google_client_id}"
        "&response_type=code"
        "&scope=openid email profile"
        f"&redirect_uri={settings.google_redirect_uri}"
        "&access_type=offline"
    )
    
    return {"auth_url": google_auth_url}


@router.get("/google/callback")
async def google_callback(code: str):
    """Handle Google OAuth callback"""
    try:
        if not code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Authorization code is required"
            )
        
        # Exchange code for token and user info
        auth_result = await auth_service.exchange_google_code(code)
        
        return {
            "access_token": auth_result["access_token"],
            "user": auth_result["user"],
            "message": "Authentication successful"
        }
        
    except Exception as e:
        logger.error(f"Google OAuth callback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )


@router.get("/status")
async def auth_status(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Get current authentication status"""
    if current_user:
        return {
            "authenticated": True,
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "name": current_user["name"],
            "picture": current_user.get("picture")
        }
    else:
        return {
            "authenticated": False,
            "user_id": None,
            "email": None,
            "name": None,
            "picture": None
        }


@router.post("/logout")
async def logout():
    """Logout user (client-side token cleanup)"""
    return {"message": "Logout successful"} 