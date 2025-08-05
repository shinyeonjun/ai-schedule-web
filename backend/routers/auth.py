"""
Authentication routes for MUFI application
"""
from fastapi import APIRouter, HTTPException, status, Depends, Request
from typing import Dict, Any, Optional
from services.auth_service import AuthService
from services.google_token_service import google_token_service
from core.dependencies import get_current_user_optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])
auth_service = AuthService()


@router.get("/google/login")
async def google_login(request: Request):
    """Get Google OAuth login URL"""
    from config.config import settings
    
    # 현재 요청의 호스트를 기반으로 동적으로 리다이렉트 URI 생성
    host = request.headers.get("host")
    scheme = "https" if request.headers.get("x-forwarded-proto") == "https" else "http"
    redirect_uri = f"{scheme}://{host}/auth/google/callback"
    
    google_auth_url = (
        "https://accounts.google.com/o/oauth2/auth"
        f"?client_id={settings.google_client_id}"
        "&response_type=code"
        "&scope=openid email profile"
        f"&redirect_uri={redirect_uri}"
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


@router.post("/verify")
async def verify_token(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Verify if the provided token is valid"""
    if current_user:
        return {
            "valid": True,
            "user_id": current_user["user_id"],
            "email": current_user["email"],
            "name": current_user["name"]
        }
    else:
        return {
            "valid": False,
            "message": "Invalid or expired token"
        }


@router.post("/logout")
async def logout(current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)):
    """Logout user (client-side token cleanup)"""
    if current_user:
        # Google 토큰도 함께 삭제
        google_token_service.delete_tokens(current_user["user_id"])
    return {"message": "Logout successful"}


@router.post("/google/store-tokens")
async def store_google_tokens(
    request: Dict[str, Any],
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Store Google OAuth tokens in database"""
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Google 토큰 정보 추출
        google_credentials = request.get("google_credentials")
        if not google_credentials:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Google credentials are required"
            )
        
        # DB에 토큰 저장
        stored_tokens = google_token_service.save_tokens(
            user_id=current_user["user_id"],
            token_data=google_credentials
        )
        
        return {
            "success": True,
            "message": "Google tokens stored successfully",
            "expires_at": stored_tokens.get("expires_at")
        }
        
    except Exception as e:
        logger.error(f"Google 토큰 저장 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store Google tokens: {str(e)}"
        )


@router.get("/google/tokens")
async def get_google_tokens(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """Get valid Google tokens for current user"""
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_id = current_user["user_id"]
        logger.info(f"🔍 [DEBUG] Google 토큰 조회 요청 - User ID: {user_id}")
        
        # 먼저 DB에서 원본 토큰 확인
        raw_tokens = google_token_service.get_tokens(user_id)
        logger.info(f"🔍 [DEBUG] DB 원본 토큰 존재: {bool(raw_tokens)}")
        if raw_tokens:
            logger.info(f"🔍 [DEBUG] 원본 토큰 정보: expires_at={raw_tokens.get('expires_at')}, "
                       f"refresh_token_exists={bool(raw_tokens.get('refresh_token'))}")
        
        # 유효한 토큰 가져오기 (자동 갱신 포함)
        valid_tokens = await google_token_service.get_valid_tokens(user_id)
        
        if not valid_tokens:
            logger.warning(f"❌ [DEBUG] 유효한 토큰을 가져올 수 없음 - User ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No valid Google tokens found. Please re-authenticate."
            )
        
        logger.info(f"✅ [DEBUG] 유효한 토큰 반환 성공 - User ID: {user_id}")
        
        # 민감한 정보는 제외하고 반환
        return {
            "success": True,
            "tokens": {
                "access_token": valid_tokens["access_token"],
                "expires_at": valid_tokens["expires_at"],
                "scopes": valid_tokens["scopes"]
            },
            "debug_info": {
                "raw_token_exists": bool(raw_tokens),
                "refresh_token_exists": bool(raw_tokens and raw_tokens.get("refresh_token")),
                "original_expires_at": raw_tokens.get("expires_at") if raw_tokens else None,
                "final_expires_at": valid_tokens.get("expires_at")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google 토큰 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get Google tokens: {str(e)}"
        )

@router.post("/google/force-refresh")
async def force_refresh_google_tokens(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user_optional)
):
    """강제로 Google 토큰 갱신"""
    try:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        user_id = current_user["user_id"]
        logger.info(f"🔄 [DEBUG] 강제 토큰 갱신 요청 - User ID: {user_id}")
        
        # 강제 토큰 갱신
        refreshed_tokens = await google_token_service.refresh_access_token(user_id)
        
        if not refreshed_tokens:
            logger.error(f"❌ [DEBUG] 강제 토큰 갱신 실패 - User ID: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Token refresh failed. Please re-authenticate with Google."
            )
        
        logger.info(f"✅ [DEBUG] 강제 토큰 갱신 성공 - User ID: {user_id}")
        
        return {
            "success": True,
            "message": "Google tokens refreshed successfully",
            "tokens": {
                "access_token": refreshed_tokens["access_token"][:20] + "...",  # 보안을 위해 일부만 표시
                "expires_at": refreshed_tokens["expires_at"]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"강제 토큰 갱신 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh Google tokens: {str(e)}"
        ) 