import json
from datetime import datetime
from typing import Dict, Any, Optional
from openai import OpenAI
from config import settings


class GPTService:
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            print("⚠️  경고: OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인해주세요.")
            self.client = None
        else:
            try:
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
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
                model="gpt-4",
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
                temperature=0.3,
                max_tokens=1000
            )
            
            # 응답 파싱
            result = response.choices[0].message.content
            
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
통화 내용을 분석하여 참석자별 일정 정보를 추출해주세요.

현재 시간: {current_date_str} ({current_weekday}) {current_time_str}

통화 내용:
{content}

다음 JSON 형식으로 응답해주세요:
{{
    "participants": [
        {{
            "name": "참석자 이름",
            "role": "역할/직책 (없으면 null)"
        }}
    ],
    "schedules": [
        {{
            "summary": "일정 제목",
            "description": "일정 상세 설명",
            "location": "장소 (없으면 '미정')",
            "startdate": "YYYY-MM-DD HH:MM",
            "enddate": "YYYY-MM-DD HH:MM",
            "assignees": ["담당자 이름들"]
        }}
    ]
}}

규칙:
- 참석자: 통화 언급된 모든 사람
- 일정: 논의된 활동별로 분리
- 날짜: 상대 표현은 현재 시간 기준 계산
- 시간: 미언급시 업무시간(09:00-18:00) 적용
- 한국어 응답 필수
"""
    
    def _validate_and_format_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """결과를 검증하고 포맷팅합니다."""
        # participants 필드 확인 및 기본값 설정
        if "participants" not in result or not isinstance(result["participants"], list):
            result["participants"] = [{"name": "미확인", "email": None, "role": None}]
        
        # schedules 필드 확인 및 기본값 설정
        if "schedules" not in result or not isinstance(result["schedules"], list):
            result["schedules"] = [self._create_default_schedule()]
        
        # 각 일정 검증 - 5개 핵심 필드만
        for schedule in result["schedules"]:
            required_fields = ["summary", "description", "location", "startdate", "enddate", "assignees"]
            
            # 필수 필드 확인
            for field in required_fields:
                if field not in schedule:
                    if field == "assignees":
                        schedule[field] = []
                    else:
                        schedule[field] = "정보 없음"
            
            # 날짜 형식 검증 및 보정
            schedule["startdate"] = self._validate_datetime(schedule["startdate"])
            schedule["enddate"] = self._validate_datetime(schedule["enddate"])
            
            # 종료 시간이 시작 시간보다 빠른 경우 보정
            try:
                start_dt = datetime.strptime(schedule["startdate"], "%Y-%m-%d %H:%M")
                end_dt = datetime.strptime(schedule["enddate"], "%Y-%m-%d %H:%M")
                
                if end_dt <= start_dt:
                    from datetime import timedelta
                    end_dt = start_dt + timedelta(hours=1)
                    schedule["enddate"] = end_dt.strftime("%Y-%m-%d %H:%M")
            except:
                pass
        
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
            "participants": [{"name": "미확인", "email": None, "role": None}],
            "schedules": [self._create_default_schedule()]
        }
    
    def _create_default_schedule(self) -> Dict[str, Any]:
        """기본 일정을 생성합니다."""
        now = datetime.now()
        start_time = now.strftime("%Y-%m-%d %H:%M")
        end_time = (now.replace(hour=now.hour + 1)).strftime("%Y-%m-%d %H:%M")
        
        return {
            "summary": "통화 내용 분석 결과",
            "description": "통화 내용을 분석하여 일정을 생성했습니다.",
            "location": "미정",
            "startdate": start_time,
            "enddate": end_time,
            "assignees": []
        }
    
    def _create_error_result(self, error_message: str) -> Dict[str, Any]:
        """오류 결과를 생성합니다."""
        error_schedule = self._create_default_schedule()
        error_schedule["summary"] = "분석 오류"
        error_schedule["description"] = f"통화 내용 분석 중 오류가 발생했습니다: {error_message}"
        
        return {
            "participants": [{"name": "미확인", "email": None, "role": None}],
            "schedules": [error_schedule],
            "error": True
        }
    
    async def generate_ics_content(self, analysis_result: Dict[str, Any]) -> str:
        """
        분석 결과를 ICS 포맷으로 변환합니다.
        
        Args:
            analysis_result: 분석 결과 딕셔너리
            
        Returns:
            ICS 포맷 문자열
        """
        try:
            # 날짜 파싱
            start_dt = datetime.strptime(analysis_result["startdate"], "%Y-%m-%d %H:%M")
            end_dt = datetime.strptime(analysis_result["enddate"], "%Y-%m-%d %H:%M")
            
            # ICS 날짜 형식으로 변환
            start_ics = start_dt.strftime("%Y%m%dT%H%M%S")
            end_ics = end_dt.strftime("%Y%m%dT%H%M%S")
            
            # 고유 UID 생성
            uid = f"{start_ics}@mufi.com"
            
            # ICS 내용 생성
            ics_content = f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MUFI//MUFI Calendar//KR
BEGIN:VEVENT
UID:{uid}
DTSTART:{start_ics}
DTEND:{end_ics}
SUMMARY:{analysis_result['summary']}
DESCRIPTION:{analysis_result['description']}
LOCATION:{analysis_result['location']}
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""
            
            return ics_content
            
        except Exception as e:
            print(f"ICS 생성 중 오류 발생: {e}")
            return self._create_default_ics()
    
    def _create_default_ics(self) -> str:
        """기본 ICS 내용을 생성합니다."""
        now = datetime.now()
        start_ics = now.strftime("%Y%m%dT%H%M%S")
        end_ics = (now.replace(hour=now.hour + 1)).strftime("%Y%m%dT%H%M%S")
        
        return f"""BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//MUFI//MUFI Calendar//KR
BEGIN:VEVENT
UID:{start_ics}@mufi.com
DTSTART:{start_ics}
DTEND:{end_ics}
SUMMARY:통화 분석 결과
DESCRIPTION:통화 내용을 분석하여 생성된 일정입니다.
LOCATION:미정
STATUS:CONFIRMED
TRANSP:OPAQUE
END:VEVENT
END:VCALENDAR"""


# 싱글톤 인스턴스
gpt_service = GPTService() 