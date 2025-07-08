from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import tempfile
from datetime import datetime, date, time
import re

from models.analysis import (
    AnalysisRequest, 
    AnalysisResponse as LegacyAnalysisResponse,
    AnalysisResultData,
    AnalysisResult, 
    AnalysisResponse,
    AnalysisListResponse,
    ScheduleData,
    ParticipantData,
    ActionData
)
from services.gpt_service import GPTService
from services.file_service import FileService
from services.database_service import DatabaseService

router = APIRouter()

# 서비스 인스턴스 생성
gpt_service = GPTService()
file_service = FileService()
database_service = DatabaseService()

def parse_gpt_response_to_data(gpt_response: dict, analysis_type: str, source_name: str, source_content: str = None) -> AnalysisResultData:
    """GPT 응답을 AnalysisResultData로 변환"""
    
    # 일정 정보 파싱
    schedules = []
    if gpt_response.get("schedules"):
        for schedule_item in gpt_response["schedules"]:
            schedule = ScheduleData(
                title=schedule_item.get("title"),
                location=schedule_item.get("location"),
                start_date=parse_date(schedule_item.get("date")),
                start_time=parse_time(schedule_item.get("time") or schedule_item.get("start_time")),
                end_date=parse_date(schedule_item.get("end_date")),
                end_time=parse_time(schedule_item.get("end_time"))
            )
            schedules.append(schedule)
    
    # 참석자 정보 파싱
    participants = []
    if gpt_response.get("participants"):
        for participant_item in gpt_response["participants"]:
            if isinstance(participant_item, str):
                participant = ParticipantData(name=participant_item)
            else:
                participant = ParticipantData(
                    name=participant_item.get("name", ""),
                    role=participant_item.get("role"),
                    email=participant_item.get("email")
                )
            participants.append(participant)
    
    # 액션 아이템 파싱
    actions = []
    if gpt_response.get("action_items") or gpt_response.get("actions"):
        action_items = gpt_response.get("action_items") or gpt_response.get("actions")
        for action_item in action_items:
            if isinstance(action_item, str):
                action = ActionData(text=action_item)
            else:
                action = ActionData(
                    text=action_item.get("text", action_item.get("description", "")),
                    assignee=action_item.get("assignee"),
                    due_date=parse_date(action_item.get("due_date"))
                )
            actions.append(action)
    
    return AnalysisResultData(
        type=analysis_type,
        source_name=source_name,
        source_content=source_content,
        summary=gpt_response.get("summary"),
        description=gpt_response.get("description") or gpt_response.get("details"),
        schedules=schedules,
        participants=participants,
        actions=actions
    )

def parse_date(date_str: str) -> Optional[date]:
    """날짜 문자열을 date 객체로 변환"""
    if not date_str:
        return None
    
    try:
        # 다양한 날짜 형식 지원
        for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        
        # 한국어 날짜 형식 처리
        if "년" in date_str and "월" in date_str and "일" in date_str:
            match = re.search(r"(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일", date_str)
            if match:
                year, month, day = match.groups()
                return date(int(year), int(month), int(day))
        
        return None
    except Exception:
        return None

def parse_time(time_str: str) -> Optional[time]:
    """시간 문자열을 time 객체로 변환"""
    if not time_str:
        return None
    
    try:
        # 다양한 시간 형식 지원
        for fmt in ["%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"]:
            try:
                return datetime.strptime(time_str, fmt).time()
            except ValueError:
                continue
        
        # 한국어 시간 형식 처리
        if "시" in time_str:
            match = re.search(r"(\d{1,2})시\s*(\d{1,2})?분?", time_str)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                return time(hour, minute)
        
        return None
    except Exception:
        return None

@router.post("/analyze/file", response_model=AnalysisResponse)
async def analyze_file(file: UploadFile = File(...)):
    """파일 업로드 및 분석 (DB 저장)"""
    try:
        # 파일 검증
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        # 임시 파일로 저장
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # 파일 내용 추출
            file_content = await file_service.extract_text_from_file(temp_file_path)
            
            if not file_content.strip():
                raise HTTPException(status_code=400, detail="파일에서 텍스트를 추출할 수 없습니다.")
            
            # GPT 분석
            gpt_response = await gpt_service.analyze_call_content(file_content)
            
            # 데이터 변환
            analysis_data = parse_gpt_response_to_data(
                gpt_response, 
                "file", 
                file.filename, 
                file_content
            )
            
            # 데이터베이스에 저장
            analysis_id = await database_service.save_analysis_result(analysis_data)
            
            # 저장된 결과 조회
            saved_result = await database_service.get_analysis_result(analysis_id)
            
            if not saved_result:
                raise HTTPException(status_code=500, detail="저장된 분석 결과를 조회할 수 없습니다.")
            
            return AnalysisResponse(
                success=True,
                message="파일 분석이 완료되고 저장되었습니다.",
                data=saved_result
            )
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"파일 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/analyze/text", response_model=AnalysisResponse)
async def analyze_text(request: AnalysisRequest):
    """텍스트 분석 (DB 저장)"""
    try:
        # GPT 분석
        gpt_response = await gpt_service.analyze_call_content(request.content)
        
        # 데이터 변환
        analysis_data = parse_gpt_response_to_data(
            gpt_response, 
            "text", 
            "직접 입력", 
            request.content
        )
        
        # 데이터베이스에 저장
        analysis_id = await database_service.save_analysis_result(analysis_data)
        
        # 저장된 결과 조회
        saved_result = await database_service.get_analysis_result(analysis_id)
        
        if not saved_result:
            raise HTTPException(status_code=500, detail="저장된 분석 결과를 조회할 수 없습니다.")
        
        return AnalysisResponse(
            success=True,
            message="텍스트 분석이 완료되고 저장되었습니다.",
            data=saved_result
        )
        
    except Exception as e:
        print(f"텍스트 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"텍스트 분석 중 오류가 발생했습니다: {str(e)}")

@router.get("/results", response_model=AnalysisListResponse)
async def get_analysis_results(limit: int = 50, offset: int = 0):
    """저장된 분석 결과 목록 조회"""
    try:
        results, total = await database_service.get_analysis_list(limit, offset)
        
        return AnalysisListResponse(
            success=True,
            message=f"분석 결과 {len(results)}개를 조회했습니다.",
            data=results,
            total=total
        )
        
    except Exception as e:
        print(f"분석 결과 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 결과 목록 조회 중 오류가 발생했습니다: {str(e)}")

@router.get("/results/{analysis_id}", response_model=AnalysisResponse)
async def get_analysis_result(analysis_id: str):
    """특정 분석 결과 조회"""
    try:
        result = await database_service.get_analysis_result(analysis_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
        
        return AnalysisResponse(
            success=True,
            message="분석 결과를 조회했습니다.",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"분석 결과 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 결과 조회 중 오류가 발생했습니다: {str(e)}")

@router.delete("/results/{analysis_id}")
async def delete_analysis_result(analysis_id: str):
    """분석 결과 삭제"""
    try:
        success = await database_service.delete_analysis_result(analysis_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="삭제할 분석 결과를 찾을 수 없습니다.")
        
        return {"success": True, "message": "분석 결과가 삭제되었습니다."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"분석 결과 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 결과 삭제 중 오류가 발생했습니다: {str(e)}")

@router.patch("/results/{analysis_id}/actions/{action_index}")
async def update_action_status(analysis_id: str, action_index: int, is_completed: bool):
    """액션 아이템 완료 상태 업데이트"""
    try:
        success = await database_service.update_action_status(analysis_id, action_index, is_completed)
        
        if success:
            return {"success": True, "message": "액션 상태가 업데이트되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="액션 아이템을 찾을 수 없습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"액션 상태 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"액션 상태 업데이트 중 오류가 발생했습니다: {str(e)}")

@router.patch("/results/{analysis_id}")
async def update_analysis_field(analysis_id: str, request: dict):
    """분석 결과 특정 필드 업데이트"""
    try:
        field = request.get("field")
        value = request.get("value")
        
        if not field or value is None:
            raise HTTPException(status_code=400, detail="필드명과 값이 필요합니다.")
        
        success = await database_service.update_analysis_field(analysis_id, field, value)
        
        if success:
            return {"success": True, "message": f"{field} 필드가 업데이트되었습니다."}
        else:
            raise HTTPException(status_code=404, detail="분석 결과를 찾을 수 없습니다.")
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"분석 필드 업데이트 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"분석 필드 업데이트 중 오류가 발생했습니다: {str(e)}")

# 기존 API 호환성을 위한 레거시 엔드포인트
@router.post("/file", response_model=LegacyAnalysisResponse)
async def analyze_file_legacy(file: UploadFile = File(...)):
    """파일 업로드 및 분석 (레거시 - DB 저장 안함)"""
    try:
        if not file.filename:
            raise HTTPException(status_code=400, detail="파일명이 없습니다.")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            file_content = await file_service.extract_text(temp_file_path)
            
            if not file_content.strip():
                raise HTTPException(status_code=400, detail="파일에서 텍스트를 추출할 수 없습니다.")
            
            analysis_result = await gpt_service.analyze_call_content(file_content)
            
            return LegacyAnalysisResponse(
                success=True,
                message="파일 분석이 완료되었습니다.",
                data=analysis_result
            )
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"파일 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/text", response_model=LegacyAnalysisResponse)
async def analyze_text_legacy(request: AnalysisRequest):
    """텍스트 분석 (레거시 - DB 저장 안함)"""
    try:
        analysis_result = await gpt_service.analyze_call_content(request.content)
        
        return LegacyAnalysisResponse(
            success=True,
            message="텍스트 분석이 완료되었습니다.",
            data=analysis_result
        )
        
    except Exception as e:
        print(f"텍스트 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"텍스트 분석 중 오류가 발생했습니다: {str(e)}") 