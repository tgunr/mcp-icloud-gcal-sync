#!/usr/bin/env python3

"""
Test script for iCloud to Google Calendar Sync MCP Server
Run this to verify that the installation is working correctly.
"""

import json
import sys
from pathlib import Path

def test_imports():
    """Test that all required modules can be imported"""
    print("🔍 Testing imports...")
    
    try:
        import asyncio
        print("  ✅ asyncio")
    except ImportError as e:
        print(f"  ❌ asyncio: {e}")
        return False
    
    try:
        import mcp.server.stdio
        import mcp.types as types
        from mcp.server import Server
        print("  ✅ MCP server modules")
    except ImportError as e:
        print(f"  ❌ MCP server modules: {e}")
        return False
    
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        print("  ✅ Google Calendar API modules (optional)")
        google_available = True
    except ImportError:
        print("  ⚠️  Google Calendar API modules not available (optional)")
        google_available = False
    
    return True, google_available

def test_directory_structure():
    """Test that the directory structure is correct"""
    print("\n📁 Testing directory structure...")
    
    base_dir = Path.home() / "AI" / "Servers" / "MCP" / "icloud-gcal-sync"
    required_dirs = [
        base_dir,
        base_dir / "src",
        base_dir / "data",
        base_dir / "logs",
        base_dir / "venv"
    ]
    
    all_exist = True
    for dir_path in required_dirs:
        if dir_path.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path}")
            all_exist = False
    
    return all_exist

def test_source_files():
    """Test that source files exist and are valid"""
    print("\n📄 Testing source files...")
    
    base_dir = Path.home() / "AI" / "Servers" / "MCP" / "icloud-gcal-sync"
    src_dir = base_dir / "src"
    
    required_files = [
        src_dir / "icloud_gcal_sync.py",
        base_dir / "requirements.txt",
        base_dir / "package.json"
    ]
    
    optional_files = [
        src_dir / "google_calendar_integration.py",
        base_dir / "README.md",
        base_dir / "SETUP.md"
    ]
    
    all_required_exist = True
    
    for file_path in required_files:
        if file_path.exists() and file_path.stat().st_size > 0:
            print(f"  ✅ {file_path.name}")
        else:
            print(f"  ❌ {file_path.name}")
            all_required_exist = False
    
    for file_path in optional_files:
        if file_path.exists():
            print(f"  ✅ {file_path.name} (optional)")
        else:
            print(f"  ⚠️  {file_path.name} (optional, missing)")
    
    return all_required_exist

def test_configuration():
    """Test that configuration files are valid"""
    print("\n⚙️  Testing configuration...")
    
    base_dir = Path.home() / "AI" / "Servers" / "MCP" / "icloud-gcal-sync"
    config_path = base_dir / "data" / "config.json"
    
    if config_path.exists():
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            required_keys = [
                'sync_enabled', 'sync_interval_hours', 'calendars_to_sync',
                'google_calendar_id', 'days_back', 'days_forward'
            ]
            
            missing_keys = [key for key in required_keys if key not in config]
            
            if not missing_keys:
                print("  ✅ config.json is valid")
                return True
            else:
                print(f"  ❌ config.json missing keys: {missing_keys}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"  ❌ config.json invalid JSON: {e}")
            return False
    else:
        print("  ❌ config.json not found")
        return False

def test_virtual_environment():
    """Test that virtual environment is set up correctly"""
    print("\n🐍 Testing virtual environment...")
    
    base_dir = Path.home() / "AI" / "Servers" / "MCP" / "icloud-gcal-sync"
    venv_dir = base_dir / "venv"
    
    if not venv_dir.exists():
        print("  ❌ Virtual environment directory not found")
        return False
    
    python_path = venv_dir / "bin" / "python"
    if not python_path.exists():
        python_path = venv_dir / "Scripts" / "python.exe"  # Windows
    
    if python_path.exists():
        print("  ✅ Python executable found")
    else:
        print("  ❌ Python executable not found in venv")
        return False
    
    # Check if MCP is installed
    try:
        import subprocess
        result = subprocess.run(
            [str(python_path), "-c", "import mcp; print('MCP version:', mcp.__version__ if hasattr(mcp, '__version__') else 'unknown')"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"  ✅ MCP installed: {result.stdout.strip()}")
        else:
            print(f"  ❌ MCP not properly installed: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ❌ Error checking MCP installation: {e}")
        return False
    
    return True

def test_applescript():
    """Test that AppleScript can access Calendar app"""
    print("\n🍎 Testing AppleScript Calendar access...")
    
    try:
        import subprocess
        
        # Simple test to see if Calendar app is accessible
        script = '''
        tell application "Calendar"
            try
                set calendarCount to count of calendars
                return "Found " & calendarCount & " calendars"
            on error errMsg
                return "Error: " & errMsg
            end try
        end tell
        '''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "Found" in output and "calendars" in output:
                print(f"  ✅ Calendar access working: {output}")
                return True
            else:
                print(f"  ⚠️  Calendar access uncertain: {output}")
                return False
        else:
            print(f"  ❌ Calendar access failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("  ❌ Calendar access timed out (may need permission)")
        return False
    except Exception as e:
        print(f"  ❌ Error testing Calendar access: {e}")
        return False

def test_server_syntax():
    """Test that the main server script has valid syntax"""
    print("\n🔧 Testing server script syntax...")
    
    base_dir = Path.home() / "AI" / "Servers" / "MCP" / "icloud-gcal-sync"
    server_script = base_dir / "src" / "icloud_gcal_sync.py"
    
    if not server_script.exists():
        print("  ❌ Server script not found")
        return False
    
    try:
        import subprocess
        venv_python = base_dir / "venv" / "bin" / "python"
        if not venv_python.exists():
            venv_python = base_dir / "venv" / "Scripts" / "python.exe"
        
        result = subprocess.run(
            [str(venv_python), "-m", "py_compile", str(server_script)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("  ✅ Server script syntax is valid")
            return True
        else:
            print(f"  ❌ Server script syntax error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error checking server script: {e}")
        return False

def generate_claude_config():
    """Generate the Claude Desktop configuration snippet"""
    print("\n📋 Claude Desktop Configuration:")
    print("=" * 50)
    
    base_dir = Path.home() / "AI" / "Servers" / "MCP" / "icloud-gcal-sync"
    venv_python = base_dir / "venv" / "bin" / "python"
    server_script = base_dir / "src" / "icloud_gcal_sync.py"
    
    config = {
        "mcpServers": {
            "icloud-gcal-sync": {
                "command": str(venv_python),
                "args": [str(server_script)],
                "env": {}
            }
        }
    }
    
    print(json.dumps(config, indent=2))
    print()
    print(f"Add this to: ~/Library/Application Support/Claude/claude_desktop_config.json")
    print()

def main():
    """Run all tests"""
    print("🍎📅 iCloud to Google Calendar Sync - Installation Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_imports),
        ("Directory Structure", test_directory_structure),
        ("Source Files", test_source_files),
        ("Configuration", test_configuration),
        ("Virtual Environment", test_virtual_environment),
        ("AppleScript Access", test_applescript),
        ("Server Script Syntax", test_server_syntax)
    ]
    
    results = []
    google_available = False
    
    for test_name, test_func in tests:
        try:
            if test_name == "Import Test":
                result, google_available = test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"  ❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if google_available:
        print("✅ Google Calendar integration available")
    else:
        print("⚠️  Google Calendar integration not available (optional)")
    
    if passed == total:
        print("\n🎉 All tests passed! Installation looks good.")
        generate_claude_config()
        
        print("🚀 Next steps:")
        print("1. Add the configuration above to Claude Desktop")
        print("2. Restart Claude Desktop")
        print("3. Try: list_icloud_calendars()")
        
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please check the issues above.")
        print("\nTroubleshooting tips:")
        print("- Run: chmod +x install.sh && ./install.sh")
        print("- Check Calendar app permissions in System Preferences")
        print("- Ensure iCloud is configured in Calendar app")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
