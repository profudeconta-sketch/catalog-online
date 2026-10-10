"""Isolated fixed topic-switch and return experiment; no user input transmitted."""
from __future__ import annotations

import json
from urllib import request, error
from nelutu_gemini_optional import ENDPOINT, SYSTEM, TIMEOUT

TOPIC_RETURN_EXCHANGE = (
    ("user", "Sâmbătă vreau să plantez un trandafir în grădină."),
    ("model", "Pregătește o groapă potrivită și udă planta după așezare."),
    ("user", "Apropo, de ce apar curcubeele?"),
    ("model", "Lumina soarelui este refractată, reflectată și dispersată în picăturile de apă."),
    ("user", "Revenind la ce voiam să fac sâmbătă, ce plantă am pomenit?"),
)


def fixed_topic_return_test(*, api_key: str | None = None,
                            enabled: bool = False, confirmed: bool = False) -> str | None:
    """Only the public fixed transcript is transmitted after explicit opt-in."""
    if not enabled or not confirmed or not isinstance(api_key, str) or not api_key.strip():
        return None
    payload = json.dumps({
        "systemInstruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"role": role, "parts": [{"text": message}]}
                     for role, message in TOPIC_RETURN_EXCHANGE],
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
