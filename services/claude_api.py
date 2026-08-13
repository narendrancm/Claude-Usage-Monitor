"""
Anthropic Usage API Client.
Isolates endpoint definitions and handles network/auth errors gracefully.
"""
from typing import Tuple, Optional, Dict, Any
import httpx

from config import DEFAULT_API_URL, DEFAULT_USER_AGENT, DEFAULT_BETA_HEADER
from models.usage import ClaudeUsage, StatusLevel, UsageWindow
from utils.logging import logger
from utils.time import get_utc_iso_now

class ClaudeApiError(Exception):
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code


class ClaudeApiClient:
    def __init__(self, api_url: str = DEFAULT_API_URL, timeout_seconds: float = 10.0):
        self.api_url = api_url
        self.timeout_seconds = timeout_seconds

    def fetch_usage(
        self,
        token: str,
        warning_threshold: float = 80.0,
        critical_threshold: float = 90.0
    ) -> Tuple[Optional[ClaudeUsage], Optional[str]]:
        """
        Fetches usage from Anthropic API.
        Returns (ClaudeUsage, error_message).
        If successful, error_message is None.
        If error occurs, returns (stale_or_error_model, error_message).
        """
        if not token:
            logger.warning("Fetch usage called without OAuth token.")
            err_msg = "No OAuth credential available."
            error_usage = ClaudeUsage(
                five_hour=UsageWindow(0.0),
                seven_day=UsageWindow(0.0),
                status_level=StatusLevel.ERROR,
                error_message=err_msg
            )
            return error_usage, err_msg

        headers = {
            "Authorization": f"Bearer {token.strip()}",
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/json",
            "anthropic-beta": DEFAULT_BETA_HEADER,
        }

        try:
            logger.info(f"Sending GET request to {self.api_url}")
            with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
                response = client.get(self.api_url, headers=headers)

            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.info("Successfully fetched and parsed usage response.")
                    usage = ClaudeUsage.from_api_json(data, warning_threshold, critical_threshold)
                    return usage, None
                except Exception as json_err:
                    logger.error(f"Failed to parse JSON response: {json_err}")
                    err_msg = "Malformed JSON returned from server."
                    return ClaudeUsage(
                        five_hour=UsageWindow(0.0),
                        seven_day=UsageWindow(0.0),
                        status_level=StatusLevel.ERROR,
                        error_message=err_msg
                    ), err_msg

            elif response.status_code == 401:
                logger.warning("API Returned 401 Unauthorized.")
                err_msg = "Authentication failed (401 Unauthorized)."
            elif response.status_code == 403:
                logger.warning("API Returned 403 Forbidden.")
                err_msg = "Access forbidden (403 Forbidden)."
            elif response.status_code == 429:
                logger.warning("API Returned 429 Rate Limit Exceeded.")
                err_msg = "Rate limit exceeded (429 Rate Limit)."
            elif response.status_code >= 500:
                logger.warning(f"API Returned server error {response.status_code}.")
                err_msg = f"Anthropic service error ({response.status_code})."
            else:
                logger.warning(f"API Returned unexpected status {response.status_code}.")
                err_msg = f"API error ({response.status_code})."

            error_usage = ClaudeUsage(
                five_hour=UsageWindow(0.0),
                seven_day=UsageWindow(0.0),
                status_level=StatusLevel.ERROR,
                error_message=err_msg
            )
            return error_usage, err_msg

        except httpx.TimeoutException:
            logger.warning("API Request timed out.")
            err_msg = "Network request timed out."
        except httpx.NetworkError as net_err:
            logger.warning(f"Network error: {net_err}")
            err_msg = "Network connectivity issue."
        except Exception as e:
            logger.error(f"Unexpected API client error: {e}")
            err_msg = "Unexpected error fetching usage."

        error_usage = ClaudeUsage(
            five_hour=UsageWindow(0.0),
            seven_day=UsageWindow(0.0),
            status_level=StatusLevel.OFFLINE,
            error_message=err_msg
        )
        return error_usage, err_msg
