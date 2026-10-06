import unittest
from nelutu_mascot import render_nelutu_mascot, visual_contract

class NelutuMascotTests(unittest.TestCase):
    def test_visual_contract_is_safe(self):
        c=visual_contract()
        self.assertFalse(c["writes_data"])
        self.assertFalse(c["uses_network"])
        self.assertFalse(c["uses_javascript"])
        self.assertFalse(c["external_assets"])
        self.assertTrue(c["reusable_system_component"])

    def test_all_states_render(self):
        for state in ("idle","thinking","answering","serious","success"):
            html=render_nelutu_mascot(state,"No, amu testăm.")
            self.assertIn("Neluțu",html)
            self.assertIn("nelutu-"+state,html)

    def test_message_is_escaped(self):
        html=render_nelutu_mascot("idle","<script>alert(1)</script>")
        self.assertNotIn("<script>",html)
        self.assertIn("&lt;script&gt;",html)

    def test_no_external_or_script_dependencies(self):
        html=render_nelutu_mascot()
        low=html.lower()
        self.assertNotIn("<script",low)
        self.assertNotIn("http://",low)
        self.assertNotIn("https://",low)

if __name__=="__main__":
    unittest.main()
