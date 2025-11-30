"""
Gmail 서비스 - Google 토큰을 사용한 Gmail API 연동
"""
import base64
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid
from datetime import datetime, timezone
import uuid
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from backend.dashboard.auth.google_token_service import GoogleTokenService

class GmailService:
    def __init__(self):
        self.token_service = GoogleTokenService()
    
    def _get_gmail_service(self, user_id):
        """Gmail API 서비스 객체 생성 (Supabase 토큰 사용)"""
        try:
            print(f"📧 Gmail 서비스 생성 시작: 사용자 {user_id}")
            
            # 유효한 credentials 가져오기 (자동 갱신 포함)
            credentials = self.token_service.get_valid_credentials(user_id)
            if not credentials:
                raise Exception("유효한 Google 토큰을 찾을 수 없습니다")
            
            # Gmail API 서비스 생성
            service = build('gmail', 'v1', credentials=credentials)
            print(f"✅ Gmail 서비스 생성 완료: 사용자 {user_id}")
            return service
            
        except Exception as e:
            print(f"❌ Gmail 서비스 생성 실패: {e}")
            raise
    
    def send_email(self, user_id, to_email, subject, body, is_html=False, attachments=None):
        """이메일 전송"""
        try:
            service = self._get_gmail_service(user_id)
            
            # 이메일 메시지 생성
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            message['Date'] = formatdate(localtime=True)
            message['Message-ID'] = make_msgid()
            
            # 본문 추가
            if is_html:
                message.attach(MIMEText(body, 'html', 'utf-8'))
            else:
                message.attach(MIMEText(body, 'plain', 'utf-8'))

            # 첨부파일 추가
            if attachments:
                for attachment in attachments:
                    part = MIMEApplication(attachment['content'], _subtype=attachment.get('subtype', 'octet-stream'))
                    part.add_header('Content-Disposition', 'attachment', filename=attachment['filename'])
                    if 'content_type' in attachment:
                        part.add_header('Content-Type', attachment['content_type'])
                    message.attach(part)
            
            # 메시지를 base64로 인코딩
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            # Gmail API로 전송
            send_message = service.users().messages().send(
                userId='me',
                body={'raw': raw_message}
            ).execute()
            
            print(f"이메일 전송 성공: {send_message['id']}")
            return {
                'success': True,
                'message_id': send_message['id'],
                'message': '이메일이 성공적으로 전송되었습니다.'
            }
            
        except HttpError as error:
            error_details = json.loads(error.content.decode('utf-8'))
            print(f"Gmail API 오류: {error_details}")
            
            if error.resp.status == 403:
                return {
                    'success': False,
                    'error': 'Gmail 전송 권한이 없습니다. Google 계정 설정을 확인해주세요.',
                    'details': error_details
                }
            elif error.resp.status == 400:
                return {
                    'success': False,
                    'error': '이메일 형식이 올바르지 않습니다.',
                    'details': error_details
                }
            else:
                return {
                    'success': False,
                    'error': f'Gmail API 오류가 발생했습니다: {error_details.get("error", {}).get("message", "알 수 없는 오류")}',
                    'details': error_details
                }
                
        except Exception as e:
            print(f"이메일 전송 실패: {e}")
            return {
                'success': False,
                'error': f'이메일 전송 중 오류가 발생했습니다: {str(e)}'
            }
    
    def send_schedule_email(self, user_id, schedule_data, recipients, subject=None, extra_message=""):
        """일정 정보를 이메일로 전송 (ICS 첨부 및 다중 수신자 지원)"""
        try:
            # 이메일 제목 생성
            final_subject = subject or f"[SULLIVAN] 일정 공유: {schedule_data.get('title', '제목 없음')}"
            
            # 이메일 본문 생성 (HTML)
            body = self._create_schedule_email_body(schedule_data)
            if extra_message:
                body = f"<p>{extra_message}</p>" + body

            # ICS 첨부 생성
            ics_content = self._create_ics_attachment(schedule_data)
            attachments = []
            if ics_content:
                safe_title = (schedule_data.get('title') or 'event').strip() or 'event'
                filename = f"{safe_title}.ics"
                attachments.append({
                    'filename': filename,
                    'content': ics_content.encode('utf-8'),
                    'subtype': 'octet-stream',
                    'content_type': 'text/calendar; method=PUBLISH; charset="UTF-8"'
                })
            
            # 각 수신자에게 이메일 전송
            results = []
            for recipient in recipients:
                result = self.send_email(
                    user_id=user_id,
                    to_email=recipient,
                    subject=final_subject,
                    body=body,
                    is_html=True,
                    attachments=attachments
                )
                results.append({
                    'recipient': recipient,
                    'result': result
                })
            
            # 전체 결과 반환
            success_count = sum(1 for r in results if r['result']['success'])
            total_count = len(results)
            
            return {
                'success': success_count > 0,
                'message': f'{success_count}/{total_count}명에게 이메일을 전송했습니다.',
                'results': results
            }
            
        except Exception as e:
            print(f"일정 이메일 전송 실패: {e}")
            return {
                'success': False,
                'error': f'일정 이메일 전송 중 오류가 발생했습니다: {str(e)}'
            }

    def _format_dt_for_ics(self, dt_str):
        """ISO/로컬 문자열을 ICS용 UTC 포맷(YYYYMMDDTHHMMSSZ)으로 변환"""
        try:
            # 다양한 형식 시도
            try:
                dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
            except Exception:
                # 'YYYY-MM-DD HH:MM' 형식 대비
                dt = datetime.strptime(dt_str, '%Y-%m-%d %H:%M')
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            dt_utc = dt.astimezone(timezone.utc)
            return dt_utc.strftime('%Y%m%dT%H%M%SZ')
        except Exception:
            now = datetime.now(timezone.utc)
            return now.strftime('%Y%m%dT%H%M%SZ')

    def _escape_ics_text(self, text):
        if text is None:
            return ''
        return str(text).replace('\\', '\\\\').replace('\n', '\\n').replace(',', '\\,').replace(';', '\\;')

    def _create_ics_attachment(self, schedule_data):
        """일정 데이터를 기반으로 단일 이벤트 ICS 문자열 생성"""
        try:
            uid = f"sullivan-{uuid.uuid4()}@sullivan"
            dtstamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
            dtstart = self._format_dt_for_ics(schedule_data.get('start_datetime', ''))
            dtend = self._format_dt_for_ics(schedule_data.get('end_datetime', ''))
            summary = self._escape_ics_text(schedule_data.get('title', '일정'))
            description = self._escape_ics_text(schedule_data.get('description', ''))
            location = self._escape_ics_text(schedule_data.get('location', ''))

            ics = []
            ics.append('BEGIN:VCALENDAR')
            ics.append('PRODID:-//SULLIVAN//Calendar 1.0//KO')
            ics.append('VERSION:2.0')
            ics.append('CALSCALE:GREGORIAN')
            ics.append('METHOD:PUBLISH')
            ics.append('BEGIN:VEVENT')
            ics.append(f'UID:{uid}')
            ics.append(f'DTSTAMP:{dtstamp}')
            ics.append(f'DTSTART:{dtstart}')
            ics.append(f'DTEND:{dtend}')
            if summary:
                ics.append(f'SUMMARY:{summary}')
            if description:
                ics.append(f'DESCRIPTION:{description}')
            if location:
                ics.append(f'LOCATION:{location}')
            ics.append('END:VEVENT')
            ics.append('END:VCALENDAR')

            return '\r\n'.join(ics)
        except Exception as e:
            print(f"ICS 생성 실패: {e}")
            return None
    
    def _create_schedule_email_body(self, schedule_data):
        """일정 정보를 HTML 이메일 본문으로 변환"""
        title = schedule_data.get('title', '제목 없음')
        description = schedule_data.get('description', '설명 없음')
        start_datetime = schedule_data.get('start_datetime', '')
        end_datetime = schedule_data.get('end_datetime', '')
        location = schedule_data.get('location', '장소 미정')
        participants = schedule_data.get('participants', [])
        
        # 참여자 목록 생성
        participants_html = ''
        if participants:
            participants_html = '<ul>'
            for participant in participants:
                participants_html += f'<li>{participant}</li>'
            participants_html += '</ul>'
        else:
            participants_html = '<p>참여자 정보 없음</p>'
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #1f2937; color: white; padding: 20px; text-align: center; }}
                .content {{ background-color: #f8f9fa; padding: 20px; }}
                .schedule-item {{ margin-bottom: 15px; }}
                .schedule-label {{ font-weight: bold; color: #1f2937; }}
                .schedule-value {{ margin-left: 10px; }}
                .footer {{ text-align: center; padding: 20px; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>SULLIVAN 일정 공유</h1>
                </div>
                <div class="content">
                    <div class="schedule-item">
                        <span class="schedule-label">📅 일정 제목:</span>
                        <span class="schedule-value">{title}</span>
                    </div>
                    <div class="schedule-item">
                        <span class="schedule-label">📝 설명:</span>
                        <span class="schedule-value">{description}</span>
                    </div>
                    <div class="schedule-item">
                        <span class="schedule-label">🕐 시작 시간:</span>
                        <span class="schedule-value">{start_datetime}</span>
                    </div>
                    <div class="schedule-item">
                        <span class="schedule-label">🕑 종료 시간:</span>
                        <span class="schedule-value">{end_datetime}</span>
                    </div>
                    <div class="schedule-item">
                        <span class="schedule-label">📍 장소:</span>
                        <span class="schedule-value">{location}</span>
                    </div>
                    <div class="schedule-item">
                        <span class="schedule-label">👥 참여자:</span>
                        <div class="schedule-value">{participants_html}</div>
                    </div>
                </div>
                <div class="footer">
                    <p>이 이메일은 SULLIVAN 시스템에서 자동으로 발송되었습니다.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_body
    
    def check_gmail_permissions(self, user_id):
        """Gmail 권한 확인 (DB 토큰 기반)"""
        try:
            print(f"🔍 Gmail 권한 확인 시작: 사용자 {user_id}")
            
            # 먼저 DB에서 토큰 존재 여부 확인
            from supabase import create_client, Client
            import os
            
            supabase_url = os.getenv("SUPABASE_URL", "https://znvwtoozdcnaqpuzbnhu.supabase.co")
            supabase_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inpudnd0b296ZGNuYXFwdXpibmh1Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTQ2Mjk0MjQsImV4cCI6MjA3MDIwNTQyNH0.UdqqsxqdUoPtPNyQSRfEjKL6cg90dUDNuzsancxIYR0")
            supabase: Client = create_client(supabase_url, supabase_key)
            
            result = supabase.table('google_tokens').select('*').eq('user_id', user_id).execute()
            
            if not result.data:
                print(f"❌ 사용자 {user_id}의 Google 토큰이 DB에 없습니다")
                return {
                    'success': False,
                    'error': 'Google 토큰이 없습니다. 인증이 필요합니다.'
                }
            
            token_data = result.data[0]
            print(f"✅ DB에서 토큰 발견: 사용자 {user_id}")
            print(f"📧 토큰 스코프: {token_data.get('scope', 'N/A')}")
            
            # Gmail 스코프 확인
            scope = token_data.get('scope', '')
            if 'gmail.send' not in scope:
                print(f"❌ Gmail 전송 권한이 없습니다: {scope}")
                return {
                    'success': False,
                    'error': 'Gmail 전송 권한이 없습니다. 재인증이 필요합니다.'
                }
            
            # gmail.readonly 스코프도 확인 (getProfile API용)
            if 'gmail.readonly' not in scope:
                print(f"⚠️ Gmail 읽기 권한이 없습니다: {scope}")
                # 읽기 권한이 없어도 전송은 가능하므로 경고만 출력
            
            # Gmail 서비스로 실제 권한 테스트
            try:
                service = self._get_gmail_service(user_id)
                
                # gmail.readonly 스코프가 있으면 getProfile 테스트, 없으면 서비스 생성만 확인
                if 'gmail.readonly' in scope:
                    try:
                        profile = service.users().getProfile(userId='me').execute()
                        print(f"✅ Gmail API 테스트 성공: {profile.get('emailAddress')}")
                        email_address = profile.get('emailAddress')
                    except Exception as profile_error:
                        print(f"⚠️ getProfile 실패하지만 send 권한은 있음: {profile_error}")
                        email_address = 'Gmail 전송 권한 확인됨'
                else:
                    print(f"✅ Gmail 서비스 생성 성공 - send 권한 확인됨")
                    email_address = 'Gmail 전송 권한 확인됨'
                
                return {
                    'success': True,
                    'email': email_address,
                    'message': 'Gmail 권한이 정상적으로 설정되어 있습니다.',
                    'scope': scope
                }
                
            except Exception as api_error:
                print(f"❌ Gmail 서비스 생성 실패: {api_error}")
                return {
                    'success': False,
                    'error': f'Gmail 서비스 생성 실패: {str(api_error)}'
                }
            
        except Exception as e:
            print(f"❌ Gmail 권한 확인 오류: {str(e)}")
            return {
                'success': False,
                'error': f'Gmail 권한 확인 중 오류가 발생했습니다: {str(e)}'
            }