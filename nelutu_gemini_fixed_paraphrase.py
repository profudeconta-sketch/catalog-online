"""Fixed public paraphrase/context experiment, isolated from school records."""
from __future__ import annotations

import json
from urllib import request, error
from nelutu_gemini_optional import ENDPOINT, SYSTEM, TIMEOUT

PARAPHRASE_EXCHANGE = (
    ("user", "Am trei treburi mâine: să ud florile, să duc o carte la bibliotecă și să cumpăr pâine."),
    ("model", "Le poți nota în ordinea în care vrei să le faci."),
    ("user", "Pe aia de la mijloc aș vrea s-o rezolv prima. Ce trebuie să duc?"),
)


def fixed_paraphrase_test(*, api_key: str | None = None,
                          enabled: bool = False, confirmed: bool = False) -> str | None:
    """Send exactly the fixed fictional transcript, only after opt-in."""
    if not enabled or not confirmed or not isinstance(api_key, str) or not api_key.strip():
        return None
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": role, "parts": [{"text": message}]}
                     for role, message in PARAPHRASE_EXCHANGE],
        "generationConfig": {"maxOutputTokens": 240, "temperature": 0.4},
    }).encode("utf-8")
    req = request.Request(ENDPOINT, data=payload, method="POST",
                          headers={"Content-Type": "application/json", "x-goog-api-key": api_key})
    try:
        with request.urlopen(req, timeout=TIMEOUT) as response:
            result = json.load(response)
        answer = "".join(part.get("text", "") for part in result["candidates"][0]["content"]["parts"]).strip()
        return answer[:1500] or None
    except (error.HTTPError, error.URLError, TimeoutError, OSError,
            ValueError, KeyError, IndexError, TypeError, UnicodeError):
        return None
