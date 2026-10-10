"""Single-answer experimental router; local answer always remains available.

No UI, no student-data transport, no school application imports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from nelutu_optional_integration_adapter import AdapterSettings, handle_optional_demo


@dataclass(frozen=True)
class RoutedAnswer:
    text: str
    source: str
    provider_status: str


def route_single_answer(question: str, *, local_answer: Callable[[str], str],
                        settings: AdapterSettings, confirmed: bool,
                        provider_key_present: bool, durable_budget,
                        session_budget, instance_gate,
                        sender: Callable[[str], str | None]) -> RoutedAnswer:
    """Use one existing response surface; safely fall back to local on any block."""
    # The local fallback is calculated independently and never sent to the provider.
    try:
        local = local_answer(question)
    except Exception:
        return RoutedAnswer("Neluțu nu poate răspunde momentan. Încearcă din nou mai târziu.", "local", "local_error")
    if not isinstance(local, str):
        return RoutedAnswer("Neluțu nu poate răspunde momentan. Încearcă din nou mai târziu.", "local", "local_invalid")
    try:
        result = handle_optional_demo(
            question, settings=settings, confirmed=confirmed,
            provider_key_present=provider_key_present,
            durable_budget=durable_budget, session_budget=session_budget,
            instance_gate=instance_gate, sender=sender,
        )
    except Exception:
        # The optional path cannot interrupt the existing local response.
        return RoutedAnswer(local, "local", "experimental_error")
    if result.status == "ok" and result.answer:
        return RoutedAnswer(result.answer, "experimental", result.status)
    return RoutedAnswer(local, "local", result.status)
