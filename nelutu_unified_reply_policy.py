"""Read-only decision policy for upgrading the existing Neluțu.

Existing school/portal answers take priority. The external provider is optional,
never sees student context, and must not be invoked without explicit opt-in.
"""
from __future__ import annotations

from nelutu_free_dialogue_preparation import prepare_public_dialogue
from nelutu_system_tutorial_context import tutorial_context
from nelutu_local_dialogue import _norm


def choose_reply_route(question, *, existing_intent=None, consent=False, history=()):
    """Return (route, guide) without network or state mutation.

    route: existing, tutorial, generative_eligible, local_only.
    Eligibility is not permission to transmit: a separate quota and provider
    enablement gate remain mandatory.
    """
    if not isinstance(question, str) or not question.strip():
        return "local_only", ""
    # The lexical word "tehnic" is never a routing command. Public,
    # contextually general questions may use Gemini even if the local
    # educational router produced a generic educational answer.
    # Privacy/safety/portal and all other authoritative intents remain local.
    from nelutu_contextual_intent import classify_context
    from nelutu_gemini_optional import is_public_general_chat
    kind = classify_context(question)
    public = is_public_general_chat(question)
    non_authoritative = (
        existing_intent in (None, "fallback", "clarification", "smalltalk_followup")
        or (isinstance(existing_intent, str) and existing_intent.startswith(
            ("education_", "education_followup_")
        ))
    )
    if public and kind not in ("portal", "ambiguous") and non_authoritative:
        if prepare_public_dialogue(history, question, consent=consent) is not None:
            return "generative_eligible", ""
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
    from nelutu_contextual_intent import asks_about_portal
    guide = tutorial_context(question) if asks_about_portal(question) else ""
    if guide:
        return "tutorial", guide
    if prepare_public_dialogue(history, question, consent=consent) is not None:
        return "generative_eligible", ""
    return "local_only", ""
