"""
Claude Usage Monitor — Application Entry Point.
Coordinates background polling thread, system tray lifecycle, and dashboard window manager.
"""
import sys
import os

# Ensure package root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.monitor import UsageMonitor
from services.storage import StorageService
from ui.tray import SystemTrayApp
from ui.dashboard import DashboardWindow
from utils.logging import logger

class Application:
    def __init__(self):
        logger.info("Initializing Claude Usage Monitor Application...")
        self.storage = StorageService()
        self.monitor = UsageMonitor(storage_service=self.storage)
        self.dashboard = DashboardWindow(
            monitor=self.monitor,
            storage=self.storage,
            on_settings_change=self._on_settings_change
        )
        self.tray = SystemTrayApp(
            on_open_dashboard=self.open_dashboard,
            on_open_settings=self.open_settings,
            on_refresh_now=self.refresh_now,
            on_exit=self.exit_app
        )

        # Wire monitor listener to tray icon updates
        self.monitor.add_listener(self.tray.update_usage)

    def _on_settings_change(self):
        logger.info("Settings changed event received.")
        self.monitor.refresh_now()

    def open_dashboard(self):
        logger.info("Opening dashboard window...")
        self.dashboard.show()

    def open_settings(self):
        logger.info("Opening settings...")
        self.dashboard.show()

    def refresh_now(self):
        logger.info("Manual refresh requested...")
        self.monitor.refresh_now()

    def exit_app(self):
        logger.info("Shutting down Claude Usage Monitor...")
        self.monitor.stop()
        sys.exit(0)

    def run(self):
        # Start background polling loop
        self.monitor.start()

        # Run system tray loop on main thread (blocking)
        try:
            self.tray.run()
        except KeyboardInterrupt:
            self.exit_app()

def main():
    app = Application()
    app.run()

if __name__ == "__main__":
    main()
