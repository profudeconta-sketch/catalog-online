"""Local conversation follow-up planner, without access to personal data.

Offers optional engagement without pushing for emotional disclosure.
"""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class FollowUp:
    text: str
    category: str

def suggest_followup(*, helpful_answer: bool, sensitive: bool, previous_category: str = "",
                     user_wants_to_stop: bool = False) -> FollowUp | None:
    """A follow-up is optional; do not ask after distress or an explicit stop."""
    if not helpful_answer or sensitive or user_wants_to_stop:
        return None
    if previous_category == "check":
        return FollowUp("Dacă vrei, putem vedea și un exemplu împreună.", "example")
    if previous_category == "example":
        return None
    return FollowUp("No, ți-o fost de folos explicația ori mai lămurim ceva?", "check")
