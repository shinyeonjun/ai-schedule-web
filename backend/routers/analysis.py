from fastapi import APIRouter, HTTPException, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
import os
import tempfile
from datetime import datetime, date, time
import pytz
import re
import uuid

from models.analysis import (
    AnalysisRequest, 
    AnalysisResultData,
    AnalysisResult, 
    AnalysisResponse,
    AnalysisListResponse,
    ScheduleData,
    ParticipantData,
    ActionData,
    SaveAnalysisRequestNew,
    SaveScheduleResponse
)
from services.gpt_service import GPTService
from services.file_service import FileService
from services.database_service import DatabaseService
from services.ics_service import ICSService

router = APIRouter()

# 서비스 인스턴스 생성
gpt_service = GPTService()
file_service = FileService()
database_service = DatabaseService()
ics_service = ICSService()

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

@router.post("/analyze/file")
async def analyze_file(file: UploadFile = File(...)):
    """파일 업로드 및 분석 (결과 반환만)"""
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
            
            return {
                "success": True,
                "message": "파일 분석이 완료되었습니다.",
                "data": {
                    "source_type": "file",
                    "source_name": file.filename,
                    "source_content": file_content,
                    "summary": gpt_response.get("summary", ""),
                    "schedules": gpt_response.get("schedules", []),
                    "participants": gpt_response.get("participants", []),
                    "actions": gpt_response.get("actions", [])
                }
            }
            
        finally:
            # 임시 파일 삭제
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"파일 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/analyze/text")
async def analyze_text(request: AnalysisRequest):
    """텍스트 분석 (결과 반환만)"""
    try:
        # GPT 분석
        gpt_response = await gpt_service.analyze_call_content(request.content)
        
        return {
            "success": True,
            "message": "텍스트 분석이 완료되었습니다.",
            "data": {
                "source_type": "text",
                "source_name": "직접 입력",
                "source_content": request.content,
                "summary": gpt_response.get("summary", ""),
                "schedules": gpt_response.get("schedules", []),
                "participants": gpt_response.get("participants", []),
                "actions": gpt_response.get("actions", [])
            }
        }
        
    except Exception as e:
        print(f"텍스트 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"텍스트 분석 중 오류가 발생했습니다: {str(e)}")

@router.post("/save-debug")
async def save_analysis_debug(request: dict):
    """디버깅용 저장 엔드포인트 - raw data 확인"""
    print("\n" + "="*50)
    print("🔍 디버깅 API 호출됨")
    print("="*50)
    print(f"📝 Raw 요청 데이터:")
    import json
    print(json.dumps(request, indent=2, ensure_ascii=False))
    print("="*50 + "\n")
    return {"status": "debug_ok", "data": request}

@router.post("/save", response_model=SaveScheduleResponse)
async def save_analysis_results(request: SaveAnalysisRequestNew):
    """분석 결과를 schedules 테이블에 저장"""
    try:
        print("\n" + "="*50)
        print("💾 저장 API 호출됨")
        print("="*50)
        print(f"📝 전체 요청 데이터:")
        print(f"  - user_id: {request.user_id}")
        print(f"  - source_name: {request.source_name}")
        print(f"  - source_type: {request.source_type}")
        print(f"  - summary: {request.summary}")
        print(f"  - schedules: {len(request.schedules)}개")
        print(f"  - participants: {len(request.participants) if request.participants else 0}개")
        print(f"  - actions: {len(request.actions) if request.actions else 0}개")
        print("="*50 + "\n")
        
        # Supabase 클라이언트 생성
        from supabase import create_client
        from config.config import settings
        
        supabase = create_client(settings.supabase_url, settings.supabase_service_key)
        saved_schedule_ids = []
        
        # 분석 ID 생성 (모든 스케줄에 공통)
        analysis_id = f"{request.source_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 파일 ID 생성 (같은 분석의 모든 일정에 동일한 UUID 적용)
        file_id = str(uuid.uuid4())
        print(f"📁 생성된 file_id: {file_id}")
        
        # 전체 participants는 더이상 사용하지 않음 (각 일정별 participants만 사용)
        
        saved_schedule_data = []
        schedule_count = 0
        
        # 1. 실제 스케줄들 저장
        if request.schedules:
            for idx, schedule in enumerate(request.schedules):
                try:
                    # 스케줄 설명
                    full_description = getattr(schedule, 'description', None) or ""
                    
                    # 타입 정보 미리 준비
                    schedule_type = getattr(schedule, 'type', 'group')
                    schedule_type_emoji = "👥" if schedule_type == 'group' else "👤"
                    schedule_type_name = "단체일정" if schedule_type == 'group' else "개인일정"
                    
                    # 날짜 문자열 처리 및 ISO 형식 변환
                    def convert_datetime_str(dt_str):
                        """날짜 문자열을 ISO 형식으로 변환"""
                        if not dt_str:
                            return None
                        
                        if isinstance(dt_str, str):
                            # "2025-08-05 09:00" 형식을 "2025-08-05T09:00:00+09:00" 형식으로 변환
                            try:
                                # 시간대 정보가 없는 경우 KST로 가정
                                if 'T' not in dt_str and '+' not in dt_str and '-' not in dt_str[-6:]:
                                    # "2025-08-05 09:00" 형식 처리
                                    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
                                    kst = pytz.timezone('Asia/Seoul')
                                    dt_kst = kst.localize(dt)
                                    return dt_kst.isoformat()
                                else:
                                    # 이미 ISO 형식이거나 시간대 정보가 있는 경우
                                    return dt_str
                            except Exception as e:
                                print(f"⚠️ 날짜 파싱 실패: {dt_str}, 오류: {e}")
                                # 파싱 실패 시 원본 반환
                                return dt_str
                        else:
                            # datetime 객체인 경우
                            return dt_str.isoformat()
                    
                    start_dt = getattr(schedule, 'start_datetime', None)
                    end_dt = getattr(schedule, 'end_datetime', None)
                    
                    start_datetime_str = convert_datetime_str(start_dt)
                    end_datetime_str = convert_datetime_str(end_dt)
                    
                    # 개별 일정의 참석자 JSON 데이터 준비 - GPT 반환값 그대로 사용
                    schedule_participants = getattr(schedule, 'participants', [])
                    participants_json = schedule_participants if schedule_participants else []
                    

                    
                    schedule_data = {
                        "user_id": request.user_id,
                        "analysis_id": analysis_id,  # 모든 일정이 같은 analysis_id 사용
                        "file_id": file_id,  # 같은 분석의 모든 일정에 동일한 file_id
                        "title": getattr(schedule, 'title', None) or "제목 없음",
                        "description": full_description,
                        "location": getattr(schedule, 'location', None) or "",
                        "start_datetime": start_datetime_str,
                        "end_datetime": end_datetime_str,
                        "type": schedule_type,
                        "participants": participants_json  # JSON 형태로 저장
                    }
                    
                    print(f"{schedule_type_emoji} {schedule_type_name} {schedule_count+1} 저장 중: {schedule_data['title']}")
                    
                    # Supabase에 저장
                    result = supabase.table("schedules").insert(schedule_data).execute()
                    
                    if result.data and len(result.data) > 0:
                        schedule_id = str(result.data[0]["id"])
                        saved_schedule_ids.append(schedule_id)
                        saved_schedule_data.append(result.data[0])
                        print(f"✅ {schedule_type_name} {schedule_count+1} 저장 성공: {schedule_id}")
                        schedule_count += 1
                    else:
                        print(f"❌ {schedule_type_name} {schedule_count+1} 저장 실패: 응답 데이터 없음")
                        
                except Exception as schedule_error:
                    print(f"❌ {schedule_type_name} {schedule_count+1} 저장 중 오류: {str(schedule_error)}")
                    continue
        
        # 2. 개인일정들을 각각 개별 스케줄로 저장 (이제 schedules에 포함되므로 비활성화)
        if request.actions and False:  # 비활성화
            for idx, action in enumerate(request.actions):
                try:
                    action_text = getattr(action, 'text', None) or str(action) if isinstance(action, str) else '개인일정 없음'
                    assignee = getattr(action, 'assignee', None) or '담당자 미정'
                    due_date = getattr(action, 'due_date', None)
                    
                    # 개인일정 설명 구성
                    personal_description = f"담당자: {assignee}"
                    if participants_str:
                        personal_description += f" | 관련자: {participants_str}"
                    
                    # 날짜 직렬화 처리
                    start_dt = None
                    end_dt = None
                    if due_date:
                        if hasattr(due_date, 'isoformat'):
                            start_dt = due_date.isoformat()
                            end_dt = due_date.isoformat()
                        else:
                            start_dt = str(due_date)
                            end_dt = str(due_date)
                    
                    personal_schedule_data = {
                        "user_id": request.user_id,
                        "analysis_id": f"{analysis_id}_personal_{idx}",
                        "title": f"[개인] {action_text}",
                        "description": personal_description,
                        "location": "",
                        "start_datetime": start_dt,
                        "end_datetime": end_dt,
                        "type": "personal",
                        "participants": []  # JSON 저장 안함
                    }
                    
                    print(f"👤 개인일정 {idx+1} 저장 중: {action_text}")
                    
                    # Supabase에 저장
                    result = supabase.table("schedules").insert(personal_schedule_data).execute()
                    
                    if result.data and len(result.data) > 0:
                        personal_id = str(result.data[0]["id"])
                        saved_schedule_ids.append(personal_id)
                        saved_schedule_data.append(result.data[0])
                        print(f"✅ 개인일정 {idx+1} 저장 성공: {personal_id}")
                    else:
                        print(f"❌ 개인일정 {idx+1} 저장 실패: 응답 데이터 없음")
                        
                except Exception as personal_error:
                    print(f"❌ 개인일정 {idx+1} 저장 중 오류: {str(personal_error)}")
                    continue
        
        # ICS 파일 생성 및 스토리지 저장 (DB 기반)
        if saved_schedule_ids:
            try:
                print(f"📅 DB 기반 ICS 파일 생성 중... ({len(saved_schedule_ids)}개 일정)")
                
                # 각 스케줄에 ICS 파일 경로 업데이트
                for schedule_id in saved_schedule_ids:
                    try:
                        # DB에서 저장된 스케줄 데이터 다시 조회 (정확한 날짜/시간 포함)
                        db_result = supabase.table("schedules").select("*").eq("id", schedule_id).execute()
                        
                        if not db_result.data:
                            print(f"❌ 스케줄 {schedule_id} DB 조회 실패")
                            continue
                            
                        db_schedule = db_result.data[0]
                        print(f"📊 DB에서 조회한 스케줄 {schedule_id}: {db_schedule.get('title')}")
                        print(f"📅 시작시간: {db_schedule.get('start_datetime')}")
                        print(f"📅 종료시간: {db_schedule.get('end_datetime')}")
                        
                        # DB 기반 개별 스케줄 ICS 파일 생성
                        individual_ics = ics_service.generate_ics_content(
                            schedules=[db_schedule],  # DB에서 조회한 정확한 데이터 사용
                            title=db_schedule.get("title", "일정")
                        )
                        
                        # 스토리지에 저장 (analysis_id 포함)
                        filename = f"schedule_{schedule_id}"
                        save_result = await ics_service.save_ics_to_storage(
                            ics_content=individual_ics,
                            filename=filename,
                            user_id=request.user_id,
                            analysis_id=analysis_id  # 통화별 폴더 구분
                        )
                        file_path = save_result.get("public_url", "")
                        
                        # 스케줄 테이블에 ICS 파일 경로 업데이트
                        supabase.table("schedules").update({
                            "ics_file_path": file_path
                        }).eq("id", schedule_id).execute()
                        
                        print(f"📁 스케줄 {schedule_id} ICS 파일 저장 성공: {file_path}")
                
                    except Exception as ics_error:
                        print(f"❌ 스케줄 {schedule_id} ICS 저장 오류: {str(ics_error)}")
                        continue
                        
                print(f"✅ 모든 DB 기반 ICS 파일 생성 완료!")
                
            except Exception as ics_error:
                print(f"⚠️ DB 기반 ICS 파일 생성 오류 (DB 저장은 성공): {str(ics_error)}")
                # ICS 생성 실패해도 DB 저장은 성공했으므로 계속 진행
        
        if saved_schedule_ids:
            group_count = len([s for s in saved_schedule_data if s.get('type') == 'group'])
            personal_count = len([s for s in saved_schedule_data if s.get('type') == 'personal'])
            
            message_parts = []
            if group_count > 0:
                message_parts.append(f"단체일정 {group_count}개")
            if personal_count > 0:
                message_parts.append(f"개인일정 {personal_count}개")
            
            message = f"{', '.join(message_parts)}가 저장되고 ICS 파일이 생성되었습니다."
            
            return SaveScheduleResponse(
                success=True,
                message=message,
                schedule_ids=saved_schedule_ids
            )
        else:
            raise HTTPException(status_code=500, detail="저장된 일정이 없습니다.")
        
    except Exception as e:
        print(f"💥 분석 결과 저장 전체 오류: {str(e)}")
        print(f"💥 오류 타입: {type(e)}")
        import traceback
        print(f"💥 스택 트레이스: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"분석 결과 저장 중 오류가 발생했습니다: {str(e)}")

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
@router.post("/file", response_model=AnalysisResponse)
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
            
            return AnalysisResponse(
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

@router.post("/text", response_model=AnalysisResponse)
async def analyze_text_legacy(request: AnalysisRequest):
    """텍스트 분석 (레거시 - DB 저장 안함)"""
    try:
        analysis_result = await gpt_service.analyze_call_content(request.content)
        
        return AnalysisResponse(
            success=True,
            message="텍스트 분석이 완료되었습니다.",
            data=analysis_result
        )
        
    except Exception as e:
        print(f"텍스트 분석 오류: {str(e)}")
        raise HTTPException(status_code=500, detail=f"텍스트 분석 중 오류가 발생했습니다: {str(e)}") 