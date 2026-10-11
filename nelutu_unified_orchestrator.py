"""Offline orchestration for the existing Neluțu; no network or data writes.

The caller supplies the established local answer and, optionally, a provider
callback. The provider is never invoked without an explicitly reserved budget.
"""
from __future__ import annotations
from nelutu_unified_reply_policy import choose_reply_route


def respond(question, existing_answer, *, history=(), consent=False,
            enabled=False, budget_reserved=False, provider=None, mode="auto"):
    """Return (answer, route). The existing assistant remains authoritative."""
    intent = getattr(existing_answer, "intent", None)
    # The selected mode is authoritative only for public, non-portal questions.
    # Safety, privacy and school operations keep their existing local routing.
    from nelutu_gemini_optional import is_public_general_chat
    from nelutu_contextual_intent import classify_context
    protected = bool(getattr(existing_answer, "serious", False)) or (
        isinstance(intent, str) and (
            intent.startswith(("privacy", "credential", "access_", "authority",
                               "parent_", "portal_", "system_", "sensitive"))
        )
    )
    if mode == "portal":
        return existing_answer, "existing"
    if (mode == "chat" and not protected
            and is_public_general_chat(question)
            and classify_context(question) not in ("portal", "ambiguous")):
        intent = "fallback"
    route, guide = choose_reply_route(
        question, existing_intent=intent, consent=consent, history=history
    )
    if route == "tutorial":
        from nelutu_assistant import NelutuAnswer
        return NelutuAnswer("system_tutorial", "No, potrivit ghidului sistemului:\n\n" + guide), route
    if (route == "generative_eligible" and enabled is True
            and budget_reserved is True and callable(provider)):
        try:
            response = provider(history, question)
            if isinstance(response, str) and response.strip():
                from nelutu_assistant import NelutuAnswer
                return NelutuAnswer("generative", response.strip()[:1500]), "generative"
        except Exception:
            pass
    if mode == "chat" and not protected:
        from nelutu_assistant import NelutuAnswer
        return NelutuAnswer("chat_unavailable", "No, momentan nu pot continua discutia libera. Mai incearca putin mai tarziu. 🤠"), "local_only"
    return existing_answer, "existing"
