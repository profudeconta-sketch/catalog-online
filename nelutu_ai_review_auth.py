"""Authorization boundary for human-reviewed Neluțu lessons.

The caller MUST verify authenticated identity and permission separately.
This module does not accept a user-supplied reviewer name as proof of authority.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable
from nelutu_ai_learning import LearningNotebook

@dataclass(frozen=True)
class ReviewIdentity:
    principal_id: str
    authenticated: bool

class ReviewDenied(PermissionError):
    pass

def approve_with_authorization(
    notebook: LearningNotebook,
    question: str,
    *,
    identity: ReviewIdentity,
    authorize: Callable[[str, str], bool],
) -> bool:
    """Authorization must be supplied by a trusted server-side access check."""
    if not isinstance(identity, ReviewIdentity) or identity.authenticated is not True:
        raise ReviewDenied("not_authenticated")
    if not isinstance(identity.principal_id, str) or not identity.principal_id.strip():
        raise ReviewDenied("invalid_principal")
    if not callable(authorize) or authorize(identity.principal_id, "nelutu_lesson_review") is not True:
        raise ReviewDenied("not_authorized")
    return notebook.approve(question, reviewer=identity.principal_id)
