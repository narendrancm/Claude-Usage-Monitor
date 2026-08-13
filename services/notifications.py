"""
Windows Toast Notification Service with threshold debouncing.
"""
from typing import Optional
from datetime import datetime, timezone, timedelta

from utils.logging import logger

try:
    from windows_toasts import WindowsToaster, ToastText1, ToastText2
    HAS_WIN_TOASTS = True
except ImportError:
    HAS_WIN_TOASTS = False


class NotificationService:
    def __init__(self, warning_threshold: float = 80.0, critical_threshold: float = 90.0):
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.last_notified_5h: Optional[float] = None
        self.last_notified_weekly: Optional[float] = None
        self.last_notified_time: Optional[datetime] = None
        self.cooldown_minutes = 60

    def notify(self, title: str, message: str):
        """Displays Windows notification."""
        logger.info(f"Notification triggered: '{title}' - '{message}'")
        if HAS_WIN_TOASTS:
            try:
                toaster = WindowsToaster("Claude Usage Monitor")
                toast = ToastText2()
                toast.SetHeadline(title)
                toast.SetFirstLine(message)
                toaster.show_toast(toast)
                return
            except Exception as e:
                logger.warning(f"Failed to display windows_toasts notification: {e}")

        # Fallback using PowerShell balloon tip / system notification script if library missing
        try:
            import subprocess
            ps_script = f'''
            [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
            $objNotify = New-Object System.Windows.Forms.NotifyIcon
            $objNotify.Icon = [System.Drawing.SystemIcons]::Information
            $objNotify.BalloonTipIcon = "Warning"
            $objNotify.BalloonTipText = "{message}"
            $objNotify.BalloonTipTitle = "{title}"
            $objNotify.Visible = $True
            $objNotify.ShowBalloonTip(5000)
            '''
            subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            logger.warning(f"Fallback notification failed: {e}")

    def check_and_notify(self, five_hour_util: float, weekly_util: float):
        """Evaluates thresholds and fires notification if exceeded and not in cooldown."""
        now = datetime.now(timezone.utc)
        if self.last_notified_time and (now - self.last_notified_time) < timedelta(minutes=self.cooldown_minutes):
            return

        # Check 5-hour limit
        if five_hour_util >= self.critical_threshold and (self.last_notified_5h is None or self.last_notified_5h < self.critical_threshold):
            self.notify("Claude Usage Critical", f"Your 5-hour usage has reached {five_hour_util:.0f}%.")
            self.last_notified_5h = five_hour_util
            self.last_notified_time = now
        elif five_hour_util >= self.warning_threshold and (self.last_notified_5h is None or self.last_notified_5h < self.warning_threshold):
            self.notify("Claude Usage Warning", f"Your 5-hour usage has reached {five_hour_util:.0f}%.")
            self.last_notified_5h = five_hour_util
            self.last_notified_time = now

        # Check Weekly limit
        if weekly_util >= self.critical_threshold and (self.last_notified_weekly is None or self.last_notified_weekly < self.critical_threshold):
            self.notify("Claude Weekly Usage Critical", f"Your weekly usage has reached {weekly_util:.0f}%.")
            self.last_notified_weekly = weekly_util
            self.last_notified_time = now
