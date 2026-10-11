"""Offline Streamlit-facing safety contract tests, with no Streamlit import.

These simulate the decision point only; no production UI is changed.
"""
import unittest
from unittest.mock import patch
from nelutu_experimental_quota_bridge import ExperimentalQuotaConfig, reserve_experimental_attempt

class StreamlitDecisionContractTests(unittest.TestCase):
    def test_default_settings_cannot_trigger_db(self):
        with patch("nelutu_experimental_quota_bridge.PostgreSQLBudget") as db:
            self.assertFalse(reserve_experimental_attempt(ExperimentalQuotaConfig()))
            db.assert_not_called()

    def test_unverified_persistence_disables_external_attempt(self):
        config = ExperimentalQuotaConfig(
            enabled=True, dedicated_postgres_dsn="postgresql://not-a-real-host",
            provider_costs_approved=True, privacy_approved=True,
            persistence_verified=False)
        with patch("nelutu_experimental_quota_bridge.PostgreSQLBudget") as db:
            self.assertFalse(reserve_experimental_attempt(config))
            db.assert_not_called()

    def test_database_unavailable_denies_without_exception(self):
        config = ExperimentalQuotaConfig(
            enabled=True, dedicated_postgres_dsn="postgresql://not-a-real-host",
            provider_costs_approved=True, privacy_approved=True,
            persistence_verified=True)
        with patch("nelutu_experimental_quota_bridge.PostgreSQLBudget") as db:
            db.return_value.reserve.side_effect = RuntimeError("DB offline")
            self.assertFalse(reserve_experimental_attempt(config))

    def test_no_school_apps_imported_by_bridge(self):
        import sys
        self.assertNotIn("app_web_catalog", sys.modules)
        self.assertNotIn("app_parinti", sys.modules)

if __name__ == "__main__":
    unittest.main()
