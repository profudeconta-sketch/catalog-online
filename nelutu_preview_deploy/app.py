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
from nelutu_neon_isolated_health import isolated_neon_ready

st.divider()
st.subheader("🔒 Verificare Neon — laborator izolat")
st.caption("Doar verificare de conectivitate și permisiuni. Nu modifică date și nu apelează Gemini.")
if st.button("Verifică Neon izolat", key="nelutu_isolated_neon_health"):
    _test_dsn = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
    if not _test_dsn:
        st.info("Conexiunea de test nu este configurată în Secrets. Nicio conexiune nu a fost încercată.")
    elif isolated_neon_ready(_test_dsn, enabled=True):
        st.success("Neon: conexiune de test validă, rol și permisiuni izolate confirmate.")
    else:
        st.warning("Verificarea Neon nu a trecut. Conexiunea, rolul sau permisiunile nu sunt confirmate; nicio modificare nu a fost făcută.")
