"""Offline safety tests; no PostgreSQL connection and no Gemini requests."""
import unittest
from unittest.mock import patch
from nelutu_postgres_budget import PostgreSQLBudget


class PostgreSQLBudgetSafetyTests(unittest.TestCase):
    def test_rejects_invalid_configuration(self):
        for dsn in ("", "   ", None, 42):
            with self.assertRaises(ValueError):
                PostgreSQLBudget(dsn)
        for limit in (0, -1, True, 1.5):
            with self.assertRaises(ValueError):
                PostgreSQLBudget("postgresql://unused", limit)

    def test_missing_driver_fails_closed(self):
        gate = PostgreSQLBudget("postgresql://unused")
        with patch.dict("sys.modules", {"psycopg": None}):
            self.assertFalse(gate.reserve())
            self.assertEqual(gate.remaining(), 0)

    def test_no_external_configuration_is_read_automatically(self):
        gate = PostgreSQLBudget("postgresql://unused")
        self.assertEqual(gate.limit, 12)


if __name__ == "__main__":
    unittest.main()
