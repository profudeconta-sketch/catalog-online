import datetime
import os
import openpyxl
import streamlit as st
import urllib.request
import urllib.parse
import json
import base64

from document_storage import DOCUMENT_CATEGORIES, SCHOLARSHIP_TYPES, DocumentStorageError, build_document_record, store_new_document, parent_excuse_usage, validate_parent_excuse_hours, register_transmitted_parent_excuse, find_parent_excuse_document, list_student_documents, read_registered_document, register_first_school_document_access
from parent_excuse_pdf import generate_parent_excuse_pdf

st.set_page_config(
    page_title="Portal Părinți - Catalog IX TH",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxf-chEeMc6pA02EU0-pwqMTVp8htzzku6TvX5Uhea_nqqCNEcT3D6RYrmke1n0tAwD/exec"

def _atomic_replace_bytes(filename, content, validator):
    base, ext = os.path.splitext(filename)
    temp = base + ".download" + ext
    try:
        with open(temp, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        validator(temp)
        os.replace(temp, filename)
        return filename
    except Exception:
        try:
            if os.path.exists(temp):
                os.remove(temp)
        except Exception:
            pass
        raise

def _validate_excel(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
    try:
        required = {"Centralizator Medii", "Cultură Generală", "Module Tehnologice", "Absențe & Purtare"}
        missing = required.difference(wb.sheetnames)
        if missing:
            raise ValueError("Fișier Excel incomplet.")
    finally:
        wb.close()

def _validate_gestiune(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("Fișierul de gestiune este gol sau invalid.")
    for row in data:
        if not isinstance(row, dict) or not {"id", "rand_excel", "matricol", "pin"}.issubset(row):
            raise ValueError("Structură invalidă în fișierul de gestiune.")

# --- FUNCTIE DE SINCRONIZARE SI DESCARCARE AUTOMATA EXCEL DIN GITHUB ---
def sync_excel_from_github():
    filename = "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

    token = os.environ.get("GITHUB_TOKEN") or ""

    try:
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or str(st.secrets["GITHUB_TOKEN"])
    except Exception:
        pass

    if not token:
        return False

    api_url = (
        "https://api.github.com/repos/"
        "profudeconta-sketch/catalog-online-date-private/"
        f"contents/{filename}?ref=main"
    )

    headers = {
        "User-Agent": "StreamlitApp",
        "Cache-Control": "no-cache",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)

        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return False

            payload = json.loads(resp.read().decode("utf-8"))

        content_b64 = payload.get("content", "")

        if not content_b64:
            return False

        content = base64.b64decode(content_b64)

        return _atomic_replace_bytes(
            filename,
            content,
            _validate_excel
        )

    except Exception:
        return False

# Sincronizare la incarcarea portalului
sync_excel_from_github()

GESTIUNE_FILE = "gestiune_elevi.json"

def sync_gestiune_from_github():
    filename = GESTIUNE_FILE

    token = os.environ.get("GITHUB_TOKEN") or ""

    try:
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or str(st.secrets["GITHUB_TOKEN"])
    except Exception:
        pass

    if not token:
        return False

    api_url = (
        "https://api.github.com/repos/"
        "profudeconta-sketch/catalog-online-date-private/"
        f"contents/{filename}?ref=main"
    )

    headers = {
        "User-Agent": "StreamlitApp",
        "Cache-Control": "no-cache",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    temp_file = filename + ".download.tmp"

    try:
        req = urllib.request.Request(api_url, headers=headers)

        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return False

            payload = json.loads(resp.read().decode("utf-8"))

        content_b64 = payload.get("content", "")

        if not content_b64:
            return False

        content = base64.b64decode(content_b64)

        with open(temp_file, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        _validate_gestiune(temp_file)

        os.replace(temp_file, filename)
        return True

    except Exception:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass

        return False
        
try:
    sync_gestiune_from_github()
except Exception:
    pass

def get_current_elevi_parinti():
    if os.path.exists(GESTIUNE_FILE):
        try:
            with open(GESTIUNE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    elevi_list = []
                    for d in data:
                        nume_full = d.get("nume_complet", f"{d.get('nume','')} {d.get('initiala','')} {d.get('prenume','')}".strip())
                        nume_full = " ".join(nume_full.split())
                        elevi_list.append((
                            d["id"],
                            nume_full,
                            d["rand_excel"],
                            d["matricol"],
                            str(d.get("pin", "1234")),
                            str(d.get("status_scolar", "ACTIV")).upper()
                        ))
                    return elevi_list
        except Exception:
            pass
    st.error(
        "Datele elevilor nu au putut fi încărcate din sursa privată. "
        "Portalul părinților a fost oprit pentru protejarea datelor."
    )
    st.stop()


def get_authenticated_student_details(student_rm_pg):
    target = str(student_rm_pg or "").strip().casefold()
    if not target:
        raise ValueError("RM/PG lipseste pentru elevul autentificat.")
    if not os.path.exists(GESTIUNE_FILE):
        raise ValueError("Datele administrative ale elevului nu sunt disponibile.")
    with open(GESTIUNE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    matches = [
        d for d in data
        if str(d.get("matricol", "")).strip().casefold() == target
    ]
    if len(matches) != 1:
        raise ValueError("Datele administrative ale elevului nu pot fi identificate unic.")
    d = matches[0]
    address_parts = [
        d.get("strada", ""),
        d.get("numar_strada", ""),
        d.get("bloc", ""),
        d.get("apartament", ""),
        d.get("localitate", ""),
        d.get("judet", ""),
    ]
    return {
        "nume_complet": str(d.get("nume_complet", "")).strip(),
        "nr_matr": str(d.get("rand_excel", "")).strip(),
        "rm_pg": str(d.get("matricol", "")).strip(),
        "nume_mama": str(d.get("nume_mama", "")).strip(),
        "nume_tata": str(d.get("nume_tata", "")).strip(),
        "adresa": ", ".join(str(value).strip() for value in address_parts if str(value).strip()),
    }


# Lista celor 32 de elevi (ID, Nume, RM/PG, Nr. Matr., PIN)


ELEVI = get_current_elevi_parinti()
DISCIPLINE_CG = [
    ("Limba și literatura română", 8),
    ("Limba engleză (L1)", 61),
    ("Limba franceză (L2)", 114),
    ("Matematică", 167),
    ("Fizică", 220),
    ("Chimie", 273),
    ("Biologie", 326),
    ("Istorie", 379),
    ("Geografie", 432),
    ("Logică, argumentare și comunicare", 485),
    ("Informatică / TIC", 538),
    ("Educație fizică", 591),
    ("Religie", 644),
    ("Arte vizuale și educație plastică", 697)
]

MODULE_TH = [
    ("M1: Bazele contabilității", 8),
    ("M2: Etică și comunicare", 61),
    ("M3: Structuri de primire turistică", 114),
    ("M4: Procese și calitate în HoReCa", 167),
    ("M5: CDEOȘ (IP) - Instruire Practică", 220),
    ("M6: Curriculum de aprofundare și inserție profesională", 273)
]

def find_excel_file():
    candidates = [
        "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "CATALOG/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "/workspace/artifacts/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "/workspace/out/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

excel_path = find_excel_file()

st.title("🏫 Colegiul 'Emil Negruțiu' Turda")
st.subheader("👨‍👩‍👧‍👦 Portal Părinți — Vizualizare Fișă Școlară Elev (IX TH)")
st.info("🔒 Acces securizat pentru părinți. Vă rugăm să vă autentificați mai jos cu Numărul Matricol și Codul PIN confidențial primit de la diriginte.")

col_auth1, col_auth2 = st.columns(2)

with col_auth1:
    nr_matricol_input = st.text_input(
        "🔑 Introduceți Numărul Matricol:",
        value="",
        placeholder="Introduceți numărul matricol",
        help="Numărul matricol se găsește pe carnetul de elev sau adeverința de înscriere."
    ).strip()

with col_auth2:
    pin_input = st.text_input(
        "🔒 Introduceți Codul PIN Confidențial (4 cifre):",
        value="",
        type="password",
        placeholder="Introduceți codul PIN",
        help="Codul PIN confidențial individual eliberat de către diriginte."
    ).strip()

def safe_str(val):
    if val is None:
        return ""
    return str(val).strip()


def resolve_student_row(wb, elev_info):
    """Rezolvă rândul elevului exclusiv prin RM/PG și verifică toate foile sursă."""
    required = ("Cultură Generală", "Module Tehnologice", "Absențe & Purtare", "Centralizator Medii")
    missing = [name for name in required if name not in wb.sheetnames]
    if missing:
        raise RuntimeError("Catalog incompatibil v15: lipsesc foi obligatorii.")

    expected_rm = str(elev_info[3]).strip()
    if not expected_rm:
        raise RuntimeError("RM/PG lipsește pentru elevul selectat.")

    rows = []
    for sheet_name in required:
        ws = wb[sheet_name]
        matches = [
            row for row in range(9, ws.max_row + 1)
            if str(ws.cell(row=row, column=4).value or "").strip().lower() == expected_rm.lower()
        ]
        if len(matches) != 1:
            raise RuntimeError(
                f"RM/PG trebuie să apară exact o dată în foaia {sheet_name}; "
                "afișarea a fost blocată pentru protecția datelor."
            )
        rows.append(matches[0])

    if len(set(rows)) != 1:
        raise RuntimeError("Rândul elevului nu este consistent între foile catalogului.")
    return rows[0]


def safe_float_str(val):
    if val is None or val == "":
        return "-"
    try:
        return f"{float(val):.2f}"
    except Exception:
        return str(val)

student_found = None
pin_correct = False

if nr_matricol_input:
    for e in ELEVI:
        if nr_matricol_input == str(e[2]) or nr_matricol_input == str(e[3]) or nr_matricol_input.lower() == str(e[3]).lower():
            student_found = e
            if pin_input and pin_input == str(e[4]):
                pin_correct = True
            break

if not nr_matricol_input or not pin_input:
    st.warning("👈 Vă rugăm să completați atât Numărul Matricol, cât și Codul PIN confidențial de mai sus.")
elif not student_found:
    st.error("❌ Nu s-a găsit niciun elev cu acest Număr Matricol. Verificați carnetul elevului și încercați din nou.")
elif not pin_correct:
    st.error("❌ Cod PIN incorect pentru acest elev! Vă rugăm să verificați biletul confidențial primit de la diriginte.")
else:
    status_scolar = str(student_found[5] if len(student_found) > 5 else "ACTIV").upper()
    if status_scolar in ("TRANSFERAT", "RETRAS"):
        st.warning(
            f"ℹ️ Elev {status_scolar}. Situația școlară afișată este păstrată pentru consultarea "
            "istoricului existent."
        )

    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
       st.success(
        f"✅ Autentificare securizată reușită pentru elevul:"
        f" **{student_found[1]}** (Matricol {student_found[3]})"
    )

    # --- ÎNREGISTRARE CONECTARE ÎN GOOGLE SHEETS (O SINGURĂ DATĂ PER SESIUNE) ---
    if "logged_to_sheet" not in st.session_state:
      st.session_state["logged_to_sheet"] = False

    if not st.session_state["logged_to_sheet"]:
      import requests

      try:
        nume_e = requests.utils.quote(str(student_found[1]))
        matr_e = requests.utils.quote(str(student_found[3]))
        url_call = f"{WEBAPP_URL}?elev={nume_e}&matricol={matr_e}"

        res = requests.get(url_call, timeout=8)

        if "SUCCESS_LOGGED" in res.text:
          st.session_state["logged_to_sheet"] = True
          st.toast(
              "✅ Autentificarea a fost înregistrată în Google Sheet!", icon="📊"
          )
        else:
          st.warning(
              "⚠️ Răspuns Google: "
              + (res.text[:100] if res.text else "Niciun răspuns")
          )
      except Exception as err:
        st.warning(f"⚠️ Eroare conectare Google Sheet: {err}")

    with col_hdr2:
      if st.button(
          "🔄 Actualizează Datele", use_container_width=True, type="primary"
      ):
        sync_excel_from_github()
        st.rerun()

    st.divider()

    try:
        school_documents = list_student_documents(
            student_found[3],
            direction="SCOALA_PARINTE",
        )
        unread_school_documents = [
            item for item in school_documents
            if not item.get("first_accessed_at_utc")
        ]

        if unread_school_documents:
            st.markdown(
                """
                <style>
                @keyframes schoolNoticePulse {
                    0% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0.55); }
                    70% { box-shadow: 0 0 0 12px rgba(255, 75, 75, 0); }
                    100% { box-shadow: 0 0 0 0 rgba(255, 75, 75, 0); }
                }
                div[data-testid="stExpander"]:has(.school-notice-marker) {
                    border: 2px solid #ff4b4b;
                    border-radius: 0.5rem;
                    animation: schoolNoticePulse 1.8s infinite;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

        notice_title = (
            f"🔔 Înștiințări de la școală — {len(unread_school_documents)} document(e) nou(i)"
            if unread_school_documents
            else "🔔 Înștiințări de la școală"
        )
        with st.expander(notice_title, expanded=bool(unread_school_documents)):
            if unread_school_documents:
                st.markdown(
                    '<span class="school-notice-marker"></span>',
                    unsafe_allow_html=True,
                )
            if not school_documents:
                st.info("Nu există înștiințări sau documente transmise de școală.")
            else:
                school_type_labels = {
                    "INSTIINTARE": "Înștiințare",
                    "DOCUMENT_SCOALA": "Document transmis de școală",
                }
                selected_school_document_id = st.selectbox(
                    "Selectați documentul:",
                    [item["id"] for item in school_documents],
                    format_func=lambda doc_id: next(
                        (
                            f"{'🔔 NOU — ' if not item.get('first_accessed_at_utc') else '✅ '}"
                            f"{school_type_labels.get(item.get('document_type'), item.get('document_type'))} — "
                            f"{item.get('original_filename')}"
                        )
                        for item in school_documents
                        if item["id"] == doc_id
                    ),
                    key="parent_school_document_select",
                )
                selected_school_document = next(
                    item for item in school_documents
                    if item["id"] == selected_school_document_id
                )

                if selected_school_document.get("first_accessed_at_utc"):
                    st.success(
                        "✅ Acest document a fost deja accesat prin contul autentificat "
                        "aferent elevului."
                    )
                else:
                    st.warning(
                        "🔔 Document nou de la școală. Confirmarea de primire și luare la "
                        "cunoștință va fi înregistrată numai când apăsați butonul de mai jos."
                    )

                access_key = f"school_document_access_{student_found[3]}_{selected_school_document_id}"
                if st.button(
                    "📄 Deschide documentul și confirmă luarea la cunoștință",
                    type="primary" if not selected_school_document.get("first_accessed_at_utc") else "secondary",
                    use_container_width=True,
                    key=f"open_{access_key}",
                ):
                    try:
                        access_was_new = False
                        if not selected_school_document.get("first_accessed_at_utc"):
                            access_result = register_first_school_document_access(
                                student_rm_pg=student_found[3],
                                student_name=student_found[1],
                                document_id=selected_school_document_id,
                            )
                            access_was_new = bool(access_result.get("created"))
                        verified_meta, verified_content = read_registered_document(
                            student_found[3],
                            selected_school_document_id,
                        )
                        st.session_state[access_key] = {
                            "document_id": selected_school_document_id,
                            "filename": verified_meta.get("original_filename", "document"),
                            "mime_type": verified_meta.get("mime_type", "application/octet-stream"),
                            "content": verified_content,
                        }
                        if access_was_new:
                            st.success(
                                "✅ Documentul a fost accesat. Confirmarea de primire și luare "
                                "la cunoștință a fost înregistrată automat."
                            )
                        elif not selected_school_document.get("first_accessed_at_utc"):
                            st.info(
                                "ℹ️ Prima accesare era deja înregistrată în sistem. "
                                "Documentul poate fi consultat în continuare."
                            )
                    except DocumentStorageError as ex:
                        st.session_state.pop(access_key, None)
                        st.error(
                            f"Documentul nu poate fi accesat sau confirmat în siguranță: {ex}"
                        )

                opened_document = st.session_state.get(access_key)
                if (
                    opened_document
                    and opened_document.get("document_id") == selected_school_document_id
                ):
                    st.download_button(
                        "📥 Descarcă documentul de la școală",
                        data=opened_document["content"],
                        file_name=opened_document["filename"],
                        mime=opened_document["mime_type"],
                        use_container_width=True,
                        key=f"download_{access_key}",
                    )
    except DocumentStorageError as ex:
        st.error(f"Înștiințările de la școală nu pot fi încărcate în siguranță: {ex}")

    st.divider()

    with st.expander("📁 Încarcă Documente și Solicitări Către Școală", expanded=False):
        st.caption(
            "Selectați secțiunea corespunzătoare documentului sau solicitării pe care doriți "
            "să o transmiteți către școală pentru elevul autentificat."
        )

        type_labels = {
            "CARTE_IDENTITATE": "Carte de identitate",
            "DOVADA_ADRESA": "Dovadă adresă",
            "CERTIFICAT_NASTERE": "Certificat de naștere",
            "DIVERSE": "Diverse",
            "SCUTIRE_MEDICALA": "Scutire medicală",
            "CERERE_BURSA": "Cerere bursă",
            "ACORD_PRELUCRARE_DATE": "Acord prelucrare date",
            "DECLARATIE_VENITURI_NETE_IMPOZABILE": "Declarație venituri nete impozabile",
            "DOCUMENTE_MEDICALE": "Documente medicale",
            "CI_PARINTE_TUTORE": "CI părinte / tutore",
            "CERTIFICATE_NASTERE_FRATI_SURORI": "Certificate naștere frați / surori",
            "CERTIFICAT_CASATORIE_PARINTI": "Certificat căsătorie părinți",
            "HOTARARE_SENTINTA_DIVORT": "Hotărâre / sentință divorț",
            "CERTIFICAT_DECES_PARINTE": "Certificat deces părinte",
            "ALTE_DOCUMENTE_JUSTIFICATIVE": "Alte documente justificative",
        }

        def render_document_upload(category, key_prefix, scholarship_type=None):
            document_types = sorted(DOCUMENT_CATEGORIES[category])
            document_type = st.selectbox(
                "Tipul documentului",
                document_types,
                format_func=lambda value: type_labels.get(value, value),
                key=f"{key_prefix}_type",
            )
            uploaded_document = st.file_uploader(
                "Selectează documentul (PDF, JPG/JPEG sau PNG)",
                type=["pdf", "jpg", "jpeg", "png"],
                accept_multiple_files=False,
                key=f"{key_prefix}_upload",
            )
            send_document = st.button(
                "📤 Salvează și trimite",
                use_container_width=True,
                key=f"{key_prefix}_send",
            )
            if send_document and uploaded_document is None:
                st.warning("Selectați mai întâi documentul care trebuie transmis.")
            elif send_document:
                try:
                    record, validated_bytes = build_document_record(
                        student_rm_pg=student_found[3],
                        direction="PARINTE_SCOALA",
                        category=category,
                        document_type=document_type,
                        original_filename=uploaded_document.name,
                        mime_type=uploaded_document.type,
                        content=uploaded_document.getvalue(),
                        school_year="2026-2027",
                        scholarship_type=scholarship_type,
                        sender_role="PARINTE_REPREZENTANT",
                        recipient_role="DIRIGINTE",
                    )
                    store_new_document(record, validated_bytes)
                    st.success(
                        "✅ Documentul a fost salvat și înregistrat. Transmiterea a fost confirmată."
                    )
                except (ValueError, DocumentStorageError) as ex:
                    st.error(f"❌ Documentul nu a fost transmis: {ex}")
                except Exception:
                    st.error("❌ Eroare neașteptată. Documentul nu este considerat transmis.")

        tab_personal, tab_medical, tab_scholarship, tab_excuse = st.tabs(
            [
                "👤 Dosar personal",
                "🏥 Scutiri medicale",
                "🎓 Dosar bursă",
                "📝 Motivare absențe părinte",
            ]
        )

        with tab_personal:
            st.markdown("#### Dosar personal")
            st.caption("Selectați tipul documentului pe care doriți să îl încărcați.")
            render_document_upload("DOSAR_PERSONAL", "doc_personal")

        with tab_medical:
            st.markdown("#### Scutiri medicale")
            st.caption("Încărcați scutirea medicală pe care doriți să o transmiteți dirigintelui.")
            render_document_upload("SCUTIRE_MEDICALA", "doc_medical")

        with tab_scholarship:
            st.markdown("#### Dosar bursă")
            st.caption(
                "Selectați tipul bursei, apoi tipul documentului pe care doriți să îl încărcați."
            )
            scholarship_tabs = st.tabs(
                [
                    "🏅 Merit",
                    "💰 Socială – venit",
                    "👨‍👩‍👧 Socială – orfan",
                    "🏥 Socială – medicală",
                    "👩‍🍼 Mame minore",
                    "♿ CES",
                ]
            )
            scholarship_types = [
                "MERIT",
                "SOCIALA_VENIT",
                "SOCIALA_ORFAN",
                "SOCIALA_MEDICALA",
                "SOCIALA_MAME_MINORE",
                "CES",
            ]
            scholarship_keys = [
                "merit",
                "sociala_venit",
                "sociala_orfan",
                "sociala_medicala",
                "mame_minore",
                "ces",
            ]
            for scholarship_tab, scholarship_type, scholarship_key in zip(
                scholarship_tabs, scholarship_types, scholarship_keys
            ):
                with scholarship_tab:
                    render_document_upload(
                        "DOSAR_BURSA",
                        f"doc_bursa_{scholarship_key}",
                        scholarship_type=scholarship_type,
                    )

        with tab_excuse:
            try:
                excuse_student = get_authenticated_student_details(student_found[3])
                excuse_usage = parent_excuse_usage(student_found[3], "2026-2027")

                st.metric(
                    "Ore disponibile pentru cereri în anul școlar 2026-2027",
                    f"{excuse_usage['remaining_hours']} / {excuse_usage['annual_limit']}",
                )

                parent_options = []
                if excuse_student["nume_mama"]:
                    parent_options.append((excuse_student["nume_mama"], "Părinte"))
                if excuse_student["nume_tata"]:
                    parent_options.append((excuse_student["nume_tata"], "Părinte"))

                if not parent_options:
                    st.warning(
                        "Nu există încă un părinte/reprezentant legal înregistrat pentru acest elev. "
                        "Contactați dirigintele pentru actualizarea datelor."
                    )
                else:
                    selected_parent = st.selectbox(
                        "Persoana care transmite cererea:",
                        parent_options,
                        format_func=lambda item: f"{item[0]} — {item[1]}",
                        key="excuse_parent",
                    )

                    st.text_input(
                        "Elev:",
                        value=excuse_student["nume_complet"] or student_found[1],
                        disabled=True,
                        key="excuse_student_name",
                    )
                    st.text_input(
                        "Adresa elevului:",
                        value=excuse_student["adresa"],
                        disabled=True,
                        key="excuse_address",
                    )
                    st.text_input(
                        "NR. MATR.:",
                        value=excuse_student["nr_matr"],
                        disabled=True,
                        key="excuse_nr_matr",
                    )
                    st.date_input(
                        "Data absenței:",
                        value=datetime.date.today(),
                        max_value=datetime.date.today(),
                        key="excuse_absence_date",
                    )
                    st.number_input(
                        "Numărul de ore absente în ziua selectată:",
                        min_value=1,
                        max_value=max(1, excuse_usage["remaining_hours"]),
                        value=1,
                        step=1,
                        key="excuse_hours",
                    )

                    st.caption(
                        "Cererea va fi considerată depusă la diriginte numai după confirmarea "
                        "generării, salvării și transmiterii documentului."
                    )
                    preview_excuse = st.button(
                        "📄 Generează previzualizare PDF",
                        use_container_width=True,
                        key="excuse_generate_preview",
                    )
                    if preview_excuse:
                        try:
                            preview_pdf = generate_parent_excuse_pdf(
                                parent_name=selected_parent[0],
                                parent_role=selected_parent[1],
                                student_name=excuse_student["nume_complet"] or student_found[1],
                                student_address=excuse_student["adresa"],
                                nr_matr=excuse_student["nr_matr"],
                                absence_date=st.session_state["excuse_absence_date"],
                                hours=st.session_state["excuse_hours"],
                            )
                            st.session_state["excuse_preview_pdf"] = preview_pdf
                        except ValueError as ex:
                            st.error(f"PDF-ul nu poate fi generat: {ex}")

                    if st.session_state.get("excuse_preview_pdf"):
                        st.download_button(
                            "📥 Descarcă previzualizarea PDF",
                            data=st.session_state["excuse_preview_pdf"],
                            file_name="Scutire_Motivare_Absente_PREVIZUALIZARE.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                            key="excuse_download_preview",
                        )
                        st.info(
                            "Previzualizarea nu este transmisă dirigintelui și nu consumă ore "
                            "din plafonul anual."
                        )

                    send_excuse = st.button(
                        "📨 Generează, salvează și trimite",
                        use_container_width=True,
                        type="primary",
                        key="excuse_send_preview",
                    )
                    if send_excuse:
                        try:
                            absence_date = st.session_state["excuse_absence_date"]
                            requested_hours = st.session_state["excuse_hours"]
                            validate_parent_excuse_hours(student_found[3], "2026-2027", requested_hours)
                            final_pdf = generate_parent_excuse_pdf(
                                parent_name=selected_parent[0],
                                parent_role=selected_parent[1],
                                student_name=excuse_student["nume_complet"] or student_found[1],
                                student_address=excuse_student["adresa"],
                                nr_matr=excuse_student["nr_matr"],
                                absence_date=absence_date,
                                hours=requested_hours,
                            )
                            record, validated_pdf = build_document_record(
                                student_rm_pg=student_found[3],
                                direction="PARINTE_SCOALA",
                                category="MOTIVARE_PARINTE",
                                document_type="MOTIVARE_ABSENTE_PARINTE",
                                original_filename=f"Scutire_Motivare_Absente_{absence_date.isoformat()}.pdf",
                                mime_type="application/pdf",
                                content=final_pdf,
                                school_year="2026-2027",
                                sender_role="PARINTE_REPREZENTANT",
                                recipient_role="DIRIGINTE",
                            )
                            existing_record = find_parent_excuse_document(
                                student_found[3], "2026-2027", record["sha256"]
                            )
                            if existing_record is None:
                                store_new_document(record, validated_pdf)
                            else:
                                record = existing_record
                            register_transmitted_parent_excuse(
                                student_rm_pg=student_found[3],
                                school_year="2026-2027",
                                absence_date=absence_date.isoformat(),
                                hours=requested_hours,
                                document_id=record["id"],
                                parent_name=selected_parent[0],
                            )
                            st.session_state.pop("excuse_preview_pdf", None)
                            st.success(
                                "✅ Cererea a fost transmisă cu succes dirigintelui și este considerată depusă. "
                                "Nu este necesar să prezentați la școală aceeași cerere în format tipărit."
                            )
                        except (ValueError, DocumentStorageError) as ex:
                            st.error(f"❌ Cererea nu este considerată transmisă: {ex}")
                        except Exception:
                            st.error("❌ Eroare neașteptată. Cererea nu este considerată transmisă.")
            except (ValueError, DocumentStorageError) as ex:
                st.error(f"Formularul de motivare nu poate fi încărcat: {ex}")

    if not os.path.exists(excel_path):
        st.error(f"Fișierul catalog '{excel_path}' nu a fost găsit.")
    else:
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            ws_cg = wb["Cultură Generală"]
            ws_th = wb["Module Tehnologice"]
            
            # Recalculare statistici si clasamente pentru toti elevii din clasa
            all_mgs = []
            all_abs = []
            student_specific_data = None

            for e_item in ELEVI:
                r_row = resolve_student_row(wb, e_item)
                
                c_avgs = []
                t_nem = 0
                t_mot = 0
                
                for _, c_col in DISCIPLINE_CG:
                    nts = []
                    for k in range(10):
                        nv = ws_cg.cell(row=r_row, column=c_col + (k * 2)).value
                        if nv is not None and str(nv).strip() != "":
                            try: nts.append(float(nv))
                            except Exception: pass
                    if nts: c_avgs.append(round(sum(nts)/len(nts), 2))
                    
                    for k in range(30):
                        av = ws_cg.cell(row=r_row, column=c_col + 21 + k).value
                        if av is not None and str(av).strip() != "":
                            sa = str(av).strip()
                            if sa.endswith('m') or sa.endswith('M'): t_mot += 1
                            else: t_nem += 1
                            
                h_avgs = []
                for _, c_col in MODULE_TH:
                    nts = []
                    for k in range(10):
                        nv = ws_th.cell(row=r_row, column=c_col + (k * 2)).value
                        if nv is not None and str(nv).strip() != "":
                            try: nts.append(float(nv))
                            except Exception: pass
                    if nts: h_avgs.append(round(sum(nts)/len(nts), 2))
                    
                    for k in range(30):
                        av = ws_th.cell(row=r_row, column=c_col + 21 + k).value
                        if av is not None and str(av).strip() != "":
                            sa = str(av).strip()
                            if sa.endswith('m') or sa.endswith('M'): t_mot += 1
                            else: t_nem += 1

                mcg_val = round(sum(c_avgs)/len(c_avgs), 2) if c_avgs else None
                mth_val = round(sum(h_avgs)/len(h_avgs), 2) if h_avgs else None
                
                if mcg_val is not None and mth_val is not None: mg_val = round((mcg_val + mth_val)/2.0, 2)
                elif mcg_val is not None: mg_val = mcg_val
                elif mth_val is not None: mg_val = mth_val
                else: mg_val = None
                    
                tot_abs_val = t_nem + t_mot
                all_mgs.append((e_item[3], mg_val))
                all_abs.append((e_item[3], tot_abs_val, t_nem))
                
                if str(e_item[3]).strip().lower() == str(student_found[3]).strip().lower():
                    purtare_val = max(1, 10 - int(t_nem / 20))
                    student_specific_data = {
                        'mcg': mcg_val,
                        'mth': mth_val,
                        'mg': mg_val,
                        'purtare': purtare_val,
                        'tot_abs': tot_abs_val,
                        'abs_nem': t_nem,
                        'abs_mot': t_mot
                    }

            # Clasament medii
            valid_mgs_list = sorted([m[1] for m in all_mgs if m[1] is not None], reverse=True)
            if student_specific_data['mg'] is not None and valid_mgs_list:
                rank_mg_str = f"Locul {valid_mgs_list.index(student_specific_data['mg']) + 1} din {len(ELEVI)}"
            else:
                rank_mg_str = "Fără medie generală"

            # Clasament absente
            sorted_abs_list = sorted([a[1] for a in all_abs], reverse=True)
            rank_abs_num = sorted_abs_list.index(student_specific_data['tot_abs']) + 1
            rank_abs_str = f"Locul {rank_abs_num} din {len(ELEVI)}"

            col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
            col_kpi1.metric("Media Cultură Gen.", safe_float_str(student_specific_data['mcg']))
            col_kpi2.metric("Media Module TH.", safe_float_str(student_specific_data['mth']))
            col_kpi3.metric("Media Generală", safe_float_str(student_specific_data['mg']), help=rank_mg_str)
            col_kpi4.metric("Nota la Purtare", str(student_specific_data['purtare']))
            col_kpi5.metric("Total Absențe", f"{student_specific_data['tot_abs']} ({student_specific_data['abs_nem']} nem. / {student_specific_data['abs_mot']} mot.)", help=rank_abs_str)

            st.info(f"🏆 **Poziție Școlară Elev în Clasă**: **{rank_mg_str}** în clasamentul mediilor generale | **{rank_abs_str}** în clasamentul numărului de absențe ({student_specific_data['tot_abs']} absențe din care {student_specific_data['abs_nem']} nemotivate).")

            st.divider()

            s_row = resolve_student_row(wb, student_found)

            for cat_title, ws, sub_list in [("📚 DISCIPLINE CULTURĂ GENERALĂ", ws_cg, DISCIPLINE_CG), ("⚙️ MODULE TEHNOLOGICE", ws_th, MODULE_TH)]:
                st.markdown(f"#### {cat_title}")

                rows_data = []
                for s_name, start_col in sub_list:
                    notes = []
                    for k in range(10):
                        n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                        if n_val is not None and str(n_val).strip() != "":
                            d_str = f" ({d_val})" if d_val else ""
                            notes.append(f"{n_val}{d_str}")
                            
                    absences = []
                    sub_nem = 0
                    sub_mot = 0
                    for k in range(30):
                        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            s_a = str(a_val).strip()
                            absences.append(s_a)
                            if s_a.endswith('m') or s_a.endswith('M'): sub_mot += 1
                            else: sub_nem += 1
                            
                    sub_tot = sub_nem + sub_mot
                    abs_str_formatted = f"{sub_tot} total ({sub_nem} nem. / {sub_mot} mot.) — Date: {', '.join(absences)}" if sub_tot > 0 else "Fără absențe (0)"

                    sub_notes_float = []
                    for k in range(10):
                        nv = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        if nv is not None and str(nv).strip() != "":
                            try:
                                sub_notes_float.append(float(nv))
                            except Exception:
                                pass
                    media_str = f"{(sum(sub_notes_float)/len(sub_notes_float)):.2f}" if sub_notes_float else "-"

                    rows_data.append({
                        "Disciplină / Modul": s_name,
                        "Note Obtinute": ", ".join(notes) if notes else "Fără note înregistrate",
                        "Absențe Înregistrate (Total / Nem / Mot)": abs_str_formatted,
                        "Medie Actuală": media_str
                    })
                st.dataframe(rows_data, use_container_width=True, hide_index=True)

            wb.close()
        except Exception as ex:
            st.error(f"Eroare la încărcarea fișei elevului: {ex}")

st.markdown("---")
st.caption("© 2026 Prof. Ec. Gherman Octavian-Theodor. Toate drepturile de autor rezervate.")
st.caption("🏫 Colegiul 'Emil Negruțiu' Turda — Sistem Școlar Securizat pentru Părinți | Date actualizate în timp real.")
