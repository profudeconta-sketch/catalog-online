"""Stage 66 integrated authorization flags must be actual booleans."""
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_integration_gate import authorize_experimental_request
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class IntegratedBoundaryTests(unittest.TestCase):
    def test_truthy_nonboolean_flags_are_rejected(self):
        valid = dict(explicitly_enabled=True, confirmed=True,
                     provider_key_present=True, durable_gate_ready=True)
        for key in valid:
            for value in ("true", 1, object()):
                with self.subTest(flag=key, value=repr(value)):
                    decision = authorize_experimental_request(
                        DEMO_PROMPTS[0], **{**valid, key: value})
                    self.assertFalse(decision.allowed)
                    self.assertEqual(decision.reason, "invalid_gate_flags")

    def test_all_four_gates_must_be_true(self):
        valid = dict(explicitly_enabled=True, confirmed=True,
                     provider_key_present=True, durable_gate_ready=True)
        self.assertTrue(authorize_experimental_request(DEMO_PROMPTS[0], **valid).allowed)
        for key in valid:
            with self.subTest(flag=key):
                self.assertFalse(authorize_experimental_request(
                    DEMO_PROMPTS[0], **{**valid, key: False}).allowed)

    def test_malformed_confirmation_preserves_local_without_sender(self):
        with tempfile.TemporaryDirectory() as folder:
            sent = []
            result = route_single_answer(
                DEMO_PROMPTS[0], local_answer=lambda _: "Răspuns local.",
                settings=AdapterSettings(enabled=True, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed="yes", provider_key_present=True,
                durable_budget=DurableBudget(str(Path(folder) / "quota.sqlite3")),
                session_budget=DemoBudget(), instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda message: sent.append(message) or "Provider")
            self.assertEqual((result.source, result.text), ("local", "Răspuns local."))
            self.assertEqual(result.provider_status, "invalid_gate_flags")
            self.assertFalse(sent)


if __name__ == "__main__":
    unittest.main()
