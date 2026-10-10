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

st.divider()
st.subheader("Test separat: memorie conversațională cu text prestabilit")
st.write("Mesajul 1: Ce înseamnă să fii punctual?")
st.write("Răspuns demonstrativ: Să ajungi la ora promisă și să respecți timpul celorlalți.")
st.write("Mesajul 2: Și de ce este important acest lucru?")
st.caption("Aceste trei replici publice, afișate mai sus, vor fi trimise împreună către Google. Nu se transmite istoricul real al utilizatorului.")
context_confirmed = st.checkbox(
    "Confirm transmiterea celor trei replici demonstrative către Google.",
    key="fixed_context_consent",
)
if st.button("Testează memoria demonstrativă", disabled=not context_confirmed):
    from nelutu_gemini_fixed_context import fixed_context_test
    try:
        context_key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        context_key = None
    if not context_key:
        st.error("Cheia de test nu este configurată.")
    else:
        with st.spinner("Neluțu urmărește firul discuției..."):
            context_answer = fixed_context_test(
                api_key=context_key, enabled=True, confirmed=context_confirmed)
        if context_answer:
            st.write(context_answer)
        else:
            st.info("Testul de memorie nu a primit un răspuns utilizabil.")

st.divider()
st.subheader("Test extins: cinci replici demonstrative")
from nelutu_gemini_fixed_multiturn import FIXED_EXCHANGE, fixed_multiturn_test
for role, message in FIXED_EXCHANGE:
    st.write(("Întrebare: " if role == "user" else "Răspuns demonstrativ: ") + message)
st.caption("Se trimit doar aceste cinci replici prestabilite, nu conversații reale.")
multi_confirmed = st.checkbox(
    "Confirm transmiterea celor cinci replici demonstrative către Google.",
    key="fixed_multiturn_consent",
)
if st.button("Testează dialogul extins", disabled=not multi_confirmed):
    try:
        multi_key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        multi_key = None
    if not multi_key:
        st.error("Cheia de test nu este configurată.")
    else:
        with st.spinner("Neluțu urmărește conversația..."):
            multi_answer = fixed_multiturn_test(
                api_key=multi_key, enabled=True, confirmed=multi_confirmed)
        if multi_answer:
            st.write(multi_answer)
        else:
            st.info("Testul extins nu a primit un răspuns utilizabil.")
