"""Offline PostgreSQL adapter transaction tests; no external database required."""
import sys
import types
import unittest
from unittest.mock import patch

from nelutu_postgres_budget import PostgreSQLBudget


class Cursor:
    def __init__(self, *, used=0, fail_at=None):
        self.used = used
        self.fail_at = fail_at
        self.calls = []
        self.result = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        if self.fail_at and self.fail_at in sql:
            raise RuntimeError("simulated database failure")
        if sql.startswith("UPDATE "):
            limit = params[0]
            self.result = (self.used + 1,) if self.used < limit else None
            if self.result:
                self.used += 1
        elif sql.startswith("SELECT "):
            self.result = (self.used,)

    def fetchone(self):
        return self.result


class Connection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.transaction_entered = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def transaction(self):
        parent = self
        class Tx:
            def __enter__(self):
                parent.transaction_entered = True
                return self
            def __exit__(self, *args):
                return False
        return Tx()

    def cursor(self):
        return self._cursor


class AdapterTests(unittest.TestCase):
    def _driver(self, connection):
        return patch.dict(sys.modules, {"psycopg": types.SimpleNamespace(
            connect=lambda dsn, connect_timeout: connection
        )})

    def test_atomic_conditional_update_and_limit(self):
        cursor = Cursor()
        connection = Connection(cursor)
        with self._driver(connection):
            budget = PostgreSQLBudget("postgresql://fake", limit=2)
            self.assertTrue(budget.reserve())
            self.assertTrue(budget.reserve())
            self.assertFalse(budget.reserve())
            self.assertEqual(budget.remaining(), 0)
        self.assertTrue(any("FROM public.nelutu_gemini_budget" in sql for sql, _ in cursor.calls))
        self.assertTrue(connection.transaction_entered)
        self.assertFalse(any(sql.startswith(('CREATE', 'INSERT', 'DROP', 'ALTER')) for sql, _ in cursor.calls))
        updates = [(sql, params) for sql, params in cursor.calls if sql.startswith("UPDATE")]
        self.assertEqual(len(updates), 3)
        self.assertTrue(all("UPDATE public.nelutu_gemini_budget SET used" in sql and "used < %s RETURNING used" in sql for sql, _ in updates))
        self.assertTrue(all(params == (2,) for _, params in updates))

    def test_failed_transaction_denies_reservation(self):
        cursor = Cursor(fail_at="UPDATE")
        with self._driver(Connection(cursor)):
            self.assertFalse(PostgreSQLBudget("postgresql://fake").reserve())

    def test_failed_read_reports_zero_remaining(self):
        cursor = Cursor(fail_at="SELECT")
        with self._driver(Connection(cursor)):
            self.assertEqual(PostgreSQLBudget("postgresql://fake").remaining(), 0)

    def test_invalid_limits_are_rejected(self):
        for invalid in (0, -1, True, 1.5, "3"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    PostgreSQLBudget("postgresql://fake", limit=invalid)

    def test_empty_connection_string_is_rejected(self):
        for invalid in ("", "  ", None):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    PostgreSQLBudget(invalid)

    def test_missing_row_returns_zero(self):
        cursor = Cursor()
        cursor.used = 0
        with self._driver(Connection(cursor)):
            self.assertEqual(PostgreSQLBudget("postgresql://fake").remaining(), 12)


if __name__ == "__main__":
    unittest.main()
