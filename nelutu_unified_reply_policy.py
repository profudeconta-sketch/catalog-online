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
    # A public follow-up must remain with the generative conversation instead
    # of being hijacked by an unrelated legacy/local educational reply.
    # Never bypass serious, privacy, school or portal intents.
    followup = _norm(question)
    public_followup = bool(history) and (
        followup in ("continua", "continuam", "da", "sigur", "mai mult", "detaliaza")
        or followup.startswith(("da din punct de vedere", "din punct de vedere tehnic",
                              "vreau mai multe", "poti continua", "explica mai mult"))
    )
    from nelutu_contextual_intent import classify_context
    if public_followup and classify_context(question) not in ("portal", "ambiguous"):
        if existing_intent in (None, "fallback", "clarification", "smalltalk_followup") and (
            prepare_public_dialogue(history, question, consent=consent) is not None
        ):
            return "generative_eligible", ""
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
