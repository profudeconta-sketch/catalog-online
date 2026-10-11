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
