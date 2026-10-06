import unittest

import nelutu_assistant as n


class NelutuTests(unittest.TestCase):
    def test_read_only_contract(self):
        self.assertTrue(all(value is False for value in n.read_only_contract().values()))

    def test_personality_is_kind_and_self_ironic(self):
        a = n.answer("nu inteleg cum functioneaza portalul")
        self.assertIn("😄", a.text)
        self.assertIn("nu-l apăs eu", a.text)

    def test_regional_voice(self):
        samples = [n.answer("salut"), n.answer("absente"), n.answer("ce e o instiintare")]
        joined = " ".join(x.text.lower() for x in samples)
        self.assertTrue(any(token in joined for token in ("ie mă", "no,", "amu", "api")))

    def test_absence_legal_guardrail(self):
        a = n.answer("cate absente poate motiva parintele?")
        self.assertEqual(a.intent, "absences")
        self.assertIn("40 de ore", a.text)
        self.assertIn("20%", a.text)
        self.assertIsNotNone(a.source_url)

    def test_serious_topics_drop_jokes(self):
        a = n.answer("copilul meu a fost lovit si amenintat")
        self.assertTrue(a.serious)
        self.assertNotIn("😂", a.text)
        self.assertIn("situație serioasă", a.text)

    def test_unknown_does_not_invent(self):
        a = n.answer("care este raspunsul la hiperpropulsorul clasei?")
        self.assertEqual(a.intent, "fallback")
        self.assertIn("Nu vreau să scot un răspuns din clop", a.text)

    def test_no_storage_or_network_imports(self):
        source = open("nelutu_assistant.py", encoding="utf-8").read()
        forbidden = ("document_storage", "notification_storage", "urllib", "requests", "openai", "anthropic")
        for item in forbidden:
            self.assertNotIn("import " + item, source)


if __name__ == "__main__":
    unittest.main()
