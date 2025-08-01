"""
Schedule management routes
"""
from fastapi import APIRouter, HTTPException, status, Depends
from typing import Dict, Any, List
from services.database_service import DatabaseService
from services.ics_service import ICSService
from core.dependencies import get_current_user
from models.analysis import Schedule
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/schedules", tags=["schedules"])
db_service = DatabaseService()
ics_service = ICSService()


@router.get("/")
async def get_user_schedules(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Get all schedules for current user"""
    try:
        # This would get schedules from database
        # For now, return empty list
        schedules = []
        
        return {
            "schedules": schedules,
            "total": len(schedules)
        }
        
    except Exception as e:
        logger.error(f"Error getting user schedules: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get schedules: {str(e)}"
        )


@router.post("/")
async def create_schedule(
    schedule: Schedule,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Create a new schedule"""
    try:
        # This would save schedule to database
        logger.info(f"Creating schedule for user: {current_user['user_id']}")
        
        return {
            "message": "Schedule created successfully",
            "schedule": schedule.dict()
        }
        
    except Exception as e:
        logger.error(f"Error creating schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create schedule: {str(e)}"
        )


@router.put("/{schedule_id}")
async def update_schedule(
    schedule_id: str,
    schedule: Schedule,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Update an existing schedule"""
    try:
        # This would update schedule in database
        logger.info(f"Updating schedule {schedule_id} for user: {current_user['user_id']}")
        
        return {
            "message": "Schedule updated successfully",
            "schedule": schedule.dict()
        }
        
    except Exception as e:
        logger.error(f"Error updating schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update schedule: {str(e)}"
        )


@router.delete("/{schedule_id}")
async def delete_schedule(
    schedule_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Delete a schedule"""
    try:
        # This would delete schedule from database
        logger.info(f"Deleting schedule {schedule_id} for user: {current_user['user_id']}")
        
        return {"message": "Schedule deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting schedule: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete schedule: {str(e)}"
        )


@router.post("/export/ics")
async def export_schedules_to_ics(
    schedule_ids: List[str] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    """Export schedules to ICS format"""
    try:
        # Get schedules from database
        # For now, create sample schedules
        schedules = [
            Schedule(
                title="Sample Meeting",
                date="2024-01-15",
                time="14:00",
                location="Conference Room",
                description="Sample meeting description",
                participants=["user1", "user2"]
            )
        ]
        
        ics_content = ics_service.create_ics_file(schedules)
        
        return {
            "ics_content": ics_content,
            "filename": f"schedules_{current_user['user_id']}.ics"
        }
        
    except Exception as e:
        logger.error(f"Error exporting schedules to ICS: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export schedules: {str(e)}"
        ) 