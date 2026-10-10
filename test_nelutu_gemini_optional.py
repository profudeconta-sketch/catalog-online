"""Offline safety and contract tests: no real Gemini calls or credentials."""
import json
import unittest
from unittest.mock import patch
import nelutu_gemini_optional as gemini


class GeminiOptionalTests(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch.object(gemini.request, "urlopen") as opener:
            self.assertIsNone(gemini.generate("Ce mai faci?", api_key="dummy"))
            opener.assert_not_called()

    def test_no_key(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(gemini.generate("Ce mai faci?", enabled=True))

    def test_blocks_private_and_school_content(self):
        for question in (
            "Ce note are elevul?", "Am nevoie de catalog",
            "Numarul meu e 0742123456", "Scrie la test@example.com",
            "Am un diagnostic medical", "PIN 123456",
        ):
            with self.subTest(question=question):
                self.assertFalse(gemini.is_public_general_chat(question))
                self.assertIsNone(gemini.generate(question, api_key="dummy", enabled=True))

    def test_rejects_unsafe_history(self):
        self.assertIsNone(gemini.generate(
            "Ce mai faci?", (("user", "Notele elevului sunt bune"),),
            api_key="dummy", enabled=True, public_text_confirmed=True,
        ))

    def test_confirmation_required(self):
        self.assertIsNone(gemini.generate("Ce mai faci?", api_key="dummy", enabled=True))

    def test_public_conversation_can_use_mocked_provider(self):
        class Response:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                return False
            def read(self):
                return json.dumps({
                    "candidates": [{"content": {"parts": [{"text": "No, bine! 🤠"}]}}]
                }).encode()
        with patch.object(gemini.request, "urlopen", return_value=Response()) as opener:
            result = gemini.generate(
                "Salut, Neluțu! Ce mai faci?",
                api_key="dummy", enabled=True, public_text_confirmed=True,
            )
            self.assertEqual(result, "No, bine! 🤠")
            args, kwargs = opener.call_args
            self.assertEqual(kwargs["timeout"], gemini.TIMEOUT)
            payload = json.loads(args[0].data)
            self.assertEqual(len(payload["contents"]), 1)
            self.assertEqual(payload["contents"][-1]["parts"][0]["text"], "Salut, Neluțu! Ce mai faci?")


class Stage31IntegrationBoundaryTests(unittest.TestCase):
    """Static fail-safe checks for the isolated demo, with no provider calls."""

    def test_preview_has_no_school_application_imports(self):
        import ast
        from pathlib import Path
        source = Path(__file__).with_name("nelutu_gemini_preview.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        forbidden = ("app_web_catalog", "app_parinti", "document_storage",
                     "leave_pass_storage", "parent_excuse_pdf")
        for name in imports:
            self.assertNotIn(name.split(".")[0], forbidden)

    def test_all_preview_network_buttons_reserve_budget(self):
        from pathlib import Path
        source = Path(__file__).with_name("nelutu_gemini_preview.py").read_text(encoding="utf-8")
        self.assertEqual(source.count("and reserve_gemini_attempt():"), 9)
        self.assertGreaterEqual(source.count("disabled=not "), 9)
        self.assertIn("budget_gate.reserve(shared_budget)", source)
        self.assertIn("SharedBudgetGate", source)

    def test_fixed_transport_requires_approved_transcript(self):
        from unittest.mock import Mock
        from nelutu_gemini_fixed_transport import send_fixed_exchange
        opener = Mock()
        self.assertIsNone(send_fixed_exchange(
            (("user", "Date despre elev"),),
            api_key="dummy", enabled=True, confirmed=True,
            temperature=0.4, opener=opener,
        ))
        opener.assert_not_called()

    def test_stage34_gate_enforces_limits(self):
        from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
        from nelutu_demo_budget import DemoBudget
        instance = InstanceBudget()
        gate = SharedBudgetGate(instance)
        sessions = [DemoBudget() for _ in range(8)]
        results = [gate.reserve(sessions[i % 8]) for i in range(30)]
        self.assertEqual(sum(results), 12)
        self.assertEqual(instance.remaining(), 0)
        self.assertTrue(all(s.used <= 3 for s in sessions))

    def test_stage34_concurrent_reservations(self):
        from concurrent.futures import ThreadPoolExecutor
        from nelutu_instance_budget import InstanceBudget, SharedBudgetGate
        from nelutu_demo_budget import DemoBudget
        gate = SharedBudgetGate(InstanceBudget())
        session = DemoBudget()
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(lambda _: gate.reserve(session), range(40)))
        self.assertEqual(sum(results), 3)


class Stage36OutboundBoundaryTests(unittest.TestCase):
    """Offline checks of all approved single-message scenarios."""

    def test_only_nine_exact_public_prompts_are_allowed(self):
        import ast
        from pathlib import Path
        from nelutu_gemini_demo import DEMO_PROMPTS
        tree = ast.parse(Path(__file__).with_name("nelutu_gemini_preview.py").read_text(encoding="utf-8"))
        assignments = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in ("style_prompt", "tone_examples"):
                        assignments[target.id] = ast.literal_eval(node.value)
        approved = DEMO_PROMPTS + (assignments["style_prompt"],) + tuple(
            message for _, message in assignments["tone_examples"]
        )
        self.assertEqual(len(approved), 9)
        self.assertEqual(len(set(approved)), 9)
        for message in approved:
            with self.subTest(message=message):
                self.assertTrue(gemini.is_approved_demo_message(message))
                self.assertFalse(gemini.is_approved_demo_message(message + " "))
        for message in ("Salut, Neluțu!", "Numele unui elev", "Bună ziua!"):
            self.assertFalse(gemini.is_approved_demo_message(message))

    def test_unapproved_messages_are_rejected_before_network(self):
        with patch.object(gemini.request, "urlopen") as opener:
            self.assertIsNone(gemini.generate(
                "Bună ziua!", api_key="dummy", enabled=True,
                public_text_confirmed=True))
            self.assertEqual(gemini.diagnose_status(
                "Bună ziua!", api_key="dummy", enabled=True,
                public_text_confirmed=True), "blocked")
            opener.assert_not_called()


if __name__ == "__main__":
    unittest.main()
