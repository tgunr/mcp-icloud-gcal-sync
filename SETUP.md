# iCloud to Google Calendar Sync - Setup Guide

## Quick Start

1. **Run the installation script:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

2. **Add to Claude Desktop configuration:**
   Edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
   ```json
   {
     "mcpServers": {
       "icloud-gcal-sync": {
         "command": "/Users/yourusername/AI/Servers/MCP/icloud-gcal-sync/venv/bin/python",
         "args": ["/Users/yourusername/AI/Servers/MCP/icloud-gcal-sync/src/icloud_gcal_sync.py"],
         "env": {}
       }
     }
   }
   ```

3. **Restart Claude Desktop**

## Initial Configuration

### 1. Check Available Calendars
```
list_icloud_calendars()
```

### 2. Configure Basic Sync
```
configure_sync({
  "sync_enabled": true,
  "sync_interval_hours": 4,
  "calendars_to_sync": ["Work", "Personal"],
  "days_back": 7,
  "days_forward": 30
})
```

### 3. Test with Dry Run
```
manual_sync({"dry_run": true})
```

## Google Calendar Integration (Optional)

### Prerequisites
1. Google Cloud Console account
2. Google Calendar API enabled
3. OAuth 2.0 credentials (Desktop application type)

### Setup Steps

1. **Enable Google Calendar API:**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create or select a project
   - Navigate to "APIs & Services" > "Library"
   - Search for "Google Calendar API" and enable it

2. **Create OAuth Credentials:**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - Choose "Desktop application"
   - Download the credentials JSON file

3. **Configure in MCP Server:**
   ```
   setup_google_calendar({
     "credentials_content": "paste the entire JSON content here"
   })
   ```

4. **Enable Integration:**
   ```
   configure_sync({
     "google_calendar_integration": true,
     "google_calendar_id": "primary"
   })
   ```

5. **Test Integration:**
   ```
   test_google_calendar()
   ```

## Available Tools

### Discovery Tools
- `list_icloud_calendars()` - Show all iCloud calendars
- `list_google_calendars()` - Show all Google calendars (requires setup)
- `get_icloud_events()` - Preview events from specific calendars

### Configuration Tools
- `configure_sync()` - Set up sync preferences
- `setup_google_calendar()` - Configure Google Calendar API

### Sync Management
- `start_sync()` - Begin automatic syncing
- `stop_sync()` - Stop automatic syncing
- `manual_sync()` - Run sync immediately
- `sync_status()` - Check current status

### Maintenance Tools
- `reset_sync_state()` - Clear sync history
- `test_google_calendar()` - Verify Google Calendar integration

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `sync_enabled` | `false` | Enable/disable automatic sync |
| `sync_interval_hours` | `4` | Hours between automatic syncs |
| `calendars_to_sync` | `[]` | List of iCloud calendar names to sync |
| `google_calendar_id` | `"primary"` | Target Google Calendar |
| `days_back` | `7` | Days in the past to sync |
| `days_forward` | `30` | Days in the future to sync |
| `auto_start_sync` | `false` | Auto-start sync on server startup |
| `google_calendar_integration` | `false` | Use Google Calendar API |
| `sync_direction` | `"icloud_to_google"` | Sync direction |
| `delete_removed_events` | `false` | Delete events removed from iCloud |
| `update_existing_events` | `true` | Update changed events |

## Troubleshooting

### Common Issues

1. **No iCloud calendars found:**
   - Ensure iCloud is configured in macOS Calendar app
   - Check that calendars are visible and syncing
   - Verify Calendar app has necessary permissions

2. **Permission denied errors:**
   - Grant Calendar access to Terminal/Claude Desktop
   - Check System Preferences > Privacy & Security > Calendar

3. **Google Calendar authentication fails:**
   - Verify credentials JSON is correct
   - Check that Google Calendar API is enabled
   - Ensure OAuth consent screen is configured

4. **Sync not working:**
   - Check `sync_status()` for current state
   - Verify `sync_enabled: true` in configuration
   - Look at logs in `~/AI/Servers/MCP/icloud-gcal-sync/logs/`

### Log Files
- Main log: `~/AI/Servers/MCP/icloud-gcal-sync/logs/icloud_sync.log`
- Configuration: `~/AI/Servers/MCP/icloud-gcal-sync/data/config.json`
- Sync state: `~/AI/Servers/MCP/icloud-gcal-sync/data/sync_state.pkl`

### Reset Everything
If you need to start fresh:
```
reset_sync_state({"confirm": true})
```

## Advanced Usage

### Custom Calendar Selection
```
configure_sync({
  "calendars_to_sync": ["Work", "Personal", "Family"],
  "google_calendar_id": "your-specific-calendar-id@gmail.com"
})
```

### Frequent Syncing
```
configure_sync({
  "sync_interval_hours": 1,  // Sync every hour
  "auto_start_sync": true    // Start automatically
})
```

### Extended Date Range
```
configure_sync({
  "days_back": 30,    // Last 30 days
  "days_forward": 90  // Next 90 days
})
```

## Security & Privacy

- All data processing happens locally on your machine
- No calendar data is transmitted except to Google Calendar (if enabled)
- OAuth tokens are stored securely in local files
- iCloud access is read-only through the Calendar app

## Support

For issues, feature requests, or contributions:
- GitHub: [mcp-icloud-gcal-sync](https://github.com/tgunr/mcp-icloud-gcal-sync)
- Check logs for detailed error information
- Use `sync_status()` to diagnose configuration issues
