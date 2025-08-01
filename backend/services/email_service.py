"""
Email service for sending notifications and reports
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for handling email operations"""
    
    def __init__(self):
        # Email configuration would be loaded from settings
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        self.email_user = None  # Would be loaded from env
        self.email_password = None  # Would be loaded from env
    
    async def send_email(
        self,
        to_addresses: List[str],
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Send email to specified addresses
        
        Args:
            to_addresses: List of recipient email addresses
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.email_user or not self.email_password:
                logger.warning("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email_user
            msg['To'] = ', '.join(to_addresses)
            msg['Subject'] = subject
            
            # Add plain text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_addresses}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False
    
    async def send_analysis_report(
        self,
        to_address: str,
        user_name: str,
        analysis_result: dict
    ) -> bool:
        """
        Send analysis report via email
        
        Args:
            to_address: Recipient email address
            user_name: Name of the user
            analysis_result: Analysis result data
            
        Returns:
            True if email sent successfully, False otherwise
        """
        subject = f"MUFI Analysis Report - {analysis_result.get('title', 'Untitled')}"
        
        # Create plain text body
        body = f"""
안녕하세요 {user_name}님,

MUFI 분석 결과를 보내드립니다.

분석 제목: {analysis_result.get('title', 'N/A')}
분석 일시: {analysis_result.get('created_at', 'N/A')}

상세 내용은 첨부된 보고서를 확인해주세요.

감사합니다.
MUFI Team
        """
        
        # Create HTML body
        html_body = f"""
        <html>
        <body>
            <h2>MUFI 분석 결과</h2>
            <p>안녕하세요 <strong>{user_name}</strong>님,</p>
            <p>요청하신 MUFI 분석 결과를 보내드립니다.</p>
            
            <h3>분석 정보</h3>
            <ul>
                <li><strong>제목:</strong> {analysis_result.get('title', 'N/A')}</li>
                <li><strong>분석 일시:</strong> {analysis_result.get('created_at', 'N/A')}</li>
            </ul>
            
            <p>상세 내용은 MUFI 대시보드에서 확인하실 수 있습니다.</p>
            
            <p>감사합니다.<br>
            <strong>MUFI Team</strong></p>
        </body>
        </html>
        """
        
        return await self.send_email([to_address], subject, body, html_body) 