from supabase import create_client, Client
from typing import List, Optional, Dict, Any
from datetime import datetime, date, time
import os
import json
from uuid import UUID, uuid4
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

from models.analysis import (
    AnalysisResult, 
    AnalysisResultData, 
    ScheduleData, 
    ParticipantData, 
    ActionData
)

class DatabaseService:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL", "https://ktcksionzsybzzpziird.supabase.co")
        self.supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imt0Y2tzaW9uenN5Ynp6cHppaXJkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEyNjAzNTgsImV4cCI6MjA2NjgzNjM1OH0.WcoHArimjWJe6nIcpRFAbECsbCvGnVUEKTvXKg0XgHM")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Supabase 환경 변수가 설정되지 않았습니다.")
        
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
    
    async def save_analysis_result(self, analysis_data: AnalysisResultData) -> str:
        """분석 결과를 데이터베이스에 저장"""
        try:
            # 메인 분석 결과 저장
            analysis_id = str(uuid4())
            
            main_result = {
                "id": analysis_id,
                "type": analysis_data.type,
                "source_name": analysis_data.source_name,
                "source_content": analysis_data.source_content,
                "summary": analysis_data.summary,
                "description": analysis_data.description
            }
            
            result = self.client.table("analysis_results").insert(main_result).execute()
            
            if not result.data:
                raise Exception("분석 결과 저장 실패")
            
            # 일정 정보 저장
            if analysis_data.schedules:
                schedule_records = []
                for schedule in analysis_data.schedules:
                    schedule_record = {
                        "id": str(uuid4()),
                        "analysis_id": analysis_id,
                        "title": schedule.title,
                        "location": schedule.location,
                        "start_date": schedule.start_date.isoformat() if schedule.start_date else None,
                        "start_time": schedule.start_time.isoformat() if schedule.start_time else None,
                        "end_date": schedule.end_date.isoformat() if schedule.end_date else None,
                        "end_time": schedule.end_time.isoformat() if schedule.end_time else None
                    }
                    schedule_records.append(schedule_record)
                
                if schedule_records:
                    self.client.table("analysis_schedules").insert(schedule_records).execute()
            
            # 참석자 정보 저장
            if analysis_data.participants:
                participant_records = []
                for participant in analysis_data.participants:
                    participant_record = {
                        "id": str(uuid4()),
                        "analysis_id": analysis_id,
                        "name": participant.name,
                        "role": participant.role,
                        "email": participant.email
                    }
                    participant_records.append(participant_record)
                
                if participant_records:
                    self.client.table("analysis_participants").insert(participant_records).execute()
            
            # 액션 아이템 저장
            if analysis_data.actions:
                action_records = []
                for action in analysis_data.actions:
                    action_record = {
                        "id": str(uuid4()),
                        "analysis_id": analysis_id,
                        "text": action.text,
                        "assignee": action.assignee,
                        "due_date": action.due_date.isoformat() if action.due_date else None,
                        "is_completed": action.is_completed
                    }
                    action_records.append(action_record)
                
                if action_records:
                    self.client.table("analysis_actions").insert(action_records).execute()
            
            return analysis_id
            
        except Exception as e:
            print(f"데이터베이스 저장 오류: {str(e)}")
            raise Exception(f"분석 결과 저장 중 오류가 발생했습니다: {str(e)}")
    
    async def get_analysis_result(self, analysis_id: str) -> Optional[AnalysisResult]:
        """특정 분석 결과 조회"""
        try:
            # 메인 분석 결과 조회
            main_result = self.client.table("analysis_results").select("*").eq("id", analysis_id).execute()
            
            if not main_result.data:
                return None
            
            analysis_data = main_result.data[0]
            
            # 일정 정보 조회
            schedules_result = self.client.table("analysis_schedules").select("*").eq("analysis_id", analysis_id).execute()
            schedules = []
            for schedule_data in schedules_result.data:
                schedule = ScheduleData(
                    title=schedule_data.get("title"),
                    location=schedule_data.get("location"),
                    start_date=datetime.fromisoformat(schedule_data["start_date"]).date() if schedule_data.get("start_date") else None,
                    start_time=datetime.fromisoformat(f"1970-01-01T{schedule_data['start_time']}").time() if schedule_data.get("start_time") else None,
                    end_date=datetime.fromisoformat(schedule_data["end_date"]).date() if schedule_data.get("end_date") else None,
                    end_time=datetime.fromisoformat(f"1970-01-01T{schedule_data['end_time']}").time() if schedule_data.get("end_time") else None
                )
                schedules.append(schedule)
            
            # 참석자 정보 조회
            participants_result = self.client.table("analysis_participants").select("*").eq("analysis_id", analysis_id).execute()
            participants = []
            for participant_data in participants_result.data:
                participant = ParticipantData(
                    name=participant_data["name"],
                    role=participant_data.get("role"),
                    email=participant_data.get("email")
                )
                participants.append(participant)
            
            # 액션 아이템 조회
            actions_result = self.client.table("analysis_actions").select("*").eq("analysis_id", analysis_id).execute()
            actions = []
            for action_data in actions_result.data:
                action = ActionData(
                    text=action_data["text"],
                    assignee=action_data.get("assignee"),
                    due_date=datetime.fromisoformat(action_data["due_date"]).date() if action_data.get("due_date") else None,
                    is_completed=action_data.get("is_completed", False)
                )
                actions.append(action)
            
            # AnalysisResult 객체 생성
            result = AnalysisResult(
                id=UUID(analysis_data["id"]),
                type=analysis_data["type"],
                source_name=analysis_data["source_name"],
                source_content=analysis_data.get("source_content"),
                summary=analysis_data.get("summary"),
                description=analysis_data.get("description"),
                schedules=schedules,
                participants=participants,
                actions=actions,
                created_at=datetime.fromisoformat(analysis_data["created_at"].replace("Z", "+00:00")),
                updated_at=datetime.fromisoformat(analysis_data["updated_at"].replace("Z", "+00:00"))
            )
            
            return result
            
        except Exception as e:
            print(f"데이터베이스 조회 오류: {str(e)}")
            raise Exception(f"분석 결과 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def get_analysis_list(self, limit: int = 50, offset: int = 0) -> tuple[List[AnalysisResult], int]:
        """분석 결과 목록 조회"""
        try:
            # 전체 개수 조회
            count_result = self.client.table("analysis_results").select("id", count="exact").execute()
            total_count = count_result.count or 0
            
            # 분석 결과 목록 조회 (최신순)
            results = self.client.table("analysis_results").select("*").order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            analysis_list = []
            for analysis_data in results.data:
                analysis_id = analysis_data["id"]
                
                # 각 분석 결과의 상세 정보 조회
                result = await self.get_analysis_result(analysis_id)
                if result:
                    analysis_list.append(result)
            
            return analysis_list, total_count
            
        except Exception as e:
            print(f"분석 목록 조회 오류: {str(e)}")
            raise Exception(f"분석 목록 조회 중 오류가 발생했습니다: {str(e)}")
    
    async def delete_analysis_result(self, analysis_id: str) -> bool:
        """분석 결과 삭제"""
        try:
            # CASCADE 설정으로 관련 데이터도 자동 삭제됨
            result = self.client.table("analysis_results").delete().eq("id", analysis_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            print(f"분석 결과 삭제 오류: {str(e)}")
            raise Exception(f"분석 결과 삭제 중 오류가 발생했습니다: {str(e)}")
    
    async def update_action_status(self, analysis_id: str, action_index: int, is_completed: bool) -> bool:
        """액션 아이템 완료 상태 업데이트"""
        try:
            # 해당 분석의 액션 아이템들을 순서대로 조회
            actions_result = self.client.table("analysis_actions").select("*").eq("analysis_id", analysis_id).order("created_at").execute()
            
            if action_index >= len(actions_result.data):
                return False
            
            action_id = actions_result.data[action_index]["id"]
            
            # 상태 업데이트
            result = self.client.table("analysis_actions").update({"is_completed": is_completed}).eq("id", action_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"액션 상태 업데이트 오류: {str(e)}")
            return False 

    async def update_analysis_field(self, analysis_id: str, field: str, value: str) -> bool:
        """분석 결과 특정 필드 업데이트"""
        try:
            # 메인 테이블 필드 업데이트
            if field in ['summary', 'description']:
                result = self.client.table("analysis_results").update({field: value}).eq("id", analysis_id).execute()
                return len(result.data) > 0
            
            # 스케줄 테이블 필드 업데이트
            elif field in ['location', 'startdate', 'enddate']:
                # 해당 분석의 첫 번째 스케줄 조회
                schedule_result = self.client.table("analysis_schedules").select("*").eq("analysis_id", analysis_id).limit(1).execute()
                
                if not schedule_result.data:
                    # 스케줄이 없으면 새로 생성
                    schedule_id = str(uuid4())
                    schedule_data = {
                        "id": schedule_id,
                        "analysis_id": analysis_id,
                        "title": "통화 일정"
                    }
                    
                    if field == 'location':
                        schedule_data['location'] = value
                    elif field == 'startdate':
                        # 날짜와 시간 분리
                        if ' ' in value:
                            date_part, time_part = value.split(' ', 1)
                            schedule_data['start_date'] = date_part
                            schedule_data['start_time'] = time_part
                        else:
                            schedule_data['start_date'] = value
                    elif field == 'enddate':
                        if ' ' in value:
                            date_part, time_part = value.split(' ', 1)
                            schedule_data['end_date'] = date_part
                            schedule_data['end_time'] = time_part
                        else:
                            schedule_data['end_date'] = value
                    
                    result = self.client.table("analysis_schedules").insert(schedule_data).execute()
                    return len(result.data) > 0
                else:
                    # 기존 스케줄 업데이트
                    schedule_id = schedule_result.data[0]["id"]
                    update_data = {}
                    
                    if field == 'location':
                        update_data['location'] = value
                    elif field == 'startdate':
                        if ' ' in value:
                            date_part, time_part = value.split(' ', 1)
                            update_data['start_date'] = date_part
                            update_data['start_time'] = time_part
                        else:
                            update_data['start_date'] = value
                    elif field == 'enddate':
                        if ' ' in value:
                            date_part, time_part = value.split(' ', 1)
                            update_data['end_date'] = date_part
                            update_data['end_time'] = time_part
                        else:
                            update_data['end_date'] = value
                    
                    result = self.client.table("analysis_schedules").update(update_data).eq("id", schedule_id).execute()
                    return len(result.data) > 0
            
            return False
            
        except Exception as e:
            print(f"분석 필드 업데이트 오류: {str(e)}")
            return False

    # User management methods
    def create_user(self, google_id: str, email: str, name: str, picture: Optional[str] = None) -> Dict[str, Any]:
        """Create a new user in the database"""
        try:
            user_data = {
                "id": str(uuid4()),
                "google_id": google_id,
                "email": email,
                "name": name,
                "picture": picture,
                "created_at": datetime.utcnow().isoformat(),
                "last_login_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table("users").insert(user_data).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to create user")
                
        except Exception as e:
            print(f"사용자 생성 오류: {str(e)}")
            raise Exception(f"사용자 생성 중 오류가 발생했습니다: {str(e)}")

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user ID"""
        try:
            result = self.client.table("users").select("*").eq("id", user_id).execute()
            
            if result.data:
                return result.data[0]
            return None
                
        except Exception as e:
            print(f"사용자 조회 오류: {str(e)}")
            return None

    def get_user_by_google_id(self, google_id: str) -> Optional[Dict[str, Any]]:
        """Get user by Google ID"""
        try:
            result = self.client.table("users").select("*").eq("google_id", google_id).execute()
            
            if result.data:
                return result.data[0]
            return None
                
        except Exception as e:
            print(f"Google ID로 사용자 조회 오류: {str(e)}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            result = self.client.table("users").select("*").eq("email", email).execute()
            
            if result.data:
                return result.data[0]
            return None
                
        except Exception as e:
            print(f"이메일로 사용자 조회 오류: {str(e)}")
            return None

    def update_user(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information"""
        try:
            # Add updated_at timestamp
            data["updated_at"] = datetime.utcnow().isoformat()
            
            result = self.client.table("users").update(data).eq("id", user_id).execute()
            
            if result.data:
                return result.data[0]
            else:
                raise Exception("Failed to update user")
                
        except Exception as e:
            print(f"사용자 업데이트 오류: {str(e)}")
            raise Exception(f"사용자 업데이트 중 오류가 발생했습니다: {str(e)}")

    def delete_user(self, user_id: str) -> bool:
        """Delete user from database"""
        try:
            result = self.client.table("users").delete().eq("id", user_id).execute()
            return len(result.data) > 0
                
        except Exception as e:
            print(f"사용자 삭제 오류: {str(e)}")
            return False
    
    # ===== 일정 공유 관련 메서드 =====
    
    def get_schedule_by_id(self, schedule_id: str) -> Optional[Dict[str, Any]]:
        """스케줄 ID로 일정 조회"""
        try:
            result = self.client.table("schedules").select("*").eq("id", schedule_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"스케줄 조회 오류: {str(e)}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """이메일로 사용자 조회"""
        try:
            result = self.client.table("users").select("*").eq("email", email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"사용자 이메일 조회 오류: {str(e)}")
            return None
    
    def update_schedule_share(self, schedule_id: str, share_data: List[Dict[str, Any]]) -> bool:
        """스케줄의 공유 정보 업데이트"""
        try:
            result = self.client.table("schedules").update({
                "share": share_data,
                "updated_at": datetime.now().isoformat()
            }).eq("id", schedule_id).execute()
            
            return len(result.data) > 0
        except Exception as e:
            print(f"스케줄 공유 업데이트 오류: {str(e)}")
            return False
    
    def get_shared_schedules_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자가 공유받은 일정들 조회"""
        try:
            # PostgreSQL JSONB에서 배열 내 객체의 필드를 검색
            # share 컬럼이 JSONB 배열이고, 각 배열 요소가 user_id를 가지고 있는 경우
            result = self.client.table("schedules").select("*").contains("share", [{"user_id": user_id}]).execute()
            
            # 더 정확한 필터링을 위해 Python에서 추가 처리
            filtered_schedules = []
            for schedule in result.data:
                share_data = schedule.get('share') or []
                for shared_user in share_data:
                    if shared_user.get('user_id') == user_id:
                        filtered_schedules.append(schedule)
                        break
            
            return filtered_schedules
        except Exception as e:
            print(f"공유받은 일정 조회 오류: {str(e)}")
            return []
    
    def get_schedules_shared_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자가 공유한 일정들 조회"""
        try:
            result = self.client.table("schedules").select("*").eq("user_id", user_id).neq("share", "[]").execute()
            return result.data
        except Exception as e:
            print(f"공유한 일정 조회 오류: {str(e)}")
            return [] 