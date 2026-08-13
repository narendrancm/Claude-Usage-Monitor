"""
SQLite Storage Service.
Manages persistent historical data storage with configurable retention.
"""
import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from pathlib import Path

from config import DB_PATH, DEFAULT_RETENTION_DAYS
from models.usage import ClaudeUsage, UsageWindow, StatusLevel
from utils.logging import logger

class StorageService:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Creates the database schema if not exists."""
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS usage_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        five_hour_utilization REAL NOT NULL,
                        weekly_utilization REAL NOT NULL,
                        five_hour_reset TEXT,
                        weekly_reset TEXT,
                        status TEXT NOT NULL
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON usage_history(timestamp)")
                conn.commit()
            logger.info(f"SQLite DB initialized at {self.db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite database: {e}")

    def save_sample(self, usage: ClaudeUsage):
        """Saves a usage sample to history."""
        if usage.status_level == StatusLevel.ERROR or usage.status_level == StatusLevel.OFFLINE:
            # Don't save invalid/error samples into numerical trend history
            return

        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT INTO usage_history (
                        timestamp, five_hour_utilization, weekly_utilization, five_hour_reset, weekly_reset, status
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    usage.timestamp,
                    usage.five_hour.utilization,
                    usage.seven_day.utilization,
                    usage.five_hour.resets_at,
                    usage.seven_day.resets_at,
                    usage.status_level.value
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error saving usage sample to DB: {e}")

    def get_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Returns history samples within the last N hours."""
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        results = []
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT timestamp, five_hour_utilization, weekly_utilization, five_hour_reset, weekly_reset, status
                    FROM usage_history
                    WHERE timestamp >= ?
                    ORDER BY timestamp ASC
                """, (cutoff,))
                for row in cursor.fetchall():
                    results.append({
                        "timestamp": row["timestamp"],
                        "five_hour": row["five_hour_utilization"],
                        "weekly": row["weekly_utilization"],
                        "five_hour_reset": row["five_hour_reset"],
                        "weekly_reset": row["weekly_reset"],
                        "status": row["status"]
                    })
        except Exception as e:
            logger.error(f"Error reading usage history: {e}")
        return results

    def get_latest(self) -> Optional[Dict[str, Any]]:
        """Returns the most recent saved record."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT timestamp, five_hour_utilization, weekly_utilization, five_hour_reset, weekly_reset, status
                    FROM usage_history
                    ORDER BY id DESC LIMIT 1
                """)
                row = cursor.fetchone()
                if row:
                    return {
                        "timestamp": row["timestamp"],
                        "five_hour": row["five_hour_utilization"],
                        "weekly": row["weekly_utilization"],
                        "five_hour_reset": row["five_hour_reset"],
                        "weekly_reset": row["weekly_reset"],
                        "status": row["status"]
                    }
        except Exception as e:
            logger.error(f"Error fetching latest record: {e}")
        return None

    def cleanup_old_records(self, retention_days: int = DEFAULT_RETENTION_DAYS):
        """Purges entries older than retention_days."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
        try:
            with self._get_connection() as conn:
                cur = conn.execute("DELETE FROM usage_history WHERE timestamp < ?", (cutoff,))
                conn.commit()
                if cur.rowcount > 0:
                    logger.info(f"Purged {cur.rowcount} usage history records older than {retention_days} days.")
        except Exception as e:
            logger.error(f"Error purging old records: {e}")
