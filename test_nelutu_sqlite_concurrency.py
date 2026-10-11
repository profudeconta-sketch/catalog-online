"""Isolated SQLite concurrency regression tests for Neluțu quota.

No network, no secrets, no Gemini, no Neon, no school catalog access.
Run: python -m unittest -v test_nelutu_sqlite_concurrency.py
"""
import os
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor

WORKERS = 8
LIMIT = 3

def reserve(path):
    with sqlite3.connect(path, timeout=10, isolation_level=None) as connection:
        connection.execute("PRAGMA busy_timeout=10000")
        try:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "UPDATE quota SET used = used + 1 "
                "WHERE id = 1 AND used < ? RETURNING used", (LIMIT,)
            ).fetchone()
            connection.execute("COMMIT")
            return row is not None
        except BaseException:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
            raise

class ConcurrencyTest(unittest.TestCase):
    def test_eight_simultaneous_reservations_never_exceed_three(self):
        with tempfile.TemporaryDirectory(prefix="nelutu_quota_") as folder:
            path = os.path.join(folder, "isolated_quota.sqlite3")
            with sqlite3.connect(path) as connection:
                connection.execute(
                    "CREATE TABLE quota (id INTEGER PRIMARY KEY CHECK (id=1), "
                    "used INTEGER NOT NULL CHECK (used>=0))"
                )
                connection.execute("INSERT INTO quota (id, used) VALUES (1, 0)")
            with ThreadPoolExecutor(max_workers=WORKERS) as executor:
                accepted = list(executor.map(reserve, [path] * WORKERS))
            with sqlite3.connect(path) as connection:
                stored = connection.execute(
                    "SELECT used FROM quota WHERE id=1"
                ).fetchone()[0]
            self.assertEqual(sum(accepted), LIMIT)
            self.assertEqual(len(accepted) - sum(accepted), WORKERS - LIMIT)
            self.assertEqual(stored, LIMIT)

    def test_limit_remains_enforced_on_subsequent_request(self):
        with tempfile.TemporaryDirectory(prefix="nelutu_quota_") as folder:
            path = os.path.join(folder, "isolated_quota.sqlite3")
            with sqlite3.connect(path) as connection:
                connection.execute("CREATE TABLE quota (id INTEGER PRIMARY KEY, used INTEGER NOT NULL)")
                connection.execute("INSERT INTO quota VALUES (1, 3)")
            self.assertFalse(reserve(path))
            with sqlite3.connect(path) as connection:
                self.assertEqual(connection.execute("SELECT used FROM quota").fetchone()[0], 3)

if __name__ == "__main__":
    unittest.main()
