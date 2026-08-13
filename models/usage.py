"""
Data models and normalization logic for Claude Usage Monitor.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from utils.time import format_relative_reset, get_utc_iso_now

class StatusLevel(str, Enum):
    SAFE = "SAFE"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    ERROR = "ERROR"
    OFFLINE = "OFFLINE"

def normalize_utilization(val: Any) -> float:
    """
    Normalize raw API utilization values.
    Handles:
      - 0.42 -> 42.0
      - 42 -> 42.0
      - "42%" -> 42.0
      - None / Invalid -> 0.0
      - Values <= 1.0 (e.g. 0.85 -> 85.0, exception: 0.0 -> 0.0, 1.0 -> 100.0 if fractional, but 1% vs 100%)
    Rule:
      If 0 < val <= 1.0, treat as fractional percentage (0.85 -> 85.0%).
      If val > 1.0, treat as direct percentage (85.0 -> 85.0%).
      Clamp final value to range [0.0, 100.0].
    """
    if val is None:
        return 0.0

    try:
        if isinstance(val, str):
            val = val.replace("%", "").strip()
        num = float(val)
    except (ValueError, TypeError):
        return 0.0

    if num < 0:
        return 0.0

    # If num is between 0.0 and 1.0 (exclusive of 0, inclusive of 1.0 if fractional)
    # Note: 1.0 represents 100% when fractional, or 1% if integer. But in Claude API, 1.0 utilization = 100% capacity limit hit.
    if 0.0 < num <= 1.0:
        num = num * 100.0

    return min(max(num, 0.0), 100.0)


@dataclass
class UsageWindow:
    utilization: float  # Percentage (0.0 - 100.0)
    resets_at: Optional[str] = None  # ISO 8601 string

    def formatted_utilization(self) -> str:
        return f"{self.utilization:.0f}%"

    def relative_reset(self) -> str:
        return format_relative_reset(self.resets_at)


@dataclass
class ClaudeUsage:
    five_hour: UsageWindow
    seven_day: UsageWindow
    timestamp: str = field(default_factory=get_utc_iso_now)
    status_level: StatusLevel = StatusLevel.SAFE
    error_message: Optional[str] = None

    @classmethod
    def from_api_json(
        cls,
        data: Dict[str, Any],
        warning_threshold: float = 80.0,
        critical_threshold: float = 90.0
    ) -> "ClaudeUsage":
        """
        Parses raw API JSON response flexibly.
        Supports expected structure:
        {
          "five_hour": {"utilization": 42, "resets_at": "..."},
          "seven_day": {"utilization": 67, "resets_at": "..."}
        }
        Also handles alternative keys like '5_hour', '7_day', 'weekly', etc.
        """
        fh_raw = data.get("five_hour") or data.get("5_hour") or data.get("five_hours") or {}
        sd_raw = data.get("seven_day") or data.get("7_day") or data.get("weekly") or data.get("seven_days") or {}

        fh_util = normalize_utilization(fh_raw.get("utilization") if isinstance(fh_raw, dict) else fh_raw)
        fh_reset = fh_raw.get("resets_at") or fh_raw.get("reset_at") if isinstance(fh_raw, dict) else None

        sd_util = normalize_utilization(sd_raw.get("utilization") if isinstance(sd_raw, dict) else sd_raw)
        sd_reset = sd_raw.get("resets_at") or sd_raw.get("reset_at") if isinstance(sd_raw, dict) else None

        five_hour_window = UsageWindow(utilization=fh_util, resets_at=fh_reset)
        seven_day_window = UsageWindow(utilization=sd_util, resets_at=sd_reset)

        # Determine status level
        max_util = max(fh_util, sd_util)
        if max_util >= critical_threshold:
            status = StatusLevel.CRITICAL
        elif max_util >= warning_threshold:
            status = StatusLevel.WARNING
        else:
            status = StatusLevel.SAFE

        return cls(
            five_hour=five_hour_window,
            seven_day=seven_day_window,
            timestamp=get_utc_iso_now(),
            status_level=status
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "five_hour": {
                "utilization": self.five_hour.utilization,
                "formatted": self.five_hour.formatted_utilization(),
                "resets_at": self.five_hour.resets_at,
                "relative_reset": self.five_hour.relative_reset()
            },
            "seven_day": {
                "utilization": self.seven_day.utilization,
                "formatted": self.seven_day.formatted_utilization(),
                "resets_at": self.seven_day.resets_at,
                "relative_reset": self.seven_day.relative_reset()
            },
            "timestamp": self.timestamp,
            "status_level": self.status_level.value,
            "error_message": self.error_message
        }
