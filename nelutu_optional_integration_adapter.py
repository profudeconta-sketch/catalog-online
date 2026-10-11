"""Reversible, opt-in Neluțu 2.0 integration adapter.

No school app imports, no school records, no Gemini transport.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from nelutu_integration_pipeline import PipelineResult, run_demo_pipeline


@dataclass(frozen=True)
class AdapterSettings:
    enabled: bool = False
    privacy_approved: bool = False
    infrastructure_verified: bool = False


def handle_optional_demo(message: str, *, settings: AdapterSettings,
                         confirmed: bool, provider_key_present: bool,
                         durable_budget, session_budget, instance_gate,
                         sender: Callable[[str], str | None]) -> PipelineResult:
    """Disabled by default; no external action when any deployment gate is off."""
    if type(settings) is not AdapterSettings:
        return PipelineResult("invalid_settings")
    if type(settings.enabled) is not bool or type(settings.privacy_approved) is not bool or type(settings.infrastructure_verified) is not bool:
        return PipelineResult("invalid_settings")
    if not settings.enabled:
        return PipelineResult("integration_disabled")
    if not settings.privacy_approved:
        return PipelineResult("privacy_review_required")
    if not settings.infrastructure_verified:
        return PipelineResult("infrastructure_review_required")
    return run_demo_pipeline(
        message, explicitly_enabled=True, confirmed=confirmed,
        provider_key_present=provider_key_present, durable_budget=durable_budget,
        session_budget=session_budget, instance_gate=instance_gate,
        sender=sender,
    )
