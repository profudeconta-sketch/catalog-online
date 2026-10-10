"""Isolated fixed topic-switch and return experiment; no user input transmitted."""
from __future__ import annotations

from urllib import request
from nelutu_gemini_fixed_transport import send_fixed_exchange

TOPIC_RETURN_EXCHANGE = (
    ("user", "Sâmbătă vreau să plantez un trandafir în grădină."),
    ("model", "Pregătește o groapă potrivită și udă planta după așezare."),
    ("user", "Apropo, de ce apar curcubeele?"),
    ("model", "Lumina soarelui este refractată, reflectată și dispersată în picăturile de apă."),
    ("user", "Revenind la ce voiam să fac sâmbătă, ce plantă am pomenit?"),
)


def fixed_topic_return_test(*, api_key: str | None = None,
                            enabled: bool = False, confirmed: bool = False) -> str | None:
    """Send only the approved fictional transcript, without retries."""
    return send_fixed_exchange(
        TOPIC_RETURN_EXCHANGE, api_key=api_key, enabled=enabled,
        confirmed=confirmed, temperature=0.4, opener=request.urlopen,
    )
