import unittest
from nelutu_ai_learning import LearningNotebook
from nelutu_ai_review_auth import ReviewIdentity, ReviewDenied, approve_with_authorization

class ReviewAuthorizationTests(unittest.TestCase):
    def setUp(self):
        self.book = LearningNotebook()
        self.question = "De ce învățăm matematica?"
        self.book.propose(self.question, "Dezvoltă logica.")

    def test_authenticated_but_unauthorized(self):
        with self.assertRaises(ReviewDenied):
            approve_with_authorization(self.book, self.question,
                identity=ReviewIdentity("person_01", True),
                authorize=lambda principal, permission: False)
        self.assertIsNone(self.book.recall_verified(self.question))

    def test_not_authenticated(self):
        with self.assertRaises(ReviewDenied):
            approve_with_authorization(self.book, self.question,
                identity=ReviewIdentity("person_01", False),
                authorize=lambda principal, permission: True)

    def test_authorized_review(self):
        ok = approve_with_authorization(self.book, self.question,
            identity=ReviewIdentity("reviewer_01", True),
            authorize=lambda principal, permission: principal == "reviewer_01"
                and permission == "nelutu_lesson_review")
        self.assertTrue(ok)
        self.assertEqual(self.book.recall_verified(self.question), "Dezvoltă logica.")

    def test_no_authorization_callback(self):
        with self.assertRaises(ReviewDenied):
            approve_with_authorization(self.book, self.question,
                identity=ReviewIdentity("person_01", True), authorize=None)

if __name__ == "__main__":
    unittest.main()
