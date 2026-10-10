"""Offline regression tests; never contact Neon."""
import sys
import types
import unittest
from unittest.mock import patch

from nelutu_streamlit_lab_budget import IsolatedLabBudget


class Cursor:
    def __init__(self, row):
        self.row = row
        self.sql = []
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def execute(self, sql, params=None):
        self.sql.append(sql)
        assert "nelutu_test_concurenta.nelutu_streamlit_lab_budget" in sql
        assert "public.nelutu_gemini_budget" not in sql
        assert not any(x in sql for x in ("CREATE ", "DROP ", "ALTER ", "TRUNCATE "))
    def fetchone(self):
        if self.sql and self.sql[-1].startswith('UPDATE ') and self.row is not None and (self.row[0] < 0 or self.row[0] >= 3):
            return None
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


class LabBudgetTests(unittest.TestCase):
    def test_default_disabled(self):
        for dsn in ("postgresql://example", "", None):
            with self.subTest(dsn=dsn), self.assertRaises(ValueError):
                IsolatedLabBudget(dsn)

    @patch("nelutu_streamlit_lab_budget.isolated_neon_ready", return_value=False)
    def test_failed_privilege_check_denies_all(self, _):
        budget = IsolatedLabBudget("postgresql://example", enabled=True)
        self.assertEqual(budget.remaining(), 0)
        self.assertFalse(budget.reserve())

    @patch("nelutu_streamlit_lab_budget.isolated_neon_ready", return_value=True)
    def test_read_and_reserve(self, _):
        for row, remaining, reserved in [
            ((0,), 3, True),
            ((2,), 1, True),
            ((3,), 0, False),
            ((-1,), 0, False),
            (None, 0, False),
        ]:
            with self.subTest(row=row):
                fake = types.SimpleNamespace(connect=lambda *a, **k: Connection(row))
                with patch.dict(sys.modules, {"psycopg": fake}):
                    budget = IsolatedLabBudget("postgresql://example", enabled=True)
                    self.assertEqual(budget.remaining(), remaining)
                    self.assertIs(budget.reserve(), reserved)

    @patch("nelutu_streamlit_lab_budget.isolated_neon_ready", return_value=True)
    def test_db_failure_fails_closed(self, _):
        def broken(*a, **k):
            raise OSError("no database")
        with patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(connect=broken)}):
            budget = IsolatedLabBudget("postgresql://example", enabled=True)
            self.assertEqual(budget.remaining(), 0)
            self.assertFalse(budget.reserve())


if __name__ == "__main__":
    unittest.main()
