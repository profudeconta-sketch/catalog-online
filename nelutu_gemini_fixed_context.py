"""Fixed, non-personal two-turn Gemini memory experiment.

Not connected to the school applications. Only hardcoded public messages are sent.
"""
from __future__ import annotations

from urllib import request

from nelutu_gemini_fixed_transport import send_fixed_exchange

FIRST_QUESTION = "Ce înseamnă să fii punctual?"
FIRST_ANSWER = "Să ajungi la ora promisă și să respecți timpul celorlalți."
FOLLOW_UP = "Și de ce este important acest lucru?"
MAX_REPLY = 1500


def fixed_context_test(*, api_key: str | None = None,
                       enabled: bool = False, confirmed: bool = False) -> str | None:
    """Send only the approved fictional transcript, without retries."""
    return send_fixed_exchange(
        (("user", FIRST_QUESTION), ("model", FIRST_ANSWER), ("user", FOLLOW_UP)), api_key=api_key, enabled=enabled,
        confirmed=confirmed, temperature=0.6, opener=request.urlopen,
    )
