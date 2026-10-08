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
    def test_bounded_live_exam_token_budget(self):
        seen=[]
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n):
                return json.dumps({"success":True,"result":{"response":"Un răspuns public complet."}}).encode()
        def fake(request,timeout):
            seen.append(json.loads(request.data))
            return Response()
        generate("Ce rol are educația tehnică?",account_id="abcdefgh1234",api_token="dummy",transport=fake,max_output_tokens=1600)
        self.assertEqual(seen[0]["max_tokens"],1600)
        self.assertEqual(len(seen[0]["messages"]),2)
        for limit in (0,1601,True,"1600"):
            with self.subTest(limit=limit):
                with self.assertRaisesRegex(AIUnavailable,"invalid_token_limit"):
                    generate("Ce rol are educația tehnică?",account_id="abcdefgh1234",api_token="dummy",transport=fake,max_output_tokens=limit)
    def test_oversized_provider_answer_is_rejected_not_cut(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n):
                return json.dumps({"success":True,"result":{"response":"x"*2201}}).encode()
        def fake(request,timeout):
            return Response()
        with self.assertRaisesRegex(AIUnavailable,"oversized_response"):
            generate("Ce rol are educația tehnică?",account_id="abcdefgh1234",api_token="dummy",transport=fake)

    def test_polish_applied_to_provider_answer(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self,*args): return False
            def read(self,n):
                return json.dumps({"success":True,"result":{"response":"Nu ezita să cere ajutorul."}}).encode()
        def fake(request,timeout):
            return Response()
        result=generate("Ce rol are educația tehnică?",account_id="abcdefgh1234",api_token="dummy",transport=fake)
        self.assertEqual(result.text,"Nu ezita să ceri ajutor.")

    def test_unapproved_model_is_rejected_before_network(self):
        for model in ("@cf/other/model", "@cf/../unsafe", "@cf/qwen/qwen3-30b-a3b-fp8?x=1"):
            with self.subTest(model=model):
                with self.assertRaisesRegex(AIUnavailable, "invalid_model"):
                    generate("Ce rol are educația tehnică?", account_id="abcdefgh1234",
                             api_token="dummy", model=model,
                             transport=lambda *args, **kwargs: self.fail("network must not run"))

    def test_malformed_provider_shapes_fail_closed(self):
        for payload in ([], {"success":True,"result":[]},
                        {"success":True,"result":{"response":"Răspuns", "choices":"wrong"}}):
            class Response:
                def __enter__(self): return self
                def __exit__(self,*args): return False
                def read(self,n): return json.dumps(payload).encode()
            def fake(request,timeout): return Response()
            with self.subTest(payload=payload):
                with self.assertRaisesRegex(AIUnavailable, "invalid_response"):
                    generate("Ce rol are educația tehnică?", account_id="abcdefgh1234",
                             api_token="dummy", transport=fake)

    def test_invalid_credentials_are_rejected_before_network(self):
        def forbidden(*args, **kwargs):
            self.fail("Network call is forbidden for invalid credentials")
        for account, token in ((12345678, "dummy"), (["abcdefgh"], "dummy"),
                               ("abcdefgh1234", 1234), ("abcdefgh1234", "bad\nheader"),
                               ("abcdefgh1234", "bad\rheader")):
            with self.subTest(account=repr(account), token=repr(token)):
                with self.assertRaisesRegex(AIUnavailable, "invalid_credentials"):
                    generate("Ce rol are educația tehnică?", account_id=account,
                             api_token=token, transport=forbidden)

    def test_malformed_choice_is_rejected(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n):
                return json.dumps({"success": True, "result": {
                    "response": "Text valid", "choices": [123]}}).encode()
        with self.assertRaisesRegex(AIUnavailable, "invalid_response"):
            generate("Ce rol are educația tehnică?", account_id="abcdefgh1234",
                     api_token="dummy", transport=lambda request, timeout: Response())

    def test_oversized_provider_json_fails_closed(self):
        expected_limit = 131073
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self, n):
                assert n == expected_limit
                return b"x" * expected_limit
        with self.assertRaisesRegex(AIUnavailable, "oversized_provider_payload"):
            generate("Ce rol are educația tehnică?", account_id="abcdefgh1234",
                     api_token="dummy", transport=lambda request, timeout: Response())

    def test_provider_reasoning_tags_are_not_displayed(self):
        for answer in ("<think>hidden reasoning</think>Răspuns public.",
                       "Răspuns public.</think>", "<THINK>hidden"):
            class Response:
                def __enter__(self): return self
                def __exit__(self, *args): return False
                def read(self, n):
                    return json.dumps({"success": True, "result": {"response": answer}}).encode()
            with self.subTest(answer=answer):
                with self.assertRaisesRegex(AIUnavailable, "untrusted_model_output"):
                    generate("Ce rol are educația tehnică?",
                             account_id="abcdefgh1234", api_token="synthetic",
                             transport=lambda request, timeout: Response())

    def test_contract(self):
        self.assertTrue(contract()["external_processing_when_enabled"])
        self.assertFalse(contract()["forwards_student_records"])

if __name__=="__main__":
    unittest.main()
