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
            app.button(key="Șterge contextul conversației").click().run()
            self.assertFalse(app.exception, str(list(app.exception)))
            self.assertEqual(app.session_state["preview_nelutu_state"].topic, "")
            self.assertIsNone(app.session_state["preview_nelutu_reply"])

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
