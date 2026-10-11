"""Offline orchestration for the existing Neluțu; no network or data writes.

The caller supplies the established local answer and, optionally, a provider
callback. The provider is never invoked without an explicitly reserved budget.
"""
from __future__ import annotations
from nelutu_unified_reply_policy import choose_reply_route


def respond(question, existing_answer, *, history=(), consent=False,
            enabled=False, budget_reserved=False, provider=None):
    """Return (answer, route). The existing assistant remains authoritative."""
    intent = getattr(existing_answer, "intent", None)
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
    return existing_answer, "existing"
