"""Separate Streamlit UI for the isolated Neon laboratory.

This is NOT the public Gemini preview and NOT a school application.
No provider calls or school records. Connection is disabled unless all flags
are explicitly true; use only a restricted test role and a private deployment.
"""
from __future__ import annotations

import streamlit as st

from nelutu_streamlit_lab_gate import LabAccess, lab_remaining, lab_reserve

st.set_page_config(page_title="Neluțu — laborator Neon izolat", page_icon="🔒")
st.title("🔒 Laborator Neon izolat")
st.warning("Nu introduceți date școlare, personale, parole sau chei în interfață.")
st.caption("Laborator separat. Nu efectuează apeluri Gemini și nu modifică aplicațiile școlare.")

# Only Streamlit secrets; never echo connection strings.
def secret(name, default=None):
    try:
        return st.secrets.get(name, default)
    except (FileNotFoundError, KeyError, AttributeError):
        return default


config = LabAccess(
    enabled=secret("NELUTU_NEON_LAB_ENABLED", False) is True,
    private_access_verified=secret("NELUTU_NEON_LAB_PRIVATE_ACCESS_VERIFIED", False) is True,
    operator_confirmed=secret("NELUTU_NEON_LAB_OPERATOR_CONFIRMED", False) is True,
    dedicated_dsn=secret("NELUTU_NEON_LAB_TEST_DSN", None),
)

# Never offer a state-changing button to unauthenticated visitors.
# These flags are operator attestations, not user authentication.
st.write("Modul laborator:", "Configurat" if config.enabled else "Dezactivat")
st.write("Acces privat confirmat:", "Da" if config.private_access_verified else "Nu")
st.write("Aprobare operator:", "Da" if config.operator_confirmed else "Nu")
st.info(
    "Această pagină afișează numai starea configurației. "
    "Testul de scriere este disponibil doar prin procedura controlată, "
    "în afara interfeței publice."
)
if config.enabled and config.private_access_verified and config.operator_confirmed:
    st.write("Rezervări fictive rămase:", lab_remaining(config))
else:
    st.write("Conexiunea Neon nu a fost inițiată.")
