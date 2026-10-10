"""Stage 67: rejected requests cannot consume quotas or reach provider."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class NoOutboundOnDenialTests(unittest.TestCase):
    def test_denials_leave_all_budgets_unchanged(self):
        cases = (
            ("disabled", DEMO_PROMPTS[0], AdapterSettings(), True, True),
            ("privacy", DEMO_PROMPTS[0], AdapterSettings(True, False, True), True, True),
            ("infrastructure", DEMO_PROMPTS[0], AdapterSettings(True, True, False), True, True),
            ("consent", DEMO_PROMPTS[0], AdapterSettings(True, True, True), False, True),
            ("key", DEMO_PROMPTS[0], AdapterSettings(True, True, True), True, False),
            ("school", "Ce note are elevul meu?", AdapterSettings(True, True, True), True, True),
            ("nonboolean", DEMO_PROMPTS[0], AdapterSettings(True, True, True), "yes", True),
        )
        for label, message, settings, confirmed, key in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as folder:
                durable = DurableBudget(str(Path(folder) / "quota.sqlite3"))
                session = DemoBudget()
                instance = InstanceBudget()
                sent = []
                result = route_single_answer(
                    message, local_answer=lambda _: "Neluțu local.",
                    settings=settings, confirmed=confirmed, provider_key_present=key,
                    durable_budget=durable, session_budget=session,
                    instance_gate=SharedBudgetGate(instance),
                    sender=lambda prompt: sent.append(prompt) or "Provider")
                self.assertEqual(result.source, "local")
                self.assertEqual(result.text, "Neluțu local.")
                self.assertEqual(sent, [])
                self.assertEqual(session.used, 0)
                self.assertEqual(instance.remaining(), 12)
                self.assertEqual(durable.remaining(), 0)
                self.assertFalse(Path(durable.path).exists())


if __name__ == "__main__":
    unittest.main()
