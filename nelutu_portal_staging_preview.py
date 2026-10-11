"""Experimental parent-portal-like Neluțu simulation.

This is a presentation shell for the EXISTING experimental Gemini preview,
not an imported copy of the real parent portal. It uses no school records.
"""
from __future__ import annotations
from pathlib import Path
import runpy
import sys
import streamlit as st

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

st.title("🤠 Neluțu-al-nost — simulare portal părinți")
st.info(
    "SIMULARE EXPERIMENTALĂ — fără autentificare de părinți, fără elevi reali "
    "și fără acces la catalogul școlar. Nu este portalul activ."
)
st.caption(
    "Aceeași logică experimentală Neluțu + tutorial + Gemini, "
    "cu protecțiile și comutatoarele existente. "
    "Dialogul generativ este disponibil doar operatorului autorizat."
)
st.markdown(
    "[Mergi la secțiunea dialog generativ experimental]"
    "(#nelutu-dialog-generativ-experimental)"
)
# Reuse the existing preview verbatim, including provider gates and budgets.
# Never fork the Gemini implementation or import school applications.
runpy.run_path(str(ROOT / "nelutu_gemini_preview.py"), run_name="__main__")

# Read-only lab diagnostics. Never expose DSN, table contents, or credentials.
st.divider()
st.subheader("🔒 Neon — verificare izolată, fără scrieri")
st.caption(
    "Verifică rolul și drepturile de execuție pentru contorul fictiv. "
    "Nu consumă cotă, nu modifică Neon și nu apelează Gemini."
)
if st.button("Verifică permisiunile Neon de laborator", key="nelutu_lab_runtime_check"):
    from nelutu_neon_runtime_permissions import runtime_permissions_ready
    _lab_dsn = st.secrets.get("NELUTU_TEST_DATABASE_URL", "")
    if not _lab_dsn:
        st.warning("Lipsește conexiunea izolată de laborator.")
    elif runtime_permissions_ready(_lab_dsn, enabled=True):
        st.success(
            "Rolul de laborator are drepturile necesare pentru contorul fictiv "
            "și nu are CREATE în schema de test sau acces la contorul Gemini."
        )
    else:
        st.warning(
            "Permisiunile de execuție nu sunt încă validate. "
            "Contorul de laborator rămâne blocat; nu se fac scrieri."
        )
