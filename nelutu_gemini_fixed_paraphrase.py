"""Fixed public paraphrase/context experiment, isolated from school records."""
from __future__ import annotations

from urllib import request
from nelutu_gemini_fixed_transport import send_fixed_exchange

PARAPHRASE_EXCHANGE = (
    ("user", "Am trei treburi mâine: să ud florile, să duc o carte la bibliotecă și să cumpăr pâine."),
    ("model", "Le poți nota în ordinea în care vrei să le faci."),
    ("user", "Pe aia de la mijloc aș vrea s-o rezolv prima. Ce trebuie să duc?"),
)


def fixed_paraphrase_test(*, api_key: str | None = None,
                          enabled: bool = False, confirmed: bool = False) -> str | None:
    """Send only the approved fictional transcript, without retries."""
    return send_fixed_exchange(
        PARAPHRASE_EXCHANGE, api_key=api_key, enabled=enabled,
        confirmed=confirmed, temperature=0.4, opener=request.urlopen,
    )
