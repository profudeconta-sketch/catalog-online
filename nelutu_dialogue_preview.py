"""Laborator izolat Neluțu: fără catalog, autentificare sau date reale.

Rulare manuală: NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL=1 streamlit run
nelutu_dialogue_preview.py
"""
from __future__ import annotations
import os

# Verificare înainte de încărcarea interfeței: laboratorul nu pornește accidental.
if os.environ.get("NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL") != "1":
    raise SystemExit("Laborator Neluțu dezactivat implicit. Setați explicit NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL=1.")

import streamlit as st
from nelutu_dialogue_adapter import answer_parent_dialogue
from nelutu_local_dialogue import DialogueState

st.set_page_config(page_title="Laborator Neluțu (experimental)", page_icon="🤠")
st.title("🤠 Laborator Neluțu — doar pentru testare")
st.warning("Prototip izolat. Nu introduceți nume, parole, documente sau date ale elevilor.")
if "preview_nelutu_state" not in st.session_state:
    st.session_state["preview_nelutu_state"] = DialogueState()
if "preview_nelutu_reply" not in st.session_state:
    st.session_state["preview_nelutu_reply"] = None

with st.form("preview_nelutu_form", clear_on_submit=True):
    question = st.text_input("Ce vrei să-l întrebi pe Neluțu?", max_chars=1200)
    submitted = st.form_submit_button("Întreabă-l pe Neluțu")
if submitted and question.strip():
    answer, state = answer_parent_dialogue(
        question, context=None, state=st.session_state["preview_nelutu_state"]
    )
    st.session_state["preview_nelutu_state"] = state
    st.session_state["preview_nelutu_reply"] = answer
if st.session_state["preview_nelutu_reply"] is not None:
    answer = st.session_state["preview_nelutu_reply"]
    st.markdown("**Neluțu:**")
    st.markdown(answer.text)
if st.button("Șterge contextul conversației", key="preview_nelutu_reset"):
    st.session_state["preview_nelutu_state"] = DialogueState()
    st.session_state["preview_nelutu_reply"] = None
    st.rerun()
st.caption("Se reține doar tema în sesiunea curentă, nu istoricul întrebărilor. Nu există acces la date școlare.")
