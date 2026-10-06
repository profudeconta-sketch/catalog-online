from pathlib import Path
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
    def test_ardelean_ai_brau_identity_is_local_and_repeated(self):
        html=render_nelutu_mascot()
        self.assertGreaterEqual(html.count("PRIMU’ AI DIN ARDEAL"),2)
        self.assertGreaterEqual(html.count("NELUȚU-AL NOST"),2)
        self.assertIn("nelutu-brau-title",html)
        self.assertIn("nelutu-brau-subtitle",html)
        self.assertIn('font-size="7.2"',html)
        self.assertNotIn("http://",html.lower())
        self.assertNotIn("https://",html.lower())
        self.assertNotIn("<script",html.lower())


    def test_corner_keeps_brau_above_streamlit_bottom_bar(self):
        html=render_nelutu_corner("idle")
        self.assertIn("bottom:82px",html)
        self.assertIn("width:112px;height:132px",html)
        self.assertIn("width:102px;height:116px",html)
        self.assertIn("bottom:70px",html)

    def test_parent_portal_shows_ardelean_identity_in_assistant_control(self):
        src=Path("app_parinti.py").read_text(encoding="utf-8")
        identity="🤠 Neluțu — PRIMU’ AI DIN ARDEAL • NELUȚU-AL NOST"
        self.assertGreaterEqual(src.count(identity),2)

    def test_parent_portal_invalidates_stale_nelutu_answer(self):
        with open("app_parinti.py", "r", encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn("def _nelutu_fresh_reply(", source)
        self.assertIn('"nelutu_answered_prompt"', source)
        self.assertIn('"nelutu_answered_reply"', source)
        self.assertNotIn('_nelutu_ask or _nelutu_topic != "— alege o temă —"', source)

    def test_fresh_reply_state_transitions(self):
        import ast
        with open("app_parinti.py", "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read())
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_nelutu_fresh_reply")
        module = ast.Module(body=[fn], type_ignores=[])
        ns = {}
        exec(compile(module, "app_parinti.py", "exec"), ns)
        fresh = ns["_nelutu_fresh_reply"]
        reply = object()
        self.assertEqual(fresh("A", reply, "A"), ("A", reply))
        self.assertEqual(fresh("A", reply, "B"), (None, None))
        self.assertEqual(fresh("A", reply, ""), (None, None))
        self.assertEqual(fresh(None, None, "B"), (None, None))

    def test_unknown_state_falls_back_to_idle(self):
        html=render_nelutu_mascot("oare-ce-o-fi")
        self.assertIn("nelutu-idle",html)

    def test_corner_mascot_is_small_fixed_and_non_interactive(self):
        html=render_nelutu_corner("idle")
        self.assertIn("position:fixed",html)
        self.assertIn("right:18px",html)
        self.assertIn("bottom:82px",html)
        self.assertIn("pointer-events:none",html)
        self.assertIn("width:82px",html)
        self.assertIn("nelutu-bubble{display:none}",html)

    def test_idle_nudge_is_one_time_css_only(self):
        html=render_nelutu_corner_nudge()
        for phrase in ("ce-ai găsit pe-acolo?","numa’ de curiozitate","zâ drept te ajută Neluțu",
                       "mai stăm aci mult sau merem",
                       "mă pui să mă culc","huțură-mă-ncet"):
            self.assertIn(phrase,html)
        self.assertIn("font-weight:800",html)
        self.assertIn("nelutu-curious-first 42s",html)
        self.assertIn("nelutu-curious-later 390s step-end 42s",html)
        self.assertIn("prefers-reduced-motion:reduce",html)
        self.assertNotIn("<script",html.lower())
        self.assertNotIn("http://",html.lower())
        self.assertNotIn("https://",html.lower())

    def test_idle_nudge_has_safe_contextual_repertoire(self):
        school=render_nelutu_corner_nudge("school")
        leave=render_nelutu_corner_nudge("leave")
        docs=render_nelutu_corner_nudge("documents")
        unknown=render_nelutu_corner_nudge("not-a-real-context")
        self.assertIn("cele de la școală",school)
        self.assertIn("învoiri",leave)
        self.assertIn("hârtiile-s multe",docs)
        self.assertIn("ce-ai găsit pe-acolo?",unknown)
        for html in (school,leave,docs,unknown):
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
