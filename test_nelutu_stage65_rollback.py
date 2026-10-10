"""Stage 65: local rollback contract, offline and independent of school apps."""
import tempfile
import unittest
from pathlib import Path

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class RollbackContractTests(unittest.TestCase):
    def call(self, local_reply, provider_reply, *, enabled=True):
        with tempfile.TemporaryDirectory() as folder:
            outbound = []
            result = route_single_answer(
                DEMO_PROMPTS[0], local_answer=lambda _: local_reply,
                settings=AdapterSettings(enabled=enabled, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed=True, provider_key_present=True,
                durable_budget=DurableBudget(str(Path(folder) / "quota.sqlite3")),
                session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda prompt: outbound.append(prompt) or provider_reply)
            return result, outbound

    def test_disabled_is_local_without_provider(self):
        result, sent = self.call("Neluțu local.", "Gemini", enabled=False)
        self.assertEqual((result.source, result.text), ("local", "Neluțu local."))
        self.assertFalse(sent)

    def test_provider_invalid_returns_one_local_answer(self):
        for answer in (None, "", " \n ", "\x00", 999):
            with self.subTest(answer=repr(answer)):
                result, sent = self.call("Neluțu local.", answer)
                self.assertEqual((result.source, result.text), ("local", "Neluțu local."))
                self.assertEqual(sent, [DEMO_PROMPTS[0]])

    def test_local_blank_blocks_provider(self):
        for local in ("", "   ", "\n\t", "\x00"):
            with self.subTest(local=repr(local)):
                result, sent = self.call(local, "Gemini")
                self.assertEqual((result.source, result.provider_status),
                                 ("local", "local_invalid"))
                self.assertTrue(result.text.strip())
                self.assertFalse(sent)

    def test_valid_local_multiline_still_works(self):
        result, sent = self.call("Primul rând\nAl doilea rând", None)
        self.assertEqual(result.text, "Primul rând\nAl doilea rând")
        self.assertEqual(result.source, "local")
        self.assertEqual(sent, [DEMO_PROMPTS[0]])


if __name__ == "__main__":
    unittest.main()
