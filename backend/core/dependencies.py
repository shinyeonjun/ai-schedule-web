"""
FastAPI dependencies for authentication and common utilities
"""
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from .auth import verify_jwt_token
from services.database_service import DatabaseService

security = HTTPBearer()
db_service = DatabaseService()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """
    Dependency to get current authenticated user from JWT token
    """
    try:
        token = credentials.credentials
        payload = verify_jwt_token(token)
        
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user_id"
            )
        
        # Get user info from database
        user_data = db_service.get_user_by_id(user_id)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        return {
            "user_id": user_id,
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "picture": user_data.get("picture")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )


async def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[Dict[str, Any]]:
    """
    Optional dependency to get current user (returns None if not authenticated)
    """
    if not authorization:
        return None
    
    try:
        # Extract token from "Bearer <token>" format
        if not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split(" ")[1]
        payload = verify_jwt_token(token)
        
        user_id = payload.get("user_id")
        if not user_id:
            return None
        
        # Get user info from database
        user_data = db_service.get_user_by_id(user_id)
        if not user_data:
            return None
        
        return {
            "user_id": user_id,
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "picture": user_data.get("picture")
        }
        
    except Exception:
        return None


async def get_current_user_id(current_user: Dict[str, Any] = Depends(get_current_user)) -> str:
    """
    Dependency to get just the current user ID
    """
    return current_user["user_id"] 