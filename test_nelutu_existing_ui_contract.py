"""Stage 55: verify the existing school UI remains untouched and unique."""
import ast
from pathlib import Path
import unittest


class ExistingInterfaceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.portal = Path("app_parinti.py").read_text(encoding="utf-8")
        cls.teacher = Path("app_web_catalog.py").read_text(encoding="utf-8")

    def test_single_existing_dialogue(self):
        self.assertEqual(self.portal.count('with st.popover("🤠 Întreabă-l pe Neluțu"'), 1)
        self.assertEqual(self.portal.count('key="nelutu_question_form"'), 1)
        self.assertEqual(self.portal.count('key="nelutu_qa_trigger"'), 1)

    def test_existing_local_rollback_is_preserved(self):
        self.assertIn('os.environ.get("NELUTU_V2_ENABLED", "1")', self.portal)
        self.assertIn("def _nelutu_answer_compat(question, context):", self.portal)
        self.assertIn("return nelutu_answer(question, context)", self.portal)

    def test_experimental_router_not_imported_by_live_apps(self):
        for source in (self.portal, self.teacher):
            tree = ast.parse(source)
            imports = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    imports.add(node.module)
                elif isinstance(node, ast.Import):
                    imports.update(alias.name for alias in node.names)
            self.assertNotIn("nelutu_single_answer_router", imports)
            self.assertNotIn("nelutu_optional_integration_adapter", imports)
            self.assertNotIn("nelutu_gemini_optional", imports)


if __name__ == "__main__":
    unittest.main()
