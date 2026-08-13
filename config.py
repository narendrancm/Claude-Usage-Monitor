"""
Configuration defaults and constants for Claude Usage Monitor.
"""
import os
import sys
from pathlib import Path

APP_NAME = "Claude Usage Monitor"
APP_AUTHOR = "Antigravity"
VERSION = "1.0.0"

# Anthropic Usage API endpoint (Internal/OAuth endpoint)
DEFAULT_API_URL = "https://api.anthropic.com/api/oauth/usage"
DEFAULT_POLL_INTERVAL_MINUTES = 15
DEFAULT_WARNING_THRESHOLD = 80.0  # Percentage
DEFAULT_CRITICAL_THRESHOLD = 90.0 # Percentage
DEFAULT_RETENTION_DAYS = 30

# Credential Manager Target Name
CREDENTIAL_TARGET = "Claude Code-credentials"

# File System Paths
def get_app_dir() -> Path:
    """Get persistent directory in %APPDATA%/ClaudeUsageMonitor."""
    app_data = os.environ.get("APPDATA")
    if app_data:
        base = Path(app_data) / "ClaudeUsageMonitor"
    else:
        base = Path.home() / ".claude_usage_monitor"
    base.mkdir(parents=True, exist_ok=True)
    return base

DB_PATH = get_app_dir() / "history.db"
LOG_PATH = get_app_dir() / "app.log"
CONFIG_FILE_PATH = get_app_dir() / "settings.json"

# Header defaults
DEFAULT_USER_AGENT = f"ClaudeUsageMonitor/{VERSION} (Windows NT)"
DEFAULT_BETA_HEADER = "oauth-2025-01-01"
