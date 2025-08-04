"""
Gmail Service
Gmail API를 사용하여 이메일 전송 기능을 제공합니다.
"""
import base64
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import Dict, List, Optional
import httpx
from config.config import settings

logger = logging.getLogger(__name__)

class GmailService:
    """Gmail API 서비스 클래스"""
    
    def __init__(self):
        self.api_base_url = "https://gmail.googleapis.com/gmail/v1"
        # ICS 파일 캐시 (파일 경로: 콘텐츠)
        self._ics_cache = {}
        self._max_cache_size = 100  # 최대 100개 파일 캐시
    
    def _manage_cache(self, file_path: str, content: str):
        """캐시 크기 관리 및 새 항목 추가"""
        # 캐시 크기 초과 시 가장 오래된 항목 제거 (FIFO)
        if len(self._ics_cache) >= self._max_cache_size:
            oldest_key = next(iter(self._ics_cache))
            del self._ics_cache[oldest_key]
            print(f"🗑️ 캐시 크기 초과로 오래된 항목 제거: {oldest_key}")
        
        # 새 항목 추가
        self._ics_cache[file_path] = content
        print(f"💾 캐시에 새 ICS 파일 저장: {file_path} (총 {len(self._ics_cache)}개)")
    
    async def send_email_with_ics(
        self,
        google_credentials: Dict,
        to_email: str,
        subject: str,
        body: str,
        ics_content: str,
        ics_filename: str = "schedule.ics"
    ) -> Dict:
        """
        ICS 파일을 첨부하여 이메일 전송
        
        Args:
            google_credentials: Google OAuth 자격증명
            to_email: 수신자 이메일
            subject: 이메일 제목
            body: 이메일 본문
            ics_content: ICS 파일 내용
            ics_filename: ICS 파일명
            
        Returns:
            전송 결과
        """
        try:
            # MIME 메시지 생성
            message = MIMEMultipart()
            message['to'] = to_email
            message['subject'] = subject
            
            # 본문 추가
            body_part = MIMEText(body, 'html', 'utf-8')
            message.attach(body_part)
            
            # ICS 파일 첨부 (MIMEBase 사용)
            from email.mime.base import MIMEBase
            from email import encoders
            
            ics_attachment = MIMEBase('text', 'calendar')
            ics_attachment.set_payload(ics_content.encode('utf-8'))
            encoders.encode_base64(ics_attachment)
            
            ics_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{ics_filename}"'
            )
            ics_attachment.add_header(
                'Content-Type',
                f'text/calendar; charset=utf-8; name="{ics_filename}"'
            )
            
            print(f"📎 ICS 첨부 파일 정보:")
            print(f"📎 파일명: {ics_filename}")
            print(f"📎 콘텐츠 길이: {len(ics_content)} 문자")
            print(f"📎 Content-Type: text/calendar")
            print(f"📎 콘텐츠 시작: {ics_content[:100]}...")
            
            message.attach(ics_attachment)
            
            # Base64 인코딩
            raw_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode('utf-8')
            
            # Gmail API로 전송
            access_token = google_credentials.get('access_token')
            if not access_token:
                raise ValueError("Google 액세스 토큰이 없습니다.")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            send_data = {
                'raw': raw_message
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base_url}/users/me/messages/send",
                    headers=headers,
                    json=send_data,
                    timeout=30
                )
                response.raise_for_status()
                result = response.json()
            
            logger.info(f"✅ Gmail 전송 성공: {result.get('id')}")
            return {
                "success": True,
                "message_id": result.get('id'),
                "message": f"이메일이 {to_email}로 성공적으로 전송되었습니다."
            }
            
        except httpx.HTTPError as e:
            logger.error(f"❌ Gmail API 오류: {e}")
            if e.response and e.response.status_code == 401:
                return {
                    "success": False,
                    "error": "Google 인증이 만료되었습니다. 다시 로그인해주세요.",
                    "error_code": "AUTH_EXPIRED"
                }
            else:
                return {
                    "success": False,
                    "error": f"이메일 전송 실패: {str(e)}",
                    "error_code": "SEND_FAILED"
                }
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.error(f"❌ Gmail 서비스 오류: {e}")
            logger.error(f"❌ 상세 에러: {error_details}")
            print(f"❌ [ERROR] Gmail 전송 상세 오류:\n{error_details}")
            
            return {
                "success": False,
                "error": f"이메일 전송 중 오류가 발생했습니다: {str(e)}",
                "error_code": "UNKNOWN_ERROR"
            }
    
    async def send_schedule_invitation(
        self,
        google_credentials: Dict,
        to_emails: List[str],
        schedule_title: str,
        schedule_description: str,
        ics_content: str,
        sender_name: str = "MUFI"
    ) -> Dict:
        """
        일정 초대 이메일 전송
        
        Args:
            google_credentials: Google OAuth 자격증명
            to_emails: 수신자 이메일 리스트
            schedule_title: 일정 제목
            schedule_description: 일정 설명
            ics_content: ICS 파일 내용
            sender_name: 발신자 이름
            
        Returns:
            전송 결과
        """
        try:
            results = []
            
            # HTML 이메일 본문 생성
            email_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                        📅 일정 초대
                    </h2>
                    
                    <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #1e40af;">{schedule_title}</h3>
                        <p style="margin-bottom: 0;">{schedule_description}</p>
                    </div>
                    
                    <p>안녕하세요,</p>
                    <p><strong>{sender_name}</strong>에서 일정 초대를 보내드립니다.</p>
                    <p>첨부된 캘린더 파일(.ics)을 클릭하여 캘린더에 일정을 추가하실 수 있습니다.</p>
                    
                    <div style="background-color: #e0f2fe; padding: 15px; border-radius: 6px; margin: 20px 0;">
                        <p style="margin: 0;"><strong>💡 참고사항:</strong></p>
                        <ul style="margin: 10px 0 0 20px;">
                            <li>첨부된 .ics 파일을 클릭하면 캘린더 앱에서 자동으로 열립니다</li>
                            <li>Google Calendar, Outlook, Apple Calendar 등에서 지원됩니다</li>
                            <li>일정이 자동으로 캘린더에 추가됩니다</li>
                        </ul>
                    </div>
                    
                    <p>감사합니다.</p>
                    
                    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                    <p style="font-size: 12px; color: #6b7280;">
                        이 이메일은 MUFI 시스템에서 자동 발송되었습니다.
                    </p>
                </div>
            </body>
            </html>
            """
            
            # 안전한 파일명 생성 (특수문자 제거)
            import re
            safe_filename = re.sub(r'[<>:"/\\|?*]', '_', schedule_title)
            safe_filename = safe_filename.strip()[:50]  # 최대 50자로 제한
            
            # 각 수신자에게 개별 전송
            for to_email in to_emails:
                result = await self.send_email_with_ics(
                    google_credentials=google_credentials,
                    to_email=to_email,
                    subject=f"📅 일정 초대: {schedule_title}",
                    body=email_body,
                    ics_content=ics_content,
                    ics_filename=f"{safe_filename}.ics"
                )
                results.append({
                    "email": to_email,
                    "result": result
                })
            
            # 전체 결과 요약
            successful_sends = [r for r in results if r["result"]["success"]]
            failed_sends = [r for r in results if not r["result"]["success"]]
            
            return {
                "success": len(failed_sends) == 0,
                "total_sent": len(successful_sends),
                "total_failed": len(failed_sends),
                "results": results,
                "message": f"총 {len(to_emails)}명 중 {len(successful_sends)}명에게 성공적으로 전송되었습니다."
            }
            
        except Exception as e:
            logger.error(f"❌ 일정 초대 전송 오류: {e}")
            return {
                "success": False,
                "error": f"일정 초대 전송 중 오류가 발생했습니다: {str(e)}",
                "error_code": "INVITATION_FAILED"
            }
    
    def create_schedule_email_body(
        self,
        schedule_title: str,
        schedule_description: str,
        start_datetime: str,
        end_datetime: str,
        location: str = "",
        participants: List[str] = None
    ) -> str:
        """
        일정 정보로 이메일 본문 생성
        
        Args:
            schedule_title: 일정 제목
            schedule_description: 일정 설명
            start_datetime: 시작 시간
            end_datetime: 종료 시간
            location: 장소
            participants: 참석자 목록
            
        Returns:
            HTML 형식의 이메일 본문
        """
        participants_html = ""
        if participants:
            participants_html = f"""
            <div style="margin: 10px 0;">
                <strong>👥 참석자:</strong> {', '.join(participants)}
            </div>
            """
        
        location_html = ""
        if location:
            location_html = f"""
            <div style="margin: 10px 0;">
                <strong>📍 장소:</strong> {location}
            </div>
            """
        
        return f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2563eb; border-bottom: 2px solid #2563eb; padding-bottom: 10px;">
                    📅 일정 공유
                </h2>
                
                <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="margin-top: 0; color: #1e40af;">{schedule_title}</h3>
                    
                    <div style="margin: 15px 0;">
                        <strong>📝 설명:</strong><br>
                        {schedule_description}
                    </div>
                    
                    <div style="margin: 10px 0;">
                        <strong>⏰ 시작:</strong> {start_datetime}
                    </div>
                    
                    <div style="margin: 10px 0;">
                        <strong>⏰ 종료:</strong> {end_datetime}
                    </div>
                    
                    {location_html}
                    {participants_html}
                </div>
                
                <p>첨부된 캘린더 파일(.ics)을 클릭하여 캘린더에 일정을 추가하실 수 있습니다.</p>
                
                <div style="background-color: #e0f2fe; padding: 15px; border-radius: 6px; margin: 20px 0;">
                    <p style="margin: 0;"><strong>💡 캘린더 추가 방법:</strong></p>
                    <ul style="margin: 10px 0 0 20px;">
                        <li>첨부된 .ics 파일을 더블클릭</li>
                        <li>캘린더 앱에서 자동으로 열림</li>
                        <li>'추가' 또는 '저장' 버튼 클릭</li>
                    </ul>
                </div>
                
                <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                <p style="font-size: 12px; color: #6b7280;">
                    이 이메일은 MUFI 시스템에서 자동 발송되었습니다.
                </p>
            </div>
        </body>
        </html>
        """