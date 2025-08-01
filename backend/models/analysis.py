"""
Data models for analysis operations
"""
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from uuid import UUID


class AnalysisRequest(BaseModel):
    """Model for analysis request"""
    content: str
    title: Optional[str] = None
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


class AnalysisListResponse(BaseModel):
    """Model for analysis list API response"""
    success: bool
    message: str
    results: List[Dict[str, Any]]
    total: int
    

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


# Database service related models
class ScheduleData(BaseModel):
    """Model for schedule data"""
    title: str
    description: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    start_time: Optional[time] = None
    end_date: Optional[date] = None
    end_time: Optional[time] = None
    start_datetime: Optional[str] = None  # 문자열로 변경
    end_datetime: Optional[str] = None    # 문자열로 변경
    type: Optional[str] = "group"
    participants: Optional[List[str]] = []  # 참여자 필드 추가


class ParticipantData(BaseModel):
    """Model for participant data"""
    name: str
    role: Optional[str] = None
    email: Optional[str] = None


class ActionData(BaseModel):
    """Model for action data"""
    text: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None  # 문자열로 변경
    is_completed: bool = False


class AnalysisResultData(BaseModel):
    """Model for complete analysis result data"""
    type: str
    source_name: str
    source_content: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    schedules: Optional[List[ScheduleData]] = None
    participants: Optional[List[ParticipantData]] = None
    actions: Optional[List[ActionData]] = None


class AnalysisResultDB(BaseModel):
    """Model for database analysis result"""
    id: UUID
    type: str
    source_name: str
    source_content: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    schedules: Optional[List[ScheduleData]] = None
    participants: Optional[List[ParticipantData]] = None
    actions: Optional[List[ActionData]] = None
    created_at: datetime
    updated_at: datetime


class SaveAnalysisRequestNew(BaseModel):
    """Model for saving analysis results to schedules table"""
    user_id: str
    source_name: str
    source_type: str = "text"
    summary: Optional[str] = None
    schedules: List[ScheduleData]
    participants: Optional[List[ParticipantData]] = None
    actions: Optional[List[ActionData]] = None


class SaveScheduleResponse(BaseModel):
    """Model for save schedule response"""
    success: bool
    message: str
    schedule_ids: List[str] = []