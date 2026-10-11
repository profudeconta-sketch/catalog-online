"""Stage 49: one response and safe local fallback, with no real provider."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class SingleAnswerTests(unittest.TestCase):
    def setup_args(self, directory, *, settings=None, sender=None):
        return dict(
            local_answer=lambda _: "Răspuns local.",
            settings=settings if settings is not None else AdapterSettings(),
            confirmed=True, provider_key_present=True,
            durable_budget=DurableBudget(str(Path(directory) / "quota.sqlite3")),
            session_budget=DemoBudget(),
            instance_gate=SharedBudgetGate(InstanceBudget()),
            sender=sender or (lambda _: "Răspuns experimental."),
        )

    def test_disabled_returns_local_without_provider(self):
        with tempfile.TemporaryDirectory() as d:
            sent = []
            args = self.setup_args(d, sender=lambda msg: sent.append(msg))
            result = route_single_answer(DEMO_PROMPTS[0], **args)
            self.assertEqual((result.text, result.source),
                             ("Răspuns local.", "local"))
            self.assertEqual(sent, [])

    def test_enabled_approved_demo_returns_one_answer(self):
        with tempfile.TemporaryDirectory() as d:
            args = self.setup_args(d, settings=AdapterSettings(
                enabled=True, privacy_approved=True, infrastructure_verified=True))
            result = route_single_answer(DEMO_PROMPTS[0], **args)
            self.assertEqual((result.text, result.source),
                             ("Răspuns experimental.", "experimental"))

    def test_private_school_question_stays_local(self):
        with tempfile.TemporaryDirectory() as d:
            sent = []
            args = self.setup_args(d, settings=AdapterSettings(
                enabled=True, privacy_approved=True, infrastructure_verified=True),
                sender=lambda msg: sent.append(msg))
            result = route_single_answer("Ce note are elevul meu?", **args)
            self.assertEqual(result.source, "local")
            self.assertEqual(sent, [])

    def test_provider_error_returns_local(self):
        with tempfile.TemporaryDirectory() as d:
            def broken(_):
                raise RuntimeError("offline simulation")
            args = self.setup_args(d, settings=AdapterSettings(
                enabled=True, privacy_approved=True, infrastructure_verified=True),
                sender=broken)
            result = route_single_answer(DEMO_PROMPTS[0], **args)
            self.assertEqual((result.source, result.provider_status),
                             ("local", "provider_error"))


if __name__ == "__main__":
    unittest.main()
