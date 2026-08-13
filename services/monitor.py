"""
Background Usage Monitor Service.
Coordinates polling, credential loading, API calls, storage, and listener updates.
"""
import threading
import time
from typing import Callable, List, Optional
from datetime import datetime, timezone

from services.credentials import CredentialService
from services.claude_api import ClaudeApiClient
from services.storage import StorageService
from services.notifications import NotificationService
from models.usage import ClaudeUsage, StatusLevel, UsageWindow
from utils.logging import logger

class UsageMonitor:
    def __init__(
        self,
        poll_interval_minutes: int = 15,
        warning_threshold: float = 80.0,
        critical_threshold: float = 90.0,
        storage_service: Optional[StorageService] = None,
        notification_service: Optional[NotificationService] = None
    ):
        self.poll_interval_seconds = max(poll_interval_minutes * 60, 60)
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.storage = storage_service or StorageService()
        self.notifier = notification_service or NotificationService(warning_threshold, critical_threshold)
        self.api_client = ClaudeApiClient()

        self._current_usage: Optional[ClaudeUsage] = None
        self._listeners: List[Callable[[ClaudeUsage], None]] = []
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    def add_listener(self, callback: Callable[[ClaudeUsage], None]):
        """Register listener callback for usage updates."""
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[ClaudeUsage], None]):
        """Unregister listener callback."""
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def get_current_usage(self) -> Optional[ClaudeUsage]:
        """Get the latest cached usage object."""
        with self._lock:
            return self._current_usage

    def start(self):
        """Start the background polling loop."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, name="UsageMonitorThread", daemon=True)
        self._thread.start()
        logger.info("UsageMonitor background thread started.")

    def stop(self):
        """Stop background polling thread."""
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=3.0)
        logger.info("UsageMonitor background thread stopped.")

    def refresh_now(self):
        """Triggers an immediate background refresh."""
        threading.Thread(target=self._fetch_and_notify, name="ManualRefreshThread", daemon=True).start()

    def _run_loop(self):
        # 1. Immediate fetch on startup
        self._fetch_and_notify()

        # 2. Polling loop
        while not self._stop_event.is_set():
            # Wait for poll interval or stop signal
            if self._stop_event.wait(timeout=self.poll_interval_seconds):
                break
            self._fetch_and_notify()

    def _fetch_and_notify(self):
        token = CredentialService.get_token()
        usage, error_msg = self.api_client.fetch_usage(
            token=token,
            warning_threshold=self.warning_threshold,
            critical_threshold=self.critical_threshold
        )

        with self._lock:
            if error_msg and self._current_usage and self._current_usage.status_level != StatusLevel.ERROR:
                # If API call failed but we had a valid previous usage, keep previous data with OFFLINE status
                usage = ClaudeUsage(
                    five_hour=self._current_usage.five_hour,
                    seven_day=self._current_usage.seven_day,
                    timestamp=self._current_usage.timestamp,
                    status_level=StatusLevel.OFFLINE,
                    error_message=f"Offline ({error_msg})"
                )
            self._current_usage = usage

        # Save to DB if valid sample
        if usage.status_level in (StatusLevel.SAFE, StatusLevel.WARNING, StatusLevel.CRITICAL):
            self.storage.save_sample(usage)
            self.notifier.check_and_notify(usage.five_hour.utilization, usage.seven_day.utilization)

        # Notify UI / Tray listeners
        listeners_copy = list(self._listeners)
        for callback in listeners_copy:
            try:
                callback(usage)
            except Exception as e:
                logger.error(f"Error in monitor listener callback: {e}")
