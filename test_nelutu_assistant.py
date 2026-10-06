import unittest
import nelutu_assistant as n

class NelutuTests(unittest.TestCase):
    def test_read_only_contract(self):
        self.assertTrue(all(v is False for v in n.read_only_contract().values()))

    def test_personality_is_kind_self_ironic_and_never_blames_user(self):
        samples=[n.answer("nu inteleg cum functioneaza portalul"),n.answer("salut"),n.answer("ce este whatsapp")]
        joined=" ".join(x.text.lower() for x in samples)
        self.assertIn("😄",joined)
        self.assertTrue(any(x in joined for x in ("n-am degete","rotițele","buzunarele mele digitale","n-am nici picioare")))
        for bad in ("întrebare proastă","nu pricepi","vina ta","trebuia să știi"):
            self.assertNotIn(bad,joined)

    def test_authentic_regional_voice(self):
        joined=" ".join(n.answer(x).text.lower() for x in ("salut","absente","document","lege"))
        for token in ("ie mă","no, amu","api"):
            self.assertIn(token,joined)

    def test_user_correction_phrase_is_preserved(self):
        self.assertIn("No, amu m-ai băgat",n.answer("hiperpropulsor necunoscut").text)

    def test_absence_legal_guardrail_and_source(self):
        a=n.answer("cate absente poate motiva parintele?")
        self.assertEqual(a.intent,"absences")
        self.assertIn("40 de ore",a.text); self.assertIn("20%",a.text)
        self.assertIn("legislatie.just.ro",a.source_url)

    def test_serious_topics_drop_comedy(self):
        a=n.answer("copilul meu a fost lovit si amenintat")
        self.assertTrue(a.serious); self.assertNotIn("😂",a.text)
        self.assertIn("situație serioasă",a.text)

    def test_discipline_is_serious_but_still_nelutu(self):
        a=n.answer("sanctiune disciplinara si contestatie")
        self.assertTrue(a.serious); self.assertEqual(a.intent,"discipline")
        self.assertIsNotNone(a.source_url)

    def test_unknown_does_not_invent(self):
        a=n.answer("care este raspunsul la hiperpropulsorul clasei?")
        self.assertEqual(a.intent,"fallback")
        self.assertIn("Nu vreau să scot un răspuns din clop",a.text)

    def test_no_mutation_storage_network_or_ai_imports(self):
        source=open("nelutu_assistant.py",encoding="utf-8").read()
        forbidden=("document_storage","notification_storage","leave_pass_storage","urllib","requests","openai","anthropic","streamlit")
        for item in forbidden:
            self.assertNotIn("import "+item,source)

    def test_all_quick_topics_answer_without_exception(self):
        for topic in n.QUICK_TOPICS:
            a=n.answer(topic)
            self.assertTrue(a.text)
            self.assertIsInstance(a.serious,bool)

    def test_legal_sources_are_official(self):
        allowed=("legislatie.just.ro","www.edu.ro")
        for _,url in n.LEGAL_SOURCES.values():
            self.assertTrue(any(domain in url for domain in allowed),url)

if __name__=="__main__":
    unittest.main()
