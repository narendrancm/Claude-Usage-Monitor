"""
Secure logging utility for Claude Usage Monitor.
Ensures secrets and sensitive headers are never logged.
"""
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys

from config import LOG_PATH

class RedactingFormatter(logging.Formatter):
    """Filter sensitive strings like tokens, bearer strings, or auth headers."""
    def format(self, record: logging.LogRecord) -> str:
        msg = super().format(record)
        # Redact any Bearer token patterns
        if "Bearer " in msg:
            parts = msg.split("Bearer ")
            redacted_parts = [parts[0]]
            for p in parts[1:]:
                token_val = p.split()[0] if p.split() else ""
                redacted_parts.append("[REDACTED_TOKEN]" + p[len(token_val):])
            msg = "Bearer ".join(redacted_parts)
        if "sk-ant-" in msg:
            import re
            msg = re.sub(r'sk-ant-[a-zA-Z0-9_\-]+', '[REDACTED_KEY]', msg)
        return msg

def setup_logger(name: str = "claude_monitor") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)
    fmt = RedactingFormatter("[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    # File Handler
    try:
        file_handler = RotatingFileHandler(LOG_PATH, maxBytes=2*1024*1024, backupCount=3, encoding="utf-8")
        file_handler.setFormatter(fmt)
        file_handler.setLevel(logging.INFO)
        logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to create file logger: {e}", file=sys.stderr)

    # Console Handler for debugging
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.INFO)
    logger.addHandler(console_handler)

    return logger

logger = setup_logger()
