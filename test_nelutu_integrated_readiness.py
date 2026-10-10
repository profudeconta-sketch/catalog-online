"""Integrated offline checks for the experimental provider boundary."""
import ast
from pathlib import Path
import tempfile
import unittest

from nelutu_demo_budget import DemoBudget
from nelutu_durable_budget import DurableBudget
from nelutu_gemini_demo import DEMO_PROMPTS
from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
from nelutu_optional_integration_adapter import AdapterSettings
from nelutu_single_answer_router import route_single_answer


class IntegratedBoundaryTests(unittest.TestCase):
    def run_case(self, answer, enabled=True):
        with tempfile.TemporaryDirectory() as folder:
            sent = []
            result = route_single_answer(
                DEMO_PROMPTS[0],
                local_answer=lambda _: "Răspuns local.",
                settings=AdapterSettings(enabled=enabled, privacy_approved=True,
                                         infrastructure_verified=True),
                confirmed=True, provider_key_present=True,
                durable_budget=DurableBudget(str(Path(folder) / "quota.sqlite3")),
                session_budget=DemoBudget(),
                instance_gate=SharedBudgetGate(InstanceBudget()),
                sender=lambda prompt: sent.append(prompt) or answer)
            return result, sent

    def test_multiline_reply_is_accepted(self):
        result, sent = self.run_case("Primul rând.\nAl doilea rând.")
        self.assertEqual(result.source, "experimental")
        self.assertEqual(result.text, "Primul rând.\nAl doilea rând.")
        self.assertEqual(sent, [DEMO_PROMPTS[0]])

    def test_tab_reply_is_accepted(self):
        result, _ = self.run_case("Coloana 1\tColoana 2")
        self.assertEqual(result.source, "experimental")

    def test_unsafe_controls_fall_back(self):
        for answer in ("Text\x00", "Text\x1b[31m", "Text\rmodificat"):
            with self.subTest(answer=repr(answer)):
                result, _ = self.run_case(answer)
                self.assertEqual((result.source, result.text), ("local", "Răspuns local."))

    def test_disabled_does_not_contact_provider(self):
        result, sent = self.run_case("Provider", enabled=False)
        self.assertEqual(result.source, "local")
        self.assertFalse(sent)

    def test_preview_has_fail_closed_durable_reservation(self):
        source = Path("nelutu_gemini_preview.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                     and node.name == "reserve_gemini_attempt"]
        self.assertEqual(len(functions), 1)
        first = functions[0].body[1] if isinstance(functions[0].body[0], ast.Expr) else functions[0].body[0]
        self.assertIsInstance(first, ast.If)
        self.assertIn("not durable_mode", ast.unparse(first.test))
        self.assertIn("durable_budget is None", ast.unparse(first.test))
        self.assertTrue(any(isinstance(n, ast.Return) and isinstance(n.value, ast.Constant)
                            and n.value.value is False for n in ast.walk(first)))


if __name__ == "__main__":
    unittest.main()
