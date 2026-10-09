"""Teste reale ale widgeturilor Streamlit, fără server sau date de elevi."""
import os
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

class PreviewUITests(unittest.TestCase):
    def make_app(self):
        with patch.dict(os.environ, {"NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL": "1"}):
            app = AppTest.from_file("nelutu_dialogue_preview.py", default_timeout=15).run()
        self.assertFalse(app.exception, str(list(app.exception)))
        return app

    def test_dialogue_and_reset(self):
        with patch.dict(os.environ, {"NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL": "1"}):
            app = self.make_app()
            app.text_input[0].set_value("De ce învățăm la școală?")
            app.button(key="FormSubmitter:preview_nelutu_form-Întreabă-l pe Neluțu").click().run()
            self.assertFalse(app.exception, str(list(app.exception)))
            self.assertEqual(app.session_state["preview_nelutu_state"].topic, "purpose")
            app.text_input[0].set_value("Dă-mi un exemplu")
            app.button(key="FormSubmitter:preview_nelutu_form-Întreabă-l pe Neluțu").click().run()
            self.assertFalse(app.exception, str(list(app.exception)))
            self.assertEqual(app.session_state["preview_nelutu_reply"].intent, "education_followup_purpose")
            app.button(key="preview_nelutu_reset").click().run()
            self.assertFalse(app.exception, str(list(app.exception)))
            self.assertEqual(app.session_state["preview_nelutu_state"].topic, "")
            self.assertIsNone(app.session_state["preview_nelutu_reply"])

    def test_real_browser_example_concret_keeps_topic(self):
        with patch.dict(os.environ, {"NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL": "1"}):
            app = self.make_app()
            for question in ("De ce învățăm la școală?", "Dă-mi un exemplu concret."):
                app.text_input[0].set_value(question)
                app.button(key="FormSubmitter:preview_nelutu_form-Întreabă-l pe Neluțu").click().run()
                self.assertFalse(app.exception, str(list(app.exception)))
            self.assertEqual(app.session_state["preview_nelutu_reply"].intent, "education_followup_purpose")
            self.assertEqual(app.session_state["preview_nelutu_state"].topic, "purpose")

    def test_math_followup_in_preview(self):
        with patch.dict(os.environ, {"NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL": "1"}):
            app = self.make_app()
            questions = ("De ce învățăm la școală?", "Dă-mi un exemplu concret.", "Matematică. Mai explică-mi.")
            for question in questions:
                app.text_input[0].set_value(question)
                app.button(key="FormSubmitter:preview_nelutu_form-Întreabă-l pe Neluțu").click().run()
                self.assertFalse(app.exception, str(list(app.exception)))
            self.assertEqual(app.session_state["preview_nelutu_reply"].intent, "education_followup_purpose")

    def test_portal_question_resets_educational_topic(self):
        with patch.dict(os.environ, {"NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL": "1"}):
            app = self.make_app()
            for question in ("De ce învățăm la școală?", "Cum trimit scutirea medicală?"):
                app.text_input[0].set_value(question)
                app.button(key="FormSubmitter:preview_nelutu_form-Întreabă-l pe Neluțu").click().run()
                self.assertFalse(app.exception, str(list(app.exception)))
            self.assertEqual(app.session_state["preview_nelutu_reply"].intent, "parent_guide_medical")
            self.assertEqual(app.session_state["preview_nelutu_state"].topic, "")

    def test_sensitive_message_resets_context(self):
        with patch.dict(os.environ, {"NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL": "1"}):
            app = self.make_app()
            for question in ("De ce învățăm la școală?", "Nu mai vreau să trăiesc, unde e butonul din portal?"):
                app.text_input[0].set_value(question)
                app.button(key="FormSubmitter:preview_nelutu_form-Întreabă-l pe Neluțu").click().run()
                self.assertFalse(app.exception, str(list(app.exception)))
            self.assertEqual(app.session_state["preview_nelutu_reply"].intent, "sensitive_redirect")
            self.assertEqual(app.session_state["preview_nelutu_state"].topic, "")

    def test_followup_after_sensitive_message_does_not_resume_old_topic(self):
        with patch.dict(os.environ, {"NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL": "1"}):
            app = self.make_app()
            for question in (
                "De ce învățăm la școală?",
                "Nu mai vreau să trăiesc, unde e butonul din portal?",
                "Dă-mi un exemplu",
            ):
                app.text_input[0].set_value(question)
                app.button(key="FormSubmitter:preview_nelutu_form-Întreabă-l pe Neluțu").click().run()
                self.assertFalse(app.exception, str(list(app.exception)))
            self.assertNotEqual(
                app.session_state["preview_nelutu_reply"].intent,
                "education_followup_purpose",
            )
            self.assertEqual(app.session_state["preview_nelutu_state"].topic, "")

    def test_separate_sessions_do_not_share_topic(self):
        with patch.dict(os.environ, {"NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL": "1"}):
            first = self.make_app()
            second = self.make_app()
            first.text_input[0].set_value("De ce învățăm la școală?")
            first.button(key="FormSubmitter:preview_nelutu_form-Întreabă-l pe Neluțu").click().run()
            self.assertEqual(first.session_state["preview_nelutu_state"].topic, "purpose")
            self.assertEqual(second.session_state["preview_nelutu_state"].topic, "")

if __name__ == "__main__":
    unittest.main()
