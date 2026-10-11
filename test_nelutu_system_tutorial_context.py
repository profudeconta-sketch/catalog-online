"""Offline tests for whole-system tutorial retrieval."""
import unittest
from nelutu_system_tutorial_context import tutorial_context, tutorial_topics


class TutorialContextTests(unittest.TestCase):
    def test_teacher_catalog(self):
        text = tutorial_context("Cum introduc notele in aplicatia profesorului?")
        self.assertIn("Notele", text)
        self.assertIn("Profesorul", text)

    def test_parent_leave(self):
        text = tutorial_context("Cum fac o solicitare de invoire?")
        self.assertIn("Învoire", text)

    def test_whole_system_not_just_parent_portal(self):
        headings = " ".join(tutorial_topics())
        self.assertIn("Importul din catalogul fizic", headings)
        self.assertIn("Catalogul oficial", headings)
        self.assertIn("Gestiunea elevilor", headings)

    def test_empty_and_overlong(self):
        self.assertEqual(tutorial_context(""), "")
        self.assertEqual(tutorial_context("x" * 601), "")

    def test_bounded(self):
        self.assertLessEqual(len(tutorial_context("catalog note absente profesor")), 3010)


if __name__ == "__main__":
    unittest.main()
