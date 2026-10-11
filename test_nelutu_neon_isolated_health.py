"""Offline checks for isolated Neon health probe. No database connections."""
import sys
import types
import unittest
from unittest.mock import patch

from nelutu_neon_isolated_health import isolated_neon_ready


class FakeCursor:
    def __init__(self, row):
        self.row = row
        self.sql = None
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, sql, params):
        self.sql = sql
        assert params == ("nelutu_test_concurenta",)
        assert sql.startswith("SELECT ")
        assert "INSERT INTO" not in sql
        assert "UPDATE " not in sql
        assert "DROP " not in sql
    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self, row):
        self.row = row
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def cursor(self):
        return FakeCursor(self.row)


class TestIsolatedNeonHealth(unittest.TestCase):
    def test_disabled_never_connects(self):
        fake = types.SimpleNamespace(connect=lambda *a, **kw: self.fail("unexpected connection"))
        with patch.dict(sys.modules, {"psycopg": fake}):
            self.assertFalse(isolated_neon_ready("postgresql://dummy"))
            self.assertFalse(isolated_neon_ready("postgresql://dummy", enabled=1))
            self.assertFalse(isolated_neon_ready("", enabled=True))

    def test_only_test_role_without_budget_access_passes(self):
        for row, expected in [
            (("nelutu_test_runner", True, False), True),
            (("neondb_owner", True, False), False),
            (("nelutu_test_runner", False, False), False),
            (("nelutu_test_runner", True, True), False),
            (None, False),
        ]:
            fake = types.SimpleNamespace(connect=lambda *a, **kw: FakeConnection(row))
            with self.subTest(row=row), patch.dict(sys.modules, {"psycopg": fake}):
                self.assertIs(isolated_neon_ready("postgresql://dummy", enabled=True), expected)

    def test_connection_error_fails_closed(self):
        def fail(*args, **kwargs):
            raise OSError("offline")
        with patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(connect=fail)}):
            self.assertFalse(isolated_neon_ready("postgresql://dummy", enabled=True))


if __name__ == "__main__":
    unittest.main()
