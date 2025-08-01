"""
Data models for analysis operations
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime


class AnalysisRequest(BaseModel):
    """Model for analysis request"""
    title: str
    content: str
    analysis_type: str = "general"


class Schedule(BaseModel):
    """Model for schedule item"""
    title: str
    date: str
    time: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    participants: Optional[List[str]] = None
    category: str = "personal"  # personal, group, meeting


class AnalysisResult(BaseModel):
    """Model for analysis result"""
    title: str
    summary: str
    key_points: List[str]
    personal_schedules: List[Schedule]
    group_schedules: List[Schedule]
    action_items: List[str]
    participants: List[str]
    sentiment: str
    confidence_score: float
    
    
class SaveAnalysisRequest(BaseModel):
    """Model for saving analysis request"""
    title: str
    analysis_data: Dict[str, Any]
    

class AnalysisResponse(BaseModel):
    """Model for analysis API response"""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    

class FileUploadResponse(BaseModel):
    """Model for file upload response"""
    success: bool
    filename: str
    file_type: str
    content: Optional[str] = None
    message: str


# User related models
class UserCreate(BaseModel):
    """Model for creating a new user"""
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None


class UserUpdate(BaseModel):
    """Model for updating user information"""
    email: Optional[str] = None
    name: Optional[str] = None
    picture: Optional[str] = None


class UserResponse(BaseModel):
    """Model for user response"""
    id: str
    google_id: str
    email: str
    name: str
    picture: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None


class AuthResponse(BaseModel):
    """Model for authentication response"""
    access_token: str
    user: UserResponse
    message: str