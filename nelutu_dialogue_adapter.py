"""Adaptor experimental pentru integrare ulterioară; nu modifică portalul activ."""
from __future__ import annotations
from nelutu_parent_guide import answer_parent
from nelutu_local_dialogue import DialogueState, reply as local_reply, _norm, _FOLLOWUP_MARKERS

def answer_parent_dialogue(question, context=None, state=None):
    """Prioritizează întotdeauna routerul portalului; continuitatea este limitată."""
    state = state if isinstance(state, DialogueState) else DialogueState()
    base = answer_parent(question, context)
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
