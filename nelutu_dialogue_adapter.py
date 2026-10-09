"""Adaptor experimental pentru integrare ulterioară; nu modifică portalul activ."""
from __future__ import annotations
import re
from nelutu_parent_guide import answer_parent
from nelutu_local_dialogue import DialogueState, reply as local_reply, _norm
from nelutu_education_dialogue import educational_reply

def answer_parent_dialogue(question, context=None, state=None):
    """Prioritizează întotdeauna routerul portalului; continuitatea este limitată."""
    state = state if isinstance(state, DialogueState) else DialogueState()
    # Filtrul de risc al dialogului nou se execută înainte de rutarea portalului.
    # Niciun răspuns neserios al routerului vechi nu poate masca o alertă detectată.
    safety, _ = local_reply(question, DialogueState())
    if safety is not None and safety.serious:
        return safety, DialogueState()
    # Limita de lungime nu poate fi ocolită de un intent al portalului.
    if isinstance(question, str) and len(question) > 1200:
        return safety, DialogueState()
    base = answer_parent(question, context)
    # Privacy-sensitive requests require a dedicated pre-routing guard.

    # Întrebările educaționale explicite pot fi mascate de clasificarea
    # prea largă «portal_component». Nu schimbăm însă ghidurile portalului.
    if base.intent == "portal_component":
        educational = educational_reply(question)
        portal_terms = ("portal", "aplicatie", "buton", "document", "nota", "note",
                        "absente", "invoire", "scutire", "mesaj", "notificare",
                        "catalog", "trimite", "incarc", "cont", "parola")
        normalized = _norm(question)
        if educational is not None and not any(
            re.search(r"(?<![a-z0-9])" + re.escape(t) + r"(?![a-z0-9])", normalized)
            for t in portal_terms
        ):
            return educational, DialogueState(educational.intent.removeprefix("education_"), 1)
    # Orice răspuns de siguranță, portal, legal sau bazat pe date rămâne autoritar.
    if base.serious or base.intent not in ("fallback", "clarification"):
        # Un subiect educațional explicit poate actualiza tema, fără a înlocui
        # răspunsul deja stabilit de routerul principal.
        if base.intent.startswith("education_"):
            return base, DialogueState(base.intent.removeprefix("education_"), 1)
        return base, DialogueState()
    local, next_state = local_reply(question, state)
    if local is not None:
        return local, next_state
    return base, DialogueState()
