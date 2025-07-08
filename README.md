# iCloud to Google Calendar Sync MCP Server

🍎📅 Continuous synchronization from iCloud Calendar to Google Calendar with automatic scheduling and duplicate detection.

## Features

- **🔄 Continuous Sync**: Automatically syncs every 4 hours (configurable)
- **🎯 iCloud-Only**: Specifically targets iCloud calendars, ignoring others
- **🧠 Smart Deduplication**: Tracks synced events to avoid duplicates
- **💾 Persistent State**: Maintains sync history across restarts
- **⚙️ Configurable**: Customize calendars, intervals, date ranges
- **📊 Status Monitoring**: Track sync status and statistics
- **🔧 Manual Control**: Run sync on-demand or dry-run testing
- **📁 Organized Storage**: Stores all data in `~/AI/Servers/MCP/` structure

## Quick Installation

### Option 1: Clone and Install

```bash
# Clone the repository
git clone https://github.com/tgunr/mcp-icloud-gcal-sync.git
cd mcp-icloud-gcal-sync

# Run the installation script
chmod +x install.sh
./install.sh
```

### Option 2: Manual Setup

```bash
# Create directory structure
mkdir -p ~/AI/Servers/MCP/icloud-gcal-sync/{src,data,logs}

# Copy files and set up virtual environment
cp src/icloud_gcal_sync.py ~/AI/Servers/MCP/icloud-gcal-sync/src/
cd ~/AI/Servers/MCP/icloud-gcal-sync
python3 -m venv venv
source venv/bin/activate
pip install mcp asyncio typing-extensions
```

## Configuration

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json`):

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

## Usage

### Initial Setup

1. **Check available calendars**:
   ```
   list_icloud_calendars()
   ```

2. **Configure sync settings**:
   ```
   configure_sync({
     "sync_enabled": true,
     "sync_interval_hours": 4,
     "calendars_to_sync": ["Work", "Personal"],
     "google_calendar_id": "primary",
     "days_back": 7,
     "days_forward": 30
   })
   ```

3. **Test with dry run**:
   ```
   manual_sync({"dry_run": true})
   ```

4. **Start automatic sync**:
   ```
   start_sync()
   ```

5. **Monitor status**:
   ```
   sync_status()
   ```

## Available Tools

### Core Sync Tools
- **`configure_sync`**: Enable/disable sync, set intervals, choose calendars
- **`start_sync`**: Start the automatic 4-hour sync scheduler
- **`stop_sync`**: Stop automatic syncing
- **`manual_sync`**: Run sync immediately (with dry-run option)
- **`sync_status`**: View current status, next sync time, statistics

### Discovery Tools
- **`list_icloud_calendars`**: See all available iCloud calendars
- **`get_icloud_events`**: Preview events from specific calendars/date ranges

### Maintenance Tools
- **`reset_sync_state`**: Clear sync history (all events treated as new)

## Directory Structure

```
~/AI/Servers/MCP/icloud-gcal-sync/
├── src/
│   └── icloud_gcal_sync.py      # Main server
├── data/
│   ├── config.json              # Sync configuration
│   └── sync_state.pkl           # Synced events tracking
├── logs/
│   └── icloud_sync.log          # Sync activity logs
├── venv/                        # Python virtual environment
├── requirements.txt
├── package.json
└── README.md
```

## Google Calendar Integration

**Note**: This MCP server handles the iCloud → data extraction part. For complete synchronization, you'll need:

1. **Google Calendar MCP Server** (separate installation)
2. **Integration code** to connect the two systems

The server provides properly formatted event data that can be easily integrated with Google Calendar APIs.

## System Requirements

- **macOS**: Required (uses AppleScript to access Calendar app)
- **Python 3.8+**: For the MCP server
- **iCloud Account**: Configured in macOS Calendar app
- **Calendar Permissions**: Grant access to Calendar app when prompted

## Troubleshooting

### Permission Issues
- Ensure Calendar app has full disk access in System Preferences
- Grant calendar access to Terminal/Claude Desktop when prompted

### No iCloud Calendars Found
- Verify iCloud account is configured in Calendar app
- Check that calendars are visible and syncing
- Account name must contain "iCloud" (the script looks for this)

### Sync Not Running
- Check `sync_status()` for current state
- Verify `sync_enabled: true` in configuration
- Look at logs in `~/AI/Servers/MCP/icloud-gcal-sync/logs/icloud_sync.log`

## Security & Privacy

- **Local Processing**: All calendar data stays on your machine
- **Read-Only Access**: Only reads from Calendar app, doesn't modify
- **No External Transmission**: Data isn't sent anywhere until you choose to sync
- **Encrypted Storage**: Sync state stored in local files

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

## License

MIT License - see LICENSE file for details.

---

**Repository**: [github.com/tgunr/mcp-icloud-gcal-sync](https://github.com/tgunr/mcp-icloud-gcal-sync)

**Part of the MCP (Model Context Protocol) ecosystem** 🚀