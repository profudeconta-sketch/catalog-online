"""Isolated deployment entrypoint for Neluțu preview, not school apps."""
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / "nelutu_gemini_preview.py"), run_name="__main__")

# Read-only connectivity check, intentionally available only in this deployment entrypoint.
# The credential is read from Streamlit Secrets and is never displayed or logged.
import streamlit as st
from nelutu_neon_isolated_diagnostic import diagnose_isolated_neon

st.divider()
st.subheader("🔒 Verificare Neon — laborator izolat")
st.caption("Doar verificare de conectivitate și permisiuni. Nu modifică date și nu apelează Gemini.")
if st.button("Verifică Neon izolat", key="nelutu_isolated_neon_health"):
    _test_dsn = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
    if not _test_dsn:
        st.info("Conexiunea de test nu este configurată în Secrets. Nicio conexiune nu a fost încercată.")
    else:
        _status = diagnose_isolated_neon(_test_dsn)
        _messages = {
            "ready": "Neon: conexiune validă, rolul și permisiunile de test sunt confirmate.",
            "invalid_scheme": "Formatul conexiunii de test nu este valid.",
            "missing_driver": "Biblioteca psycopg nu este disponibilă.",
            "wrong_role": "Conexiunea funcționează, dar rolul autentificat nu este nelutu_test_runner.",
            "permissions_failed": "Conexiunea funcționează, dar permisiunile de izolare nu corespund.",
            "connection_or_query_failed": "Conexiunea ori interogarea de verificare a eșuat. Verifică setările Neon fără a divulga datele de conectare.",
            "missing_secret": "Conexiunea de test nu este configurată.",
        }
        if _status == "ready":
            st.success(_messages[_status])
        else:
            st.warning(_messages[_status])
