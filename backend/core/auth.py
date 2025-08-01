"""
Authentication utilities and JWT handling
"""
import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status
from config.config import settings


class JWTHandler:
    """JWT token handling utilities"""
    
    @staticmethod
    def create_access_token(data: Dict[str, Any]) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expires_hours)
        to_encode.update({"exp": expire})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.jwt_secret, 
            algorithm=settings.jwt_algorithm
        )
        return encoded_jwt
    
    @staticmethod
    def decode_token(token: str) -> Dict[str, Any]:
        """Decode and validate JWT token"""
        try:
            payload = jwt.decode(
                token, 
                settings.jwt_secret, 
                algorithms=[settings.jwt_algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    
    @staticmethod
    def get_user_id_from_token(token: str) -> Optional[str]:
        """Extract user ID from JWT token"""
        try:
            payload = JWTHandler.decode_token(token)
            return payload.get("user_id")
        except HTTPException:
            return None


def create_jwt_token(user_id: str, email: str, name: str) -> str:
    """Create JWT token for user"""
    token_data = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "type": "access_token"
    }
    return JWTHandler.create_access_token(token_data)


def verify_jwt_token(token: str) -> Dict[str, Any]:
    """Verify JWT token and return payload"""
    return JWTHandler.decode_token(token) 