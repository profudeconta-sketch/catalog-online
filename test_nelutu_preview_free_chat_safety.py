"""Guard the experimental composer against fabricated model history."""
from pathlib import Path
import unittest


class PreviewComposerTests(unittest.TestCase):
    def test_local_composer_does_not_fabricate_model_turns(self):
        source = Path(__file__).with_name("nelutu_gemini_preview.py").read_text(encoding="utf-8")
        section = source.split('st.subheader("🤠 Dialog liber — verificare locală")', 1)[1]
        self.assertIn('prepare_public_dialogue((), free_question, consent=True)', section)
        self.assertIn('st.session_state["nelutu_free_chat_questions"]', section)
        self.assertNotIn('("model",', section)
        self.assertNotIn("generate_public_dialogue(", section)
        self.assertNotIn("reserve_gemini_attempt()", section)
        self.assertIn("nu sunt trimise la Google", section)


if __name__ == "__main__":
    unittest.main()
