"""
Custom exceptions for MUFI application
"""
from fastapi import HTTPException, status


class AuthenticationError(HTTPException):
    """Authentication related errors"""
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail
        )


class AuthorizationError(HTTPException):
    """Authorization related errors"""
    def __init__(self, detail: str = "Not authorized"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class DatabaseError(HTTPException):
    """Database related errors"""
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ValidationError(HTTPException):
    """Validation related errors"""
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail
        )


class NotFoundError(HTTPException):
    """Resource not found errors"""
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail
        ) 