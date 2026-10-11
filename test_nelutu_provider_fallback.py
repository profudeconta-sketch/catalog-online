"""Stage 51: fallback scenarios using only a simulated provider."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class ResilienceTests(unittest.TestCase):
    def test_provider_failures_return_local_response(self):
        for failure in ("exception", "empty", "whitespace", "none"):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as folder:
                def fake_provider(_):
                    if failure == "exception":
                        raise TimeoutError("simulated timeout")
                    return {"empty": "", "whitespace": "  ", "none": None}[failure]
                result = route_single_answer(
                    DEMO_PROMPTS[0], local_answer=lambda _: "Neluțu local funcționează.",
                    settings=AdapterSettings(enabled=True, privacy_approved=True,
                                             infrastructure_verified=True),
                    confirmed=True, provider_key_present=True,
                    durable_budget=DurableBudget(str(Path(folder) / "quota.sqlite3")),
                    session_budget=DemoBudget(),
                    instance_gate=SharedBudgetGate(InstanceBudget()),
                    sender=fake_provider)
                self.assertEqual(result.source, "local")
                self.assertEqual(result.text, "Neluțu local funcționează.")

    def test_quota_exhaustion_preserves_local_response(self):
        with tempfile.TemporaryDirectory() as folder:
            quota = DurableBudget(str(Path(folder) / "quota.sqlite3"), limit=1)
            self.assertTrue(quota.reserve())
            sent = []
            result = route_single_answer(
                DEMO_PROMPTS[0], local_answer=lambda _: "Răspuns local.",
                settings=AdapterSettings(enabled=True, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed=True, provider_key_present=True,
                durable_budget=quota, session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda m: sent.append(m) or "Nu trebuie apelat.")
            self.assertEqual(result.source, "local")
            self.assertEqual(result.provider_status, "durable_quota_unavailable")
            self.assertFalse(sent)


if __name__ == "__main__":
    unittest.main()
