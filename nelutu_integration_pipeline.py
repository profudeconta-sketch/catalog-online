"""Stage 45 isolated end-to-end request pipeline; no school app imports."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from nelutu_integration_gate import authorize_experimental_request


@dataclass(frozen=True)
class PipelineResult:
    status: str
    answer: str | None = None


def run_demo_pipeline(message: str, *, explicitly_enabled: bool, confirmed: bool,
                      provider_key_present: bool, durable_budget,
                      session_budget, instance_gate,
                      sender: Callable[[str], str | None]) -> PipelineResult:
    """Fail closed; reserve before sending; never refund a reserved attempt."""
    decision = authorize_experimental_request(
        message,
        explicitly_enabled=explicitly_enabled,
        confirmed=confirmed,
        provider_key_present=provider_key_present,
        durable_gate_ready=durable_budget is not None,
    )
    if not decision.allowed:
        return PipelineResult(decision.reason)
    if not session_budget.allowed() or not instance_gate.instance.allowed():
        return PipelineResult("session_or_instance_limit")
    if not durable_budget.reserve():
        return PipelineResult("durable_quota_unavailable")
    if not instance_gate.reserve(session_budget):
        return PipelineResult("session_or_instance_limit")
    try:
        answer = sender(message)
    except Exception:
        return PipelineResult("provider_error")
    if not isinstance(answer, str) or not answer.strip():
        return PipelineResult("provider_unavailable")
    clean_answer = answer.strip()[:1500].strip()
    if not clean_answer or not clean_answer.isprintable():
        return PipelineResult("provider_unavailable")
    return PipelineResult("ok", clean_answer)
