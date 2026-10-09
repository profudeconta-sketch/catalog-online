"""Regresii de integrare Neluțu V2: fără date reale, fără Streamlit pornit."""
import ast
from pathlib import Path
import unittest

SOURCE = Path("app_parinti.py").read_text(encoding="utf-8")
TREE = ast.parse(SOURCE)

class ParentPortalIntegrationTests(unittest.TestCase):
    def test_parent_portal_compiles(self):
        compile(SOURCE, "app_parinti.py", "exec")

    def test_only_expected_app_is_modified_by_integration(self):
        self.assertIn("from nelutu_dialogue_adapter import answer_parent_dialogue as _nelutu_v2_answer", SOURCE)
        self.assertIn('st.session_state["nelutu_answered_reply"] = _nelutu_answer_compat(', SOURCE)

    def test_legacy_fallback_and_kill_switch(self):
        self.assertIn('os.environ.get("NELUTU_V2_ENABLED", "1") == "1"', SOURCE)
        wrapper = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "_nelutu_answer_compat")
        self.assertTrue(any(isinstance(n, ast.Return) and isinstance(n.value, ast.Call)
                            and isinstance(n.value.func, ast.Name) and n.value.func.id == "nelutu_answer"
                            for n in ast.walk(wrapper)))

    def test_dialogue_state_is_session_scoped(self):
        wrapper = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "_nelutu_answer_compat")
        code = ast.get_source_segment(SOURCE, wrapper)
        self.assertIn('st.session_state.get("nelutu_v2_dialogue_state")', code)
        self.assertIn('st.session_state["nelutu_v2_dialogue_state"] = next_state', code)
        self.assertNotIn("st.secrets", code)

    def test_no_new_catalog_write_or_network_calls_in_wrapper(self):
        wrapper = next(n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == "_nelutu_answer_compat")
        code = ast.get_source_segment(SOURCE, wrapper)
        for prohibited in ("requests.", "urllib.", "open(", "write(", "save(", "store_new_document", "github"):
            with self.subTest(prohibited=prohibited):
                self.assertNotIn(prohibited, code)

if __name__ == "__main__":
    unittest.main()
