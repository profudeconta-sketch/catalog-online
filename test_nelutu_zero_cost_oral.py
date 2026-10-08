"""Offline oral rehearsal with synthetic answers. No network, billing or student data.

This does not certify real generative dialogue or native-speaker language quality.
"""
import json
import unittest

from nelutu_ai_privacy import approved_external_question
from nelutu_cloudflare_ai import AIUnavailable, generate
from nelutu_ai_romanian import polish_romanian
from nelutu_ai_tone import choose_tone

PUBLIC = (
    "De ce învățăm matematica?",
    "La ce folosește matematica în viața cotidiană?",
    "De ce este important învățământul tehnic?",
    "Ce rol are educația tehnică?",
    "Cum putem învăța mai eficient?",
    "Cum ne păstrăm motivația pentru învățare?",
    "Ce a schimbat Spiru Haret în școală?",
    "Ce rol a avut Alexandru Ioan Cuza în educație?",
)
SENSITIVE = (
    "Mi-e frică să merg la școală.",
    "M-au bătut colegii.",
    "Nu mai vreau să trăiesc.",
    "Cineva mă amenință.",
)
GOOD_ANSWERS = (
    "No, așe-i! Matematica ne ajută să gândim limpede.",
    "Învață câte puțin și exersează.",
    "Nu ezita să ceri ajutor.",
)

class ZeroCostOralRehearsal(unittest.TestCase):
    def test_public_questions_use_synthetic_transport_only(self):
        for question in PUBLIC:
            with self.subTest(question=question):
                self.assertTrue(approved_external_question(question))
                calls = []
                class Response:
                    def __enter__(self): return self
                    def __exit__(self, *args): return False
                    def read(self, n):
                        return json.dumps({"success": True, "result": {"response": GOOD_ANSWERS[1]}}).encode()
                def fake(request, timeout):
                    calls.append(json.loads(request.data))
                    return Response()
                result = generate(question, account_id="abcdefgh1234",
                                  api_token="synthetic", transport=fake)
                self.assertTrue(result.available)
                self.assertEqual(result.text, GOOD_ANSWERS[1])
                self.assertEqual(len(calls), 1)
                self.assertEqual(len(calls[0]["messages"]), 2)
                self.assertEqual(calls[0]["messages"][1]["content"], question)

    def test_sensitive_prompts_never_call_provider(self):
        def forbidden(*args, **kwargs):
            self.fail("No external transport for sensitive content")
        for question in SENSITIVE:
            with self.subTest(question=question):
                self.assertFalse(choose_tone(question).humor_allowed)
                with self.assertRaisesRegex(AIUnavailable, "not_eligible"):
                    generate(question, account_id="abcdefgh1234",
                             api_token="synthetic", transport=forbidden)

    def test_correct_feminine_agreement_is_preserved(self):
        sentence = "Ele vor să devină autonome în domenii concrete."
        self.assertEqual(polish_romanian(sentence), sentence)

    def test_romanian_and_regional_phrases_remain_stable(self):
        for sentence in GOOD_ANSWERS:
            with self.subTest(sentence=sentence):
                self.assertEqual(polish_romanian(sentence), sentence)

if __name__ == "__main__":
    unittest.main()
