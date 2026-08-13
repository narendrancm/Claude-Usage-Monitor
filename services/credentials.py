"""
CredentialService abstraction.
Retrieves Claude Code OAuth credentials safely from Windows Credential Manager,
keyring, environment variables, or local config.
"""
import os
import json
import ctypes
import ctypes.wintypes
from typing import Optional

try:
    import keyring
except ImportError:
    keyring = None

from config import CREDENTIAL_TARGET, APP_NAME
from utils.logging import logger

class CREDENTIAL(ctypes.Structure):
    _fields_ = [
        ('Flags', ctypes.wintypes.DWORD),
        ('Type', ctypes.wintypes.DWORD),
        ('TargetName', ctypes.wintypes.LPWSTR),
        ('Comment', ctypes.wintypes.LPWSTR),
        ('LastWritten', ctypes.wintypes.FILETIME),
        ('CredentialBlobSize', ctypes.wintypes.DWORD),
        ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
        ('Persist', ctypes.wintypes.DWORD),
        ('AttributeCount', ctypes.wintypes.DWORD),
        ('Attributes', ctypes.c_void_p),
        ('TargetAlias', ctypes.wintypes.LPWSTR),
        ('UserName', ctypes.wintypes.LPWSTR),
    ]

def read_win32_credential(target_name: str) -> Optional[str]:
    """Direct Win32 CredReadW API call for target_name."""
    try:
        advapi32 = ctypes.windll.advapi32
        CredRead = advapi32.CredReadW
        CredRead.argtypes = [ctypes.c_wchar_p, ctypes.wintypes.DWORD, ctypes.wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
        CredRead.restype = ctypes.wintypes.BOOL
        CredFree = advapi32.CredFree
        CredFree.argtypes = [ctypes.c_void_p]

        cred_ptr = ctypes.POINTER(CREDENTIAL)()
        # Type 1 = CRED_TYPE_GENERIC
        if CredRead(target_name, 1, 0, ctypes.byref(cred_ptr)):
            cred = cred_ptr.contents
            blob = bytes(cred.CredentialBlob[:cred.CredentialBlobSize])
            CredFree(cred_ptr)
            if not blob:
                return None
            # Try utf-8 or utf-16le
            try:
                if len(blob) % 2 == 0 and blob[1:2] == b'\x00':
                    decoded = blob.decode('utf-16le').strip('\x00\r\n ')
                else:
                    decoded = blob.decode('utf-8').strip('\x00\r\n ')
                # If JSON stored in blob
                if decoded.startswith('{') and 'oauth' in decoded.lower():
                    data = json.loads(decoded)
                    return data.get('accessToken') or data.get('oauth_token') or data.get('token')
                return decoded
            except Exception as e:
                logger.warning(f"Error decoding credential blob for {target_name}: {e}")
                return None
    except Exception as e:
        logger.warning(f"Win32 CredRead failed for {target_name}: {e}")
    return None

class CredentialService:
    @staticmethod
    def get_token() -> Optional[str]:
        """
        Retrieves the OAuth token using a prioritized lookup strategy.
        Returns token string or None if missing.
        """
        # 1. Custom app token saved in keyring
        if keyring:
            try:
                custom_token = keyring.get_password(APP_NAME, "oauth_token")
                if custom_token:
                    logger.info("Retrieved custom OAuth token from keyring.")
                    return custom_token
            except Exception as e:
                logger.warning(f"Keyring read error for {APP_NAME}: {e}")

        # 2. Environment variable
        env_token = os.environ.get("CLAUDE_OAUTH_TOKEN") or os.environ.get("CLAUDE_CODE_OAUTH_TOKEN")
        if env_token:
            logger.info("Retrieved OAuth token from environment variable.")
            return env_token.strip()

        # 3. Keyring lookup for Claude Code-credentials
        if keyring:
            for service in [CREDENTIAL_TARGET, "Claude Code", "claude-code"]:
                try:
                    token = keyring.get_password(service, "oauth_token") or keyring.get_password(service, os.environ.get("USERNAME", ""))
                    if token:
                        logger.info(f"Retrieved token from keyring service '{service}'.")
                        return token.strip()
                except Exception:
                    pass

        # 4. Direct Win32 Credential Manager targets
        for target in [CREDENTIAL_TARGET, "Claude Code-credentials", "Claude Code", "claude-code", "keyring:Claude Code-credentials"]:
            token = read_win32_credential(target)
            if token:
                logger.info(f"Retrieved token from Windows Credential Manager target '{target}'.")
                return token.strip()

        # 5. Fallback search in user home .claude config JSON files
        user_home = os.path.expanduser("~")
        candidate_paths = [
            os.path.join(user_home, ".claude.json"),
            os.path.join(user_home, ".claude", "config.json"),
            os.path.join(os.environ.get("APPDATA", ""), "Claude", "config.json")
        ]
        for p in candidate_paths:
            if os.path.isfile(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        token = data.get("oauthToken") or data.get("accessToken") or data.get("oauth_token")
                        if token:
                            logger.info(f"Retrieved token from configuration file '{p}'.")
                            return token.strip()
                except Exception:
                    pass

        logger.warning("No OAuth credential found across any lookup target.")
        return None

    @staticmethod
    def save_custom_token(token: str) -> bool:
        """Saves a user-provided custom OAuth token into keyring."""
        if not keyring:
            return False
        try:
            if token:
                keyring.set_password(APP_NAME, "oauth_token", token.strip())
            else:
                try:
                    keyring.delete_password(APP_NAME, "oauth_token")
                except Exception:
                    pass
            return True
        except Exception as e:
            logger.error(f"Failed to save custom token to keyring: {e}")
            return False
