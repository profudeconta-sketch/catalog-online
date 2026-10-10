"""Offline tests for Stage 70 fail-closed experimental integration bridge."""
import unittest
from unittest.mock import patch

from nelutu_experimental_quota_bridge import (
    ExperimentalQuotaConfig,
    reserve_experimental_attempt,
)


class QuotaBridgeTests(unittest.TestCase):
    def test_defaults_deny_without_database(self):
        with patch("nelutu_experimental_quota_bridge.PostgreSQLBudget") as db:
            self.assertFalse(reserve_experimental_attempt(ExperimentalQuotaConfig()))
            db.assert_not_called()

    def test_all_independent_approvals_required(self):
        base = dict(enabled=True, dedicated_postgres_dsn="postgresql://example",
                    provider_costs_approved=True, privacy_approved=True,
                    persistence_verified=True)
        for flag in ("enabled", "provider_costs_approved", "privacy_approved",
                     "persistence_verified"):
            with self.subTest(flag=flag):
                config = ExperimentalQuotaConfig(**{**base, flag: False})
                with patch("nelutu_experimental_quota_bridge.PostgreSQLBudget") as db:
                    self.assertFalse(reserve_experimental_attempt(config))
                    db.assert_not_called()

    def test_rejects_bad_dsn_and_excessive_limit(self):
        base = dict(enabled=True, provider_costs_approved=True,
                    privacy_approved=True, persistence_verified=True)
        for dsn, limit in ((None, 12), ("", 12), ("sqlite:///x", 12),
                           ("postgresql://example", 13), ("postgresql://example", True)):
            with self.subTest(dsn=dsn, limit=limit):
                with patch("nelutu_experimental_quota_bridge.PostgreSQLBudget") as db:
                    self.assertFalse(reserve_experimental_attempt(
                        ExperimentalQuotaConfig(**base, dedicated_postgres_dsn=dsn, limit=limit)))
                    db.assert_not_called()

    def test_approved_path_reserves_once(self):
        config = ExperimentalQuotaConfig(enabled=True,
            dedicated_postgres_dsn="postgresql://example",
            provider_costs_approved=True, privacy_approved=True,
            persistence_verified=True)
        with patch("nelutu_experimental_quota_bridge.PostgreSQLBudget") as db:
            db.return_value.reserve.return_value = True
            self.assertTrue(reserve_experimental_attempt(config))
            db.assert_called_once_with("postgresql://example", limit=12)
            db.return_value.reserve.assert_called_once_with()

    def test_database_denial_preserved(self):
        config = ExperimentalQuotaConfig(enabled=True,
            dedicated_postgres_dsn="postgresql://example",
            provider_costs_approved=True, privacy_approved=True,
            persistence_verified=True)
        with patch("nelutu_experimental_quota_bridge.PostgreSQLBudget") as db:
            db.return_value.reserve.return_value = False
            self.assertFalse(reserve_experimental_attempt(config))


if __name__ == "__main__":
    unittest.main()
