"""Stage 70: isolated opt-in quota selection, NEVER a Gemini call or UI change.

An experimental caller must check reserve_experimental_attempt() BEFORE an outbound
Gemini request. False means use the existing local fallback. No school data enters
this module. A deployment flag alone is NOT production approval.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from nelutu_postgres_budget import PostgreSQLBudget


@dataclass(frozen=True)
class ExperimentalQuotaConfig:
    enabled: bool = False
    dedicated_postgres_dsn: Optional[str] = None
    provider_costs_approved: bool = False
    privacy_approved: bool = False
    persistence_verified: bool = False
    limit: int = 12


def reserve_experimental_attempt(config: ExperimentalQuotaConfig) -> bool:
    """Fail closed unless every independent prerequisite is explicitly true."""
    if type(config) is not ExperimentalQuotaConfig:
        return False
    if not all((
        config.enabled is True,
        config.provider_costs_approved is True,
        config.privacy_approved is True,
        config.persistence_verified is True,
    )):
        return False
    if type(config.limit) is not int or not 1 <= config.limit <= 12:
        return False
    if not isinstance(config.dedicated_postgres_dsn, str):
        return False
    if not config.dedicated_postgres_dsn.startswith(("postgresql://", "postgres://")):
        return False
    try:
        return PostgreSQLBudget(config.dedicated_postgres_dsn, limit=config.limit).reserve()
    except Exception:
        # Never leak connection details; a configuration error denies Gemini.
        return False
