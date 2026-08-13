"""
Time formatting and calculation helpers.
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

def parse_iso_timestamp(ts_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO 8601 timestamp string resiliently into a timezone-aware datetime."""
    if not ts_str:
        return None
    try:
        # Handle 'Z' suffix
        cleaned = ts_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None

def format_relative_reset(resets_at_str: Optional[str], now: Optional[datetime] = None) -> str:
    """Format reset timestamp into human-readable relative duration e.g. '1h 32m' or '3d 4h'."""
    reset_dt = parse_iso_timestamp(resets_at_str)
    if not reset_dt:
        return "Unknown"

    if now is None:
        now = datetime.now(timezone.utc)

    delta = reset_dt - now
    total_seconds = int(delta.total_seconds())

    if total_seconds <= 0:
        return "Resets now"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"{days}d {hours}h"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m"
    else:
        return "< 1m"

def format_short_time(dt: Optional[datetime] = None) -> str:
    """Format short time e.g. '18:24'."""
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%H:%M")

def get_utc_iso_now() -> str:
    """Get current UTC timestamp in ISO 8601 format."""
    return datetime.now(timezone.utc).isoformat()
