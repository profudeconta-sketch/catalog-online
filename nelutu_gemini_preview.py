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

st.divider()
st.subheader("Etapa 12: separarea a două memorii locale")
st.caption("Două instanțe demonstrative, independente, în aceeași sesiune Streamlit. Fără Gemini și fără date reale.")
if "nelutu_demo_a" not in st.session_state:
    st.session_state["nelutu_demo_a"] = LocalConversation()
if "nelutu_demo_b" not in st.session_state:
    st.session_state["nelutu_demo_b"] = LocalConversation()
demo_a = st.session_state["nelutu_demo_a"]
demo_b = st.session_state["nelutu_demo_b"]
if st.button("Adaugă trandafirul numai în memoria A"):
    demo_a.append("user", "Sâmbătă plantez un trandafir.")
if st.button("Adaugă curcubeul numai în memoria B"):
    demo_b.append("user", "Cum se formează curcubeul?")
if st.button("Resetează ambele memorii demonstrative"):
    demo_a.clear()
    demo_b.clear()
st.write("Memoria A:", demo_a.snapshot())
st.write("Memoria B:", demo_b.snapshot())
st.caption("Aceasta testează separarea obiectelor în aceeași sesiune, nu izolarea între utilizatori reali.")

st.divider()
st.subheader("Etapa 13: limita de patru replici și resetarea independentă")
st.caption("Demonstrație locală cu replici prestabilite; nu sunt apeluri către Gemini.")
if "nelutu_stage13_primary" not in st.session_state:
    st.session_state["nelutu_stage13_primary"] = LocalConversation()
if "nelutu_stage13_secondary" not in st.session_state:
    st.session_state["nelutu_stage13_secondary"] = LocalConversation()
if "nelutu_stage13_index" not in st.session_state:
    st.session_state["nelutu_stage13_index"] = 0
stage13_a = st.session_state["nelutu_stage13_primary"]
stage13_b = st.session_state["nelutu_stage13_secondary"]
stage13_messages = (
    ("user", "Replica 1: pregătesc o carte."),
    ("model", "Replica 2: o poți pune pe masă."),
    ("user", "Replica 3: mâine merg la bibliotecă."),
    ("model", "Replica 4: verifică programul."),
    ("user", "Replica 5: nu uita cartea."),
    ("model", "Replica 6: pune-o lângă geantă."),
)
if st.button("Adaugă următoarea replică în memoria A (maxim 6)"):
    i = st.session_state["nelutu_stage13_index"]
    if i < len(stage13_messages):
        role, message = stage13_messages[i]
        if stage13_a.append(role, message):
            st.session_state["nelutu_stage13_index"] = i + 1
        else:
            st.error("Replica fictivă a fost respinsă.")
    else:
        st.info("Toate cele șase replici au fost adăugate.")
if st.button("Adaugă un mesaj fix în memoria B"):
    stage13_b.append("user", "Memoria B rămâne independentă.")
if st.button("Resetează numai memoria A"):
    stage13_a.clear()
    st.session_state["nelutu_stage13_index"] = 0
if st.button("Resetează numai memoria B"):
    stage13_b.clear()
st.write("Memoria A (maxim patru replici):", stage13_a.snapshot())
st.write("Memoria B:", stage13_b.snapshot())
st.caption("După șase adăugări în A, trebuie să rămână numai replicile 3–6. Resetarea A nu trebuie să modifice B.")

st.divider()
st.subheader("Etapa 14: răspuns contextual din memoria locală")
st.caption("Conversație fictivă prestabilită; răspuns determinist, fără Gemini sau date personale.")
from nelutu_context_offline import FICTIONAL_SCRIPT, answer_from_local_context
if "nelutu_stage14_memory" not in st.session_state:
    st.session_state["nelutu_stage14_memory"] = LocalConversation()
if "nelutu_stage14_index" not in st.session_state:
    st.session_state["nelutu_stage14_index"] = 0
stage14_memory = st.session_state["nelutu_stage14_memory"]
if st.button("Adaugă următoarea replică fictivă (Etapa 14)"):
    i = st.session_state["nelutu_stage14_index"]
    if i < len(FICTIONAL_SCRIPT):
        role, message = FICTIONAL_SCRIPT[i]
        if stage14_memory.append(role, message):
            st.session_state["nelutu_stage14_index"] = i + 1
    else:
        st.info("Conversația fictivă este completă.")
for role, message in stage14_memory.snapshot():
    st.write(("Utilizator: " if role == "user" else "Neluțu: ") + message)
if st.button("Întreabă ce plantă am menționat sâmbătă"):
    st.info(answer_from_local_context(stage14_memory, "Ce plantă am spus că plantez sâmbătă?"))
if st.button("Resetează contextul Etapei 14"):
    stage14_memory.clear()
    st.session_state["nelutu_stage14_index"] = 0
st.caption("Înainte de prima replică sau după resetare, răspunsul trebuie să indice lipsa informației. După prima replică, trebuie să identifice trandafirul.")

st.divider()
st.subheader("Etapa 15: expirarea contextului după depășirea limitei")
st.caption("Exercițiu complet local cu mesaje fictive. Nu transmite istoric către Gemini.")
if "nelutu_stage15_memory" not in st.session_state:
    st.session_state["nelutu_stage15_memory"] = LocalConversation()
if "nelutu_stage15_count" not in st.session_state:
    st.session_state["nelutu_stage15_count"] = 0
stage15_memory = st.session_state["nelutu_stage15_memory"]
stage15_question = "Ce plantă am spus că plantez sâmbătă?"
if st.button("Etapa 15 — memorează trandafirul"):
    stage15_memory.clear()
    stage15_memory.append("user", "Sâmbătă plantez un trandafir.")
    st.session_state["nelutu_stage15_count"] = 0
if st.button("Etapa 15 — adaugă o replică nouă"):
    count = st.session_state["nelutu_stage15_count"]
    if count < 4:
        if stage15_memory.append("model", "Replica fictivă suplimentară %d." % (count + 1)):
            st.session_state["nelutu_stage15_count"] = count + 1
    else:
        st.info("Au fost adăugate deja patru replici suplimentare.")
if st.button("Etapa 15 — șterge contextul"):
    stage15_memory.clear()
    st.session_state["nelutu_stage15_count"] = 0
st.write("Memoria disponibilă:", stage15_memory.snapshot())
st.write("Răspuns bazat pe dovezi:", answer_from_local_context(stage15_memory, stage15_question))
st.caption("După memorare: trandafir. După patru replici suplimentare: informație indisponibilă, nu răspuns inventat.")

st.divider()
st.subheader("Etapa 16: dialog Gemini cu replici fictive, controlat")
st.caption("Numai textul prestabilit afișat mai jos poate fi trimis; nu este transmisă memoria sesiunii.")
from nelutu_gemini_fixed_topic_return import TOPIC_RETURN_EXCHANGE, fixed_topic_return_test
st.write("Scenariul public prestabilit:")
for role, message in TOPIC_RETURN_EXCHANGE:
    st.write(("Utilizator: " if role == "user" else "Neluțu (replică fictivă): ") + message)
stage16_consent = st.checkbox(
    "Etapa 16: confirm transmiterea exclusivă a replicilor fictive afișate către Google Gemini.",
    key="nelutu_stage16_consent",
)
if st.button("Etapa 16 — testează răspunsul contextual Gemini", disabled=not stage16_consent):
    try:
        stage16_key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        stage16_key = None
    if not stage16_key:
        st.error("Lipsește cheia Gemini din Secrets pentru aplicația izolată.")
    else:
        with st.spinner("Gemini răspunde la scenariul fictiv..."):
            stage16_answer = fixed_topic_return_test(
                api_key=stage16_key, enabled=True, confirmed=stage16_consent
            )
        if stage16_answer:
            st.success("Răspuns primit.")
            st.write(stage16_answer)
        else:
            st.warning("Serviciul nu a returnat un răspuns. Nu se face retrimitere automată.")
st.caption("Verifică dacă răspunsul identifică trandafirul și ziua de sâmbătă, fără a confunda subiectul intermediar.")

st.divider()
st.subheader("Etapa 17: evaluarea exprimării ardelenești naturale")
st.caption("Test fix, cu acord explicit. Se transmite doar întrebarea demonstrativă, fără memoria locală.")
from nelutu_gemini_optional import generate
style_prompt = "Salut, Neluțu! Am sâmbăta liberă și vreau să ies la plimbare, dar parcă mă trage canapeaua înapoi. Dă-mi o idee practică și o glumă discretă, cu umor ardelenesc firesc, fără regionalisme forțate."
st.code(style_prompt, language=None)
style_consent = st.checkbox("Etapa 17: sunt de acord să trimit numai întrebarea fictivă afișată către Gemini.", key="nelutu_stage17_consent")
if st.button("Etapa 17 — verifică naturalitatea răspunsului", disabled=not style_consent):
    try:
        style_key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        style_key = None
    if not style_key:
        st.error("Lipsește cheia Gemini din Secrets.")
    else:
        with st.spinner("Neluțu pregătește un răspuns..."):
            style_answer = generate(style_prompt, api_key=style_key, enabled=True, public_text_confirmed=style_consent)
        if style_answer:
            st.write(style_answer)
        else:
            st.warning("Nu am primit răspuns. Nu se reîncearcă automat.")
st.caption("Evaluează: o idee utilă, glumă discretă, exprimare naturală, fără regionalisme inventate.")

st.divider()
st.subheader("Etapa 18: adaptarea tonului")
tone_examples = (
    ("Relaxat", "Salut, Neluțu! Propune o activitate relaxantă pentru o după-amiază liberă, cu umor discret."),
    ("Serios", "Cum pot discuta calm și respectuos cu un prieten după o neînțelegere? Răspunde fără glume."),
    ("Tehnic", "Explică precis diferența dintre RAM și SSD, în câteva propoziții, fără glume."),
)
tone_choice = st.selectbox("Situația fictivă", range(3), format_func=lambda i: tone_examples[i][0])
tone_prompt = tone_examples[tone_choice][1]
st.code(tone_prompt, language=None)
tone_consent = st.checkbox("Confirm transmiterea exclusivă a întrebării afișate către Gemini.", key="tone_consent")
if st.button("Testează tonul", disabled=not tone_consent):
    try:
        tone_key = st.secrets.get("NELUTU_GEMINI_API_KEY")
    except (FileNotFoundError, KeyError, AttributeError):
        tone_key = None
    if tone_key:
        answer = generate(tone_prompt, api_key=tone_key, enabled=True, public_text_confirmed=tone_consent)
        st.write(answer if answer else "Serviciul nu a răspuns; nu se reîncearcă automat.")
    else:
        st.error("Cheia de test lipsește.")

st.divider()
st.subheader("Etapa 19: buget local de apeluri — demonstrație fără Gemini")
from nelutu_demo_budget import DemoBudget
if "nelutu_stage19_budget" not in st.session_state:
    st.session_state["nelutu_stage19_budget"] = DemoBudget()
stage19_budget = st.session_state["nelutu_stage19_budget"]
st.caption("Simulare locală: maximum trei încercări într-o sesiune. Nu transmite nimic către Google.")
st.write("Încercări disponibile:", stage19_budget.remaining())
if st.button("Etapa 19 — simulează un apel", disabled=not stage19_budget.allowed()):
    if stage19_budget.consume():
        st.success("Încercare înregistrată numai local.")
    else:
        st.warning("Limita demonstrativă a fost atinsă.")
if not stage19_budget.allowed():
    st.warning("Limită locală atinsă: simularea nu mai permite încercări.")
if st.button("Etapa 19 — resetează simularea"):
    stage19_budget.reset()
    st.info("Contorul demonstrativ a fost resetat.")
st.caption("Atenție: această simulare NU limitează încă butoanele Gemini din etapele anterioare și NU oferă protecție globală contra abuzului.")
