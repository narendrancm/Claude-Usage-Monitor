"""
Unit tests for ClaudeUsage data parsing and normalization.
"""
import pytest
from models.usage import normalize_utilization, ClaudeUsage, StatusLevel

def test_normalize_utilization_fractional():
    assert normalize_utilization(0.42) == 42.0
    assert normalize_utilization(0.05) == 5.0
    assert normalize_utilization(0.99) == 99.0
    assert normalize_utilization(1.0) == 100.0

def test_normalize_utilization_percentage():
    assert normalize_utilization(42) == 42.0
    assert normalize_utilization(67.5) == 67.5
    assert normalize_utilization("42%") == 42.0
    assert normalize_utilization("85.4") == 85.4

def test_normalize_utilization_bounds():
    assert normalize_utilization(0) == 0.0
    assert normalize_utilization(-10) == 0.0
    assert normalize_utilization(150) == 100.0
    assert normalize_utilization(None) == 0.0
    assert normalize_utilization("invalid") == 0.0

def test_claude_usage_from_api_json():
    data = {
        "five_hour": {
            "utilization": 0.42,
            "resets_at": "2026-08-12T20:00:00Z"
        },
        "seven_day": {
            "utilization": 67,
            "resets_at": "2026-08-15T12:00:00Z"
        }
    }
    usage = ClaudeUsage.from_api_json(data)
    assert usage.five_hour.utilization == 42.0
    assert usage.seven_day.utilization == 67.0
    assert usage.status_level == StatusLevel.SAFE

def test_claude_usage_status_thresholds():
    data = {
        "five_hour": {"utilization": 82},
        "seven_day": {"utilization": 30}
    }
    usage = ClaudeUsage.from_api_json(data, warning_threshold=80.0, critical_threshold=90.0)
    assert usage.status_level == StatusLevel.WARNING

    data_critical = {
        "five_hour": {"utilization": 45},
        "seven_day": {"utilization": 92}
    }
    usage_crit = ClaudeUsage.from_api_json(data_critical, warning_threshold=80.0, critical_threshold=90.0)
    assert usage_crit.status_level == StatusLevel.CRITICAL
