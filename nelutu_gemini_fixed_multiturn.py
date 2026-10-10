"""Isolated, fixed five-replica context test; never accepts free-form messages."""
from __future__ import annotations

from urllib import request

from nelutu_gemini_fixed_transport import send_fixed_exchange

# Public fictional exchange, displayed in full before each outbound request.
FIXED_EXCHANGE = (
    ("user", "Aș vrea să-mi organizez mai bine diminețile."),
    ("model", "Poți pregăti seara trei lucruri importante pentru ziua următoare."),
    ("user", "Dă-mi un exemplu concret."),
    ("model", "Pregătește hainele, pune cheile la locul lor și notează prima sarcină."),
    ("user", "Și dacă uit al doilea lucru, cum îmi pot aminti?"),
)


def fixed_multiturn_test(*, api_key: str | None = None,
                         enabled: bool = False, confirmed: bool = False) -> str | None:
    """Send only the approved fictional transcript, without retries."""
    return send_fixed_exchange(
        FIXED_EXCHANGE, api_key=api_key, enabled=enabled,
        confirmed=confirmed, temperature=0.6, opener=request.urlopen,
    )
