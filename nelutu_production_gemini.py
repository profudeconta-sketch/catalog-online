"""Fail-closed Gemini gate for parent portal. No school data is transmitted."""
from nelutu_gemini_optional import is_public_general_chat
from nelutu_free_dialogue_transport import generate_public_dialogue
from nelutu_postgres_budget import PostgreSQLBudget
from nelutu_unified_reply_policy import choose_reply_route

def optional_provider(question, local_intent, *, consent=False, settings=None):
    """Return (provider, reserved). Never log prompts, keys, DSNs or errors."""
    settings = settings or {}
    required = (
        "NELUTU_GEMINI_ENABLED",
        "NELUTU_PROVIDER_PRIVACY_APPROVED",
        "NELUTU_PROVIDER_COST_APPROVED",
        "NELUTU_NEON_BUDGET_ENABLED",
        "NELUTU_NEON_LIVE_BUDGET_APPROVED",
    )
    if not consent or any(settings.get(key) is not True for key in required):
        return None, False
    if not is_public_general_chat(question):
        return None, False
    route, _ = choose_reply_route(question, existing_intent=local_intent,
                                  consent=True, history=())
    if route != "generative_eligible":
        return None, False
    key = settings.get("NELUTU_GEMINI_API_KEY")
    dsn = settings.get("NELUTU_NEON_DSN")
    if not isinstance(key, str) or not key.strip():
        return None, False
    if not isinstance(dsn, str) or not dsn.strip():
        return None, False
    if not PostgreSQLBudget(dsn).reserve():
        return None, False
    def provider(_history, text):
        return generate_public_dialogue(
            (), text, api_key=key, enabled=True,
            confirmed=True, budget_reserved=True,
        )
    return provider, True
