"""Standalone Neluțu Gemini demo, with fixed public prompts only.

Run separately with: streamlit run nelutu_gemini_preview.py
No imports from the parent app, catalog, student registries or documents.
"""
from __future__ import annotations

import streamlit as st

from nelutu_gemini_demo import DEMO_PROMPTS, demo_prompt
from nelutu_gemini_optional import diagnose_status

st.set_page_config(page_title="Neluțu — test Gemini izolat", page_icon="🤠")
st.title("🤠 Neluțu — test Gemini izolat")
st.info(
    "Această pagină este doar pentru testare. Nu este conectată la catalog, "
    "portalul părinților sau documentele școlare."
)
st.warning(
    "Nu introduceți aici date personale. Sunt disponibile exclusiv întrebări "
    "demonstrative prestabilite. Dacă activați testul, textul întrebării "
    "selectate va fi transmis către serviciul Google Gemini."
)

selection = st.selectbox("Alege o întrebare demonstrativă", list(range(len(DEMO_PROMPTS))),
                         format_func=lambda index: DEMO_PROMPTS[index])
st.code(DEMO_PROMPTS[selection], language=None)
confirmed = st.checkbox("Confirm că sunt de acord să transmit această întrebare demonstrativă către Google.")
if st.button("Testează Gemini", disabled=not confirmed):
    try:
        key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        key = None
    if not key:
        st.error("Lipsește cheia de test NELUTU_GEMINI_API_KEY din Streamlit Secrets.")
    else:
        with st.spinner("Neluțu se gândește..."):
            response = demo_prompt(selection, api_key=key, enabled=True, confirmed=confirmed)
        if response:
            st.write(response)
        else:
            st.info("Gemini nu a răspuns. Poți verifica separat categoria erorii mai jos.")

if st.button("Diagnostic sigur (un apel separat)", disabled=not confirmed):
    try:
        key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        key = None
    status = diagnose_status(DEMO_PROMPTS[selection], api_key=key,
                             enabled=True, public_text_confirmed=confirmed)
    st.write("Cod diagnostic:", status)
    st.caption("Nu se afișează cheia API, date personale sau mesajul brut de la Google.")
