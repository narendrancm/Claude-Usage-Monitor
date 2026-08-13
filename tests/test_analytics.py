"""
Unit tests for UsageAnalytics calculations.
"""
import pytest
from services.analytics import UsageAnalytics

def test_analytics_insufficient_data():
    res = UsageAnalytics.analyze([])
    assert res["has_data"] is False
    assert res["trend"] == "STABLE"

def test_analytics_increasing_trend():
    records = [
        {"timestamp": "2026-08-12T10:00:00Z", "five_hour": 20.0, "weekly": 40.0},
        {"timestamp": "2026-08-12T11:00:00Z", "five_hour": 35.0, "weekly": 42.0},
        {"timestamp": "2026-08-12T12:00:00Z", "five_hour": 50.0, "weekly": 45.0},
    ]
    res = UsageAnalytics.analyze(records)
    assert res["has_data"] is True
    assert res["trend"] == "INCREASING"
    assert res["rate_per_hour"] == 15.0
    assert res["estimated_minutes_to_limit"] is not None
    assert res["peak_today_5h"] == 50.0
