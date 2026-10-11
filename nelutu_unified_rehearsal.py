"""Unified Neluțu end-to-end rehearsal, isolated from school applications.

Uses the real local adapter, routing policy and orchestrator. The provider is a
deterministic stand-in, NOT Gemini. No database, network, secrets or school data.
"""
from __future__ import annotations

from dataclasses import dataclass
from nelutu_dialogue_adapter import answer_parent_dialogue
from nelutu_unified_orchestrator import respond
from nelutu_unified_reply_policy import choose_reply_route


@dataclass(frozen=True)
class RehearsalResult:
    local_intent: str
    planned_route: str
    actual_route: str
    answer: str
    provider_calls: int


def rehearse(question: str, *, consent: bool = False, enabled: bool = False,
             budget_reserved: bool = False, history=()) -> RehearsalResult:
    """Exercise the actual composition with a fake provider and no side effects."""
    local, _state = answer_parent_dialogue(question, context=None)
    planned, _guide = choose_reply_route(
        question, existing_intent=local.intent, consent=consent, history=history
    )
    calls = []
    def fake_provider(public_history, public_question):
        calls.append((public_history, public_question))
        return "No, acesta este un răspuns FICTIV de simulare, nu Gemini. 🤠"
    answer, route = respond(
        question, local, history=history, consent=consent,
        enabled=enabled, budget_reserved=budget_reserved,
        provider=fake_provider,
    )
    return RehearsalResult(
        local_intent=local.intent, planned_route=planned,
        actual_route=route, answer=answer.text, provider_calls=len(calls),
    )


if __name__ == "__main__":
    scenarios = (
        ("Salut, Neluțu!", False, False, False),
        ("Cum trimit o scutire medicală în portal?", False, False, False),
        ("Explică-mi pe înțelesul meu de ce plutește o barcă.", True, True, False),
        ("Explică-mi pe înțelesul meu de ce plutește o barcă.", True, True, True),
    )
    for question, consent, enabled, reserved in scenarios:
        result = rehearse(question, consent=consent, enabled=enabled, budget_reserved=reserved)
        print(f"route={result.actual_route}; calls={result.provider_calls}; intent={result.local_intent}")
