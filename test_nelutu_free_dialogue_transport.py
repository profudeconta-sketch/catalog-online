"""Offline transport tests; never access the Gemini service."""
import io
import json
import unittest
from nelutu_free_dialogue_transport import generate_public_dialogue


class Response(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class TransportTests(unittest.TestCase):
    def test_blocked_by_default_without_network(self):
        def forbidden(*args, **kwargs):
            raise AssertionError("network must not be called")
        self.assertIsNone(generate_public_dialogue((), "Salut!", api_key="test", opener=forbidden))
        self.assertIsNone(generate_public_dialogue(
            (), "Salut!", api_key="test", enabled=True, confirmed=True, opener=forbidden,
        ))
        self.assertIsNone(generate_public_dialogue(
            (), "Ce nota are elevul?", api_key="test", enabled=True,
            confirmed=True, budget_reserved=True, opener=forbidden,
        ))

    def test_context_is_sent_only_when_all_gates_true(self):
        captured = []
        def opener(req, timeout):
            captured.append(json.loads(req.data))
            return Response(json.dumps({
                "candidates": [{"content": {"parts": [{"text": "No, povestim!"}]}}]
            }).encode("utf-8"))
        answer = generate_public_dialogue(
            (("user", "Salut!"), ("model", "Buna ziua!")),
            "Ce mai faci?", api_key="test",
            enabled=True, confirmed=True, budget_reserved=True, opener=opener,
        )
        self.assertEqual(answer, "No, povestim!")
        self.assertEqual([x["role"] for x in captured[0]["contents"]],
                         ["user", "model", "user"])

    def test_provider_failure_is_silent(self):
        def failed(*args, **kwargs):
            raise OSError("offline")
        self.assertIsNone(generate_public_dialogue(
            (), "Salut!", api_key="test", enabled=True,
            confirmed=True, budget_reserved=True, opener=failed,
        ))


if __name__ == "__main__":
    unittest.main()
