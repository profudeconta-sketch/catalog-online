import datetime
import os
import openpyxl
import streamlit as st
import urllib.request
import urllib.parse
import json
import base64

st.set_page_config(
    page_title="Portal Părinți - Catalog IX TH",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# --- FUNCTIE DE SINCRONIZARE SI DESCARCARE AUTOMATA EXCEL DIN GITHUB ---
def sync_excel_from_github():
    filename = "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
    ts = int(datetime.datetime.now().timestamp())
    raw_url = f"https://raw.githubusercontent.com/profudeconta-sketch/catalog-online/main/{filename}?t={ts}"
    
    token = os.environ.get("GITHUB_TOKEN") or st.secrets.get("GITHUB_TOKEN", "")
    headers = {"User-Agent": "StreamlitApp"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    try:
        req = urllib.request.Request(raw_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                content = resp.read()
                if len(content) > 2000:
                    with open(filename, "wb") as f:
                        f.write(content)
                    return filename
    except Exception:
        pass

    try:
        api_url = f"https://api.github.com/repos/profudeconta-sketch/catalog-online/contents/{filename}"
        req_api = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req_api, timeout=5) as resp:
            if resp.status == 200:
                res_json = json.loads(resp.read().decode('utf-8'))
                content_b64 = res_json.get('content', '')
                if content_b64:
                    binary_data = base64.b64encode(content_b64)
                    with open(filename, "wb") as f:
                        f.write(binary_data)
                    return filename
    except Exception:
        pass

    return filename

# Sincronizare la incarcarea portalului
sync_excel_from_github()

# Lista celor 32 de elevi (ID, Nume, Nr. Matr. Simplu, Nr. Matr. Registru/Complet, PIN Confidențial)
ELEVI = [
    (1, "ALBAC V. ALEXANDRU ANDREI", 13, "126/76", "2951"),
    (2, "BARA D. ADRIAN DANIEL", 14, "126/77", "6234"),
    (3, "BUDACĂ I. MARIA MADALINA", 15, "126/78", "9233"),
    (4, "BUDULĂU I.M. VLAD IOAN", 16, "126/79", "9385"),
    (5, "CHESZOVAN D.E. IRINA JULIETA", 17, "126/80", "2681"),
    (6, "CIURCUI V. DIANA", 18, "126/81", "4658"),
    (7, "CORDIȘ M.C. EDUARD IONUȚ", 19, "126/82", "7891"),
    (8, "DEMETER D.C. DENIS RĂZVAN", 20, "126/83", "9975"),
    (9, "FERENCZI E.C. MEDEA MARICARMEN", 21, "126/84", "9042"),
    (10, "FLOREA V. FLAVIU CRISTIAN", 22, "126/85", "8226"),
    (11, "GHERMAN M.I. DAVID MARIUS", 23, "126/86", "4931"),
    (12, "LOBONȚ M. MIHNEA", 24, "126/87", "1041"),
    (13, "LUKACS A.L. LORENA DENISA", 25, "126/88", "2322"),
    (14, "MAGYARI A.M. ANDREI", 26, "126/89", "2814"),
    (15, "MARCOVICI L.S. IOANA DENISA", 27, "126/90", "5706"),
    (16, "MARIAN M.I. MIHAELA DARIA", 28, "126/91", "2606"),
    (17, "MATEI V.C. ROXANA MIHAELA", 29, "126/92", "8367"),
    (18, "MENCU R.R. DIANA OLIVIA", 30, "126/93", "1188"),
    (19, "MUNTEANU V.N. ELENA", 31, "126/94", "9032"),
    (20, "NAP A.C. ALEXANDRA MARIA", 32, "126/95", "6148"),
    (21, "PETELEU C.A. CLAUDIA MARIA", 33, "126/96", "4444"),
    (22, "POP D. ANDRA MARIA", 34, "126/97", "7508"),
    (23, "POP M.V. LARISA ANDREEA", 35, "126/98", "5120"),
    (24, "POP I.C. ROBERT EUGEN", 36, "126/99", "6696"),
    (25, "POPA C.F. ILINCA", 37, "126/100", "6843"),
    (26, "PUICA G. GEORGE ROBERT", 38, "126/101", "7166"),
    (27, "RĂDUȚ I.M. ADELINA IOANA", 39, "128/1", "9414"),
    (28, "ȘIPOȘ T.R. DAVID ADRIAN", 40, "128/2", "2250"),
    (29, "TRIF S.D. TUȘA DANIEL", 41, "128/3", "6577"),
    (30, "TUȘINEAN S.V. IRINA", 42, "128/4", "2469"),
    (31, "ȚANDEA M. LUCAS MIHAI", 43, "128/5", "9815"),
    (32, "VRÎNCIANU M.G. DELIA MARIA", 44, "128/6", "5786")
]

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxZTSWP9ciRZ-gsFRzxFyLZ4TN-v4eeyNDAhIY8_bBi9z9y9fXI6TQBUIGNHINDhGYF/exec"

def log_parent_access(elev_nume, matricol):
    if "logged_students" not in st.session_state:
        st.session_state["logged_students"] = set()
    
    key = f"{elev_nume}_{matricol}"
    if key not in st.session_state["logged_students"]:
        st.session_state["logged_students"].add(key)
        try:
            params = urllib.parse.urlencode({"elev": elev_nume, "matricol": matricol})
            full_url = f"{WEBAPP_URL}?{params}"
            req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass

def find_excel_file():
    candidates = [
        "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "CATALOG/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "catalog_scolar_clasa_IX_TH_Turda-v14.xlsx",
        "/workspace/artifacts/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    try:
        for f in os.listdir("."):
            if f.endswith(".xlsx") and "catalog" in f.lower():
                return f
    except Exception:
        pass
    return "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

excel_path = find_excel_file()

st.title("🏫 Colegiul 'Emil Negruțiu' Turda")
st.subheader("👨‍👩‍👧‍👦 Portal Părinți — Vizualizare Fișă Școlară Elev (IX TH)")
st.info("🔒 Acces securizat pentru părinți. Vă rugăm să vă autentificați mai jos cu Numărul Matricol și Codul PIN confidențial primit de la diriginte.")

# Zona de Autentificare
col_auth1, col_auth2 = st.columns(2)

with col_auth1:
    nr_matricol_input = st.text_input(
        "🔑 Introduceți Numărul Matricol (ex: 126/76 sau 13):",
        value="",
        placeholder="Exemplu: 126/76",
        help="Numărul matricol se găsește pe carnetul de elev sau pe biletul individual de acces."
    ).strip()

with col_auth2:
    pin_input = st.text_input(
        "🔒 Introduceți Codul PIN Confidențial (4 cifre):",
        value="",
        type="password",
        placeholder="Exemplu: 2951",
        help="Codul PIN confidențial individual eliberat de către diriginte."
    ).strip()

matched_student = None
if nr_matricol_input:
    for student in ELEVI:
        if (nr_matricol_input == str(student[2]) or 
            nr_matricol_input == str(student[3]) or 
            nr_matricol_input.lower() == str(student[3]).lower()):
            matched_student = student
            break

if not nr_matricol_input:
    st.warning("👉 Vă rugăm să introduceți Numărul Matricol în caseta de mai sus pentru a afișa fișa elevului.")
elif matched_student is None:
    st.error("❌ Numărul Matricol introdus nu a fost găsit în baza de date a clasei a IX-a TH! Vă rugăm să verificați biletul de acces.")
elif not pin_input:
    st.info("🔑 Introduceți Codul PIN de 4 cifre transmis pe biletul individual de acces pentru a debloca fișa școlară.")
elif pin_input != str(matched_student[4]):
    st.error("❌ Codul PIN introdus este incorect! Vă rugăm să verificați codul PIN de 4 cifre de pe biletul de acces.")
else:
    # Autentificare completă cu succes
    idx_elev = matched_student[0] - 1
    st.success(f"✅ Autentificare securizată reușită pentru elevul: **{matched_student[1]}** (Matricol {matched_student[3]})")
    
    # Sincronizare fortata din GitHub la fiecare autentificare
    sync_excel_from_github()
    
    # Logare acces in Google Sheets
    log_parent_access(matched_student[1], matched_student[3])
    
    if os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            
            disc_cg = [
                ("Limba și literatura română", 8), ("Limba engleză (L1)", 61), ("Limba franceză (L2)", 114),
                ("Matematică", 167), ("Fizică", 220), ("Chimie", 273), ("Biologie", 326), ("Istorie", 379),
                ("Geografie", 432), ("Logică, argumentare și comunicare", 485), ("Informatică / TIC", 538),
                ("Educație fizică", 591), ("Religie", 644), ("Arte vizuale și educație plastică", 697)
            ]
            mod_th = [
                ("M1: Bazele contabilității", 8), ("M2: Etică și comunicare", 61), ("M3: Structuri de primire turistică", 114),
                ("M4: Procese și calitate în HoReCa", 167), ("M5: CDEOȘ (IP) - Instruire Practică", 220), ("M6: Curriculum de aprofundare și inserție profesională", 273)
            ]

            # Calcul medii si absente in timp real
            ws_cg = wb["Cultură Generală"]
            ws_th = wb["Module Tehnologice"]
            s_row = 9 + idx_elev
            
            cg_avgs = []
            abs_nem = 0
            abs_mot = 0
            
            for s_name, start_col in disc_cg:
                notes = []
                for k in range(10):
                    n_val = ws_cg.cell(row=s_row, column=start_col + (k * 2)).value
                    if n_val is not None and str(n_val).strip() != "" and not str(n_val).startswith("="):
                        try:
                            notes.append(float(n_val))
                        except Exception:
                            pass
                if notes:
                    cg_avgs.append(round(sum(notes)/len(notes), 2))
                for k in range(30):
                    a_val = ws_cg.cell(row=s_row, column=start_col + 21 + k).value
                    if a_val is not None and str(a_val).strip() != "" and not str(a_val).startswith("="):
                        s_a = str(a_val).strip()
                        if s_a.endswith('m') or s_a.endswith('M'):
                            abs_mot += 1
                        else:
                            abs_nem += 1
                            
            th_avgs = []
            for s_name, start_col in mod_th:
                notes = []
                for k in range(10):
                    n_val = ws_th.cell(row=s_row, column=start_col + (k * 2)).value
                    if n_val is not None and str(n_val).strip() != "" and not str(n_val).startswith("="):
                        try:
                            notes.append(float(n_val))
                        except Exception:
                            pass
                if notes:
                    th_avgs.append(round(sum(notes)/len(notes), 2))
                for k in range(30):
                    a_val = ws_th.cell(row=s_row, column=start_col + 21 + k).value
                    if a_val is not None and str(a_val).strip() != "" and not str(a_val).startswith("="):
                        s_a = str(a_val).strip()
                        if s_a.endswith('m') or s_a.endswith('M'):
                            abs_mot += 1
                        else:
                            abs_nem += 1

            med_cg = round(sum(cg_avgs)/len(cg_avgs), 2) if cg_avgs else None
            med_th = round(sum(th_avgs)/len(th_avgs), 2) if th_avgs else None
            
            if med_cg is not None and med_th is not None:
                med_gen = round((med_cg + med_th)/2.0, 2)
            elif med_cg is not None:
                med_gen = med_cg
            elif med_th is not None:
                med_gen = med_th
            else:
                med_gen = None
                
            purtare = max(1, 10 - int(abs_nem / 20))
            abs_tot = abs_nem + abs_mot

            def fmt_val(v):
                if isinstance(v, (int, float)):
                    return f"{float(v):.2f}"
                return str(v) if v else "-"

            # Carduri cu indicatori principali
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            m_col1.metric("Media Cultură Gen.", fmt_val(med_cg))
            m_col2.metric("Media Module TH.", fmt_val(med_th))
            m_col3.metric("Media Generală", fmt_val(med_gen))
            m_col4.metric("Nota la Purtare", str(purtare))
            m_col5.metric("Total Absențe", f"{abs_tot} ({abs_nem} nem. / {abs_mot} mot.)")

            st.markdown("---")

            # Situația detaliată pe discipline și module
            tab_cg, tab_th = st.tabs(["📚 Cultură Generală", "🛠️ Module Tehnologice"])

            for tab_obj, cat_title, ws, sub_list in [
                (tab_cg, "Cultură Generală", ws_cg, disc_cg),
                (tab_th, "Module Tehnologice", ws_th, mod_th)
            ]:
                with tab_obj:
                    rows_data = []

                    for s_name, start_col in sub_list:
                        notes = []
                        for k in range(10):
                            n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                            d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                            if n_val is not None and str(n_val).strip() != "" and not str(n_val).startswith("="):
                                d_str = f" ({d_val})" if d_val else ""
                                notes.append(f"{n_val}{d_str}")
                                
                        absences = []
                        for k in range(30):
                            a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                            if a_val is not None and str(a_val).strip() != "" and not str(a_val).startswith("="):
                                absences.append(str(a_val).strip())
                                        
                        sub_notes_float = []
                        for k in range(10):
                            nv = ws.cell(row=s_row, column=start_col + (k * 2)).value
                            if nv is not None and str(nv).strip() != "" and not str(nv).startswith("="):
                                try:
                                    sub_notes_float.append(float(nv))
                                except Exception:
                                    pass
                        media_str = f"{(sum(sub_notes_float)/len(sub_notes_float)):.2f}" if sub_notes_float else "-"

                        rows_data.append({
                            "Disciplină / Modul": s_name,
                            "Note & Date": ", ".join(notes) if notes else "Fără note",
                            "Absențe": ", ".join(absences) if absences else "Fără absențe",
                            "Medie": media_str
                        })

                    st.dataframe(rows_data, use_container_width=True, hide_index=True)

            wb.close()
        except Exception as ex:
            st.error(f"Eroare la încărcarea fișei elevului: {ex}")
    else:
        st.warning("⚠️ Baza de date a catalogului este momentan indisponibilă. Vă rugăm să reîncercați mai târziu.")

st.markdown("---")
st.caption("© 2026 Prof. Ec. Gherman Octavian-Theodor. Toate drepturile de autor rezervate.")
st.caption("🏫 Colegiul 'Emil Negruțiu' Turda — Sistem Școlar Securizat pentru Părinți | Date actualizate în timp real.")
