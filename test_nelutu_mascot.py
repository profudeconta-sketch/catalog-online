import unittest
from nelutu_mascot import render_nelutu_corner, render_nelutu_corner_nudge, render_nelutu_mascot, visual_contract

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

    def test_cartoon_face_and_dynamic_states(self):
        idle=render_nelutu_mascot("idle")
        answering=render_nelutu_mascot("answering")
        serious=render_nelutu_mascot("serious")
        for part in ("<svg","nelutu-eye","nelutu-pupil","nelutu-brow-l","nelutu-brow-r",
                     "nelutu-mouth","nelutu-smile","clop","pieptar"):
            self.assertIn(part,idle)
        for motion in ("nelutu-blink","nelutu-breathe","nelutu-look","nelutu-think",
                       "nelutu-talk","nelutu-nod"):
            self.assertIn("@keyframes "+motion,idle)
        self.assertIn("nelutu-answering .nelutu-mouth",answering)
        self.assertIn("nelutu-serious .nelutu-avatar",serious)
        self.assertIn("nelutu-serious-mouth",serious)
        self.assertIn("prefers-reduced-motion:reduce",idle)

    def test_unknown_state_falls_back_to_idle(self):
        html=render_nelutu_mascot("oare-ce-o-fi")
        self.assertIn("nelutu-idle",html)

    def test_corner_mascot_is_small_fixed_and_non_interactive(self):
        html=render_nelutu_corner("idle")
        self.assertIn("position:fixed",html)
        self.assertIn("right:18px",html)
        self.assertIn("bottom:18px",html)
        self.assertIn("pointer-events:none",html)
        self.assertIn("width:82px",html)
        self.assertIn("nelutu-bubble{display:none}",html)

    def test_idle_nudge_is_one_time_css_only(self):
        html=render_nelutu_corner_nudge()
        self.assertIn("No? Dacă vrei, te ajut io",html)
        self.assertIn("vin lupii",html)
        self.assertIn("animation:nelutu-nudge 18s",html)
        self.assertNotIn("<script",html.lower())
        self.assertNotIn("http://",html.lower())
        self.assertNotIn("https://",html.lower())

    def test_parent_portal_uses_small_click_assistant_not_giant_mascot(self):
        with open("app_parinti.py","r",encoding="utf-8") as handle:
            source=handle.read()
        self.assertIn('st.popover("🤠 Neluțu"',source)
        self.assertIn("întreabă-mă orișâce vrei tu... da’ nu pre mult, că mă ieftinesc",source)
        self.assertIn('st.toast("🤠 Servus!',source)
        self.assertNotIn('with st.expander("🤠 Neluțu — ajutorul simpatic din Portal"',source)
        self.assertNotIn('render_nelutu_mascot(_nelutu_state',source)

    def test_no_external_or_script_dependencies(self):
        html=render_nelutu_mascot()
        low=html.lower()
        self.assertNotIn("<script",low)
        self.assertNotIn("http://",low)
        self.assertNotIn("https://",low)

if __name__=="__main__":
    unittest.main()
