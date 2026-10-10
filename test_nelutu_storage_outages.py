"""Stage 64: quota storage outages must not authorize experimental traffic."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from nelutu_durable_budget import DurableBudget
from nelutu_demo_budget import DemoBudget
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class StorageOutageTests(unittest.TestCase):
    def test_connection_failure_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            quota = DurableBudget(str(Path(folder) / "quota.sqlite3"))
            with patch.object(quota, "_connect", side_effect=OSError("disk unavailable")):
                self.assertFalse(quota.reserve())
                self.assertEqual(quota.remaining(), 0)

    def test_locked_database_fails_closed_without_sender(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "quota.sqlite3")
            quota = DurableBudget(path)
            with sqlite3.connect(path, isolation_level=None) as conn:
                conn.execute("BEGIN EXCLUSIVE")
                with patch.object(quota, "_connect", side_effect=sqlite3.OperationalError("database is locked")):
                    sent = []
                    result = route_single_answer(
                        DEMO_PROMPTS[0], local_answer=lambda _: "Neluțu local.",
                        settings=AdapterSettings(enabled=True, privacy_approved=True,
                                                 infrastructure_verified=True),
                        confirmed=True, provider_key_present=True,
                        durable_budget=quota, session_budget=DemoBudget(),
                        instance_gate=SharedBudgetGate(InstanceBudget()),
                        sender=lambda m: sent.append(m) or "Gemini")
                    self.assertEqual(result.source, "local")
                    self.assertEqual(sent, [])
                conn.execute("ROLLBACK")

    def test_directory_missing_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            quota = DurableBudget(str(Path(folder) / "absent" / "quota.sqlite3"))
            self.assertFalse(quota.reserve())
            self.assertEqual(quota.remaining(), 0)


if __name__ == "__main__":
    unittest.main()
