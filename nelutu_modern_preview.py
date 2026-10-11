"""One Neluțu UI for controlled staging; never imports the school applications.

Gemini is present but fail-closed until an operator explicitly configures and
approves privacy, costs, access, a dedicated durable quota and per-message consent.
"""
import hmac
import streamlit as st
from nelutu_modern_core import answer
from nelutu_gemini_optional import is_public_general_chat
from nelutu_free_dialogue_transport import generate_public_dialogue
from nelutu_postgres_budget import PostgreSQLBudget
from nelutu_parent_guide import TUTORIAL_TEXT

st.set_page_config(page_title="Neluțu-al-nost — modern", page_icon="🤠")
st.title("🤠 Neluțu-al-nost")
st.caption("Un singur asistent: ghidul sistemului, explicații și conversație. Mediu experimental izolat; nu este portalul părinților.")
st.warning("Nu introduceți date despre elevi, părinți, conturi, sănătate sau documente.")
with st.expander("📖 Ghidul complet al sistemului"):
    st.markdown(TUTORIAL_TEXT)

def secret_bool(name):
    return st.secrets.get(name, False) is True

access = st.secrets.get("NELUTU_UNIFIED_ACCESS_CODE", "")
if not isinstance(access, str) or len(access) < 16:
    st.error("Accesul operatorului nu este configurat. Asistentul este blocat.")
    st.stop()
entered = st.text_input("Cod de acces pentru operatorul de test", type="password")
if not hmac.compare_digest(entered, access):
    st.info("Introdu codul operatorului pentru a continua.")
    st.stop()

if "nelutu_modern_state" not in st.session_state:
    st.session_state.nelutu_modern_state = None
if "nelutu_modern_history" not in st.session_state:
    st.session_state.nelutu_modern_history = []
for role, text in st.session_state.nelutu_modern_history[-12:]:
    with st.chat_message("assistant" if role == "assistant" else "user"):
        st.markdown(text)

question = st.chat_input("Întreabă-l pe Neluțu...")
if question:
    with st.chat_message("user"):
        st.markdown(question)
    # Never send history or authenticated portal context to the provider.
    # The current message must be explicitly approved each time.
    st.session_state.nelutu_modern_pending = question

pending = st.session_state.get("nelutu_modern_pending")
if pending:
    public = is_public_general_chat(pending)
    approved = (
        secret_bool("NELUTU_UNIFIED_LIVE_ENABLED")
        and secret_bool("NELUTU_NEON_BUDGET_ENABLED")
        and secret_bool("NELUTU_NEON_LIVE_BUDGET_APPROVED")
        and secret_bool("NELUTU_PROVIDER_PRIVACY_APPROVED")
        and secret_bool("NELUTU_PROVIDER_COST_APPROVED")
    )
    consent = st.checkbox("Confirm că întrebarea afișată este publică și accept transmiterea ei către Google Gemini.", key="nelutu_modern_consent")
    st.caption("Mesaj propus pentru transmitere: " + pending)
    if st.button("🤠 Trimite întrebarea", key="nelutu_modern_send"):
        provider = None
        reserved = False
        if public and approved and consent:
            dsn = st.secrets.get("NELUTU_NEON_DSN", "")
            key = st.secrets.get("NELUTU_GEMINI_API_KEY", "")
            if isinstance(dsn, str) and dsn.strip() and isinstance(key, str) and key.strip():
                # Reservation is possible only after independent operator gates.
                # No retries, refunds, or unbounded quota.
                reserved = PostgreSQLBudget(dsn).reserve()
                if reserved:
                    provider = lambda _history, text: generate_public_dialogue(
                        (), text, api_key=key, enabled=True,
                        confirmed=True, budget_reserved=True
                    )
        result = answer(pending, consent=bool(public and consent),
                        generative_enabled=bool(approved), budget_reserved=reserved,
                        provider=provider)
        st.session_state.nelutu_modern_history.extend(
            [("user", pending), ("assistant", result.answer.text)]
        )
        st.session_state.nelutu_modern_state = result.state
        st.session_state.nelutu_modern_pending = None
        st.rerun()
