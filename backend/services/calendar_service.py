"""
Calendar service for managing calendar operations and integrations
"""
from typing import List, Dict, Any, Optional
from models.analysis import Schedule
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CalendarService:
    """Service for calendar operations"""
    
    def __init__(self):
        self.calendar_providers = ["google", "outlook", "ics"]
    
    def create_calendar_event(self, schedule: Schedule, provider: str = "ics") -> Dict[str, Any]:
        """
        Create a calendar event from schedule data
        
        Args:
            schedule: Schedule object
            provider: Calendar provider (google, outlook, ics)
            
        Returns:
            Dictionary containing event data
        """
        try:
            event_data = {
                "title": schedule.title,
                "description": schedule.description or "",
                "location": schedule.location or "",
                "start_date": schedule.date,
                "start_time": schedule.time,
                "participants": schedule.participants or [],
                "category": schedule.category
            }
            
            if provider == "google":
                return self._create_google_event(event_data)
            elif provider == "outlook":
                return self._create_outlook_event(event_data)
            else:
                return self._create_ics_event(event_data)
                
        except Exception as e:
            logger.error(f"Error creating calendar event: {str(e)}")
            raise
    
    def _create_google_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Google Calendar event format"""
        return {
            "summary": event_data["title"],
            "description": event_data["description"],
            "location": event_data["location"],
            "start": {
                "dateTime": f"{event_data['start_date']}T{event_data['start_time'] or '09:00'}:00",
                "timeZone": "Asia/Seoul"
            },
            "end": {
                "dateTime": f"{event_data['start_date']}T{self._calculate_end_time(event_data['start_time'])}:00",
                "timeZone": "Asia/Seoul"
            },
            "attendees": [{"email": p} for p in event_data["participants"] if "@" in p]
        }
    
    def _create_outlook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create Outlook Calendar event format"""
        return {
            "subject": event_data["title"],
            "body": {
                "contentType": "HTML",
                "content": event_data["description"]
            },
            "location": {
                "displayName": event_data["location"]
            },
            "start": {
                "dateTime": f"{event_data['start_date']}T{event_data['start_time'] or '09:00'}:00",
                "timeZone": "Asia/Seoul"
            },
            "end": {
                "dateTime": f"{event_data['start_date']}T{self._calculate_end_time(event_data['start_time'])}:00",
                "timeZone": "Asia/Seoul"
            },
            "attendees": [{"emailAddress": {"address": p}} for p in event_data["participants"] if "@" in p]
        }
    
    def _create_ics_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create ICS format event data"""
        return {
            "summary": event_data["title"],
            "description": event_data["description"],
            "location": event_data["location"],
            "dtstart": f"{event_data['start_date']}T{event_data['start_time'] or '09:00'}:00",
            "dtend": f"{event_data['start_date']}T{self._calculate_end_time(event_data['start_time'])}:00",
            "attendees": event_data["participants"]
        }
    
    def _calculate_end_time(self, start_time: Optional[str]) -> str:
        """Calculate end time (default 1 hour after start)"""
        if not start_time:
            return "10:00"
        
        try:
            hour, minute = map(int, start_time.split(":"))
            end_hour = hour + 1
            if end_hour >= 24:
                end_hour = 23
                minute = 59
            return f"{end_hour:02d}:{minute:02d}"
        except:
            return "10:00"
    
    def batch_create_events(self, schedules: List[Schedule], provider: str = "ics") -> List[Dict[str, Any]]:
        """
        Create multiple calendar events
        
        Args:
            schedules: List of Schedule objects
            provider: Calendar provider
            
        Returns:
            List of created events
        """
        events = []
        for schedule in schedules:
            try:
                event = self.create_calendar_event(schedule, provider)
                events.append(event)
            except Exception as e:
                logger.error(f"Failed to create event for schedule {schedule.title}: {str(e)}")
        
        return events
    
    def get_calendar_url(self, provider: str) -> str:
        """Get calendar URL for provider"""
        urls = {
            "google": "https://calendar.google.com",
            "outlook": "https://outlook.live.com/calendar",
            "ics": "/api/schedules/export/ics"
        }
        return urls.get(provider, "")
    
    def validate_schedule_data(self, schedule: Schedule) -> bool:
        """Validate schedule data for calendar creation"""
        if not schedule.title:
            return False
        if not schedule.date:
            return False
        
        # Additional validation can be added here
        return True 