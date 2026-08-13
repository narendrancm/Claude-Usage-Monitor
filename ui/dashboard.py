"""
Dashboard Window Controller using pywebview.
Manages the native webview window frame, IPC API bridge, and visibility states.
"""
import os
import webview
from typing import Optional, Dict, Any, Callable

from services.monitor import UsageMonitor
from services.storage import StorageService
from services.analytics import UsageAnalytics
from services.credentials import CredentialService
from services.startup import StartupManager
from models.usage import StatusLevel
from utils.logging import logger
from utils.time import format_short_time, format_relative_reset

class JsApi:
    """Exposed Python API methods callable from frontend JavaScript."""
    def __init__(self, monitor: UsageMonitor, storage: StorageService, on_settings_change: Callable[[], None]):
        self.monitor = monitor
        self.storage = storage
        self.on_settings_change = on_settings_change

    def get_overview(self) -> Dict[str, Any]:
        usage = self.monitor.get_current_usage()
        history = self.storage.get_history(hours=24)
        analytics = UsageAnalytics.analyze(history)

        if not usage:
            return {
                "status": "INITIALIZING",
                "last_updated": format_short_time(),
                "five_hour": {"utilization": 0.0, "relative_reset": "Unknown", "resets_at": None},
                "seven_day": {"utilization": 0.0, "relative_reset": "Unknown", "resets_at": None},
                "analytics": analytics
            }

        return {
            "status": usage.status_level.value,
            "last_updated": format_short_time(),
            "five_hour": {
                "utilization": usage.five_hour.utilization,
                "relative_reset": usage.five_hour.relative_reset(),
                "resets_at": usage.five_hour.resets_at
            },
            "seven_day": {
                "utilization": usage.seven_day.utilization,
                "relative_reset": usage.seven_day.relative_reset(),
                "resets_at": usage.seven_day.resets_at
            },
            "error_message": usage.error_message,
            "analytics": analytics
        }

    def get_history(self, hours: int = 24) -> Any:
        return self.storage.get_history(hours=hours)

    def get_settings(self) -> Dict[str, Any]:
        return {
            "poll_interval": self.monitor.poll_interval_seconds // 60,
            "warning_threshold": self.monitor.warning_threshold,
            "critical_threshold": self.monitor.critical_threshold,
            "run_at_startup": StartupManager.is_enabled()
        }

    def save_settings(self, data: Dict[str, Any]) -> bool:
        try:
            poll_min = int(data.get("poll_interval", 15))
            self.monitor.poll_interval_seconds = max(poll_min * 60, 60)
            self.monitor.warning_threshold = float(data.get("warning_threshold", 80.0))
            self.monitor.critical_threshold = float(data.get("critical_threshold", 90.0))

            startup_flag = bool(data.get("run_at_startup", False))
            StartupManager.set_enabled(startup_flag)

            custom_token = data.get("custom_token")
            if custom_token:
                CredentialService.save_custom_token(custom_token)

            if self.on_settings_change:
                self.on_settings_change()

            logger.info("Settings saved successfully via JS bridge.")
            return True
        except Exception as e:
            logger.error(f"Error saving settings via JS bridge: {e}")
            return False

    def refresh_now(self):
        self.monitor.refresh_now()


class DashboardWindow:
    def __init__(self, monitor: UsageMonitor, storage: StorageService, on_settings_change: Callable[[], None]):
        self.monitor = monitor
        self.storage = storage
        self.js_api = JsApi(monitor, storage, on_settings_change)
        self._window: Optional[webview.Window] = None

    def show(self):
        """Shows or focuses the pywebview dashboard window."""
        if self._window:
            try:
                self._window.show()
                self._window.restore()
                self._window.focus()
                return
            except Exception:
                pass

        assets_dir = os.path.join(os.path.dirname(__file__), "assets")
        html_path = os.path.join(assets_dir, "index.html")

        self._window = webview.create_window(
            title="Claude Usage Monitor",
            url=html_path,
            js_api=self.js_api,
            width=640,
            height=540,
            resizable=True,
            frameless=False,
            easy_drag=False,
            on_top=False,
            background_color="#0a0a0a"
        )
        # Intercept close event to hide window instead of terminating process
        self._window.events.closing += self._on_close

    def _on_close(self):
        if self._window:
            self._window.hide()
            return False  # Prevent destroying window
        return True

    def hide(self):
        if self._window:
            try:
                self._window.hide()
            except Exception:
                pass
