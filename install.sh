#!/bin/bash

# iCloud to Google Calendar Sync MCP Server Installation Script
# This script sets up the complete project with optional Google Calendar integration

set -e

echo "🍎📅 iCloud to Google Calendar Sync MCP Server Installation"
echo "============================================================"

# Define paths
BASE_DIR="$HOME/AI/Servers/MCP/icloud-gcal-sync"
SRC_DIR="$BASE_DIR/src"
DATA_DIR="$BASE_DIR/data"
LOGS_DIR="$BASE_DIR/logs"
VENV_DIR="$BASE_DIR/venv"

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p "$BASE_DIR" "$SRC_DIR" "$DATA_DIR" "$LOGS_DIR"

# Copy source files if they exist in current directory
if [ -f "src/icloud_gcal_sync_complete.py" ]; then
    echo "📄 Copying main sync script..."
    cp "src/icloud_gcal_sync_complete.py" "$SRC_DIR/icloud_gcal_sync.py"
fi

if [ -f "src/google_calendar_integration.py" ]; then
    echo "📄 Copying Google Calendar integration..."
    cp "src/google_calendar_integration.py" "$SRC_DIR/"
fi

if [ -f "requirements.txt" ]; then
    echo "📄 Copying requirements..."
    cp "requirements.txt" "$BASE_DIR/"
fi

if [ -f "package.json" ]; then
    echo "📄 Copying package.json..."
    cp "package.json" "$BASE_DIR/"
fi

if [ -f "README.md" ]; then
    echo "📄 Copying README..."
    cp "README.md" "$BASE_DIR/"
fi

# Set up Python virtual environment
echo "🐍 Setting up Python virtual environment..."
cd "$BASE_DIR"

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install base requirements
echo "📦 Installing base requirements..."
pip install --upgrade pip
pip install mcp asyncio typing-extensions

# Ask user about Google Calendar integration
echo ""
echo "🔗 Google Calendar Integration Setup"
echo "====================================="
echo "Do you want to install Google Calendar API dependencies?"
echo "This enables direct integration with Google Calendar."
echo ""
read -p "Install Google Calendar integration? (y/N): " install_gcal

if [[ "$install_gcal" =~ ^[Yy]$ ]]; then
    echo "📦 Installing Google Calendar API dependencies..."
    pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
    
    echo ""
    echo "✅ Google Calendar dependencies installed!"
    echo ""
    echo "📋 To complete Google Calendar setup:"
    echo "1. Go to Google Cloud Console (https://console.cloud.google.com)"
    echo "2. Create a new project or select existing one"
    echo "3. Enable the Google Calendar API"
    echo "4. Create OAuth 2.0 credentials (Desktop application)"
    echo "5. Download the credentials JSON file"
    echo "6. Use the 'setup_google_calendar' tool with the JSON content"
    echo ""
else
    echo "⚠️  Skipping Google Calendar integration."
    echo "   You can install it later with:"
    echo "   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib"
fi

# Create a simple config file
echo "⚙️  Creating initial configuration..."
cat > "$DATA_DIR/config.json" << EOF
{
  "sync_enabled": false,
  "sync_interval_hours": 4,
  "calendars_to_sync": [],
  "google_calendar_id": "primary",
  "days_back": 7,
  "days_forward": 30,
  "auto_start_sync": false,
  "google_calendar_integration": false,
  "sync_direction": "icloud_to_google",
  "delete_removed_events": false,
  "update_existing_events": true
}
EOF

# Make scripts executable
chmod +x "$SRC_DIR"/*.py 2>/dev/null || true

# Create wrapper script
echo "🔧 Creating wrapper script..."
cat > "$BASE_DIR/run.sh" << EOF
#!/bin/bash
cd "$BASE_DIR"
source venv/bin/activate
python src/icloud_gcal_sync.py
EOF
chmod +x "$BASE_DIR/run.sh"

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "📁 Project installed at: $BASE_DIR"
echo ""
echo "🚀 Next Steps:"
echo "============="
echo ""
echo "1. Add to Claude Desktop config:"
echo "   File: ~/Library/Application Support/Claude/claude_desktop_config.json"
echo ""
echo '   "mcpServers": {'
echo '     "icloud-gcal-sync": {'
echo "       \"command\": \"$VENV_DIR/bin/python\","
echo "       \"args\": [\"$SRC_DIR/icloud_gcal_sync.py\"],"
echo '       "env": {}'
echo '     }'
echo '   }'
echo ""
echo "2. Restart Claude Desktop"
echo ""
echo "3. Use these tools to get started:"
echo "   - list_icloud_calendars()"
echo "   - configure_sync({...})"
echo "   - manual_sync({\"dry_run\": true})"
echo ""
if [[ "$install_gcal" =~ ^[Yy]$ ]]; then
    echo "4. For Google Calendar integration:"
    echo "   - Download OAuth credentials from Google Cloud Console"
    echo "   - Use setup_google_calendar({\"credentials_content\": \"...\"})"
    echo "   - Enable integration with configure_sync({\"google_calendar_integration\": true})"
    echo ""
fi
echo "📖 Read the full documentation: $BASE_DIR/README.md"
echo ""
echo "🎉 Happy syncing!"
