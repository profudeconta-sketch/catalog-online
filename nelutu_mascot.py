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
  <!-- chemeșă albă și laibăr negru cu broderie tricoloră -->
  <path d="M31 164 L34 128 Q40 113 55 109 L95 109 Q111 113 117 128 L120 164Z" fill="#171513" stroke="#080706" stroke-width="3"/>
  <path d="M54 113 Q75 121 96 113 L101 164 L49 164Z" fill="#fffdf6" stroke="#5c4436" stroke-width="2"/>
  <path d="M55 124 L48 155 M95 124 L102 155" fill="none" stroke="#174b9a" stroke-width="5"/>
  <path d="M57 124 L50 155 M93 124 L100 155" fill="none" stroke="#f2cf35" stroke-width="3"/>
  <path d="M59 124 L52 155 M91 124 L98 155" fill="none" stroke="#c73532" stroke-width="2"/>
  <path d="M66 118 l4 4 -4 4 4 4 -4 4 M84 118 l-4 4 4 4 -4 4 4 4" fill="none" stroke="#174b9a" stroke-width="1.8"/>
  <path d="M68 118 l4 4 -4 4 4 4 -4 4 M82 118 l-4 4 4 4 -4 4 4 4" fill="none" stroke="#f2cf35" stroke-width="1.5"/>
  <path d="M70 118 l4 4 -4 4 4 4 -4 4 M80 118 l-4 4 4 4 -4 4 4 4" fill="none" stroke="#c73532" stroke-width="1.2"/>
  <!-- cocardă tricoloră cu medalion stilizat Avram Iancu -->
  <circle cx="104" cy="121" r="9" fill="#174b9a" stroke="#f6f0df" stroke-width="1"/>
  <circle cx="104" cy="121" r="6.5" fill="#f2cf35"/>
  <circle cx="104" cy="121" r="4.3" fill="#c73532"/>
  <circle cx="104" cy="121" r="3.1" fill="#e8c39e" stroke="#4b3427" stroke-width=".6"/>
  <path d="M101 120 Q104 116 107 120 M102 123 Q104 125 106 123" fill="none" stroke="#4b3427" stroke-width=".7" stroke-linecap="round"/>
  <path d="M100 116 Q104 113 108 116" fill="none" stroke="#3c2a20" stroke-width="1.2"/>
  <path class="nelutu-brau" d="M18 131 Q75 143 132 131 L136 164 Q75 177 14 164Z" fill="#8a2f2a" stroke="#3a241d" stroke-width="2"/>
  <text class="nelutu-brau-title" x="75" y="146" text-anchor="middle" font-size="8.4" font-weight="900" fill="#fff8df">PRIMU’ AI DIN ARDEAL</text>
  <text class="nelutu-brau-subtitle" x="75" y="157" text-anchor="middle" font-size="7.0" font-weight="900" fill="#fff8df">NELUȚU-AL NOST 🤠</text>
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
  <!-- clop de paie galben -->
  <path d="M35 35 Q38 7 75 5 Q112 7 115 35 Q93 30 75 31 Q57 30 35 35Z" fill="#e6bd55" stroke="#765c24" stroke-width="3"/>
  <path d="M20 36 Q75 28 130 36 Q124 44 75 43 Q26 44 20 36Z" fill="#f0cd69" stroke="#765c24" stroke-width="2"/>
  <path d="M42 27 Q75 17 108 27 M38 33 Q75 23 112 33" fill="none" stroke="#b88b34" stroke-width="1" opacity=".8"/>
  <path d="M48 10 L44 32 M61 7 L59 30 M75 5 L75 30 M89 7 L91 30 M102 11 L106 32" stroke="#c89c3d" stroke-width=".8" opacity=".8"/>
  <path d="M38 29 Q75 23 112 29" fill="none" stroke="#174b9a" stroke-width="2"/>
  <path d="M38 31 Q75 25 112 31" fill="none" stroke="#f2cf35" stroke-width="2"/>
  <path d="M38 33 Q75 27 112 33" fill="none" stroke="#c73532" stroke-width="2"/>
 </g>
</svg>
<div class="nelutu-bubble"><strong>Neluțu</strong>{msg}</div></div>"""


def render_nelutu_corner_nudge(context:str="general") -> str:
    """Intervenții rare, locale și contextuale doar pe stări demonstrate de aplicație."""
    safe_context=context if context in {"general","school","leave","documents"} else "general"
    first={
        "general":"No, ce-ai găsit pe-acolo? Dacă-i bai, zi-i lu’ Neluțu. Dacă nu-i bai, putem scormoni numa’ de curiozitate. 🤠",
        "school":"No, dacă te uiți prin cele de la școală și ceva nu-i limpede, strigă-mă. Io nu fug nicăieri. 🤠",
        "leave":"No, la învoiri îi bine să citim tăt, nu numa’ ce ne place. Dacă-i bai, îs p-aci. 🤠",
        "documents":"No, hârtiile-s multe, Neluțu-i unu’. Dacă nu găsești ce cauți, mă întrebi. 🤠",
    }[safe_context]
    second={
        "general":"No,... zâ drept te ajută Neluțu! Da’ stai liniștit, nu te bat la cap.",
        "school":"Aha no, școala are multe rânduri. Dacă vrei, ți le descurc io pe românește.",
        "leave":"No, cu învoirea nu ne grăbim ca la autobuz. Întreabă-mă dacă ceva nu-i clar.",
        "documents":"No, dacă te-o prins dosaru’ între hârtii, fluieră după mine. Da’ numa’ dacă ai nevoie.",
    }[safe_context]
    return f"""<style>
.nelutu-corner .nelutu-wrap::before,.nelutu-corner .nelutu-wrap::after{{position:absolute;right:86px;bottom:50px;width:min(390px,72vw);padding:13px 15px;border:2px solid #b98b45;border-radius:16px;background:#fffaf0;color:#241d17;font-size:1rem;font-weight:800;line-height:1.35;box-shadow:0 7px 22px rgba(55,38,20,.20);opacity:0;visibility:hidden}}
.nelutu-corner .nelutu-wrap::before{{content:"{first}";animation:nelutu-curious-first 42s ease 1 forwards}}
.nelutu-corner .nelutu-wrap::after{{content:"";animation:nelutu-curious-later 390s step-end 42s 1 forwards}}
@keyframes nelutu-curious-first{{0%,70%{{opacity:0;visibility:hidden;transform:translateY(5px)}}72%,94%{{opacity:1;visibility:visible;transform:translateY(0)}}100%{{opacity:0;visibility:hidden}}}}
@keyframes nelutu-curious-later{{
0%,11%{{content:"";opacity:0;visibility:hidden}}
12%,15%{{content:"{second}";opacity:1;visibility:visible}}
16%,41%{{content:"";opacity:0;visibility:hidden}}
42%,45%{{content:"No? mai stăm aci mult sau merem...";opacity:1;visibility:visible}}
46%,71%{{content:"";opacity:0;visibility:hidden}}
72%,75%{{content:"No, io-s p-aci. Numa’ zic, să nu crezi că m-o luat somnu’. 🤠";opacity:1;visibility:visible}}
76%,98%{{content:"";opacity:0;visibility:hidden}}
99%,100%{{content:"No! Io mă pui să mă culc ș-apăi mă huțuri tu când să mă scol... numa vezi... huțură-mă-ncet că io când mă scol, mă sâ ridic...";opacity:1;visibility:visible}}
}}
@media(max-width:640px){{.nelutu-corner .nelutu-wrap::before,.nelutu-corner .nelutu-wrap::after{{right:64px;bottom:38px;width:min(285px,70vw);font-size:.86rem;max-height:34vh;overflow:auto}}}}
@media(prefers-reduced-motion:reduce){{.nelutu-corner .nelutu-wrap::before,.nelutu-corner .nelutu-wrap::after{{animation:none;display:none}}}}
</style>"""

def visual_contract()->dict:
    return {"writes_data":False,"uses_network":False,"uses_javascript":False,"external_assets":False,"reusable_system_component":True}


def render_nelutu_corner(state:str="idle") -> str:
    """Mascota mică, persistentă vizual în colț; fără date, JS sau acțiuni."""
    mascot=render_nelutu_mascot(state,"")
    return f"""<div class="nelutu-corner"><div class="nelutu-corner-brau"><b>📖 NELUȚU — GHIDUL ÎNTREGULUI SISTEM INFORMATIC</b><span>Apasă aici pentru tutorialul complet, cap-coadă 🤠</span></div>{mascot}</div>
<style>
.nelutu-corner .nelutu-corner-brau{{position:fixed;left:0;right:0;top:0;z-index:10020;min-height:44px;padding:5px 150px 5px 12px;border-bottom:2px solid #3a241d;background:#8a2f2a;color:#fff8df;text-align:center;box-shadow:0 3px 12px rgba(55,38,20,.18);pointer-events:none;font-size:12px;font-weight:900;line-height:1.12}}
.nelutu-corner .nelutu-corner-brau span{{display:block;font-size:9px;margin-top:2px}}
.nelutu-corner .nelutu-bottom-brau{{position:fixed;left:0;right:0;bottom:0;z-index:10020;min-height:38px;padding:9px 145px 7px 12px;border-top:2px solid #3a241d;background:#8a2f2a;color:#fff8df;text-align:center;box-shadow:0 -3px 12px rgba(55,38,20,.18);pointer-events:none;font-size:11px;font-weight:900;line-height:1.12}}
.nelutu-corner .nelutu-wrap{{position:fixed;right:24px;bottom:42px;z-index:10020;width:112px;height:132px;padding:7px;display:block;border-radius:22px;background:rgba(255,250,240,.96);box-shadow:0 8px 26px rgba(55,38,20,.22);overflow:visible;pointer-events:none}}
.nelutu-corner .nelutu-brau,.nelutu-corner .nelutu-brau-title,.nelutu-corner .nelutu-brau-subtitle{{display:none}}
.nelutu-corner .nelutu-avatar{{width:102px;height:116px;display:block;margin:auto}}
.nelutu-corner .nelutu-avatar{{animation:nelutu-corner-dance 5.8s ease-in-out 1,nelutu-breathe 3s ease-in-out 5.8s infinite}}
@keyframes nelutu-corner-dance{{0%,100%{{transform:translateY(0) rotate(0)}}12%{{transform:translateY(-5px) rotate(-4deg)}}24%{{transform:translateY(0) rotate(4deg)}}36%{{transform:translateY(-4px) rotate(-3deg)}}48%{{transform:translateY(0) rotate(3deg)}}60%{{transform:translateY(-3px) rotate(-2deg)}}72%{{transform:translateY(0) rotate(2deg)}}84%{{transform:translateY(-2px) rotate(-1deg)}}}}
.nelutu-corner .nelutu-bubble{{display:none}}
@media(max-width:640px){{.nelutu-corner .nelutu-corner-brau{{left:0;right:0;top:0;min-height:40px;padding:5px 100px 5px 8px;font-size:9px}}.nelutu-corner .nelutu-bottom-brau{{left:0;right:0;bottom:0;min-height:34px;padding:8px 100px 6px 8px;font-size:9px}}.nelutu-corner .nelutu-wrap{{right:12px;bottom:38px;width:88px;height:104px;padding:5px}}.nelutu-corner .nelutu-avatar{{width:78px;height:90px}}}}
</style>"""
