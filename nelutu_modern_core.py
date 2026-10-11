"""Single experimental Neluțu entry point; no school application imports."""
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
           provider=None):
    current_state = state if isinstance(state, DialogueState) else DialogueState()
    local_answer, next_state = answer_parent_dialogue(
        question, context=context, state=current_state
    )
    public_only = context is None or context == {}
    final_answer, route = respond(
        question, local_answer,
        history=history if public_only else (),
        consent=consent if public_only else False,
        enabled=generative_enabled if public_only else False,
        budget_reserved=budget_reserved if public_only else False,
        provider=provider if public_only else None,
    )
    return ModernReply(final_answer, next_state, route)
