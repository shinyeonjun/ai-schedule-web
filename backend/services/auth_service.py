"""
Authentication service for handling user authentication
"""
import httpx
from typing import Dict, Any, Optional
from config.config import settings
from .database_service import DatabaseService
from core.auth import create_jwt_token
import logging

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations"""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.google_client_id = settings.google_client_id
        self.google_client_secret = settings.google_client_secret
        self.google_redirect_uri = settings.google_redirect_uri
    
    async def exchange_google_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange Google OAuth code for access token and user info
        
        Args:
            code: Google OAuth authorization code
            
        Returns:
            Dictionary containing access token and user information
        """
        try:
            # Exchange code for access token
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": self.google_redirect_uri
            }
            
            async with httpx.AsyncClient() as client:
                token_response = await client.post(token_url, data=token_data)
                token_response.raise_for_status()
                token_info = token_response.json()
            
            access_token = token_info.get("access_token")
            if not access_token:
                raise ValueError("No access token received from Google")
            
            # Get user info from Google
            user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
            async with httpx.AsyncClient() as client:
                user_response = await client.get(user_info_url)
                user_response.raise_for_status()
                google_user_info = user_response.json()
            
            # Create or update user in database
            user_data = await self._create_or_update_user(google_user_info)
            
            # Create JWT token
            jwt_token = create_jwt_token(
                user_id=user_data["id"],
                email=user_data["email"],
                name=user_data["name"]
            )
            
            return {
                "access_token": jwt_token,
                "user": user_data,
                "google_user_info": google_user_info
            }
            
        except Exception as e:
            logger.error(f"Error in Google OAuth exchange: {str(e)}")
            raise
    
    async def _create_or_update_user(self, google_user_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create or update user in database based on Google user info
        
        Args:
            google_user_info: User information from Google
            
        Returns:
            User data from database
        """
        google_id = google_user_info.get("id")
        email = google_user_info.get("email")
        name = google_user_info.get("name")
        picture = google_user_info.get("picture")
        
        if not google_id or not email:
            raise ValueError("Missing required user information from Google")
        
        # Check if user already exists by google_id
        existing_user = self.db_service.get_user_by_google_id(google_id)
        
        if existing_user:
            # Update existing user
            user_data = self.db_service.update_user(
                user_id=existing_user["id"],
                data={
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "last_login_at": "now()"
                }
            )
            logger.info(f"Updated existing user: {user_data['id']}")
        else:
            # Create new user
            user_data = self.db_service.create_user(
                google_id=google_id,
                email=email,
                name=name,
                picture=picture
            )
            logger.info(f"Created new user: {user_data['id']}")
        
        return user_data
    
    def validate_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Validate JWT token and return user information
        
        Args:
            token: JWT token to validate
            
        Returns:
            User information if token is valid, None otherwise
        """
        try:
            from core.auth import verify_jwt_token
            payload = verify_jwt_token(token)
            
            user_id = payload.get("user_id")
            if not user_id:
                return None
            
            # Get current user data from database
            user_data = self.db_service.get_user_by_id(user_id)
            return user_data
            
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}")
            return None 