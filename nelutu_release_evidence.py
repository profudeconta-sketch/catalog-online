"""Read-only release evidence report for Neluțu experimental integration.

This module never deploys, writes data, or infers that CI proves cloud readiness.
"""
from __future__ import annotations

from dataclasses import dataclass

from nelutu_deployment_readiness import DeploymentEvidence, deployment_ready


@dataclass(frozen=True)
class ReleaseAssessment:
    offline_ci_passed: bool = False
    local_neon_concurrency_passed: bool = False
    streamlit_offline_ui_passed: bool = False
    shared_storage_restart_verified: bool = False
    multi_instance_quota_verified: bool = False
    provider_terms_and_costs_reviewed: bool = False
    privacy_approved: bool = False
    single_ui_end_to_end_verified: bool = False
    rollback_verified: bool = False
    explicit_production_approval: bool = False


def assess_release(evidence: ReleaseAssessment) -> tuple[bool, tuple[str, ...]]:
    if type(evidence) is not ReleaseAssessment:
        return False, ("invalid_evidence",)
    cloud = DeploymentEvidence(
        shared_storage_restart_verified=evidence.shared_storage_restart_verified,
        multi_instance_quota_verified=evidence.multi_instance_quota_verified,
        provider_terms_and_costs_reviewed=evidence.provider_terms_and_costs_reviewed,
        privacy_approved=evidence.privacy_approved,
        single_ui_end_to_end_verified=evidence.single_ui_end_to_end_verified,
        rollback_verified=evidence.rollback_verified,
        explicit_production_approval=evidence.explicit_production_approval,
    )
    checks = {
        "offline_ci_passed": evidence.offline_ci_passed,
        "local_neon_concurrency_passed": evidence.local_neon_concurrency_passed,
        "streamlit_offline_ui_passed": evidence.streamlit_offline_ui_passed,
        **vars(cloud),
    }
    missing = tuple(key for key, value in checks.items() if value is not True)
    return not missing and deployment_ready(cloud), missing
