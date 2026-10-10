"""Offline-only integration boundary for Neluțu 2.0.

This module deliberately has no Gemini transport and no school-data imports.
"""
from __future__ import annotations

from dataclasses import dataclass

from nelutu_gemini_optional import is_approved_demo_message


@dataclass(frozen=True)
class IntegrationDecision:
    allowed: bool
    reason: str


def authorize_experimental_request(message: str, *, explicitly_enabled: bool,
                                   confirmed: bool, provider_key_present: bool,
                                   durable_gate_ready: bool) -> IntegrationDecision:
    """Fail closed until every independent integration prerequisite is true."""
    if not explicitly_enabled:
        return IntegrationDecision(False, "disabled")
    if not confirmed:
        return IntegrationDecision(False, "consent_required")
    if not provider_key_present:
        return IntegrationDecision(False, "provider_unavailable")
    if not durable_gate_ready:
        return IntegrationDecision(False, "durable_quota_required")
    if not is_approved_demo_message(message):
        return IntegrationDecision(False, "not_approved_public_demo")
    return IntegrationDecision(True, "approved_public_demo")
