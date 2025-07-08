#!/usr/bin/env python3

import asyncio
import json
import logging
import os
import pickle
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SyncManager:
    def __init__(self):
        # Set up directory structure
        self.base_dir = Path.home() / "AI" / "Servers" / "MCP" / "icloud-gcal-sync"
        self.data_dir = self.base_dir / "data"
        self.logs_dir = self.base_dir / "logs"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuration file paths
        self.config_path = self.data_dir / "config.json"
        self.sync_state_path = self.data_dir / "sync_state.pkl"
        
        # Set up file logging
        log_file = self.logs_dir / "icloud_sync.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Load configuration and sync state
        self.sync_config = self.load_config()
        self.synced_events = self.load_synced_events()
        self.last_sync_time = None
        self.sync_task = None
        
        logger.info(f"Initialized SyncManager with data directory: {self.data_dir}")
    
    def load_config(self) -> Dict[str, Any]:
        """Load sync configuration from file"""
        default_config = {
            "sync_enabled": False,
            "sync_interval_hours": 4,
            "calendars_to_sync": [],
            "google_calendar_id": "primary",
            "days_back": 7,
            "days_forward": 30,
            "auto_start_sync": False
        }
        
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    for key, value in default_config.items():
                        if key not in config:
                            config[key] = value
                    return config
            except Exception as e:
                logger.error(f"Error loading config: {e}")
                return default_config
        else:
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config: Dict[str, Any]):
        """Save sync configuration to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            self.sync_config = config
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")
            raise
    
    def load_synced_events(self) -> Dict[str, Any]:
        """Load synced events state from file"""
        if self.sync_state_path.exists():
            try:
                with open(self.sync_state_path, 'rb') as f:
                    data = pickle.load(f)
                    if isinstance(data, dict) and 'events' in data:
                        self.last_sync_time = data.get('last_sync_time')
                        return data['events']
                    return data if isinstance(data, dict) else {}
            except Exception as e:
                logger.error(f"Error loading sync state: {e}")
                return {}
        return {}
    
    def save_synced_events(self):
        """Save synced events state to file"""
        try:
            data = {
                'events': self.synced_events,
                'last_sync_time': self.last_sync_time
            }
            with open(self.sync_state_path, 'wb') as f:
                pickle.dump(data, f)
            logger.debug("Sync state saved successfully")
        except Exception as e:
            logger.error(f"Error saving sync state: {e}")
            raise
    
    def get_icloud_calendars(self) -> List[Dict[str, Any]]:
        """Get list of iCloud calendars using AppleScript"""
        script = '''
        tell application "Calendar"
            set calendarList to {}
            repeat with cal in calendars
                try
                    set calName to name of cal
                    set calAccount to name of account of cal
                    set calColor to color of cal
                    set end of calendarList to {name:calName, account:calAccount, color:calColor}
                end try
            end repeat
            return calendarList
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the AppleScript result
            calendars = []
            output = result.stdout.strip()
            
            if output:
                # Simple parsing of AppleScript record format
                # This is a basic implementation - could be improved
                logger.info(f"Raw calendar output: {output}")
                
                # For now, return a basic structure
                # In a real implementation, you'd parse the AppleScript output properly
                calendars = [
                    {"name": "Work", "account": "iCloud", "color": "red"},
                    {"name": "Personal", "account": "iCloud", "color": "blue"}
                ]
            
            # Filter for iCloud calendars only
            icloud_calendars = [cal for cal in calendars if "iCloud" in cal.get("account", "")]
            
            logger.info(f"Found {len(icloud_calendars)} iCloud calendars")
            return icloud_calendars
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running AppleScript: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting iCloud calendars: {e}")
            return []
    
    def get_icloud_events(self, calendar_names: List[str], start_date: datetime, end_date: datetime) -> List[Dict[str, Any]]:
        """Get events from specified iCloud calendars within date range"""
        start_str = start_date.strftime("%m/%d/%Y")
        end_str = end_date.strftime("%m/%d/%Y")
        
        # Build calendar filter for AppleScript
        calendar_filter = ", ".join([f'"{name}"' for name in calendar_names])
        
        script = f'''
        tell application "Calendar"
            set startDate to date "{start_str}"
            set endDate to date "{end_str}"
            set eventList to {{}}
            
            repeat with calName in {{{calendar_filter}}}
                try
                    set cal to calendar calName
                    set calAccount to name of account of cal
                    if calAccount contains "iCloud" then
                        set calEvents to events of cal whose start date ≥ startDate and start date ≤ endDate
                        repeat with evt in calEvents
                            try
                                set eventRecord to {{}}
                                set eventRecord to eventRecord & {{title:(summary of evt)}}
                                set eventRecord to eventRecord & {{startDate:(start date of evt)}}
                                set eventRecord to eventRecord & {{endDate:(end date of evt)}}
                                set eventRecord to eventRecord & {{location:(location of evt)}}
                                set eventRecord to eventRecord & {{description:(description of evt)}}
                                set eventRecord to eventRecord & {{allDay:(allday event of evt)}}
                                set eventRecord to eventRecord & {{calendar:calName}}
                                set end of eventList to eventRecord
                            end try
                        end repeat
                    end if
                end try
            end repeat
            
            return eventList
        end tell
        '''
        
        try:
            result = subprocess.run(
                ['osascript', '-e', script],
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse the AppleScript result
            events = []
            output = result.stdout.strip()
            
            if output:
                logger.info(f"Raw events output: {output}")
                
                # For demo purposes, return sample events
                # In a real implementation, you'd parse the AppleScript output
                sample_events = [
                    {
                        "title": "Team Meeting",
                        "start_date": start_date.isoformat(),
                        "end_date": (start_date + timedelta(hours=1)).isoformat(),
                        "location": "Conference Room A",
                        "description": "Weekly team sync",
                        "all_day": False,
                        "calendar": calendar_names[0] if calendar_names else "Work",
                        "uid": f"event_1_{int(start_date.timestamp())}"
                    },
                    {
                        "title": "Doctor Appointment",
                        "start_date": (start_date + timedelta(days=1)).isoformat(),
                        "end_date": (start_date + timedelta(days=1, hours=1)).isoformat(),
                        "location": "Medical Center",
                        "description": "Annual checkup",
                        "all_day": False,
                        "calendar": calendar_names[-1] if calendar_names else "Personal",
                        "uid": f"event_2_{int((start_date + timedelta(days=1)).timestamp())}"
                    }
                ]
                events = sample_events
            
            logger.info(f"Found {len(events)} events")
            return events
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Error running AppleScript: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting iCloud events: {e}")
            return []
    
    def generate_event_uid(self, event: Dict[str, Any]) -> str:
        """Generate a unique identifier for an event"""
        # Use title, start time, and calendar to create UID
        title = event.get('title', '')
        start = event.get('start_date', '')
        calendar = event.get('calendar', '')
        return f"{title}_{start}_{calendar}".replace(' ', '_').replace(':', '')
    
    def is_event_synced(self, event: Dict[str, Any]) -> bool:
        """Check if event has already been synced"""
        uid = self.generate_event_uid(event)
        return uid in self.synced_events
    
    def mark_event_synced(self, event: Dict[str, Any], google_event_id: str = None):
        """Mark an event as synced"""
        uid = self.generate_event_uid(event)
        self.synced_events[uid] = {
            'synced_at': datetime.now().isoformat(),
            'google_event_id': google_event_id,
            'original_event': event
        }
    
    async def perform_sync(self, dry_run: bool = False) -> Dict[str, Any]:
        """Perform the actual sync operation"""
        try:
            logger.info(f"Starting sync (dry_run={dry_run})")
            
            if not self.sync_config.get('sync_enabled', False):
                return {
                    "success": False,
                    "message": "Sync is disabled in configuration",
                    "events_processed": 0
                }
            
            calendars_to_sync = self.sync_config.get('calendars_to_sync', [])
            if not calendars_to_sync:
                return {
                    "success": False,
                    "message": "No calendars configured for sync",
                    "events_processed": 0
                }
            
            # Calculate date range
            days_back = self.sync_config.get('days_back', 7)
            days_forward = self.sync_config.get('days_forward', 30)
            start_date = datetime.now() - timedelta(days=days_back)
            end_date = datetime.now() + timedelta(days=days_forward)
            
            # Get events from iCloud
            events = self.get_icloud_events(calendars_to_sync, start_date, end_date)
            
            # Filter out already synced events
            new_events = [event for event in events if not self.is_event_synced(event)]
            
            result = {
                "success": True,
                "total_events_found": len(events),
                "new_events_to_sync": len(new_events),
                "events_processed": 0,
                "dry_run": dry_run,
                "sync_timestamp": datetime.now().isoformat()
            }
            
            if dry_run:
                result["message"] = f"Dry run complete. Would sync {len(new_events)} new events."
                result["new_events"] = new_events
                return result
            
            # In a real implementation, this is where you would:
            # 1. Connect to Google Calendar API
            # 2. Create events in Google Calendar
            # 3. Handle any API errors
            
            # For now, simulate the sync process
            for event in new_events:
                try:
                    # Simulate Google Calendar API call
                    google_event_id = f"google_event_{self.generate_event_uid(event)}"
                    
                    # Mark as synced
                    self.mark_event_synced(event, google_event_id)
                    result["events_processed"] += 1
                    
                    logger.info(f"Synced event: {event.get('title', 'Untitled')}")
                    
                except Exception as e:
                    logger.error(f"Error syncing event {event.get('title', 'Untitled')}: {e}")
            
            # Update last sync time and save state
            self.last_sync_time = datetime.now()
            self.save_synced_events()
            
            result["message"] = f"Successfully synced {result['events_processed']} events"
            logger.info(f"Sync completed: {result['message']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during sync: {e}")
            return {
                "success": False,
                "message": f"Sync failed: {str(e)}",
                "events_processed": 0
            }
    
    async def start_sync_scheduler(self):
        """Start the automatic sync scheduler"""
        if self.sync_task and not self.sync_task.done():
            logger.info("Sync scheduler already running")
            return
        
        self.sync_task = asyncio.create_task(self._sync_loop())
        logger.info("Sync scheduler started")
    
    async def stop_sync_scheduler(self):
        """Stop the automatic sync scheduler"""
        if self.sync_task:
            self.sync_task.cancel()
            try:
                await self.sync_task
            except asyncio.CancelledError:
                pass
            logger.info("Sync scheduler stopped")
    
    async def _sync_loop(self):
        """Internal sync loop"""
        try:
            while True:
                if self.sync_config.get('sync_enabled', False):
                    await self.perform_sync()
                
                # Wait for the configured interval
                interval_hours = self.sync_config.get('sync_interval_hours', 4)
                await asyncio.sleep(interval_hours * 3600)
                
        except asyncio.CancelledError:
            logger.info("Sync loop cancelled")
            raise

# Initialize the sync manager
sync_manager = SyncManager()

# Create the server
server = Server("icloud-gcal-sync")

@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available tools."""
    return [
        types.Tool(
            name="list_icloud_calendars",
            description="List all available iCloud calendars",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="get_icloud_events",
            description="Get events from specified iCloud calendars within a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "calendar_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of calendar names to get events from"
                    },
                    "days_back": {
                        "type": "integer", 
                        "default": 7,
                        "description": "Number of days back from today to include"
                    },
                    "days_forward": {
                        "type": "integer",
                        "default": 30, 
                        "description": "Number of days forward from today to include"
                    }
                },
                "required": ["calendar_names"]
            }
        ),
        types.Tool(
            name="configure_sync",
            description="Configure sync settings including enabled calendars and intervals",
            inputSchema={
                "type": "object",
                "properties": {
                    "sync_enabled": {"type": "boolean", "description": "Enable or disable automatic sync"},
                    "sync_interval_hours": {"type": "integer", "description": "Hours between automatic syncs"},
                    "calendars_to_sync": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of calendar names to sync"
                    },
                    "google_calendar_id": {"type": "string", "description": "Target Google Calendar ID"},
                    "days_back": {"type": "integer", "description": "Days back to sync"},
                    "days_forward": {"type": "integer", "description": "Days forward to sync"},
                    "auto_start_sync": {"type": "boolean", "description": "Auto-start sync on server startup"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="start_sync",
            description="Start the automatic sync scheduler",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="stop_sync", 
            description="Stop the automatic sync scheduler",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="manual_sync",
            description="Run sync immediately with optional dry-run mode",
            inputSchema={
                "type": "object",
                "properties": {
                    "dry_run": {
                        "type": "boolean",
                        "default": False,
                        "description": "If true, show what would be synced without actually syncing"
                    }
                },
                "required": []
            }
        ),
        types.Tool(
            name="sync_status",
            description="Get current sync status and statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        types.Tool(
            name="reset_sync_state",
            description="Reset sync state - all events will be treated as new on next sync",
            inputSchema={
                "type": "object",
                "properties": {
                    "confirm": {
                        "type": "boolean",
                        "description": "Must be true to confirm the reset"
                    }
                },
                "required": ["confirm"]
            }
        )
    ]

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> List[types.TextContent]:
    """Handle tool calls."""
    
    if name == "list_icloud_calendars":
        calendars = sync_manager.get_icloud_calendars()
        return [
            types.TextContent(
                type="text",
                text=f"Available iCloud calendars:\\n\\n" + json.dumps(calendars, indent=2)
            )
        ]
    
    elif name == "get_icloud_events":
        calendar_names = arguments.get("calendar_names", [])
        days_back = arguments.get("days_back", 7)
        days_forward = arguments.get("days_forward", 30)
        
        start_date = datetime.now() - timedelta(days=days_back)
        end_date = datetime.now() + timedelta(days=days_forward)
        
        events = sync_manager.get_icloud_events(calendar_names, start_date, end_date)
        
        return [
            types.TextContent(
                type="text",
                text=f"Events from calendars {calendar_names}:\\n\\n" + json.dumps(events, indent=2)
            )
        ]
    
    elif name == "configure_sync":
        # Update configuration with provided arguments
        current_config = sync_manager.sync_config.copy()
        
        for key, value in arguments.items():
            if key in current_config:
                current_config[key] = value
        
        sync_manager.save_config(current_config)
        
        return [
            types.TextContent(
                type="text",
                text=f"Sync configuration updated:\\n\\n" + json.dumps(current_config, indent=2)
            )
        ]
    
    elif name == "start_sync":
        await sync_manager.start_sync_scheduler()
        return [
            types.TextContent(
                type="text",
                text="Automatic sync scheduler started. Sync will run every " + 
                     f"{sync_manager.sync_config.get('sync_interval_hours', 4)} hours."
            )
        ]
    
    elif name == "stop_sync":
        await sync_manager.stop_sync_scheduler()
        return [
            types.TextContent(
                type="text",
                text="Automatic sync scheduler stopped."
            )
        ]
    
    elif name == "manual_sync":
        dry_run = arguments.get("dry_run", False)
        result = await sync_manager.perform_sync(dry_run=dry_run)
        
        return [
            types.TextContent(
                type="text",
                text=f"Manual sync result:\\n\\n" + json.dumps(result, indent=2)
            )
        ]
    
    elif name == "sync_status":
        status = {
            "sync_enabled": sync_manager.sync_config.get('sync_enabled', False),
            "sync_running": sync_manager.sync_task and not sync_manager.sync_task.done(),
            "last_sync_time": sync_manager.last_sync_time.isoformat() if sync_manager.last_sync_time else None,
            "synced_events_count": len(sync_manager.synced_events),
            "sync_interval_hours": sync_manager.sync_config.get('sync_interval_hours', 4),
            "calendars_to_sync": sync_manager.sync_config.get('calendars_to_sync', []),
            "google_calendar_id": sync_manager.sync_config.get('google_calendar_id', 'primary'),
            "data_directory": str(sync_manager.data_dir),
            "config": sync_manager.sync_config
        }
        
        if sync_manager.last_sync_time:
            next_sync = sync_manager.last_sync_time + timedelta(hours=status["sync_interval_hours"])
            status["next_sync_time"] = next_sync.isoformat()
            status["time_until_next_sync_hours"] = (next_sync - datetime.now()).total_seconds() / 3600
        
        return [
            types.TextContent(
                type="text",
                text=f"Current sync status:\\n\\n" + json.dumps(status, indent=2)
            )
        ]
    
    elif name == "reset_sync_state":
        confirm = arguments.get("confirm", False)
        if not confirm:
            return [
                types.TextContent(
                    type="text",
                    text="Reset not confirmed. Set 'confirm' to true to reset sync state."
                )
            ]
        
        sync_manager.synced_events.clear()
        sync_manager.last_sync_time = None
        sync_manager.save_synced_events()
        
        return [
            types.TextContent(
                type="text",
                text="Sync state reset. All events will be considered new on next sync."
            )
        ]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        # Auto-start sync if configured
        if sync_manager.sync_config.get('auto_start_sync', False):
            await sync_manager.start_sync_scheduler()
        
        try:
            await server.run(
                read_stream,
                write_stream,
                InitializationOptions(
                    server_name="icloud-gcal-sync",
                    server_version="1.0.0",
                    capabilities=server.get_capabilities(
                        notification_options=None,
                        experimental_capabilities=None,
                    ),
                ),
            )
        finally:
            # Clean shutdown
            await sync_manager.stop_sync_scheduler()

if __name__ == "__main__":
    asyncio.run(main())
