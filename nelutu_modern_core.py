"""Unified modern Neluțu: local school authority + optional safe Gemini."""
from dataclasses import dataclass
from nelutu_dialogue_adapter import answer_parent_dialogue
from nelutu_local_dialogue import DialogueState
from nelutu_unified_orchestrator import respond

@dataclass(frozen=True)
class ModernReply:
    answer: object
    state: DialogueState
    route: str

def answer(question, *, context=None, state=None, history=(),
           consent=False, generative_enabled=False, budget_reserved=False,
           provider=None, mode="portal"):
    local, next_state = answer_parent_dialogue(
        question, context=context,
        state=state if isinstance(state, DialogueState) else DialogueState()
    )
    # No authenticated portal context or school data is passed to Gemini.
    # Only public question text; history deliberately suppressed in production.
    final, route = respond(
        question, local, history=history, consent=consent,
        enabled=generative_enabled, budget_reserved=budget_reserved,
        provider=provider, mode=mode,
    )
    return ModernReply(final, next_state, route)
