"""Explicit per-session AI request budget for experimental Neluțu.

Not a billing safeguard: multiple processes/sessions need a shared atomic
quota and provider-side hard spend limits before any production integration.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass
class SessionAIBudget:
    max_requests: int = 8
    used: int = 0

    def __post_init__(self):
        if not isinstance(self.max_requests, int) or not 0 <= self.max_requests <= 100:
            raise ValueError("invalid_limit")
        if not isinstance(self.used, int) or not 0 <= self.used <= self.max_requests:
            raise ValueError("invalid_usage")

    @property
    def remaining(self) -> int:
        return self.max_requests - self.used

    def reserve(self) -> bool:
        """Reserve before a provider call; failures still consume allowance."""
        if self.remaining <= 0:
            return False
        self.used += 1
        return True

def guarded_generate(question, *, budget: SessionAIBudget, consent: bool, generator, **kwargs):
    """Explicit opt-in and quota before invoking a caller-supplied generator."""
    if consent is not True:
        raise PermissionError("ai_consent_required")
    if not isinstance(budget, SessionAIBudget):
        raise TypeError("invalid_budget")
    if not budget.reserve():
        raise RuntimeError("session_ai_budget_exhausted")
    return generator(question, **kwargs)
