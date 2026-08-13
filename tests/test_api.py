"""
Unit tests for ClaudeApiClient.
Mocks HTTP responses without making actual external API calls.
"""
import pytest
import httpx
from unittest.mock import patch, MagicMock

from services.claude_api import ClaudeApiClient
from models.usage import StatusLevel

def test_api_client_missing_token():
    client = ClaudeApiClient()
    usage, error = client.fetch_usage(token="")
    assert usage.status_level == StatusLevel.ERROR
    assert "No OAuth credential" in error

@patch("httpx.Client.get")
def test_api_client_success_200(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "five_hour": {"utilization": 42.0, "resets_at": "2026-08-12T20:00:00Z"},
        "seven_day": {"utilization": 67.0, "resets_at": "2026-08-15T12:00:00Z"}
    }
    mock_get.return_value = mock_resp

    client = ClaudeApiClient()
    usage, error = client.fetch_usage(token="mock_valid_token")

    assert error is None
    assert usage.five_hour.utilization == 42.0
    assert usage.seven_day.utilization == 67.0
    assert usage.status_level == StatusLevel.SAFE

@patch("httpx.Client.get")
def test_api_client_401_unauthorized(mock_get):
    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_get.return_value = mock_resp

    client = ClaudeApiClient()
    usage, error = client.fetch_usage(token="invalid_token")

    assert usage.status_level == StatusLevel.ERROR
    assert "401 Unauthorized" in error

@patch("httpx.Client.get")
def test_api_client_timeout(mock_get):
    mock_get.side_effect = httpx.TimeoutException("Connection timed out")

    client = ClaudeApiClient()
    usage, error = client.fetch_usage(token="valid_token")

    assert usage.status_level == StatusLevel.OFFLINE
    assert "timed out" in error.lower()
