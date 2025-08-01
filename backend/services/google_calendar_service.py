"""
Google Calendar API 서비스
OAuth 2.0을 통해 사용자의 Google Calendar에 ICS 파일 내용을 자동으로 추가합니다.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)

class GoogleCalendarService:
    def __init__(self):
        """Google Calendar 서비스 초기화"""
        self.scopes = ['https://www.googleapis.com/auth/calendar']
        self.client_config = {
            "web": {
                "client_id": "YOUR_CLIENT_ID",  # Google Console에서 설정
                "client_secret": "YOUR_CLIENT_SECRET",  # Google Console에서 설정
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost:8000/auth/google/callback"]
            }
        }
    
    def get_auth_url(self, user_id: str) -> str:
        """
        Google OAuth 인증 URL을 생성합니다.
        
        Args:
            user_id: 사용자 ID (상태 정보로 사용)
            
        Returns:
            Google OAuth 인증 URL
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri="http://localhost:8000/auth/google/callback"
            )
            
            # 상태 정보에 user_id 포함
            flow.state = user_id
            
            auth_url, _ = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )
            
            return auth_url
            
        except Exception as e:
            logger.error(f"Google OAuth URL 생성 실패: {e}")
            raise Exception(f"인증 URL 생성 중 오류 발생: {str(e)}")
    
    def handle_oauth_callback(self, authorization_code: str, state: str) -> Dict[str, Any]:
        """
        OAuth 콜백을 처리하고 액세스 토큰을 획득합니다.
        
        Args:
            authorization_code: Google에서 반환한 인증 코드
            state: 사용자 ID
            
        Returns:
            토큰 정보와 사용자 정보
        """
        try:
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.scopes,
                redirect_uri="http://localhost:8000/auth/google/callback"
            )
            
            # 인증 코드로 토큰 교환
            flow.fetch_token(code=authorization_code)
            
            credentials = flow.credentials
            
            # 사용자 정보 가져오기 (선택사항)
            service = build('calendar', 'v3', credentials=credentials)
            calendar_list = service.calendarList().list().execute()
            
            return {
                "success": True,
                "user_id": state,
                "access_token": credentials.token,
                "refresh_token": credentials.refresh_token,
                "token_uri": credentials.token_uri,
                "client_id": credentials.client_id,
                "client_secret": credentials.client_secret,
                "scopes": credentials.scopes,
                "expiry": credentials.expiry.isoformat() if credentials.expiry else None,
                "calendar_count": len(calendar_list.get('items', []))
            }
            
        except Exception as e:
            logger.error(f"Google OAuth 콜백 처리 실패: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def add_ics_to_calendar(self, credentials_data: Dict[str, Any], ics_content: str, calendar_id: str = 'primary') -> Dict[str, Any]:
        """
        ICS 내용을 Google Calendar에 추가합니다.
        
        Args:
            credentials_data: Google OAuth 인증 정보
            ics_content: ICS 파일 내용
            calendar_id: 대상 캘린더 ID (기본값: 'primary')
            
        Returns:
            추가 결과
        """
        try:
            # 크리덴셜 재구성
            credentials = Credentials(
                token=credentials_data.get('access_token'),
                refresh_token=credentials_data.get('refresh_token'),
                token_uri=credentials_data.get('token_uri'),
                client_id=credentials_data.get('client_id'),
                client_secret=credentials_data.get('client_secret'),
                scopes=credentials_data.get('scopes')
            )
            
            # Google Calendar 서비스 생성
            service = build('calendar', 'v3', credentials=credentials)
            
            # ICS 내용을 파싱하여 개별 이벤트 추출
            events = self._parse_ics_content(ics_content)
            
            added_events = []
            failed_events = []
            
            for event_data in events:
                try:
                    # Google Calendar 이벤트 형식으로 변환
                    google_event = self._convert_to_google_event(event_data)
                    
                    # 캘린더에 이벤트 추가
                    created_event = service.events().insert(
                        calendarId=calendar_id,
                        body=google_event
                    ).execute()
                    
                    added_events.append({
                        "title": google_event.get('summary', '제목 없음'),
                        "event_id": created_event.get('id'),
                        "html_link": created_event.get('htmlLink')
                    })
                    
                    logger.info(f"이벤트 추가 성공: {google_event.get('summary', '제목 없음')}")
                    
                except HttpError as e:
                    error_msg = f"이벤트 추가 실패: {event_data.get('summary', '제목 없음')} - {str(e)}"
                    logger.error(error_msg)
                    failed_events.append({
                        "title": event_data.get('summary', '제목 없음'),
                        "error": str(e)
                    })
                    continue
            
            return {
                "success": True,
                "total_events": len(events),
                "added_count": len(added_events),
                "failed_count": len(failed_events),
                "added_events": added_events,
                "failed_events": failed_events,
                "calendar_id": calendar_id
            }
            
        except Exception as e:
            logger.error(f"Google Calendar 추가 실패: {e}")
            return {
                "success": False,
                "error": f"ICS 파일 처리 중 오류 발생: {str(e)}",
                "total_events": 0,
                "added_count": 0,
                "failed_count": 0,
                "error_type": "parsing_failed"
            }
    
    def _parse_ics_content(self, ics_content: str) -> List[Dict[str, Any]]:
        """
        ICS 내용을 파싱하여 JSON 이벤트 리스트로 변환합니다.
        
        Args:
            ics_content: ICS 파일 내용
            
        Returns:
            JSON 형태로 파싱된 이벤트 리스트
        """
        events = []
        current_event = {}
        in_event = False
        
        print(f"🔍 ICS 파싱 시작, 총 라인 수: {len(ics_content.split('\\n'))}")
        
        for line_num, line in enumerate(ics_content.split('\n'), 1):
            line = line.strip()
            
            if line == 'BEGIN:VEVENT':
                in_event = True
                current_event = {}
                print(f"📅 이벤트 시작 (라인 {line_num})")
                
            elif line == 'END:VEVENT':
                if current_event:
                    # 기본값 설정
                    if 'summary' not in current_event:
                        current_event['summary'] = '제목 없음'
                    if 'description' not in current_event:
                        current_event['description'] = ''
                    if 'location' not in current_event:
                        current_event['location'] = ''
                    
                    # 시간 정보 검증
                    if 'start' not in current_event:
                        # 기본 시작 시간 설정 (현재 시간)
                        now = datetime.now()
                        current_event['start'] = {
                            'dateTime': now.isoformat() + '+09:00',
                            'timeZone': 'Asia/Seoul'
                        }
                    
                    if 'end' not in current_event:
                        # 시작 시간 + 1시간으로 종료 시간 설정
                        if 'dateTime' in current_event['start']:
                            start_dt = datetime.fromisoformat(current_event['start']['dateTime'].replace('+09:00', ''))
                            end_dt = start_dt + timedelta(hours=1)
                            current_event['end'] = {
                                'dateTime': end_dt.isoformat() + '+09:00',
                                'timeZone': 'Asia/Seoul'
                            }
                        else:
                            current_event['end'] = current_event['start'].copy()
                    
                    events.append(current_event)
                    print(f"✅ 이벤트 파싱 완료: {current_event.get('summary', '제목 없음')}")
                    
                in_event = False
                current_event = {}
                
            elif in_event and ':' in line:
                try:
                    # RFC 5545 형식 처리 (PROPERTY;PARAM=value:data)
                    if ';' in line.split(':', 1)[0]:
                        # 매개변수가 있는 경우
                        prop_part, value = line.split(':', 1)
                        prop_name = prop_part.split(';')[0]
                        params = prop_part.split(';')[1:] if ';' in prop_part else []
                    else:
                        # 단순한 경우
                        prop_name, value = line.split(':', 1)
                        params = []
                    
                    # 속성별 처리
                    if prop_name == 'SUMMARY':
                        current_event['summary'] = self._decode_ics_text(value)
                        
                    elif prop_name == 'DESCRIPTION':
                        current_event['description'] = self._decode_ics_text(value)
                        
                    elif prop_name == 'LOCATION':
                        current_event['location'] = self._decode_ics_text(value)
                        
                    elif prop_name == 'DTSTART':
                        current_event['start'] = self._parse_ics_datetime(value, params)
                        
                    elif prop_name == 'DTEND':
                        current_event['end'] = self._parse_ics_datetime(value, params)
                        
                    elif prop_name == 'UID':
                        current_event['uid'] = value
                        
                    elif prop_name == 'CREATED':
                        current_event['created'] = self._parse_ics_datetime(value, params)
                        
                    elif prop_name == 'LAST-MODIFIED':
                        current_event['updated'] = self._parse_ics_datetime(value, params)
                        
                    elif prop_name == 'STATUS':
                        current_event['status'] = value.lower()
                        
                    elif prop_name == 'TRANSP':
                        # 투명도 → 사용 가능 시간 표시
                        current_event['transparency'] = 'transparent' if value == 'TRANSPARENT' else 'opaque'
                        
                    elif prop_name == 'CLASS':
                        # 공개 수준
                        visibility_map = {
                            'PUBLIC': 'public',
                            'PRIVATE': 'private', 
                            'CONFIDENTIAL': 'confidential'
                        }
                        current_event['visibility'] = visibility_map.get(value, 'default')
                        
                except Exception as parse_error:
                    error_msg = f"ICS 라인 파싱 실패 (라인 {line_num}): '{line}' - {str(parse_error)}"
                    print(f"❌ {error_msg}")
                    logger.error(error_msg)
                    raise ValueError(f"ICS 파싱 실패: {error_msg}")
        
        # 파싱 결과 검증
        if not events:
            error_msg = "ICS 파일에서 유효한 이벤트를 찾을 수 없습니다"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        print(f"🎉 ICS 파싱 완료: 총 {len(events)}개 이벤트 추출")
        return events
    
    def _parse_ics_datetime(self, dt_string: str, params: List[str] = None) -> Dict[str, str]:
        """
        ICS 날짜/시간 문자열을 Google Calendar JSON 형식으로 변환합니다.
        
        Args:
            dt_string: ICS 날짜/시간 문자열 (예: 20250801T143000, 20250801T143000Z, 20250801)
            params: ICS 매개변수 리스트 (예: ['TZID=Asia/Seoul'])
            
        Returns:
            Google Calendar 날짜/시간 JSON 형식
        """
        if params is None:
            params = []
            
        try:
            # 타임존 정보 추출
            timezone = 'Asia/Seoul'  # 기본값
            for param in params:
                if param.startswith('TZID='):
                    timezone = param.split('=', 1)[1]
                    break
            
            # UTC 시간인지 확인 (Z 접미사)
            is_utc = dt_string.endswith('Z')
            if is_utc:
                dt_string = dt_string[:-1]  # Z 제거
                timezone = 'UTC'
            
            print(f"📅 날짜 파싱: {dt_string}, 타임존: {timezone}")
            
            if 'T' in dt_string:
                # 날짜와 시간이 있는 경우
                try:
                    # 일반적인 형식: 20250801T143000
                    dt = datetime.strptime(dt_string, '%Y%m%dT%H%M%S')
                except ValueError:
                    try:
                        # 초가 포함된 형식: 20250801T143000
                        dt = datetime.strptime(dt_string, '%Y%m%dT%H%M%S')
                    except ValueError:
                        # 다른 형식 시도
                        dt = datetime.strptime(dt_string.replace('-', '').replace(':', ''), '%Y%m%dT%H%M%S')
                
                # UTC인 경우 KST로 변환
                if is_utc:
                    import pytz
                    utc = pytz.timezone('UTC')
                    kst = pytz.timezone('Asia/Seoul')
                    dt = utc.localize(dt).astimezone(kst)
                    timezone = 'Asia/Seoul'
                
                return {
                    'dateTime': dt.isoformat() + ('+09:00' if timezone == 'Asia/Seoul' else '+00:00'),
                    'timeZone': timezone
                }
            else:
                # 날짜만 있는 경우 (종일 이벤트)
                try:
                    dt = datetime.strptime(dt_string, '%Y%m%d')
                except ValueError:
                    # 다른 날짜 형식 시도
                    dt = datetime.strptime(dt_string.replace('-', ''), '%Y%m%d')
                
                return {
                    'date': dt.strftime('%Y-%m-%d')
                }
                
        except Exception as e:
            # 파싱 실패 시 예외 발생
            error_msg = f"날짜/시간 파싱 실패: '{dt_string}' (params: {params}) - {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _decode_ics_text(self, text: str) -> str:
        """
        ICS 텍스트 인코딩을 디코딩합니다.
        
        Args:
            text: 인코딩된 ICS 텍스트
            
        Returns:
            디코딩된 텍스트
        """
        if not text:
            return ""
        
        try:
            # RFC 5545에 따른 이스케이프 처리
            text = text.replace('\\\\n', '\n')  # 줄바꿈
            text = text.replace('\\\\,', ',')   # 쉼표
            text = text.replace('\\\\;', ';')   # 세미콜론
            text = text.replace('\\\\\\\\', '\\\\')  # 백슬래시
            
            # URL 디코딩 (필요한 경우)
            if '%' in text:
                import urllib.parse
                text = urllib.parse.unquote(text)
            
            return text.strip()
            
        except Exception as e:
            error_msg = f"텍스트 디코딩 실패: '{text}' - {str(e)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _convert_to_google_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        파싱된 JSON 이벤트를 Google Calendar API 형식으로 최종 변환합니다.
        
        Args:
            event_data: 파싱된 JSON 이벤트 데이터
            
        Returns:
            Google Calendar API 완전 호환 JSON 형식
        """
        
        # 기본 이벤트 구조
        google_event = {
            'summary': event_data.get('summary', '제목 없음'),
            'description': event_data.get('description', ''),
            'location': event_data.get('location', ''),
            'start': event_data.get('start', {}),
            'end': event_data.get('end', {}),
            'source': {
                'title': 'MUFI 분석 시스템',
                'url': 'http://localhost:8000'
            }
        }
        
        # 추가 속성들
        if 'uid' in event_data:
            google_event['iCalUID'] = event_data['uid']
            
        if 'status' in event_data:
            # ICS 상태를 Google Calendar 상태로 매핑
            status_map = {
                'tentative': 'tentative',
                'confirmed': 'confirmed', 
                'cancelled': 'cancelled'
            }
            google_event['status'] = status_map.get(event_data['status'], 'confirmed')
            
        if 'visibility' in event_data:
            google_event['visibility'] = event_data['visibility']
            
        if 'transparency' in event_data:
            google_event['transparency'] = event_data['transparency']
        
        # 시간 검증 및 보정
        if not google_event['start']:
            # 시작 시간이 없으면 현재 시간으로 설정
            now = datetime.now()
            google_event['start'] = {
                'dateTime': now.isoformat() + '+09:00',
                'timeZone': 'Asia/Seoul'
            }
        
        if not google_event['end']:
            # 종료 시간이 없으면 시작 시간 + 1시간으로 설정
            if 'dateTime' in google_event['start']:
                try:
                    start_dt = datetime.fromisoformat(google_event['start']['dateTime'].replace('+09:00', ''))
                    end_dt = start_dt + timedelta(hours=1)
                    google_event['end'] = {
                        'dateTime': end_dt.isoformat() + '+09:00',
                        'timeZone': 'Asia/Seoul'
                    }
                except Exception:
                    # 파싱 실패 시 시작 시간과 동일하게 설정
                    google_event['end'] = google_event['start'].copy()
            elif 'date' in google_event['start']:
                # 종일 이벤트인 경우
                google_event['end'] = google_event['start'].copy()
            else:
                # 기본 종료 시간 설정
                now = datetime.now() + timedelta(hours=1)
                google_event['end'] = {
                    'dateTime': now.isoformat() + '+09:00',
                    'timeZone': 'Asia/Seoul'
                }
        
        # 알림 설정 (기본값)
        google_event['reminders'] = {
            'useDefault': False,
            'overrides': [
                {'method': 'popup', 'minutes': 10}  # 10분 전 알림
            ]
        }
        
        # 이벤트 색상 (MUFI 브랜딩)
        google_event['colorId'] = '9'  # 파란색
        
        print(f"✅ Google Event JSON 변환 완료: {google_event['summary']}")
        print(f"   📅 시작: {google_event['start']}")
        print(f"   📅 종료: {google_event['end']}")
        
        return google_event
    
    def get_user_calendars(self, credentials_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        사용자의 Google Calendar 목록을 가져옵니다.
        
        Args:
            credentials_data: Google OAuth 인증 정보
            
        Returns:
            캘린더 목록
        """
        try:
            # 크리덴셜 재구성
            credentials = Credentials(
                token=credentials_data.get('access_token'),
                refresh_token=credentials_data.get('refresh_token'),
                token_uri=credentials_data.get('token_uri'),
                client_id=credentials_data.get('client_id'),
                client_secret=credentials_data.get('client_secret'),
                scopes=credentials_data.get('scopes')
            )
            
            # Google Calendar 서비스 생성
            service = build('calendar', 'v3', credentials=credentials)
            
            # 캘린더 목록 가져오기
            calendar_list = service.calendarList().list().execute()
            
            calendars = []
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar.get('id'),
                    'summary': calendar.get('summary'),
                    'description': calendar.get('description', ''),
                    'primary': calendar.get('primary', False),
                    'access_role': calendar.get('accessRole', ''),
                    'background_color': calendar.get('backgroundColor', '#ffffff')
                })
            
            return {
                "success": True,
                "calendars": calendars,
                "total_count": len(calendars)
            }
            
        except Exception as e:
            logger.error(f"캘린더 목록 조회 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "calendars": [],
                "total_count": 0
            }