"""Neluțu — componentă vizuală locală, reutilizabilă și fără efecte secundare."""
from __future__ import annotations
from html import escape

_ALLOWED_STATES={"idle","thinking","answering","serious","success"}

def render_nelutu_mascot(state:str="idle",message:str="Servus! Eu-s Neluțu.") -> str:
    """Returnează HTML/CSS autonom. Nu citește și nu scrie date; nu execută JS."""
    state=state if state in _ALLOWED_STATES else "idle"
    msg=escape(str(message or "Servus! Eu-s Neluțu."))
    serious=state=="serious"
    eyes="• •" if not serious else "• •"
    mouth="⌣" if not serious else "—"
    return f"""<div class="nelutu-wrap nelutu-{state}" role="img" aria-label="Neluțu, mascota sistemului">
<style>
.nelutu-wrap{{display:flex;align-items:center;gap:18px;padding:18px 20px;border:1px solid #d7c29a;border-radius:22px;background:linear-gradient(135deg,#fff9eb,#f3ead7);box-shadow:0 8px 28px rgba(80,58,25,.10);overflow:hidden}}
.nelutu-avatar{{position:relative;width:112px;height:132px;flex:0 0 112px;animation:nelutu-breathe 3.2s ease-in-out infinite;transform-origin:50% 100%}}
.nelutu-hat{{position:absolute;left:15px;top:0;width:82px;height:28px;background:#4d3928;border-radius:50% 50% 18% 18%;transform:rotate(-4deg)}}
.nelutu-hat:after{{content:"";position:absolute;left:-11px;top:21px;width:103px;height:10px;background:#3d2d21;border-radius:50%}}
.nelutu-head{{position:absolute;left:25px;top:30px;width:65px;height:67px;background:#f1c69f;border-radius:48% 48% 46% 46%;border:2px solid #5d4432}}
.nelutu-eyes{{position:absolute;left:13px;top:20px;width:39px;text-align:center;font-weight:900;letter-spacing:9px;animation:nelutu-blink 5s infinite}}
.nelutu-mouth{{position:absolute;left:23px;top:40px;font-size:25px;font-weight:800}}
.nelutu-body{{position:absolute;left:17px;top:92px;width:82px;height:40px;background:#3f332c;border-radius:18px 18px 8px 8px;border:2px solid #2d241f}}
.nelutu-shirt{{position:absolute;left:31px;top:94px;width:52px;height:38px;background:#fffaf0;border-radius:13px 13px 5px 5px}}
.nelutu-shirt:after{{content:"◆ ◆ ◆";position:absolute;top:7px;left:6px;font-size:9px;color:#7b3028;letter-spacing:2px}}
.nelutu-bubble{{font-size:1.02rem;line-height:1.45;max-width:720px}}
.nelutu-bubble strong{{display:block;font-size:1.15rem;margin-bottom:3px}}
.nelutu-thinking .nelutu-avatar{{animation:nelutu-think 1.05s ease-in-out infinite}}
.nelutu-answering .nelutu-mouth{{animation:nelutu-talk .55s ease-in-out infinite}}
.nelutu-success .nelutu-avatar{{animation:nelutu-nod .8s ease-in-out 2}}
.nelutu-serious{{background:linear-gradient(135deg,#fff8ed,#f1ece4);border-color:#b8a58a}}
.nelutu-serious .nelutu-avatar{{animation:none}}
@keyframes nelutu-breathe{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(-3px)}}}}
@keyframes nelutu-blink{{0%,46%,50%,100%{{transform:scaleY(1)}}48%{{transform:scaleY(.08)}}}}
@keyframes nelutu-think{{0%,100%{{transform:rotate(-2deg)}}50%{{transform:rotate(3deg) translateY(-2px)}}}}
@keyframes nelutu-talk{{0%,100%{{transform:scaleY(.7)}}50%{{transform:scaleY(1.15)}}}}
@keyframes nelutu-nod{{0%,100%{{transform:rotate(0)}}50%{{transform:rotate(5deg) translateY(3px)}}}}
@media (prefers-reduced-motion:reduce){{.nelutu-wrap *{{animation:none!important}}}}
</style>
<div class="nelutu-avatar" aria-hidden="true"><div class="nelutu-hat"></div><div class="nelutu-head"><div class="nelutu-eyes">{eyes}</div><div class="nelutu-mouth">{mouth}</div></div><div class="nelutu-body"></div><div class="nelutu-shirt"></div></div>
<div class="nelutu-bubble"><strong>Neluțu</strong>{msg}</div></div>"""

def visual_contract()->dict:
    return {"writes_data":False,"uses_network":False,"uses_javascript":False,"external_assets":False,"reusable_system_component":True}
