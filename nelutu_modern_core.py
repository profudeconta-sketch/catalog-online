"""Single modern Neluțu entry point for the existing portal.

School facts and protected local answers remain authoritative. Generative
calls are optional and forbidden for authenticated school context.
"""
from dataclasses import dataclass
from nelutu_dialogue_adapter import answer_parent_dialogue
from nelutu_local_dialogue import DialogueState

@dataclass(frozen=True)
class ModernReply:
    answer: object
    state: DialogueState
    route: str

def answer(question, *, context=None, state=None, history=(),
           consent=False, generative_enabled=False, budget_reserved=False,
           provider=None):
    local, next_state = answer_parent_dialogue(
        question, context=context,
        state=state if isinstance(state, DialogueState) else DialogueState()
    )
    # No outbound data in authenticated parent sessions. Provider integration
    # must be independently reviewed before any external call is enabled.
    return ModernReply(local, next_state, "local")
