"""Single Neluțu UI contract; no changes to the live school applications."""
import ast
from pathlib import Path
import unittest


class SingleNelutuUiTests(unittest.TestCase):
    def test_parent_portal_has_one_dialog_entrypoint(self):
        source = Path("app_parinti.py").read_text(encoding="utf-8")
        self.assertEqual(source.count('with st.popover("🤠 Întreabă-l pe Neluțu"'), 1)
        self.assertEqual(source.count('key="nelutu_question_form"'), 1)
        self.assertEqual(source.count('key="nelutu_qa_trigger"'), 1)

    def test_experimental_adapter_has_no_ui_rendering(self):
        for name in ("nelutu_integration_gate.py",
                     "nelutu_integration_pipeline.py",
                     "nelutu_optional_integration_adapter.py"):
            tree = ast.parse(Path(name).read_text(encoding="utf-8"))
            imports = [node.module for node in ast.walk(tree)
                       if isinstance(node, ast.ImportFrom) and node.module]
            self.assertNotIn("streamlit", imports)
            self.assertNotIn("app_parinti", imports)
            self.assertNotIn("app_web_catalog", imports)

if __name__ == "__main__":
    unittest.main()
