"""Stage 46 offline integration adapter safety checks."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings, handle_optional_demo


class AdapterTests(unittest.TestCase):
    def test_disabled_by_default_never_uses_sender_or_quota(self):
        with tempfile.TemporaryDirectory() as directory:
            quota = DurableBudget(str(Path(directory) / "quota.sqlite3"))
            sent = []
            base = dict(message=DEMO_PROMPTS[0], confirmed=True,
                        provider_key_present=True, durable_budget=quota,
                        session_budget=DemoBudget(),
                        instance_gate=SharedBudgetGate(InstanceBudget()),
                        sender=lambda msg: sent.append(msg) or "Răspuns fictiv")
            self.assertEqual(handle_optional_demo(settings=AdapterSettings(), **base).status,
                             "integration_disabled")
            self.assertEqual(sent, [])
            self.assertTrue(quota.reserve())

    def test_privacy_and_infrastructure_both_required(self):
        with tempfile.TemporaryDirectory() as directory:
            quota = DurableBudget(str(Path(directory) / "quota.sqlite3"))
            sent = []
            base = dict(message=DEMO_PROMPTS[0], confirmed=True,
                        provider_key_present=True, durable_budget=quota,
                        session_budget=DemoBudget(),
                        instance_gate=SharedBudgetGate(InstanceBudget()),
                        sender=lambda msg: sent.append(msg) or "Răspuns fictiv")
            self.assertEqual(handle_optional_demo(
                settings=AdapterSettings(enabled=True), **base).status,
                "privacy_review_required")
            self.assertEqual(handle_optional_demo(
                settings=AdapterSettings(enabled=True, privacy_approved=True),
                **base).status, "infrastructure_review_required")
            self.assertEqual(sent, [])
            self.assertEqual(handle_optional_demo(
                settings=AdapterSettings(enabled=True, privacy_approved=True,
                                         infrastructure_verified=True),
                **base).status, "ok")
            self.assertEqual(sent, [DEMO_PROMPTS[0]])


if __name__ == "__main__":
    unittest.main()
