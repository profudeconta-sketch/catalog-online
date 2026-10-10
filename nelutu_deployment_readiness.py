"""Stage 62: deployment evidence gate. Offline tests are never deployment evidence."""
from dataclasses import dataclass


@dataclass(frozen=True)
class DeploymentEvidence:
    shared_storage_restart_verified: bool = False
    multi_instance_quota_verified: bool = False
    provider_terms_and_costs_reviewed: bool = False
    privacy_approved: bool = False
    single_ui_end_to_end_verified: bool = False
    rollback_verified: bool = False
    explicit_production_approval: bool = False


def deployment_ready(evidence: DeploymentEvidence) -> bool:
    """Require independent, explicit attestations before any production recommendation."""
    if type(evidence) is not DeploymentEvidence:
        return False
    return all(type(value) is bool and value is True for value in vars(evidence).values())
