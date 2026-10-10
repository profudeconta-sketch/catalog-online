"""Stage 45 pipeline tests using only fictional prompts and fake sender."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_integration_pipeline import run_demo_pipeline


class PipelineTests(unittest.TestCase):
    def test_success_and_durable_limit_without_real_network(self):
        with tempfile.TemporaryDirectory() as d:
            budget = DurableBudget(str(Path(d) / "quota.sqlite3"), limit=2)
            gate = SharedBudgetGate(InstanceBudget())
            session = DemoBudget()
            sent = []
            sender = lambda message: sent.append(message) or "Răspuns fictiv."
            params = dict(explicitly_enabled=True, confirmed=True,
                          provider_key_present=True, durable_budget=budget,
                          session_budget=session, instance_gate=gate, sender=sender)
            self.assertEqual(run_demo_pipeline(DEMO_PROMPTS[0], **params).status, "ok")
            self.assertEqual(run_demo_pipeline(DEMO_PROMPTS[0], **params).status, "ok")
            self.assertEqual(run_demo_pipeline(DEMO_PROMPTS[0], **params).status, "durable_quota_unavailable")
            self.assertEqual(len(sent), 2)

    def test_unapproved_message_never_reaches_sender_or_quota(self):
        with tempfile.TemporaryDirectory() as d:
            budget = DurableBudget(str(Path(d) / "quota.sqlite3"))
            sent = []
            result = run_demo_pipeline(
                "Date despre un elev", explicitly_enabled=True, confirmed=True,
                provider_key_present=True, durable_budget=budget,
                session_budget=DemoBudget(), instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda m: sent.append(m))
            self.assertEqual(result.status, "not_approved_public_demo")
            self.assertEqual(sent, [])
            self.assertTrue(budget.reserve())

    def test_missing_durable_gate_blocks_sender(self):
        sent = []
        result = run_demo_pipeline(
            DEMO_PROMPTS[0], explicitly_enabled=True, confirmed=True,
            provider_key_present=True, durable_budget=None,
            session_budget=DemoBudget(), instance_gate=SharedBudgetGate(InstanceBudget()),
            sender=lambda m: sent.append(m))
        self.assertEqual(result.status, "durable_quota_required")
        self.assertFalse(sent)

    def test_sender_failure_does_not_refund_attempt(self):
        with tempfile.TemporaryDirectory() as d:
            budget = DurableBudget(str(Path(d) / "quota.sqlite3"), limit=1)
            def failed_sender(_):
                raise RuntimeError("simulated")
            params = dict(explicitly_enabled=True, confirmed=True,
                          provider_key_present=True, durable_budget=budget,
                          session_budget=DemoBudget(),
                          instance_gate=SharedBudgetGate(InstanceBudget()),
                          sender=failed_sender)
            self.assertEqual(run_demo_pipeline(DEMO_PROMPTS[0], **params).status, "provider_error")
            self.assertEqual(budget.remaining(), 0)


if __name__ == "__main__":
    unittest.main()
