import httpx
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException
from backend.dashboard.auth.google_token_service import GoogleTokenService


class GoogleCalendarService:
    """Google Calendar API 서비스"""
    
    @staticmethod
    async def create_calendar_event(schedule: dict, user_data: dict) -> Optional[Dict[str, Any]]:
        """
        Google Calendar API를 사용하여 일정을 생성합니다.
        """
        try:
            # 사용자 ID 추출
            user_id = int(user_data.get('sub'))
            
            # 유효한 Google 액세스 토큰 가져오기 (자동 갱신 포함)
            access_token = await GoogleTokenService.get_valid_access_token(user_id)
            
            if not access_token:
                print(f"❌ 사용자 {user_id}의 유효한 Google 액세스 토큰이 없습니다.")
                return None
            
            # 일정 데이터 준비
            title = schedule.get('title', '일정')
            description = schedule.get('description', '')
            location = schedule.get('location', '')
            start_datetime = schedule.get('start_datetime')
            end_datetime = schedule.get('end_datetime')
            
            # 시간 형식 변환
            if start_datetime:
                start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
                start_str = start_dt.isoformat()
            else:
                start_str = datetime.now().isoformat()
                
            if end_datetime:
                end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
                end_str = end_dt.isoformat()
            else:
                # 기본적으로 1시간 후
                if start_datetime:
                    end_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00')) + timedelta(hours=1)
                    end_str = end_dt.isoformat()
                else:
                    end_str = (datetime.now() + timedelta(hours=1)).isoformat()
            
            # Google Calendar API 이벤트 데이터
            event_data = {
                'summary': title,
                'description': description,
                'location': location,
                'start': {
                    'dateTime': start_str,
                    'timeZone': 'Asia/Seoul'
                },
                'end': {
                    'dateTime': end_str,
                    'timeZone': 'Asia/Seoul'
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1일 전
                        {'method': 'popup', 'minutes': 15}        # 15분 전
                    ]
                }
            }
            
            print(f"📅 이벤트 데이터: {event_data}")
            
            # Google Calendar API 호출
            calendar_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(calendar_url, json=event_data, headers=headers)
                
                print(f"📡 Google Calendar API 응답: {response.status_code}")
                print(f"📄 응답 내용: {response.text}")
                
                if response.status_code == 200:
                    calendar_event = response.json()
                    print(f"✅ Google Calendar 이벤트 생성 성공: {calendar_event.get('id')}")
                    return {
                        "id": calendar_event.get('id'),
                        "htmlLink": calendar_event.get('htmlLink'),
                        "status": calendar_event.get('status')
                    }
                else:
                    print(f"❌ Google Calendar API 오류: {response.status_code} - {response.text}")
                    # 구체적인 오류 메시지 파싱
                    try:
                        error_data = response.json()
                        error_message = error_data.get('error', {}).get('message', '알 수 없는 오류')
                        print(f"❌ Google API 오류 메시지: {error_message}")
                    except:
                        print(f"❌ Google API 오류 응답 파싱 실패")
                    return None
                
        except Exception as e:
            print(f"❌ Google Calendar 이벤트 생성 오류: {str(e)}")
            return None
    
    @staticmethod
    async def delete_calendar_event(user_id: int, event_id: str) -> bool:
        """
        Google Calendar에서 이벤트를 삭제합니다.
        """
        try:
            # 유효한 Google 액세스 토큰 가져오기
            access_token = await GoogleTokenService.get_valid_access_token(user_id)
            
            if not access_token:
                print(f"❌ 사용자 {user_id}의 유효한 Google 액세스 토큰이 없습니다.")
                return False
            
            # Google Calendar API 호출
            calendar_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.delete(calendar_url, headers=headers)
                
                if response.status_code == 204:
                    print(f"✅ Google Calendar 이벤트 삭제 성공: {event_id}")
                    return True
                else:
                    print(f"❌ Google Calendar 이벤트 삭제 실패: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            print(f"❌ Google Calendar 이벤트 삭제 오류: {str(e)}")
            return False
    
    @staticmethod
    async def update_calendar_event(user_id: int, event_id: str, event_data: dict) -> Optional[Dict[str, Any]]:
        """
        Google Calendar에서 이벤트를 업데이트합니다.
        """
        try:
            # 유효한 Google 액세스 토큰 가져오기
            access_token = await GoogleTokenService.get_valid_access_token(user_id)
            
            if not access_token:
                print(f"❌ 사용자 {user_id}의 유효한 Google 액세스 토큰이 없습니다.")
                return None
            
            # Google Calendar API 호출
            calendar_url = f"https://www.googleapis.com/calendar/v3/calendars/primary/events/{event_id}"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.patch(calendar_url, json=event_data, headers=headers)
                
                if response.status_code == 200:
                    calendar_event = response.json()
                    print(f"✅ Google Calendar 이벤트 업데이트 성공: {event_id}")
                    return {
                        "id": calendar_event.get('id'),
                        "htmlLink": calendar_event.get('htmlLink'),
                        "status": calendar_event.get('status')
                    }
                else:
                    print(f"❌ Google Calendar 이벤트 업데이트 실패: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Google Calendar 이벤트 업데이트 오류: {str(e)}")
            return None
    
    @staticmethod
    async def get_calendar_events(user_id: int, time_min: str = None, time_max: str = None) -> Optional[list]:
        """
        Google Calendar에서 이벤트 목록을 가져옵니다.
        """
        try:
            # 유효한 Google 액세스 토큰 가져오기
            access_token = await GoogleTokenService.get_valid_access_token(user_id)
            
            if not access_token:
                print(f"❌ 사용자 {user_id}의 유효한 Google 액세스 토큰이 없습니다.")
                return None
            
            # 기본 시간 범위 설정
            if not time_min:
                time_min = datetime.now().isoformat()
            if not time_max:
                time_max = (datetime.now() + timedelta(days=30)).isoformat()
            
            # Google Calendar API 호출
            calendar_url = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
            params = {
                'timeMin': time_min,
                'timeMax': time_max,
                'singleEvents': True,
                'orderBy': 'startTime'
            }
            headers = {
                'Authorization': f'Bearer {access_token}'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(calendar_url, params=params, headers=headers)
                
                if response.status_code == 200:
                    events_data = response.json()
                    events = events_data.get('items', [])
                    print(f"✅ Google Calendar 이벤트 목록 조회 성공: {len(events)}개")
                    return events
                else:
                    print(f"❌ Google Calendar 이벤트 목록 조회 실패: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"❌ Google Calendar 이벤트 목록 조회 오류: {str(e)}")
            return None
