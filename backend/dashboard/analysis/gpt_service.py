import json
from datetime import datetime
from typing import Dict, Any, Optional
from openai import OpenAI
from ..config.config import settings


class GPTService:
    def __init__(self):
        if not settings.openai_api_key:
            print("⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=settings.openai_api_key)
            except Exception as e:
                print(f"⚠️  OpenAI 클라이언트 초기화 실패: {e}")
                self.client = None
        
    async def analyze_call_content(self, content: str) -> Dict[str, Any]:
        """
        통화 내용을 분석하여 일정 정보를 추출합니다.
        
        Args:
            content: 통화 내용 텍스트
            
        Returns:
            분석 결과 딕셔너리 (participants, schedules)
        """
        # OpenAI 클라이언트 확인
        if not self.client:
            print("⚠️  OpenAI 클라이언트가 초기화되지 않았습니다. 기본값을 반환합니다.")
            return self._create_default_result()
            
        try:
            # GPT 프롬프트 구성
            prompt = self._create_analysis_prompt(content)
            
            # GPT API 호출
            response = self.client.chat.completions.create(
                model=settings.openai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "당신은 통화 내용을 분석하여 일정 정보를 추출하는 AI 어시스턴트입니다. 항상 JSON 형식으로 응답해주세요."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=settings.openai_temperature,
                max_tokens=settings.openai_max_tokens
            )
            
            # 응답 파싱
            result = response.choices[0].message.content
            
            # 🔍 GPT 원문 응답 터미널 출력
            print("\n" + "="*80)
            print("🤖 GPT 분석 결과 원문:")
            print("="*80)
            print(result)
            print("="*80 + "\n")
            
            # JSON 파싱 시도
            try:
                parsed_result = json.loads(result)
                return self._validate_and_format_result(parsed_result)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 기본값 반환
                return self._create_default_result()
                
        except Exception as e:
            print(f"GPT 분석 중 오류 발생: {e}")
            return self._create_error_result(str(e))
    
    def _create_analysis_prompt(self, content: str) -> str:
        """분석용 프롬프트를 생성합니다."""
        # 현재 시간 정보 추가
        current_time = datetime.now()
        current_date_str = current_time.strftime("%Y년 %m월 %d일")
        current_time_str = current_time.strftime("%H시 %M분")
        current_weekday = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"][current_time.weekday()]
        
        return f"""
통화 내용을 분석하여 참석자, 요약, 일정 정보를 추출해주세요.

현재 시간: {current_date_str} ({current_weekday}) {current_time_str}

통화 내용:
{content}

분석 지침:
1. 단체일정(group): 여러 명이 함께 참여하는 회의, 미팅, 이벤트 (participants에 참여자 이름들 포함)
2. 개인일정(personal): 특정 개인에게 할당된 업무, 작업 (participants에 담당자 이름만 포함)

다음 JSON 형식으로 응답해주세요:
{{
    "group": [
        {{
            "title": "단체일정 제목",
            "description": "단체일정 상세 설명",
            "location": "장소 (없으면 '미정')",
            "start_datetime": "YYYY-MM-DD HH:MM",
            "end_datetime": "YYYY-MM-DD HH:MM",
            "participants": ["참여자1 이름", "참여자2 이름"]
        }}
    ],
    "personal": [
        {{
            "title": "개인일정 제목",
            "description": "개인일정 상세 설명",
            "location": "장소 (개인일정은 보통 '미정')",
            "start_datetime": "YYYY-MM-DD HH:MM",
            "end_datetime": "YYYY-MM-DD HH:MM",
            "participants": ["담당자 이름"]
        }}
    ]
}}

규칙:
- 참석자: 통화 언급된 모든 사람
- 일정: 논의된 활동별로 분리
- 날짜: 상대 표현은 현재 시간 기준 계산
- 시간: 최대한 텍스트 내에서 분석 후 추출 후 적용
- 한국어 응답 필수
- 대화의 흐름을 잘 파악하여 중요한 일정을 위주로 분석해주세요*중요!*
"""
    
    def _validate_and_format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """결과를 검증하고 포맷팅합니다."""
        print("🔍 GPT 응답 그대로 사용")
        
        # GPT가 반환한 JSON을 그대로 사용
        print(f"🔍 GPT 반환 결과: {result}")
        
        # GPT 응답을 그대로 반환
        return result
    
    def _validate_datetime(self, datetime_str: str) -> str:
        """날짜 시간 문자열을 검증하고 포맷팅합니다."""
        try:
            # 다양한 형식 시도
            formats = [
                "%Y-%m-%d %H:%M",
                "%Y-%m-%d %H:%M:%S",
                "%Y/%m/%d %H:%M",
                "%Y.%m.%d %H:%M"
            ]
            
            for fmt in formats:
                try:
                    dt = datetime.strptime(datetime_str, fmt)
                    return dt.strftime("%Y-%m-%d %H:%M")
                except ValueError:
                    continue
            
            # 파싱 실패 시 현재 시간 기준으로 설정
            return datetime.now().strftime("%Y-%m-%d %H:%M")
            
        except:
            return datetime.now().strftime("%Y-%m-%d %H:%M")
    
    def _create_default_result(self) -> Dict[str, Any]:
        """기본 결과를 생성합니다."""
        return {
            "participants": [{"name": "미확인", "role": None}],
            "schedules": [self._create_default_schedule()],
            "actions": []
        }
    
    def _create_default_schedule(self, schedule_type: str = "group") -> Dict[str, Any]:
        """기본 일정을 생성합니다."""
        now = datetime.now()
        start_time = now.strftime("%Y-%m-%d %H:%M")
        end_time = (now.replace(hour=now.hour + 1)).strftime("%Y-%m-%d %H:%M")
        
        if schedule_type == "personal":
            title = "개인일정"
            description = "통화에서 논의된 개인 담당 업무입니다."
        else:
            title = "단체일정"
            description = "통화에서 논의된 단체 일정입니다."
        
        return {
            "title": title,
            "description": description,
            "location": "미정",
            "start_datetime": start_time,
            "end_datetime": end_time
        }
    
    def _validate_schedule_fields(self, schedule: Dict[str, Any], schedule_type: str) -> None:
        """일정 필드를 검증하고 보정합니다."""
        required_fields = ["title", "description", "location", "start_datetime", "end_datetime", "participants"]
        
        # 필수 필드 확인
        for field in required_fields:
            if field not in schedule:
                if field in ["start_datetime", "end_datetime"]:
                    schedule[field] = datetime.now().strftime("%Y-%m-%d %H:%M")
                elif field == "participants":
                    schedule[field] = ["미확인"]
                else:
                    schedule[field] = "정보 없음"
        
        # participants 필드 검증
        if not isinstance(schedule["participants"], list):
            schedule["participants"] = ["미확인"]
        elif len(schedule["participants"]) == 0:
            schedule["participants"] = ["미확인"]
        
        # 날짜 형식 검증 및 보정
        schedule["start_datetime"] = self._validate_datetime(schedule["start_datetime"])
        schedule["end_datetime"] = self._validate_datetime(schedule["end_datetime"])
        
        # 종료 시간이 시작 시간보다 빠른 경우 보정
        try:
            start_dt = datetime.strptime(schedule["start_datetime"], "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(schedule["end_datetime"], "%Y-%m-%d %H:%M")
            
            if end_dt <= start_dt:
                from datetime import timedelta
                end_dt = start_dt + timedelta(hours=1)
                schedule["end_datetime"] = end_dt.strftime("%Y-%m-%d %H:%M")
        except:
            pass
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """오류 결과를 생성합니다."""
        error_schedule = self._create_default_schedule()
        error_schedule["title"] = "분석 오류"
        error_schedule["description"] = f"통화 내용 분석 중 오류가 발생했습니다: {error_message}"
        
        return {
            "participants": [{"name": "미확인", "role": None}],
            "schedules": [error_schedule],
            "actions": [],
            "error": True
        }
    
# 싱글톤 인스턴스
gpt_service = GPTService() 