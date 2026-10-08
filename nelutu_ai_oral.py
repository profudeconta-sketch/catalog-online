"""Offline timed oral-exam harness for Neluțu's AI adapter.

Requires an injected fake provider. Never sends network requests.
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from nelutu_cloudflare_ai import generate, AIUnavailable

@dataclass(frozen=True)
class OralResult:
    elapsed_seconds: float
    within_budget: bool
    available: bool
    answer: str
    reason: str

def timed_oral_exam(question: str, *, transport, budget_seconds: float = 3.0) -> OralResult:
    if not callable(transport) or budget_seconds <= 0:
        raise ValueError("invalid_exam_configuration")
    start = time.perf_counter()
    try:
        response = generate(question, account_id="offlineexam1234",
                            api_token="synthetic-test-token", transport=transport)
        answer, available, reason = response.text, response.available, ""
    except AIUnavailable as exc:
        answer, available, reason = "", False, str(exc)
    elapsed = time.perf_counter() - start
    return OralResult(elapsed, elapsed <= budget_seconds, available, answer, reason)
