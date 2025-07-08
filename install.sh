#!/bin/bash

# iCloud to Google Calendar Sync MCP Server Installation Script

set -e

# Configuration
INSTALL_DIR="$HOME/AI/Servers/MCP/icloud-gcal-sync"
PYTHON_ENV="$INSTALL_DIR/venv"
CONFIG_FILE="$HOME/Library/Application Support/Claude/claude_desktop_config.json"

echo "🍎📅 Installing iCloud to Google Calendar Sync MCP Server..."

# Create directory structure
echo "📁 Creating directory structure..."
mkdir -p "$INSTALL_DIR/src"
mkdir -p "$INSTALL_DIR/data"
mkdir -p "$INSTALL_DIR/logs"

# Copy files if running from git repo
if [ -f "src/icloud_gcal_sync.py" ]; then
    echo "📋 Copying files from repository..."
    cp src/icloud_gcal_sync.py "$INSTALL_DIR/src/"
    cp requirements.txt "$INSTALL_DIR/"
    cp package.json "$INSTALL_DIR/"
else
    echo "⚠️  Running outside of git repository. Please manually copy files."
fi

# Create Python virtual environment
echo "🐍 Setting up Python virtual environment..."
python3 -m venv "$PYTHON_ENV"
source "$PYTHON_ENV/bin/activate"

# Install dependencies
echo "📦 Installing dependencies..."
pip install --upgrade pip
pip install mcp asyncio typing-extensions

# Make the script executable
chmod +x "$INSTALL_DIR/src/icloud_gcal_sync.py"

echo "✅ Installation complete!"
echo
echo "📋 Next steps:"
echo "1. Add this to your Claude Desktop config:"
echo "   \"icloud-gcal-sync\": {"
echo "     \"command\": \"$PYTHON_ENV/bin/python\","
echo "     \"args\": [\"$INSTALL_DIR/src/icloud_gcal_sync.py\"]"
echo "   }"
echo
echo "2. Restart Claude Desktop"
echo "3. Use configure_sync to enable and set up sync"
echo "4. Use start_sync to begin automatic syncing"
echo
echo "📁 Installed to: $INSTALL_DIR"
echo "📊 Status: Ready to configure"
echo
echo "🔧 Quick start commands:"
echo "   list_icloud_calendars()                    # See available calendars"
echo "   configure_sync({\"sync_enabled\": true})     # Enable sync"
echo "   start_sync()                               # Start automatic sync"