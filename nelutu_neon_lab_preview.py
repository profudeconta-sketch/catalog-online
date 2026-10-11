"""Separate, public-safe Streamlit landing page for an isolated Neon lab.

No database connections occur in this UI. An operator must first provide a
genuinely access-restricted environment and validate it out of band.
"""
from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="Neluțu — laborator izolat", page_icon="🔒")
st.title("🔒 Neluțu — laborator experimental")
st.warning("Laborator închis: accesul la baza de date este dezactivat.")
st.write(
    "Această pagină este doar o verificare a pornirii aplicației separate. "
    "Nu citește și nu scrie în Neon, nu folosește Gemini și nu accesează date școlare."
)
st.info(
    "Nu introduceți parole, chei API, conexiuni Neon sau date personale aici. "
    "O adresă web diferită nu înseamnă acces privat."
)
