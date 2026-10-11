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
            "ready": "Neon: conexiune validă, izolare confirmată și drept CREATE în schema de laborator verificat (fără scrieri).",
            "schema_create_missing": "Neon: conexiune și izolare confirmate, dar rolul nu poate crea tabele în schema de laborator. Nu s-a scris nimic.",
            "invalid_scheme": "Formatul conexiunii de test nu este valid.",
            "missing_driver": "Biblioteca psycopg nu este disponibilă.",
            "wrong_role": "Conexiunea funcționează, dar rolul autentificat nu este nelutu_test_runner.",
            "permissions_failed": "Conexiunea funcționează, dar permisiunile de izolare nu corespund.",
            "incomplete_dsn": "Adresa din Secrets este incompletă sau are format greșit. Copiază integral Connection string din Neon, fără să o trimiți în chat.",
            "dsn_missing_host": "În adresa de test lipsește numele serverului Neon.",
            "dsn_missing_user": "În adresa de test lipsește numele utilizatorului.",
            "dsn_missing_database": "În adresa de test lipsește numele bazei de date.",
            "dsn_missing_password": "În adresa de test nu există o parolă utilizabilă; verifică în Neon opțiunea de copiere cu parola reală, fără a o trimite în chat.",
            "dsn_wrong_role": "Adresa din Secrets indică alt rol decât nelutu_test_runner. Selectează rolul de test în Neon.",
            "connection_operational_failure": "Adresa are structura așteptată, dar Neon a refuzat sau nu a putut stabili conexiunea (autentificare, host, SSL ori rețea).",
            "connection_other_failure": "Conectarea a eșuat dintr-o cauză tehnică locală. Verifică jurnalul fără a divulga date confidențiale.",
            "query_failed": "Conectarea la Neon a reușit, dar interogarea de verificare a eșuat. Nu modifica permisiunile înainte de diagnostic.",
            "missing_secret": "Conexiunea de test nu este configurată.",
        }
        if _status == "ready":
            st.success(_messages[_status])
        else:
            st.warning(_messages[_status])
