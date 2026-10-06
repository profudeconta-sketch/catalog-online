"""Neluțu — mascotă cartoon locală, animată, reutilizabilă și fără efecte secundare."""
from __future__ import annotations
from html import escape

_ALLOWED_STATES={"idle","thinking","answering","serious","success"}

def render_nelutu_mascot(state:str="idle",message:str="Servus! Eu-s Neluțu.") -> str:
    """Returnează HTML/CSS/SVG autonom. Nu citește/scrie date, nu execută JS."""
    state=state if state in _ALLOWED_STATES else "idle"
    msg=escape(str(message or "Servus! Eu-s Neluțu."))
    return f"""<div class="nelutu-wrap nelutu-{state}" role="img" aria-label="Neluțu, mascota sistemului">
<style>
.nelutu-wrap{{display:flex;align-items:center;gap:22px;padding:18px 22px;border:1px solid #dfc28d;border-radius:24px;background:linear-gradient(135deg,#fffaf0,#f5ead5);box-shadow:0 8px 28px rgba(80,58,25,.10);overflow:hidden}}
.nelutu-avatar{{width:142px;height:154px;flex:0 0 142px;filter:drop-shadow(0 5px 4px rgba(70,45,25,.16));animation:nelutu-breathe 3s ease-in-out infinite;transform-origin:50% 95%}}
.nelutu-svg{{width:100%;height:100%;overflow:visible}}
.nelutu-eye{{transform-box:fill-box;transform-origin:center;animation:nelutu-blink 4.7s infinite}}
.nelutu-pupil{{animation:nelutu-look 6s ease-in-out infinite}}
.nelutu-mouth{{transform-box:fill-box;transform-origin:center}}
.nelutu-thinking .nelutu-avatar{{animation:nelutu-think 1.15s ease-in-out infinite}}
.nelutu-thinking .nelutu-pupil{{animation:nelutu-look-think 1.15s ease-in-out infinite}}
.nelutu-answering .nelutu-mouth{{animation:nelutu-talk .42s ease-in-out infinite}}
.nelutu-success .nelutu-avatar{{animation:nelutu-nod .72s ease-in-out 2}}
.nelutu-success .nelutu-cheek{{opacity:.9}}
.nelutu-serious{{background:linear-gradient(135deg,#fff9f0,#eee8df);border-color:#b9a78c}}
.nelutu-serious .nelutu-avatar,.nelutu-serious .nelutu-eye,.nelutu-serious .nelutu-pupil{{animation:none}}
.nelutu-serious .nelutu-smile{{display:none}} .nelutu-serious .nelutu-serious-mouth{{display:block}}
.nelutu-serious .nelutu-brow-l{{transform:rotate(8deg);transform-origin:center}} .nelutu-serious .nelutu-brow-r{{transform:rotate(-8deg);transform-origin:center}}
.nelutu-serious-mouth{{display:none}}
.nelutu-bubble{{font-size:1.02rem;line-height:1.48;max-width:760px;color:#2e2925}}
.nelutu-bubble strong{{display:block;font-size:1.18rem;margin-bottom:4px;color:#29231f}}
@keyframes nelutu-breathe{{0%,100%{{transform:translateY(0) rotate(0)}}50%{{transform:translateY(-4px) rotate(.5deg)}}}}
@keyframes nelutu-blink{{0%,45%,49%,100%{{transform:scaleY(1)}}47%{{transform:scaleY(.08)}}}}
@keyframes nelutu-look{{0%,30%,100%{{transform:translateX(0)}}42%,58%{{transform:translateX(2px)}}70%,82%{{transform:translateX(-1.5px)}}}}
@keyframes nelutu-look-think{{0%,100%{{transform:translate(0,0)}}50%{{transform:translate(2px,-2px)}}}}
@keyframes nelutu-think{{0%,100%{{transform:rotate(-2deg) translateY(0)}}50%{{transform:rotate(3deg) translateY(-3px)}}}}
@keyframes nelutu-talk{{0%,100%{{transform:scaleY(.55)}}50%{{transform:scaleY(1.18)}}}}
@keyframes nelutu-nod{{0%,100%{{transform:rotate(0)}}50%{{transform:rotate(4deg) translateY(4px)}}}}
@media(max-width:640px){{.nelutu-wrap{{gap:12px;padding:14px}}.nelutu-avatar{{width:112px;height:125px;flex-basis:112px}}}}
@media(prefers-reduced-motion:reduce){{.nelutu-wrap *{{animation:none!important}}}}
</style>
<svg class="nelutu-avatar nelutu-svg" viewBox="0 0 150 165" aria-hidden="true">
 <g>
  <!-- pieptar și cămașă -->
  <path d="M31 164 L34 128 Q40 113 55 109 L95 109 Q111 113 117 128 L120 164Z" fill="#49352b" stroke="#2f211c" stroke-width="3"/>
  <path d="M54 113 Q75 121 96 113 L101 164 L49 164Z" fill="#fffaf0" stroke="#5c4436" stroke-width="2"/>
  <path d="M55 124 L48 155 M95 124 L102 155" stroke="#b23a32" stroke-width="3"/>
  <path class="nelutu-brau" d="M35 137 Q75 145 115 137 L117 160 Q75 168 33 160Z" fill="#8a2f2a" stroke="#3a241d" stroke-width="2"/>
  <text class="nelutu-brau-title" x="75" y="148" text-anchor="middle" font-size="7.2" font-weight="900" fill="#fff8df">PRIMU’ AI</text>
  <text class="nelutu-brau-subtitle" x="75" y="156.5" text-anchor="middle" font-size="5.8" font-weight="900" fill="#fff8df">DIN ARDEAL</text>
  <title>PRIMU’ AI DIN ARDEAL • NELUȚU-AL NOST • PRIMU’ AI DIN ARDEAL • NELUȚU-AL NOST</title>

  <path d="M66 122 l5 5 -5 5 5 5 -5 5 M84 122 l-5 5 5 5 -5 5 5 5" fill="none" stroke="#b23a32" stroke-width="2"/>
  <!-- urechi -->
  <ellipse cx="35" cy="74" rx="10" ry="15" fill="#efbd94" stroke="#664634" stroke-width="2.5"/>
  <ellipse cx="115" cy="74" rx="10" ry="15" fill="#efbd94" stroke="#664634" stroke-width="2.5"/>
  <!-- cap + păr -->
  <ellipse cx="75" cy="72" rx="42" ry="48" fill="#f2c49d" stroke="#5b3d2d" stroke-width="3"/>
  <path d="M39 54 Q45 26 75 25 Q105 26 111 54 Q98 43 88 45 Q73 35 61 45 Q50 43 39 54Z" fill="#5a3827"/>
  <!-- sprâncene -->
  <path class="nelutu-brow-l" d="M48 58 Q57 52 65 57" fill="none" stroke="#513326" stroke-width="4" stroke-linecap="round"/>
  <path class="nelutu-brow-r" d="M85 57 Q94 52 102 58" fill="none" stroke="#513326" stroke-width="4" stroke-linecap="round"/>
  <!-- ochi -->
  <g class="nelutu-eye"><ellipse cx="57" cy="68" rx="10" ry="11" fill="white" stroke="#51382b" stroke-width="2"/><circle class="nelutu-pupil" cx="58" cy="69" r="5" fill="#563b2d"/><circle cx="60" cy="66" r="1.7" fill="white"/></g>
  <g class="nelutu-eye"><ellipse cx="93" cy="68" rx="10" ry="11" fill="white" stroke="#51382b" stroke-width="2"/><circle class="nelutu-pupil" cx="92" cy="69" r="5" fill="#563b2d"/><circle cx="94" cy="66" r="1.7" fill="white"/></g>
  <!-- nas + obraji -->
  <path d="M75 70 Q70 82 76 84 Q81 84 82 81" fill="none" stroke="#b5765b" stroke-width="2.5" stroke-linecap="round"/>
  <ellipse class="nelutu-cheek" cx="48" cy="87" rx="9" ry="5" fill="#df8378" opacity=".38"/><ellipse class="nelutu-cheek" cx="102" cy="87" rx="9" ry="5" fill="#df8378" opacity=".38"/>
  <!-- barbă/mustață discretă -->
  <path d="M62 91 Q68 87 75 92 Q82 87 88 91" fill="none" stroke="#704735" stroke-width="2.3" stroke-linecap="round"/>
  <path d="M58 99 Q75 112 92 99" fill="none" stroke="#8a5a43" stroke-width="1.5" opacity=".55"/>
  <!-- gură -->
  <g class="nelutu-mouth"><path class="nelutu-smile" d="M65 96 Q75 105 86 96 Q83 108 75 109 Q67 108 65 96Z" fill="#8e4545" stroke="#6f3735" stroke-width="1.5"/><path class="nelutu-serious-mouth" d="M66 101 Q75 98 85 101" fill="none" stroke="#713b35" stroke-width="3" stroke-linecap="round"/></g>
  <!-- clop -->
  <path d="M35 35 Q38 7 75 5 Q112 7 115 35 Q93 30 75 31 Q57 30 35 35Z" fill="#58402d" stroke="#302219" stroke-width="3"/>
  <path d="M20 36 Q75 28 130 36 Q124 44 75 43 Q26 44 20 36Z" fill="#3d2c21" stroke="#2b1f18" stroke-width="2"/>
  <path d="M104 18 Q114 5 118 0" fill="none" stroke="#4f743e" stroke-width="4" stroke-linecap="round"/>
  <circle cx="113" cy="9" r="4" fill="#c9473e"/>
 </g>
</svg>
<div class="nelutu-bubble"><strong>Neluțu</strong>{msg}</div></div>"""


def render_nelutu_corner_nudge() -> str:
    """Curiozitate vizuală rară, CSS-only; prezentă fără a deveni cicălitoare."""
    return """<style>
.nelutu-corner .nelutu-wrap::before,.nelutu-corner .nelutu-wrap::after{position:absolute;right:86px;bottom:50px;width:min(390px,72vw);padding:13px 15px;border:2px solid #b98b45;border-radius:16px;background:#fffaf0;color:#241d17;font-size:1rem;font-weight:800;line-height:1.35;box-shadow:0 7px 22px rgba(55,38,20,.20);opacity:0;visibility:hidden}
.nelutu-corner .nelutu-wrap::before{content:"No, ce-ai găsit pe-acolo? Dacă-i bai, zi-i lu’ Neluțu. Dacă nu-i bai, putem scormoni numa’ de curiozitate. 🤠";animation:nelutu-curious-first 42s ease 1 forwards}
.nelutu-corner .nelutu-wrap::after{content:"";animation:nelutu-curious-later 390s step-end 42s 1 forwards}
@keyframes nelutu-curious-first{0%,70%{opacity:0;visibility:hidden;transform:translateY(5px)}72%,94%{opacity:1;visibility:visible;transform:translateY(0)}100%{opacity:0;visibility:hidden}}
@keyframes nelutu-curious-later{
0%,11%{content:"";opacity:0;visibility:hidden}
12%,15%{content:"No,... zâ drept te ajută Neluțu! zâ nu-ț șie rusâne? că de nu api mai binie merem acasă, că vin lupii șâ tăt ne rup!";opacity:1;visibility:visible}
16%,41%{content:"";opacity:0;visibility:hidden}
42%,45%{content:"No? mai stăm aci mult sau merem...";opacity:1;visibility:visible}
46%,71%{content:"";opacity:0;visibility:hidden}
72%,75%{content:"No? mai stăm aci mult sau merem...";opacity:1;visibility:visible}
76%,98%{content:"";opacity:0;visibility:hidden}
99%,100%{content:"No! Io mă pui să mă culc ș-apăi mă huțuri tu când să mă scol... numa vezi... huțură-mă-ncet că io când mă scol, mă sâ ridic...";opacity:1;visibility:visible}
}
@media(max-width:640px){.nelutu-corner .nelutu-wrap::before,.nelutu-corner .nelutu-wrap::after{right:64px;bottom:38px;width:min(285px,70vw);font-size:.86rem;max-height:34vh;overflow:auto}}
@media(prefers-reduced-motion:reduce){.nelutu-corner .nelutu-wrap::before,.nelutu-corner .nelutu-wrap::after{animation:none;display:none}}
</style>"""

def visual_contract()->dict:
    return {"writes_data":False,"uses_network":False,"uses_javascript":False,"external_assets":False,"reusable_system_component":True}


def render_nelutu_corner(state:str="idle") -> str:
    """Mascota mică, persistentă vizual în colț; fără date, JS sau acțiuni."""
    mascot=render_nelutu_mascot(state,"")
    return f"""<div class="nelutu-corner">{mascot}</div>
<style>
.nelutu-corner .nelutu-wrap{{position:fixed;right:18px;bottom:18px;z-index:9999;width:92px;height:104px;padding:7px;display:block;border-radius:22px;background:rgba(255,250,240,.96);box-shadow:0 8px 26px rgba(55,38,20,.22);overflow:visible;pointer-events:none}}
.nelutu-corner .nelutu-avatar{{width:82px;height:92px;display:block;margin:auto}}
.nelutu-corner .nelutu-bubble{{display:none}}
@media(max-width:640px){{.nelutu-corner .nelutu-wrap{{right:9px;bottom:9px;width:70px;height:80px;padding:5px}}.nelutu-corner .nelutu-avatar{{width:62px;height:70px}}}}
</style>"""
