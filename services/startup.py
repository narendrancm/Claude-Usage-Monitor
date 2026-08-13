"""
Windows Startup Manager using HKCU registry.
"""
import sys
import os
import winreg
from utils.logging import logger

REG_KEY_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_REG_NAME = "ClaudeUsageMonitor"

class StartupManager:
    @staticmethod
    def get_executable_path() -> str:
        """Returns the command line string to run on Windows startup."""
        if getattr(sys, 'frozen', False):
            # PyInstaller binary executable
            return f'"{sys.executable}"'
        else:
            # Running as Python script
            script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app.py"))
            return f'"{sys.executable}" "{script_path}"'

    @staticmethod
    def is_enabled() -> bool:
        """Checks if app is registered in HKCU Run key."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_READ) as key:
                value, _ = winreg.QueryValueEx(key, APP_REG_NAME)
                return bool(value)
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.warning(f"Error checking startup registry key: {e}")
            return False

    @classmethod
    def set_enabled(cls, enable: bool) -> bool:
        """Enables or disables automatic Windows startup."""
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, REG_KEY_PATH, 0, winreg.KEY_SET_VALUE) as key:
                if enable:
                    exe_cmd = cls.get_executable_path()
                    winreg.SetValueEx(key, APP_REG_NAME, 0, winreg.REG_SZ, exe_cmd)
                    logger.info(f"Enabled Windows startup registry key: {exe_cmd}")
                else:
                    try:
                        winreg.DeleteValue(key, APP_REG_NAME)
                        logger.info("Disabled Windows startup registry key.")
                    except FileNotFoundError:
                        pass
            return True
        except Exception as e:
            logger.error(f"Failed to set startup registry key: {e}")
            return False
