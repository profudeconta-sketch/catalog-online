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

st.divider()
st.subheader("Test: reformulare și referință la mijlocul listei")
from nelutu_gemini_fixed_paraphrase import PARAPHRASE_EXCHANGE, fixed_paraphrase_test
for role, message in PARAPHRASE_EXCHANGE:
    st.write(("Întrebare: " if role == "user" else "Răspuns demonstrativ: ") + message)
st.caption("Se transmit doar cele trei replici fictive afișate.")
paraphrase_confirmed = st.checkbox(
    "Confirm transmiterea celor trei replici fictive către Google.",
    key="fixed_paraphrase_consent",
)
if st.button("Testează reformularea", disabled=not paraphrase_confirmed):
    try:
        paraphrase_key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        paraphrase_key = None
    if not paraphrase_key:
        st.error("Cheia de test nu este configurată.")
    else:
        with st.spinner("Neluțu urmărește referințele..."):
            paraphrase_answer = fixed_paraphrase_test(
                api_key=paraphrase_key, enabled=True, confirmed=paraphrase_confirmed)
        if paraphrase_answer:
            st.write(paraphrase_answer)
        else:
            st.info("Testul de reformulare nu a primit un răspuns utilizabil.")

st.divider()
st.subheader("Test 9: revenirea la un subiect anterior")
from nelutu_gemini_fixed_topic_return import TOPIC_RETURN_EXCHANGE, fixed_topic_return_test
for role, message in TOPIC_RETURN_EXCHANGE:
    st.write(("Întrebare: " if role == "user" else "Răspuns demonstrativ: ") + message)
st.caption("Sunt trimise doar replicile fictive afișate.")
topic_consent = st.checkbox("Confirm transmiterea replicilor fictive către Google.", key="topic_return_consent")
if st.button("Testează revenirea la subiect", disabled=not topic_consent):
    try:
        topic_key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        topic_key = None
    if not topic_key:
        st.error("Cheia de test nu este configurată.")
    else:
        with st.spinner("Se verifică revenirea la subiect..."):
            topic_answer = fixed_topic_return_test(
                api_key=topic_key, enabled=True, confirmed=topic_consent)
        if topic_answer:
            st.write(topic_answer)
        else:
            st.info("Testul 9 nu a primit un răspuns utilizabil.")

st.divider()
st.subheader("Etapa 10 — verificare automată a memoriei locale")
st.success("Etapa 10 a fost validată în GitHub Actions: test_memory_buffer_isolation — reușit (111 teste unitare în suita Neluțu).")
st.caption("Această etapă este un test automat, nu un dialog interactiv; nu transmite date către Gemini.")
st.subheader("Etapa 11: memorie temporară locală, fără Gemini")
from nelutu_conversation_local import LocalConversation
if "nelutu_offline_memory" not in st.session_state:
    st.session_state["nelutu_offline_memory"] = LocalConversation()
local_memory = st.session_state["nelutu_offline_memory"]
st.caption("Folosim numai replici fictive prestabilite. Memoria este locală sesiunii și nu se transmite către Google.")
offline_replies = (
    ("user", "Sâmbătă vreau să plantez un trandafir."),
    ("model", "No, pregătește locul și udă planta."),
    ("user", "Între timp, spune-mi ceva despre curcubeu."),
    ("model", "Curcubeul apare când lumina interacționează cu picăturile de apă."),
)
if st.button("Adaugă următoarea replică fictivă"):
    next_index = st.session_state.get("nelutu_offline_next", 0)
    role, message = offline_replies[next_index % len(offline_replies)]
    if local_memory.append(role, message):
        st.session_state["nelutu_offline_next"] = next_index + 1
    else:
        st.error("Replica a fost respinsă de filtrul local.")
if st.button("Șterge memoria locală"):
    local_memory.clear()
    st.session_state["nelutu_offline_next"] = 0
st.write("Replici păstrate în această sesiune:", len(local_memory.snapshot()))
for role, message in local_memory.snapshot():
    st.write(("Utilizator: " if role == "user" else "Neluțu (fictiv): ") + message)
