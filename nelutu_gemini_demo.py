"""Isolated demo prompts for evaluating Gemini without personal data.

Only predefined text can reach the external provider from this module.
This is NOT integrated into the active parent/teacher applications.
"""
from __future__ import annotations

from nelutu_gemini_optional import generate

DEMO_PROMPTS = (
    "Salut, Neluțu! Ce mai faci?",
    "Și eu sunt bine. Ce idee ai pentru o plimbare de duminică?",
    "Explică-mi diferența dintre o presupunere și o dovadă.",
    "Dă-mi o idee simplă ca să-mi organizez mai bine timpul.",
    "De ce spunem că două lucruri sunt asemănătoare, dar nu identice?",
)

def demo_prompt(index: int, *, api_key: str | None = None,
                enabled: bool = False, confirmed: bool = False) -> str | None:
    """Predefined, non-user-editable public text only; fail closed."""
    if type(index) is not int or index < 0 or index >= len(DEMO_PROMPTS):
        return None
    if not confirmed or not enabled:
        return None
    return generate(
        DEMO_PROMPTS[index], api_key=api_key,
        enabled=True, public_text_confirmed=True,
    )
