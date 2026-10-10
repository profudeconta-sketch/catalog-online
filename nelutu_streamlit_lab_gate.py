"""Offline-only safety gate for the isolated Streamlit-Neon lab.

No provider calls, no school data, and no secrets are stored here.
"""
from __future__ import annotations

from dataclasses import dataclass

from nelutu_streamlit_lab_budget import IsolatedLabBudget


@dataclass(frozen=True)
class LabAccess:
    enabled: bool = False
    private_access_verified: bool = False
    operator_confirmed: bool = False
    dedicated_dsn: str | None = None


def lab_remaining(config: LabAccess) -> int:
    if not _allowed(config):
        return 0
    try:
        return IsolatedLabBudget(config.dedicated_dsn, enabled=True).remaining()
    except Exception:
        return 0


def lab_reserve(config: LabAccess) -> bool:
    if not _allowed(config):
        return False
    try:
        return IsolatedLabBudget(config.dedicated_dsn, enabled=True).reserve()
    except Exception:
        return False


def _allowed(config: LabAccess) -> bool:
    return (
        type(config) is LabAccess
        and config.enabled is True
        and config.private_access_verified is True
        and config.operator_confirmed is True
        and isinstance(config.dedicated_dsn, str)
        and config.dedicated_dsn.startswith(("postgresql://", "postgres://"))
    )
