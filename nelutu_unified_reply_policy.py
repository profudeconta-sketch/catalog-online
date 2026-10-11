"""Read-only decision policy for upgrading the existing Neluțu.

Existing school/portal answers take priority. The external provider is optional,
never sees student context, and must not be invoked without explicit opt-in.
"""
from __future__ import annotations

from nelutu_free_dialogue_preparation import prepare_public_dialogue
from nelutu_system_tutorial_context import tutorial_context


def choose_reply_route(question, *, existing_intent=None, consent=False, history=()):
    """Return (route, guide) without network or state mutation.

    route: existing, tutorial, generative_eligible, local_only.
    Eligibility is not permission to transmit: a separate quota and provider
    enablement gate remain mandatory.
    """
    if not isinstance(question, str) or not question.strip():
        return "local_only", ""
    if existing_intent not in (None, "fallback", "clarification", "smalltalk", "smalltalk_followup"):
        return "existing", ""
    # A generic public question must never trigger tutorial retrieval by
    # coincidental shared words (e.g. 'unde pleaca soarele noaptea').
    from nelutu_gemini_optional import is_public_general_chat
    if is_public_general_chat(question):
        if prepare_public_dialogue(history, question, consent=consent) is not None:
            return "generative_eligible", ""
        return "local_only", ""
    guide = tutorial_context(question)
    if guide:
        return "tutorial", guide
    if prepare_public_dialogue(history, question, consent=consent) is not None:
        return "generative_eligible", ""
    return "local_only", ""
