from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
from uuid import UUID


class AnalysisRequest(BaseModel):
    """분석 요청 모델"""
    content: str = Field(..., description="분석할 텍스트 내용")
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "내일 오후 2시에 회의실에서 프로젝트 회의를 진행하겠습니다. 참석자는 김과장, 이대리, 박사원입니다."
            }
        }


class Participant(BaseModel):
    """참석자 정보 모델"""
    name: str = Field(..., description="참석자 이름")
    role: Optional[str] = Field(None, description="역할/직책")


class Schedule(BaseModel):
    """일정 정보 모델"""
    summary: str = Field(..., description="일정 제목")
    description: str = Field(..., description="일정 상세 설명")
    location: str = Field(..., description="장소")
    startdate: str = Field(..., description="시작 날짜 및 시간 (YYYY-MM-DD HH:MM)")
    enddate: str = Field(..., description="종료 날짜 및 시간 (YYYY-MM-DD HH:MM)")
    assignees: List[str] = Field(default_factory=list, description="담당자 목록")


class AnalysisResult(BaseModel):
    """분석 결과 모델"""
    participants: List[Participant] = Field(..., description="참석자 목록")
    schedules: List[Schedule] = Field(..., description="일정 목록")
    error: Optional[bool] = Field(None, description="오류 발생 여부")
    
    class Config:
        json_schema_extra = {
            "example": {
                "participants": [
                    {"name": "김과장", "role": "과장"},
                    {"name": "이대리", "role": "대리"}
                ],
                "schedules": [
                    {
                        "summary": "프로젝트 회의",
                        "description": "프로젝트 진행 상황 점검 및 향후 계획 논의",
                        "location": "회의실",
                        "startdate": "2024-01-15 14:00",
                        "enddate": "2024-01-15 15:00",
                        "assignees": ["김과장", "이대리"]
                    }
                ]
            }
        }


class FileUploadResponse(BaseModel):
    """파일 업로드 응답 모델"""
    filename: str = Field(..., description="원본 파일명")
    saved_filename: str = Field(..., description="저장된 파일명")
    file_size: int = Field(..., description="파일 크기 (바이트)")
    content_type: Optional[str] = Field(None, description="파일 MIME 타입")
    upload_time: str = Field(..., description="업로드 시간")
    
    class Config:
        json_schema_extra = {
            "example": {
                "filename": "meeting_notes.txt",
                "saved_filename": "12345678-1234-1234-1234-123456789012.txt",
                "file_size": 1024,
                "content_type": "text/plain",
                "upload_time": "2024-01-15T10:30:00"
            }
        }


class FileAnalysisRequest(BaseModel):
    """파일 분석 요청 모델"""
    file_path: str = Field(..., description="분석할 파일 경로")
    
    class Config:
        json_schema_extra = {
            "example": {
                "file_path": "uploads/12345678-1234-1234-1234-123456789012.txt"
            }
        }


class ICSRequest(BaseModel):
    """ICS 생성 요청 모델"""
    schedules: List[Schedule] = Field(..., description="ICS로 변환할 일정 목록")
    
    class Config:
        json_schema_extra = {
            "example": {
                "schedules": [
                    {
                        "summary": "프로젝트 회의",
                        "description": "프로젝트 진행 상황 점검",
                        "location": "회의실",
                        "startdate": "2024-01-15 14:00",
                        "enddate": "2024-01-15 15:00",
                        "assignees": ["김과장", "이대리"]
                    }
                ]
            }
        }


class ICSResponse(BaseModel):
    """ICS 응답 모델"""
    ics_content: str = Field(..., description="ICS 포맷 내용")
    filename: str = Field(..., description="ICS 파일명")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ics_content": "BEGIN:VCALENDAR\nVERSION:2.0\n...",
                "filename": "meeting_20240115.ics"
            }
        }


class ErrorResponse(BaseModel):
    """오류 응답 모델"""
    detail: str = Field(..., description="오류 메시지")
    error_code: Optional[str] = Field(None, description="오류 코드")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "분석 중 오류가 발생했습니다.",
                "error_code": "ANALYSIS_ERROR"
            }
        } 

class ScheduleData(BaseModel):
    title: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    start_time: Optional[time] = None
    end_date: Optional[date] = None
    end_time: Optional[time] = None

class ParticipantData(BaseModel):
    name: str
    role: Optional[str] = None
    email: Optional[str] = None

class ActionData(BaseModel):
    text: str
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    is_completed: bool = False

class AnalysisResultData(BaseModel):
    type: str = Field(..., description="분석 타입: file 또는 text")
    source_name: str = Field(..., description="소스 이름 (파일명 또는 '직접 입력')")
    source_content: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    schedules: List[ScheduleData] = []
    participants: List[ParticipantData] = []
    actions: List[ActionData] = []

class AnalysisResult(BaseModel):
    id: UUID
    type: str
    source_name: str
    source_content: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    schedules: List[ScheduleData] = []
    participants: List[ParticipantData] = []
    actions: List[ActionData] = []
    created_at: datetime
    updated_at: datetime

class AnalysisResponse(BaseModel):
    success: bool
    message: str
    data: Optional[AnalysisResult] = None

class AnalysisListResponse(BaseModel):
    success: bool
    message: str
    data: List[AnalysisResult] = []
    total: int = 0 