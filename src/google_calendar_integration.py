#!/usr/bin/env python3

"""
Google Calendar Integration Module for iCloud-GCal Sync
This module provides functions to integrate with Google Calendar API
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Google Calendar API libraries not installed.")
    print("Install with: pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    exit(1)

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar']

class GoogleCalendarManager:
    def __init__(self, credentials_file: str = 'credentials.json', token_file: str = 'token.json'):
        """
        Initialize Google Calendar Manager
        
        Args:
            credentials_file: Path to the OAuth2 credentials file from Google Cloud Console
            token_file: Path to store the user's access and refresh tokens
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API"""
        creds = None
        
        # The file token.json stores the user's access and refresh tokens.
        try:
            if os.path.exists(self.token_file):
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
        except Exception as e:
            logger.warning(f"Could not load existing credentials: {e}")
        
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Could not refresh credentials: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file not found: {self.credentials_file}\n"
                        "Please download your OAuth2 credentials from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('calendar', 'v3', credentials=creds)
        logger.info("Successfully authenticated with Google Calendar API")
    
    def list_calendars(self) -> List[Dict[str, Any]]:
        """List all calendars accessible to the user"""
        try:
            calendar_list = self.service.calendarList().list().execute()
            calendars = []
            
            for calendar in calendar_list.get('items', []):
                calendars.append({
                    'id': calendar['id'],
                    'name': calendar['summary'],
                    'primary': calendar.get('primary', False),
                    'access_role': calendar.get('accessRole', ''),
                    'background_color': calendar.get('backgroundColor', ''),
                    'foreground_color': calendar.get('foregroundColor', '')
                })
            
            return calendars
            
        except HttpError as error:
            logger.error(f"An error occurred: {error}")
            return []
    
    def create_event(self, calendar_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create an event in Google Calendar
        
        Args:
            calendar_id: The calendar to create the event in
            event_data: Dictionary containing event information from iCloud
        
        Returns:
            Created event data or None if failed
        """
        try:
            # Convert iCloud event format to Google Calendar format
            google_event = self._convert_icloud_to_google_event(event_data)
            
            event = self.service.events().insert(
                calendarId=calendar_id,
                body=google_event
            ).execute()
            
            logger.info(f"Event created: {event.get('htmlLink')}")
            return event
            
        except HttpError as error:
            logger.error(f"An error occurred creating event: {error}")
            return None
    
    def update_event(self, calendar_id: str, event_id: str, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update an existing event in Google Calendar"""
        try:
            google_event = self._convert_icloud_to_google_event(event_data)
            
            event = self.service.events().update(
                calendarId=calendar_id,
                eventId=event_id,
                body=google_event
            ).execute()
            
            logger.info(f"Event updated: {event.get('htmlLink')}")
            return event
            
        except HttpError as error:
            logger.error(f"An error occurred updating event: {error}")
            return None
    
    def delete_event(self, calendar_id: str, event_id: str) -> bool:
        """Delete an event from Google Calendar"""
        try:
            self.service.events().delete(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            logger.info(f"Event deleted: {event_id}")
            return True
            
        except HttpError as error:
            logger.error(f"An error occurred deleting event: {error}")
            return False
    
    def get_event(self, calendar_id: str, event_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific event from Google Calendar"""
        try:
            event = self.service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            return event
            
        except HttpError as error:
            logger.error(f"An error occurred getting event: {error}")
            return None
    
    def search_events(self, calendar_id: str, query: str, time_min: str = None, time_max: str = None) -> List[Dict[str, Any]]:
        """Search for events in Google Calendar"""
        try:
            events_result = self.service.events().list(
                calendarId=calendar_id,
                q=query,
                timeMin=time_min,
                timeMax=time_max,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            return events
            
        except HttpError as error:
            logger.error(f"An error occurred searching events: {error}")
            return []
    
    def _convert_icloud_to_google_event(self, icloud_event: Dict[str, Any]) -> Dict[str, Any]:
        """Convert iCloud event format to Google Calendar event format"""
        google_event = {
            'summary': icloud_event.get('title', 'Untitled Event'),
            'description': icloud_event.get('description', ''),
            'location': icloud_event.get('location', ''),
        }
        
        # Handle all-day events
        if icloud_event.get('all_day', False):
            # For all-day events, use date format instead of dateTime
            start_date = datetime.fromisoformat(icloud_event['start_date']).date()
            end_date = datetime.fromisoformat(icloud_event['end_date']).date()
            
            google_event['start'] = {'date': start_date.isoformat()}
            google_event['end'] = {'date': end_date.isoformat()}
        else:
            # For timed events, use dateTime format
            google_event['start'] = {
                'dateTime': icloud_event['start_date'],
                'timeZone': 'America/Chicago',  # You may want to make this configurable
            }
            google_event['end'] = {
                'dateTime': icloud_event['end_date'],
                'timeZone': 'America/Chicago',
            }
        
        # Add source information
        google_event['source'] = {
            'title': f"Synced from iCloud ({icloud_event.get('calendar', 'Unknown')})",
            'url': ''
        }
        
        # Add extended properties to track sync information
        google_event['extendedProperties'] = {
            'private': {
                'icloud_sync': 'true',
                'icloud_calendar': icloud_event.get('calendar', ''),
                'icloud_uid': icloud_event.get('uid', ''),
                'sync_timestamp': datetime.now().isoformat()
            }
        }
        
        return google_event

def test_google_calendar_integration():
    """Test function to verify Google Calendar integration works"""
    try:
        gcal = GoogleCalendarManager()
        
        print("Testing Google Calendar integration...")
        
        # List calendars
        calendars = gcal.list_calendars()
        print(f"Found {len(calendars)} calendars:")
        for cal in calendars:
            print(f"  - {cal['name']} ({'primary' if cal['primary'] else cal['id']})")
        
        # Test event creation
        test_event = {
            'title': 'Test iCloud Sync Event',
            'description': 'This is a test event created by the iCloud sync script',
            'location': 'Test Location',
            'start_date': datetime.now().isoformat(),
            'end_date': (datetime.now() + timedelta(hours=1)).isoformat(),
            'all_day': False,
            'calendar': 'Test Calendar',
            'uid': 'test_event_123'
        }
        
        primary_calendar = next((cal for cal in calendars if cal['primary']), calendars[0] if calendars else None)
        
        if primary_calendar:
            print(f"\nCreating test event in {primary_calendar['name']}...")
            created_event = gcal.create_event(primary_calendar['id'], test_event)
            
            if created_event:
                print(f"✅ Event created successfully: {created_event['id']}")
                print(f"   Link: {created_event.get('htmlLink', 'N/A')}")
                
                # Clean up - delete the test event
                print("\nCleaning up test event...")
                if gcal.delete_event(primary_calendar['id'], created_event['id']):
                    print("✅ Test event deleted successfully")
                else:
                    print("❌ Failed to delete test event")
            else:
                print("❌ Failed to create test event")
        else:
            print("❌ No calendars found")
        
        print("\n✅ Google Calendar integration test completed")
        
    except Exception as e:
        print(f"❌ Google Calendar integration test failed: {e}")

if __name__ == "__main__":
    # Import timedelta here for the test function
    from datetime import timedelta
    test_google_calendar_integration()
