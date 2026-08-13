"""
System Tray Controller using pystray.
Handles menu items, tooltip formatting, dynamic icon updates, and tray actions.
"""
from typing import Callable, Optional
import pystray
from pystray import MenuItem as item, Menu as menu

from models.usage import ClaudeUsage, StatusLevel
from ui.icons import create_tray_icon
from services.startup import StartupManager
from utils.logging import logger
from utils.time import format_short_time

class SystemTrayApp:
    def __init__(
        self,
        on_open_dashboard: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_refresh_now: Callable[[], None],
        on_exit: Callable[[], None]
    ):
        self.on_open_dashboard = on_open_dashboard
        self.on_open_settings = on_open_settings
        self.on_refresh_now = on_refresh_now
        self.on_exit = on_exit

        self._usage: Optional[ClaudeUsage] = None
        self._icon: Optional[pystray.Icon] = None
        self.startup_enabled = StartupManager.is_enabled()

    def _build_menu(self) -> menu:
        fh_str = f"5-hour limit: {self._usage.five_hour.formatted_utilization()}" if self._usage else "5-hour limit: --%"
        sd_str = f"Weekly limit: {self._usage.seven_day.formatted_utilization()}" if self._usage else "Weekly limit: --%"

        return menu(
            item("Claude Usage Monitor", None, enabled=False),
            menu.SEPARATOR,
            item(fh_str, None, enabled=False),
            item(sd_str, None, enabled=False),
            menu.SEPARATOR,
            item("Refresh Now", self._handle_refresh),
            item("Open Dashboard", self._handle_open_dashboard, default=True),
            item("Run at Startup", self._toggle_startup, checked=lambda item: self.startup_enabled),
            item("Settings", self._handle_open_settings),
            menu.SEPARATOR,
            item("Exit", self._handle_exit)
        )

    def _get_tooltip(self) -> str:
        if not self._usage:
            return "Claude Usage\nInitializing..."

        if self._usage.status_level == StatusLevel.ERROR or self._usage.status_level == StatusLevel.OFFLINE:
            err = self._usage.error_message or "Unable to retrieve usage."
            return f"Claude Usage\n{err}\nClick to retry."

        fh_pct = self._usage.five_hour.formatted_utilization()
        sd_pct = self._usage.seven_day.formatted_utilization()
        t_str = format_short_time()

        return f"Claude Usage\n5-hour   {fh_pct}\nWeekly   {sd_pct}\nUpdated {t_str}"

    def update_usage(self, usage: ClaudeUsage):
        """Called by UsageMonitor when new usage data arrives."""
        self._usage = usage
        status = usage.status_level if usage else StatusLevel.SAFE
        icon_img = create_tray_icon(status=status)

        if self._icon:
            self._icon.icon = icon_img
            self._icon.title = self._get_tooltip()
            self._icon.menu = self._build_menu()

    def _handle_refresh(self, icon, item):
        logger.info("Tray context menu: Refresh Now clicked.")
        if self.on_refresh_now:
            self.on_refresh_now()

    def _handle_open_dashboard(self, icon, item):
        logger.info("Tray context menu: Open Dashboard clicked.")
        if self.on_open_dashboard:
            self.on_open_dashboard()

    def _handle_open_settings(self, icon, item):
        logger.info("Tray context menu: Settings clicked.")
        if self.on_open_settings:
            self.on_open_settings()

    def _toggle_startup(self, icon, item):
        self.startup_enabled = not self.startup_enabled
        StartupManager.set_enabled(self.startup_enabled)
        if self._icon:
            self._icon.menu = self._build_menu()

    def _handle_exit(self, icon, item):
        logger.info("Tray context menu: Exit clicked.")
        if self._icon:
            self._icon.stop()
        if self.on_exit:
            self.on_exit()

    def run(self):
        """Launches the pystray system tray loop (blocking)."""
        icon_img = create_tray_icon(StatusLevel.SAFE)
        self._icon = pystray.Icon(
            "ClaudeUsageMonitor",
            icon=icon_img,
            title="Claude Usage\nInitializing...",
            menu=self._build_menu()
        )
        logger.info("Starting pystray system tray event loop.")
        self._icon.run()
