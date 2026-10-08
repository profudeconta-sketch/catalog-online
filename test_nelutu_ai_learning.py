import unittest
from nelutu_ai_learning import LearningNotebook
from nelutu_ai_review_auth import ReviewIdentity, approve_with_authorization

class LearningTests(unittest.TestCase):
    def test_pending_not_a_fact(self):
        notebook = LearningNotebook()
        q = "De ce învățăm matematica?"
        self.assertTrue(notebook.propose(q, "Dezvoltă logica."))
        self.assertIsNone(notebook.recall_verified(q))
        self.assertTrue(approve_with_authorization(notebook, q, identity=ReviewIdentity("human_review", True), authorize=lambda principal, permission: True))
        self.assertEqual(notebook.recall_verified(q), "Dezvoltă logica.")

    def test_reject_private_and_sensitive(self):
        notebook = LearningNotebook()
        self.assertFalse(notebook.propose("Ce note are copilul meu?", "Un răspuns."))
        self.assertFalse(notebook.propose("De ce învățăm matematica?", "PIN: 1234"))
        self.assertEqual(notebook.lessons, {})

    def test_retract_and_correction_requires_review(self):
        notebook = LearningNotebook()
        q = "De ce învățăm matematica?"
        notebook.propose(q, "Prima explicație.")
        approve_with_authorization(notebook, q, identity=ReviewIdentity("human_review", True), authorize=lambda principal, permission: True)
        notebook.propose(q, "Explicație corectată.")
        self.assertIsNone(notebook.recall_verified(q))
        notebook.retract(q)
        self.assertIsNone(notebook.recall_verified(q))

    def test_no_approval_without_reviewer(self):
        notebook = LearningNotebook()
        q = "De ce învățăm matematica?"
        notebook.propose(q, "Explicație.")
        with self.assertRaises(PermissionError):
            notebook.approve(q, reviewer="")

if __name__ == "__main__":
    unittest.main()
