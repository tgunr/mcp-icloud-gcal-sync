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
    asyncio.run(main())                interval_hours = self.sync_config.get('sync_interval_hours', 4)
                await asyncio.sleep(interval_hours * 3600)
                
        except asyncio.CancelledError:
            logger.info("Sync loop cancelled")
            raise

# Initialize the sync manager
sync_manager = EnhancedSyncManager()

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
            name="list_google_calendars",
            description="List all available Google Calendar calendars (requires Google Calendar integration)",
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
            description="Configure sync settings including enabled calendars, intervals, and Google Calendar integration",
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
                    "auto_start_sync": {"type": "boolean", "description": "Auto-start sync on server startup"},
                    "google_calendar_integration": {"type": "boolean", "description": "Enable Google Calendar API integration"},
                    "sync_direction": {"type": "string", "description": "Sync direction: 'icloud_to_google' or 'bidirectional'"},
                    "delete_removed_events": {"type": "boolean", "description": "Delete events from Google Calendar when removed from iCloud"},
                    "update_existing_events": {"type": "boolean", "description": "Update existing events when changed in iCloud"}
                },
                "required": []
            }
        ),
        types.Tool(
            name="setup_google_calendar",
            description="Setup Google Calendar integration with OAuth credentials",
            inputSchema={
                "type": "object",
                "properties": {
                    "credentials_content": {
                        "type": "string",
                        "description": "Content of the Google Cloud Console OAuth2 credentials JSON file"
                    }
                },
                "required": ["credentials_content"]
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
        ),
        types.Tool(
            name="test_google_calendar",
            description="Test Google Calendar integration by creating and deleting a test event",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
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
    
    elif name == "list_google_calendars":
        if not GOOGLE_CALENDAR_AVAILABLE:
            return [
                types.TextContent(
                    type="text",
                    text="Google Calendar integration not available. Please install required packages:\\n" +
                         "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
                )
            ]
        
        if not sync_manager.gcal_manager:
            return [
                types.TextContent(
                    type="text",
                    text="Google Calendar not configured. Use 'setup_google_calendar' tool first."
                )
            ]
        
        calendars = sync_manager.get_google_calendars()
        return [
            types.TextContent(
                type="text",
                text=f"Available Google Calendar calendars:\\n\\n" + json.dumps(calendars, indent=2)
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
            if key in current_config or key in [
                'sync_enabled', 'sync_interval_hours', 'calendars_to_sync', 'google_calendar_id',
                'days_back', 'days_forward', 'auto_start_sync', 'google_calendar_integration',
                'sync_direction', 'delete_removed_events', 'update_existing_events'
            ]:
                current_config[key] = value
        
        sync_manager.save_config(current_config)
        
        return [
            types.TextContent(
                type="text",
                text=f"Sync configuration updated:\\n\\n" + json.dumps(current_config, indent=2)
            )
        ]
    
    elif name == "setup_google_calendar":
        if not GOOGLE_CALENDAR_AVAILABLE:
            return [
                types.TextContent(
                    type="text",
                    text="Google Calendar integration not available. Please install required packages:\\n" +
                         "pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
                )
            ]
        
        credentials_content = arguments.get("credentials_content", "")
        if not credentials_content:
            return [
                types.TextContent(
                    type="text",
                    text="Please provide the content of your Google Cloud Console OAuth2 credentials JSON file."
                )
            ]
        
        try:
            # Validate JSON format
            credentials_data = json.loads(credentials_content)
            
            # Save credentials file
            with open(sync_manager.credentials_path, 'w') as f:
                json.dump(credentials_data, f, indent=2)
            
            # Initialize Google Calendar manager
            from google_calendar_integration import GoogleCalendarManager
            sync_manager.gcal_manager = GoogleCalendarManager(
                str(sync_manager.credentials_path),
                str(sync_manager.token_path)
            )
            
            return [
                types.TextContent(
                    type="text",
                    text="Google Calendar integration setup completed successfully. " +
                         "You may need to authenticate in your browser."
                )
            ]
            
        except json.JSONDecodeError:
            return [
                types.TextContent(
                    type="text",
                    text="Invalid JSON format in credentials content."
                )
            ]
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Error setting up Google Calendar integration: {str(e)}"
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
            "google_calendar_integration": sync_manager.sync_config.get('google_calendar_integration', False),
            "google_calendar_available": GOOGLE_CALENDAR_AVAILABLE,
            "google_calendar_configured": sync_manager.gcal_manager is not None,
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
    
    elif name == "test_google_calendar":
        if not GOOGLE_CALENDAR_AVAILABLE:
            return [
                types.TextContent(
                    type="text",
                    text="Google Calendar integration not available. Please install required packages."
                )
            ]
        
        if not sync_manager.gcal_manager:
            return [
                types.TextContent(
                    type="text",
                    text="Google Calendar not configured. Use 'setup_google_calendar' tool first."
                )
            ]
        
        try:
            # Create a test event
            test_event = {
                'title': 'iCloud Sync Test Event',
                'description': 'This is a test event created by the iCloud sync MCP server',
                'location': 'Test Location',
                'start_date': datetime.now().isoformat(),
                'end_date': (datetime.now() + timedelta(hours=1)).isoformat(),
                'all_day': False,
                'calendar': 'Test',
                'uid': f'test_event_{int(datetime.now().timestamp())}'
            }
            
            google_calendar_id = sync_manager.sync_config.get('google_calendar_id', 'primary')
            
            # Create the event
            created_event = sync_manager.gcal_manager.create_event(google_calendar_id, test_event)
            
            if created_event:
                # Delete the test event
                deleted = sync_manager.gcal_manager.delete_event(google_calendar_id, created_event['id'])
                
                result = {
                    "success": True,
                    "message": "Google Calendar integration test successful",
                    "test_event_created": True,
                    "test_event_deleted": deleted,
                    "google_calendar_id": google_calendar_id,
                    "created_event_id": created_event['id']
                }
            else:
                result = {
                    "success": False,
                    "message": "Failed to create test event in Google Calendar",
                    "google_calendar_id": google_calendar_id
                }
            
            return [
                types.TextContent(
                    type="text",
                    text=f"Google Calendar test result:\\n\\n" + json.dumps(result, indent=2)
                )
            ]
            
        except Exception as e:
            return [
                types.TextContent(
                    type="text",
                    text=f"Google Calendar test failed: {str(e)}"
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
