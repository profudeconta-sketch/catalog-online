import io
import json
import unittest
from nelutu_ai_oral import timed_oral_exam

class OralExamTests(unittest.TestCase):
    def test_mock_response_is_timely_and_useful(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n):
                return json.dumps({"success": True, "result": {"response": "Matematica ne ajută să gândim logic."}}).encode()
        result = timed_oral_exam("De ce învățăm matematica?", transport=lambda request, timeout: Response())
        self.assertTrue(result.within_budget)
        self.assertTrue(result.available)
        self.assertIn("logic", result.answer)

    def test_private_question_rejected_without_network(self):
        calls = []
        result = timed_oral_exam("Ce note are copilul meu?", transport=lambda *args: calls.append(args))
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "not_eligible")
        self.assertEqual(calls, [])

    def test_invalid_budget_rejected(self):
        with self.assertRaises(ValueError):
            timed_oral_exam("De ce învățăm matematica?", transport=lambda *args: None, budget_seconds=0)


    def test_empty_provider_answer_is_rejected(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n):
                return json.dumps({"success": True, "result": {"response": "   "}}).encode()
        result = timed_oral_exam("De ce învățăm matematica?", transport=lambda *args: Response())
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "invalid_response")

    def test_provider_timeout_is_rejected(self):
        def timeout(*args, **kwargs):
            raise TimeoutError("synthetic timeout")
        result = timed_oral_exam("De ce învățăm matematica?", transport=timeout)
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "provider_unavailable")

    def test_slow_provider_fails_time_budget(self):
        import time
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n):
                return json.dumps({"success": True, "result": {"response": "Răspuns de test."}}).encode()
        def slow(*args, **kwargs):
            time.sleep(0.02)
            return Response()
        result = timed_oral_exam("De ce învățăm matematica?", transport=slow, budget_seconds=0.001)
        self.assertTrue(result.available)
        self.assertFalse(result.within_budget)

    def test_truncated_provider_answer_is_rejected(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n):
                return json.dumps({"success": True, "result": {"response": "Incomplet", "choices": [{"finish_reason": "length"}]}}).encode()
        result = timed_oral_exam("De ce învățăm matematica?", transport=lambda *args: Response())
        self.assertFalse(result.available)
        self.assertEqual(result.reason, "truncated_response")

if __name__ == "__main__":
    unittest.main()
