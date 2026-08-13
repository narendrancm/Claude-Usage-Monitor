"""
Unit tests for StorageService using an in-memory or temporary SQLite database.
"""
import pytest
import os
import tempfile
from pathlib import Path

from services.storage import StorageService
from models.usage import ClaudeUsage, UsageWindow, StatusLevel

@pytest.fixture
def temp_storage():
    tmp_dir = tempfile.mkdtemp()
    db_path = Path(tmp_dir) / "test_history.db"
    storage = StorageService(db_path=db_path)
    yield storage

def test_save_and_retrieve_sample(temp_storage):
    sample = ClaudeUsage(
        five_hour=UsageWindow(utilization=42.0, resets_at="2026-08-12T20:00:00Z"),
        seven_day=UsageWindow(utilization=67.0, resets_at="2026-08-15T12:00:00Z"),
        status_level=StatusLevel.SAFE
    )
    temp_storage.save_sample(sample)

    history = temp_storage.get_history(hours=24)
    assert len(history) == 1
    assert history[0]["five_hour"] == 42.0
    assert history[0]["weekly"] == 67.0

def test_latest_record(temp_storage):
    sample1 = ClaudeUsage(
        five_hour=UsageWindow(utilization=30.0),
        seven_day=UsageWindow(utilization=50.0),
        status_level=StatusLevel.SAFE
    )
    sample2 = ClaudeUsage(
        five_hour=UsageWindow(utilization=55.0),
        seven_day=UsageWindow(utilization=70.0),
        status_level=StatusLevel.WARNING
    )
    temp_storage.save_sample(sample1)
    temp_storage.save_sample(sample2)

    latest = temp_storage.get_latest()
    assert latest is not None
    assert latest["five_hour"] == 55.0
    assert latest["status"] == StatusLevel.WARNING.value
