"""Experimental durable Gemini attempt budget, isolated from school storage.

SQLite reservations are atomic across processes sharing the same persistent file.
Never use a school data file or a temporary filesystem for durability.
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

MAX_DURABLE_ATTEMPTS = 12


class DurableBudget:
    """Fail-closed persistent counter; no automatic resets or refunds."""

    def __init__(self, path: str, limit: int = MAX_DURABLE_ATTEMPTS):
        if not isinstance(path, str) or not path.strip() or not os.path.isabs(path):
            raise ValueError("An absolute, dedicated database path is required")
        if type(limit) is not int or limit < 1:
            raise ValueError("A positive integer limit is required")
        self.path = str(Path(path).resolve())
        self.limit = limit

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=5, isolation_level=None)
        db.execute("PRAGMA busy_timeout = 5000")
        return db

    def reserve(self) -> bool:
        """Reserve exactly one attempt before the network call."""
        try:
            with self._connect() as db:
                db.execute("BEGIN IMMEDIATE")
                db.execute(
                    "CREATE TABLE IF NOT EXISTS gemini_budget "
                    "(id INTEGER PRIMARY KEY CHECK(id=1), used INTEGER NOT NULL CHECK(used>=0))"
                )
                db.execute("INSERT OR IGNORE INTO gemini_budget(id, used) VALUES(1, 0)")
                cursor = db.execute(
                    "UPDATE gemini_budget SET used=used+1 "
                    "WHERE id=1 AND used < ?", (self.limit,)
                )
                permitted = cursor.rowcount == 1
                db.execute("COMMIT")
                return permitted
        except (sqlite3.Error, OSError):
            return False

    def remaining(self) -> int:
        """Return zero if storage cannot be verified."""
        try:
            with self._connect() as db:
                row = db.execute(
                    "SELECT used FROM gemini_budget WHERE id=1"
                ).fetchone()
                if row is None:
                    return 0
                return max(0, self.limit - row[0])
        except (sqlite3.Error, OSError, TypeError, ValueError):
            return 0
