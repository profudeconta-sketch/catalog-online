"""Offline regression for runtime role permissions; never contacts Neon."""
import sys
import types
import unittest
from unittest.mock import patch

from nelutu_neon_runtime_permissions import runtime_permissions_ready


class Cursor:
    def __init__(self, row):
        self.row = row
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, sql, params):
        assert sql.startswith("SELECT ")
        assert params == (
            "nelutu_test_concurenta", "nelutu_test_concurenta",
            "nelutu_test_concurenta.nelutu_streamlit_lab_budget",
            "nelutu_test_concurenta.nelutu_streamlit_lab_budget",
        )
        assert "public.nelutu_gemini_budget" in sql
    def fetchone(self):
        return self.row


class Connection:
    def __init__(self, row):
        self.row = row
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def cursor(self):
        return Cursor(self.row)


class RuntimePermissionTests(unittest.TestCase):
    def test_disabled_never_connects(self):
        with patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(
            connect=lambda *a, **k: self.fail("unexpected connection")
        )}):
            self.assertFalse(runtime_permissions_ready("postgresql://fake"))
            self.assertFalse(runtime_permissions_ready("postgresql://fake", enabled=1))

    def test_strict_least_privilege(self):
        for row, expected in [
            (("nelutu_test_runner", True, False, True, True, False), True),
            (("nelutu_test_runner", True, True, True, True, False), False),
            (("nelutu_test_runner", True, False, True, False, False), False),
            (("nelutu_test_runner", True, False, True, True, True), False),
            (("neondb_owner", True, False, True, True, False), False),
            (None, False),
        ]:
            with self.subTest(row=row), patch.dict(sys.modules, {
                "psycopg": types.SimpleNamespace(
                    connect=lambda *a, **k: Connection(row)
                )
            }):
                self.assertIs(runtime_permissions_ready("postgresql://fake", enabled=True), expected)

    def test_connection_failure_denies(self):
        def fail(*a, **k):
            raise OSError("offline")
        with patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(connect=fail)}):
            self.assertFalse(runtime_permissions_ready("postgresql://fake", enabled=True))


if __name__ == "__main__":
    unittest.main()
