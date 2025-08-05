"""
Email routes for sending analysis reports and notifications
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any
from services.email_service import EmailService
from core.dependencies import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["email"])
email_service = EmailService()


@router.post("/send-report")
async def send_analysis_report(
    analysis_id: str,
    recipient_email: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Send analysis report via email"""
    try:
        # Here you would get the analysis data from database
        # For now, we'll create a sample report
        analysis_result = {
            "title": "Analysis Report",
            "created_at": "2024-01-01 12:00:00",
            "summary": "Analysis completed successfully"
        }
        
        success = await email_service.send_analysis_report(
            to_address=recipient_email,
            user_name=current_user["name"],
            analysis_result=analysis_result
        )
        
        if success:
            return {"message": "Report sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email"
            )
            
    except Exception as e:
        logger.error(f"Error sending email report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email sending failed: {str(e)}"
        )


@router.post("/test")
async def test_email(
    recipient_email: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Test email functionality"""
    try:
        success = await email_service.send_email(
            to_addresses=[recipient_email],
            subject="MUFI Test Email",
            body=f"Hello {current_user['name']}, this is a test email from MUFI!"
        )
        
        if success:
            return {"message": "Test email sent successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send test email"
            )
            
    except Exception as e:
        logger.error(f"Error sending test email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Test email failed: {str(e)}"
        ) 