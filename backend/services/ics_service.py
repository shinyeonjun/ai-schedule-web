"""
ICS (iCalendar) Service for generating and managing calendar files
"""
import os
import tempfile
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import uuid4
import logging

from config.config import settings
from supabase import create_client

logger = logging.getLogger(__name__)


class ICSService:
    """Service for generating and managing ICS calendar files"""
    
    def __init__(self):
        # Supabase 클라이언트 직접 생성
        self.supabase = create_client(settings.supabase_url, settings.supabase_service_key)
    
    def generate_ics_content(self, schedules: List[Dict[str, Any]], title: str = "MUFI 분석 일정") -> str:
        """
        일정 목록을 ICS 포맷으로 변환합니다.
        
        Args:
            schedules: 일정 데이터 리스트
            title: 캘린더 제목
            
        Returns:
            ICS 포맷 문자열
        """
        try:
            # ICS 헤더
            ics_content = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//MUFI//MUFI Calendar//KR",
                f"X-WR-CALNAME:{title}",
                "X-WR-TIMEZONE:Asia/Seoul",
                "CALSCALE:GREGORIAN",
                "METHOD:PUBLISH"
            ]
            
            # 각 일정을 VEVENT로 변환
            for schedule in schedules:
                event_lines = self._create_vevent(schedule)
                ics_content.extend(event_lines)
            
            # ICS 푸터
            ics_content.append("END:VCALENDAR")
            
            return "\r\n".join(ics_content)
            
        except Exception as e:
            logger.error(f"ICS 생성 중 오류 발생: {e}")
            return self._create_default_ics(title)
    
    def _create_vevent(self, schedule: Dict[str, Any]) -> List[str]:
        """단일 일정을 VEVENT 형식으로 변환"""
        try:
            # 필수 필드 확인 및 기본값 설정
            summary = schedule.get('title', schedule.get('summary', '제목 없음'))
            description = schedule.get('description', '')
            location = schedule.get('location', '')
            
            # 날짜/시간 파싱 (DB의 start_datetime, end_datetime 필드 우선 사용)
            start_datetime_str = schedule.get('start_datetime')
            end_datetime_str = schedule.get('end_datetime')
            
            if start_datetime_str:
                start_dt = self._parse_db_datetime(start_datetime_str)
            else:
                # 호환성을 위한 기존 방식
                start_dt = self._parse_datetime(schedule.get('start_date'), schedule.get('start_time', '09:00'))
            
            if end_datetime_str:
                end_dt = self._parse_db_datetime(end_datetime_str)
            else:
                # 호환성을 위한 기존 방식
                end_dt = self._parse_datetime(schedule.get('end_date'), schedule.get('end_time', '10:00'))
            
            # 종료 시간이 시작 시간보다 이전이면 1시간 후로 설정
            if end_dt <= start_dt:
                end_dt = start_dt.replace(hour=min(start_dt.hour + 1, 23))
            
            # ICS 날짜 형식으로 변환
            start_ics = start_dt.strftime("%Y%m%dT%H%M%S")
            end_ics = end_dt.strftime("%Y%m%dT%H%M%S")
            created_ics = datetime.now().strftime("%Y%m%dT%H%M%S")
            
            # 고유 UID 생성
            uid = f"{uuid4()}@mufi.com"
            
            # VEVENT 생성
            vevent = [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{created_ics}",
                f"DTSTART:{start_ics}",
                f"DTEND:{end_ics}",
                f"SUMMARY:{self._escape_ics_text(summary)}",
                f"CREATED:{created_ics}",
                f"LAST-MODIFIED:{created_ics}",
                "STATUS:CONFIRMED",
                "TRANSP:OPAQUE"
            ]
            
            # 선택적 필드 추가
            if description:
                vevent.append(f"DESCRIPTION:{self._escape_ics_text(description)}")
            
            if location:
                vevent.append(f"LOCATION:{self._escape_ics_text(location)}")
            
            # 참석자 정보 추가
            participants = schedule.get('participants', [])
            if participants:
                for participant in participants:
                    if isinstance(participant, dict):
                        name = participant.get('name', '')
                        email = participant.get('email', '')
                        if email:
                            vevent.append(f"ATTENDEE;CN={name}:mailto:{email}")
                        elif name:
                            vevent.append(f"ATTENDEE;CN={name}:mailto:noreply@mufi.com")
                    elif isinstance(participant, str):
                        vevent.append(f"ATTENDEE;CN={participant}:mailto:noreply@mufi.com")
            
            vevent.append("END:VEVENT")
            
            return vevent
            
        except Exception as e:
            logger.error(f"VEVENT 생성 중 오류: {e}")
            return self._create_default_vevent()
    
    def _parse_db_datetime(self, datetime_str: str) -> datetime:
        """DB에서 저장된 datetime 문자열을 파싱"""
        try:
            print(f"🔍 DB datetime 파싱 시도: {datetime_str}")
            
            # ISO 형식 시도 (DB에서 저장된 형식)
            iso_formats = [
                "%Y-%m-%dT%H:%M:%S%z",       # 2025-08-05T09:00:00+09:00
                "%Y-%m-%dT%H:%M:%S",         # 2025-08-05T09:00:00
                "%Y-%m-%d %H:%M:%S",         # 2025-08-05 09:00:00
                "%Y-%m-%d %H:%M",            # 2025-08-05 09:00
                "%Y-%m-%dT%H:%M",            # 2025-08-05T09:00
            ]
            
            for fmt in iso_formats:
                try:
                    parsed_dt = datetime.strptime(datetime_str, fmt)
                    print(f"✅ DB datetime 파싱 성공: {parsed_dt} (형식: {fmt})")
                    return parsed_dt
                except ValueError:
                    continue
            
            # 파싱 실패시 현재 시간 반환
            print(f"❌ DB datetime 파싱 실패, 현재 시간 사용: {datetime_str}")
            return datetime.now()
            
        except Exception as e:
            print(f"❌ DB datetime 파싱 오류: {e}")
            return datetime.now()

    def _parse_datetime(self, date_str: Optional[str], time_str: Optional[str] = None) -> datetime:
        """날짜 문자열을 datetime 객체로 변환"""
        try:
            if not date_str:
                return datetime.now()
            
            # 다양한 날짜 형식 지원
            date_formats = [
                "%Y-%m-%d",
                "%Y/%m/%d", 
                "%m/%d/%Y",
                "%d/%m/%Y",
                "%Y.%m.%d",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%d %H:%M"
            ]
            
            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
            
            if not parsed_date:
                # 기본값으로 오늘 날짜 사용
                parsed_date = datetime.now()
            
            # 시간 정보가 별도로 있으면 적용
            if time_str and not any(fmt for fmt in ["%H:%M:%S", "%H:%M"] if fmt in date_formats):
                try:
                    time_parts = time_str.split(':')
                    hour = int(time_parts[0])
                    minute = int(time_parts[1]) if len(time_parts) > 1 else 0
                    parsed_date = parsed_date.replace(hour=hour, minute=minute, second=0)
                except (ValueError, IndexError):
                    pass
            
            return parsed_date
            
        except Exception as e:
            logger.error(f"날짜 파싱 오류: {e}")
            return datetime.now()
    
    def _escape_ics_text(self, text: str) -> str:
        """ICS 텍스트 이스케이프 처리"""
        if not text:
            return ""
        
        # ICS 표준에 따른 이스케이프 처리
        text = str(text)
        text = text.replace("\\", "\\\\")
        text = text.replace(";", "\\;")
        text = text.replace(",", "\\,")
        text = text.replace("\n", "\\n")
        text = text.replace("\r", "")
        
        # 라인 길이 제한 (75자)
        if len(text) > 70:
            lines = []
            while text:
                if len(text) <= 70:
                    lines.append(text)
                    break
                else:
                    lines.append(text[:70])
                    text = " " + text[70:]  # 다음 줄은 공백으로 시작
            text = "\r\n".join(lines)
        
        return text
    
    def _create_default_vevent(self) -> List[str]:
        """기본 VEVENT 생성"""
        now = datetime.now()
        start_ics = now.strftime("%Y%m%dT%H%M%S")
        end_ics = (now.replace(hour=min(now.hour + 1, 23))).strftime("%Y%m%dT%H%M%S")
        uid = f"{uuid4()}@mufi.com"
        
        return [
            "BEGIN:VEVENT",
            f"UID:{uid}",
            f"DTSTAMP:{start_ics}",
            f"DTSTART:{start_ics}",
            f"DTEND:{end_ics}",
            "SUMMARY:분석 오류",
            "DESCRIPTION:일정 분석 중 오류가 발생했습니다.",
            "STATUS:CONFIRMED",
            "END:VEVENT"
        ]
    
    def _create_default_ics(self, title: str = "MUFI 분석 일정") -> str:
        """기본 ICS 내용 생성"""
        vevent = self._create_default_vevent()
        
        ics_content = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//MUFI//MUFI Calendar//KR",
            f"X-WR-CALNAME:{title}",
            "CALSCALE:GREGORIAN"
        ]
        
        ics_content.extend(vevent)
        ics_content.append("END:VCALENDAR")
        
        return "\r\n".join(ics_content)
    
    async def save_ics_to_storage(self, ics_content: str, filename: str, user_id: str, analysis_id: str = None) -> Dict[str, Any]:
        """
        ICS 내용을 Supabase Storage에 저장합니다.
        
        Args:
            ics_content: ICS 파일 내용
            filename: 파일명
            user_id: 사용자 ID
            analysis_id: 분석 ID (통화별 폴더 구분용)
            
        Returns:
            저장 결과 딕셔너리
        """
        try:
            # 파일명에 .ics 확장자가 없으면 추가
            if not filename.endswith('.ics'):
                filename += '.ics'
            
            # 통화별 폴더 경로 구조
            if analysis_id:
                file_path = f"users/{user_id}/{analysis_id}/{filename}"
                print(f"📁 통화별 ICS 저장 경로: {file_path}")
            else:
                # 기존 호환성을 위한 fallback
                file_path = f"users/{user_id}/ics/{filename}"
                print(f"📁 기본 ICS 저장 경로: {file_path}")
            
            # Supabase Storage에 업로드
            result = self.supabase.storage.from_("schedules").upload(
                file_path,
                ics_content.encode('utf-8'),
                {
                    "content-type": "text/calendar",
                    "x-upsert": "true"  # 같은 이름의 파일이 있으면 덮어쓰기
                }
            )
            
            if hasattr(result, 'error') and result.error:
                raise Exception(f"Storage 업로드 실패: {result.error}")
            
            # 공개 URL 생성
            public_url_response = self.supabase.storage.from_("schedules").get_public_url(file_path)
            
            return {
                "success": True,
                "file_path": file_path,
                "public_url": public_url_response if isinstance(public_url_response, str) else public_url_response.get("publicURL", ""),
                "filename": filename,
                "size": len(ics_content.encode('utf-8'))
            }
            
        except Exception as e:
            logger.error(f"ICS 파일 저장 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    async def generate_and_save_ics(self, schedules: List[Dict[str, Any]], user_id: str, title: str = None, analysis_id: str = None) -> Dict[str, Any]:
        """
        일정 목록으로부터 ICS를 생성하고 저장합니다.
        
        Args:
            schedules: 일정 데이터 리스트
            user_id: 사용자 ID  
            title: 캘린더 제목
            analysis_id: 분석 ID (통화별 폴더 구분용)
            
        Returns:
            생성 및 저장 결과
        """
        try:
            # 제목 생성
            if not title:
                title = f"MUFI 분석 일정 - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # ICS 내용 생성
            ics_content = self.generate_ics_content(schedules, title)
            
            # 파일명 생성
            if analysis_id:
                filename = f"schedule_{schedules[0].get('id', 'unknown')}.ics"
            else:
                filename = f"mufi_schedules_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ics"
            
            # Storage에 저장
            save_result = await self.save_ics_to_storage(ics_content, filename, user_id, analysis_id)
            
            return {
                "ics_content": ics_content,
                "title": title,
                "schedules_count": len(schedules),
                **save_result
            }
            
        except Exception as e:
            logger.error(f"ICS 생성 및 저장 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "schedules_count": len(schedules) if schedules else 0
            }