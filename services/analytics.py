"""
Analytics calculations service.
Derives trend, rate of change, peak usage, and estimated time-to-limit.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from utils.time import parse_iso_timestamp

class UsageAnalytics:
    @staticmethod
    def analyze(history_records: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyzes historical records to derive meaningful stats.
        Returns dictionary with analytics metrics.
        """
        if not history_records or len(history_records) < 2:
            return {
                "has_data": False,
                "rate_per_hour": 0.0,
                "trend": "STABLE",
                "estimated_minutes_to_limit": None,
                "peak_today_5h": 0.0,
                "peak_today_weekly": 0.0,
                "summary": "Insufficient data to compute trend."
            }

        # Filter sorted by timestamp
        sorted_recs = sorted(history_records, key=lambda r: r.get("timestamp", ""))

        # Compute peak today
        now = datetime.now(timezone.utc)
        today_str = now.strftime("%Y-%m-%d")

        today_recs = [r for r in sorted_recs if r.get("timestamp", "").startswith(today_str)]
        peak_5h = max((r.get("five_hour", 0.0) for r in today_recs), default=sorted_recs[-1].get("five_hour", 0.0))
        peak_weekly = max((r.get("weekly", 0.0) for r in today_recs), default=sorted_recs[-1].get("weekly", 0.0))

        # Recent trend using latest 2-5 records (last 1-2 hours)
        recent = sorted_recs[-5:]
        first_rec = recent[0]
        last_rec = recent[-1]

        dt_start = parse_iso_timestamp(first_rec.get("timestamp"))
        dt_end = parse_iso_timestamp(last_rec.get("timestamp"))

        if not dt_start or not dt_end or dt_end <= dt_start:
            return {
                "has_data": True,
                "rate_per_hour": 0.0,
                "trend": "STABLE",
                "estimated_minutes_to_limit": None,
                "peak_today_5h": round(peak_5h, 1),
                "peak_today_weekly": round(peak_weekly, 1),
                "summary": "Usage is steady."
            }

        hours_elapsed = (dt_end - dt_start).total_seconds() / 3600.0
        val_start = first_rec.get("five_hour", 0.0)
        val_end = last_rec.get("five_hour", 0.0)

        delta_val = val_end - val_start
        rate_per_hour = delta_val / hours_elapsed if hours_elapsed > 0 else 0.0

        # Determine trend
        if rate_per_hour > 2.0:
            trend = "INCREASING"
        elif rate_per_hour < -2.0:
            trend = "DECREASING"
        else:
            trend = "STABLE"

        # Estimated minutes to limit (100%) if increasing
        est_minutes = None
        summary = "Usage is steady."
        if trend == "INCREASING" and val_end < 100.0 and rate_per_hour > 0:
            remaining_pct = 100.0 - val_end
            est_hours = remaining_pct / rate_per_hour
            est_minutes = int(est_hours * 60)

            if est_minutes < 60:
                summary = f"At current rate, 5-hour limit may be reached in ~{est_minutes} minutes."
            else:
                summary = f"Usage increasing at +{rate_per_hour:.1f}%/hr."
        elif trend == "DECREASING":
            summary = "Usage rate is declining."

        return {
            "has_data": True,
            "rate_per_hour": round(rate_per_hour, 1),
            "trend": trend,
            "estimated_minutes_to_limit": est_minutes,
            "peak_today_5h": round(peak_5h, 1),
            "peak_today_weekly": round(peak_weekly, 1),
            "summary": summary
        }
