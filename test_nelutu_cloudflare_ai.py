import io
import json
import unittest
from nelutu_cloudflare_ai import generate,AIUnavailable,contract
from nelutu_ai_privacy import approved_external_question

class CloudflarePrototypeTests(unittest.TestCase):
    def test_public_education_only(self):
        self.assertTrue(approved_external_question("De ce este important învățământul tehnic?"))
        self.assertTrue(approved_external_question("Ce a schimbat Spiru Haret în școală?"))
        for q in ("O întrebare privată despre elev", "Solicit informații despre portal"):
            with self.subTest(q=q):
                self.assertFalse(approved_external_question(q))
    def test_history_rejected_even_when_empty(self):
        with self.assertRaisesRegex(AIUnavailable, "history_not_allowed"):
            generate("De ce învățăm matematica?", history=[])

    def test_history_rejected_with_private_context(self):
        with self.assertRaisesRegex(AIUnavailable, "history_not_allowed"):
            generate("De ce învățăm matematica?", history=[{"role":"assistant","content":"Date private"}])

    def test_off_by_default(self):
        with self.assertRaises(AIUnavailable):
            generate("De ce este importantă educația?")
    def test_mock_provider(self):
        seen=[]
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n): return json.dumps({"success":True,"result":{"response":"No, meseria se învață și cu mâinile!"}}).encode()
        def fake(request,timeout):
            seen.append((request.full_url,request.data,timeout))
            return Response()
        result=generate("Ce rol are educația tehnică?",account_id="abcdefgh1234",api_token="dummy",transport=fake)
        self.assertTrue(result.available)
        self.assertIn("meseria",result.text)
        self.assertIn(b"educa",seen[0][1])
    def test_contract(self):
        self.assertTrue(contract()["external_processing_when_enabled"])
        self.assertFalse(contract()["forwards_student_records"])

if __name__=="__main__":
    unittest.main()
