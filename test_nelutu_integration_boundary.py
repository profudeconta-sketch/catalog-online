"""Regression guard: existing Neluțu must remain the only production assistant.

These tests are offline and do not access school data or Gemini.
"""
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parent


class IntegrationBoundaryTests(unittest.TestCase):
    def test_teacher_and_parent_apps_are_not_imported_by_gemini(self):
        for name in ("nelutu_free_dialogue_transport.py", "nelutu_system_tutorial_context.py"):
            source = (ROOT / name).read_text(encoding="utf-8")
            self.assertNotIn("import app_parinti", source)
            self.assertNotIn("import app_web_catalog", source)

    def test_existing_parent_assistant_is_still_used(self):
        source = (ROOT / "app_parinti.py").read_text(encoding="utf-8")
        self.assertIn("nelutu_dialogue_adapter", source)
        self.assertIn("_nelutu_answer_compat", source)
        self.assertIn("render_nelutu_corner", source)

    def test_existing_tutorial_is_source_not_duplicate(self):
        source = (ROOT / "nelutu_system_tutorial_context.py").read_text(encoding="utf-8")
        self.assertIn("from nelutu_parent_guide import TUTORIAL_TEXT", source)

    def test_generative_transport_is_not_silently_active(self):
        source = (ROOT / "nelutu_free_dialogue_transport.py").read_text(encoding="utf-8")
        self.assertIn("enabled=False", source)
        self.assertIn("confirmed=False", source)
        self.assertIn("budget_reserved=False", source)


if __name__ == "__main__":
    unittest.main()
