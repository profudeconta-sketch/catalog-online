import datetime
import os
import openpyxl
import streamlit as st
import urllib.request
import urllib.parse
import json

st.set_page_config(
    page_title="Portal Părinți - Catalog IX TH",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# Lista implicită a celor 32 de elevi
ELEVI_DEFAULT = [
    (1, "ALBAC V. ALEXANDRU ANDREI", 13, "126/76"),
    (2, "BARA D. ADRIAN DANIEL", 14, "126/77"),
    (3, "BUDACĂ I. MARIA MADALINA", 15, "126/78"),
    (4, "BUDULĂU I.M. VLAD IOAN", 16, "126/79"),
    (5, "CHESZOVAN D.E. IRINA JULIETA", 17, "126/80"),
    (6, "CIURCUI V. DIANA", 18, "126/81"),
    (7, "CORDIȘ M.C. EDUARD IONUȚ", 19, "126/82"),
    (8, "DEMETER D.C. DENIS RĂZVAN", 20, "126/83"),
    (9, "FERENCZI E.C. MEDEA MARICARMEN", 21, "126/84"),
    (10, "FLOREA V. FLAVIU CRISTIAN", 22, "126/85"),
    (11, "GHERMAN M.I. DAVID MARIUS", 23, "126/86"),
    (12, "LOBONȚ M. MIHNEA", 24, "126/87"),
    (13, "LUKACS A.L. LORENA DENISA", 25, "126/88"),
    (14, "MAGYARI A.M. ANDREI", 26, "126/89"),
    (15, "MARCOVICI L.S. IOANA DENISA", 27, "126/90"),
    (16, "MARIAN M.I. MIHAELA DARIA", 28, "126/91"),
    (17, "MATEI V.C. ROXANA MIHAELA", 29, "126/92"),
    (18, "MENCU R.R. DIANA OLIVIA", 30, "126/93"),
    (19, "MUNTEANU V.N. ELENA", 31, "126/94"),
    (20, "NAP A.C. ALEXANDRA MARIA", 32, "126/95"),
    (21, "PETELEU C.A. CLAUDIA MARIA", 33, "126/96"),
    (22, "POP D. ANDRA MARIA", 34, "126/97"),
    (23, "POP M.V. LARISA ANDREEA", 35, "126/98"),
    (24, "POP I.C. ROBERT EUGEN", 36, "126/99"),
    (25, "POPA C.F. ILINCA", 37, "126/100"),
    (26, "PUICA G. GEORGE ROBERT", 38, "126/101"),
    (27, "RĂDUȚ I.M. ADELINA IOANA", 39, "128/1"),
    (28, "ȘIPOȘ T.R. DAVID ADRIAN", 40, "128/2"),
    (29, "TRIF S.D. TUȘA DANIEL", 41, "128/3"),
    (30, "TUȘINEAN S.V. IRINA", 42, "128/4"),
    (31, "ȚANDEA M. LUCAS MIHAI", 43, "128/5"),
    (32, "VRÎNCIANU M.G. DELIA MARIA", 44, "128/6")
]

ELEVI = list(ELEVI_DEFAULT)

if os.path.exists("gestiune_elevi.json"):
    try:
        with open("gestiune_elevi.json", "r", encoding="utf-8") as f:
            g_data = json.load(f)
        if g_data:
            ELEVI = [(s["id"], s["nume_complet"], s["rand_excel"], s["matricol"]) for s in g_data]
    except Exception: pass

DISCIPLINE_CG = [
    ("Limba și literatura română", 8),
    ("Limba engleză (L1)", 29),
    ("Limba franceză (L2)", 50),
    ("Matematică", 71),
    ("Fizică", 92),
    ("Chimie", 113),
    ("Biologie", 134),
    ("Istorie", 155),
    ("Geografie", 176),
    ("Logică, argumentare și comunicare", 197),
    ("Informatică / TIC", 218),
    ("Educație fizică", 239),
    ("Religie", 260),
    ("Arte vizuale și educație plastică", 281)
]

MODULE_TH = [
    ("M1: Bazele contabilității", 8),
    ("M2: Etică și comunicare", 29),
    ("M3: Structuri de primire turistică", 50),
    ("M4: Procese și calitate în HoReCa", 71),
    ("M5: CDEOȘ (IP) - Instruire Practică", 92),
    ("M6: Curriculum de aprofundare și inserție profesională", 113)
]

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxf-chEeMc6pA02EU0-pwqMTVp8htzzku6TvX5Uhea_nqqCNEcT3D6RYrmke1n0tAwD/exec"

def find_excel_file():
    candidates = [
        "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "CATALOG/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "/workspace/artifacts/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

def sync_excel_from_github():
    url = "https://raw.githubusercontent.com/profudeconta-sketch/catalog-online/main/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
    target_path = find_excel_file()
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                with open(target_path, "wb") as f:
                    f.write(response.read())
                return True
    except Exception:
        pass
    return False

excel_file = find_excel_file()

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "student_idx" not in st.session_state:
    st.session_state["student_idx"] = None

def safe_float_str(val):
    if val is None or val == "": return "-"
    try: return f"{float(val):.2f}"
    except Exception: return str(val)

if not st.session_state["authenticated"]:
    st.title("👨‍👩‍👧‍👦 Portal Părinți & Elevi — Catalog IX TH")
    st.caption("Colegiul 'Emil Negruțiu' Turda | Acces Securizat Foaie Școlară Individuală")
    
    sync_excel_from_github()
    
    with st.form("login_form"):
        col_matr, col_pin = st.columns(2)
        with col_matr:
            matricol_input = st.text_input("🆔 Număr Matricol Elev:", placeholder="Ex: 126/76 sau 13").strip()
        with col_pin:
            pin_input = st.text_input("🔑 Cod PIN Confidențial Părinte:", type="password", placeholder="Cod din 4 cifre").strip()
            
        submit_btn = st.form_submit_button("🔓 Autentificare Părinte", type="primary", use_container_width=True)
        
        if submit_btn:
            if not matricol_input or not pin_input:
                st.warning("⚠️ Vă rugăm să introduceți atât numărul matricol, cât și codul PIN!")
            elif os.path.exists(excel_file):
                try:
                    wb = openpyxl.load_workbook(excel_file, data_only=True)
                    matched_idx = None
                    student_found = None
                    
                    for idx, e in enumerate(ELEVI):
                        matr_registru = str(e[3]).strip()
                        matr_simplu = str(e[2]).strip()
                        
                        if matricol_input.lower() in [matr_registru.lower(), matr_simplu.lower()]:
                            student_found = e
                            matched_idx = idx
                            break
                            
                    if student_found is not None:
                        pin_correct = False
                        if "Centralizator Medii" in wb.sheetnames:
                            ws_cent = wb["Centralizator Medii"]
                            s_row = 9 + matched_idx
                            pin_val = ws_cent.cell(row=s_row, column=13).value
                            if pin_val and str(pin_val).strip() == pin_input:
                                pin_correct = True
                                
                        if not pin_correct and pin_input == PINS_DEFAULT[matched_idx] if matched_idx < len(PINS_DEFAULT) else False:
                            pin_correct = True
                            
                        if pin_correct:
                            st.session_state["authenticated"] = True
                            st.session_state["student_idx"] = matched_idx
                            st.success(f"✅ Autentificare securizată reușită pentru elevul: **{student_found[1]}** (Matricol {student_found[3]})")
                            
                            # Log connection to Google Sheet
                            if "logged_to_sheet" not in st.session_state:
                                st.session_state["logged_to_sheet"] = False
                                
                            if not st.session_state["logged_to_sheet"]:
                                import requests
                                try:
                                    nume_e = requests.utils.quote(str(student_found[1]))
                                    matr_e = requests.utils.quote(str(student_found[3]))
                                    url_call = f"{WEBAPP_URL}?elev={nume_e}&matricol={matr_e}"
                                    res = requests.get(url_call, timeout=8)
                                    if "SUCCESS_LOGGED" in res.text or "OK" in res.text:
                                        st.session_state["logged_to_sheet"] = True
                                        st.toast("✅ Acces înregistrat cu succes în Google Sheet!", icon="📊")
                                except Exception: pass
                                
                            st.rerun()
                        else:
                            st.error("❌ Codul PIN introdus este incorect pentru numărul matricol specificat!")
                    else:
                        st.error("❌ Numărul matricol introdus nu a fost găsit în baza de date a clasei!")
                    wb.close()
                except Exception as ex:
                    st.error(f"Eroare la procesare autentificare: {ex}")
            else:
                st.error("❌ Baza de date a catalogului nu este disponibilă momentan.")

    st.markdown("---")
    st.markdown("""
    **© Software Creat și Deținut de Prof. Ec. Gherman Octavian-Theodor**  
    *Acest program este protejat de legea privind drepturile de autor (Legea nr. 8/1996) și legislația internațională aplicabilă.*  
    **🚫 ESTE STRICT INTERZISĂ COMERCIALIZAREA ACESTUI PRODUS!**
    """)
    st.stop()

# --- VIZUALIZARE BAZĂ DE DATE ELEV AUTENTIFICAT ---
e_idx = st.session_state["student_idx"]
e_info = ELEVI[e_idx]

col_hdr1, col_hdr2 = st.columns([3, 1])
with col_hdr1:
    st.title(f"👤 {e_info[1]}")
    st.caption(f"Colegiul 'Emil Negruțiu' Turda | Clasa a IX-a TH — Turism și Alimentație | Matricol {e_info[3]}")
with col_hdr2:
    st.write("")
    if st.button("🚪 Deconectare (Logout)", use_container_width=True, type="secondary"):
        st.session_state["authenticated"] = False
        st.session_state["student_idx"] = None
        st.rerun()

if st.button("🔄 Actualizează Datele", use_container_width=True, type="primary"):
    sync_excel_from_github()
    st.toast("🔄 Datele catalogului au fost reîmprospătate de pe GitHub!")
    st.rerun()

st.divider()

if os.path.exists(excel_file):
    try:
        wb = openpyxl.load_workbook(excel_file, data_only=True)
        s_row = 9 + e_idx
        
        col_mg1, col_mg2, col_mg3, col_mg4 = st.columns(4)
        mcg_val = None; mth_val = None; mg_val = None; purt_val = 10
        
        if "Centralizator Medii" in wb.sheetnames:
            ws_c = wb["Centralizator Medii"]
            mcg_val = ws_c.cell(row=s_row, column=5).value
            mth_val = ws_c.cell(row=s_row, column=6).value
            mg_val = ws_c.cell(row=s_row, column=7).value
            purt_val = ws_c.cell(row=s_row, column=8).value
            
        col_mg1.metric("Media Cultură Generală", safe_float_str(mcg_val))
        col_mg2.metric("Media Module Tehnologice", safe_float_str(mth_val))
        col_mg3.metric("Media Generală Clasă", safe_float_str(mg_val))
        col_mg4.metric("Nota la Purtare", str(purt_val) if purt_val is not None else "10")
        
        st.divider()
        
        for cat_title, sheet_n, sub_list in [("📚 Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("⚙️ Module Tehnologice", "Module Tehnologice", MODULE_TH)]:
            st.subheader(cat_title)
            ws = wb[sheet_n]
            
            rows_display = []
            for s_name, start_col in sub_list:
                notes = []
                for k in range(10):
                    n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                    d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                    if n_val is not None and str(n_val).strip() != "":
                        d_str = f" ({d_val})" if d_val else ""
                        notes.append(f"**{n_val}**{d_str}")
                
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
                
                media_val = ws.cell(row=s_row, column=start_col + 20).value
                media_str = safe_float_str(media_val)
                
                rows_display.append({
                    "Disciplină / Modul": s_name,
                    "Note & Date Obtinerii": ", ".join(notes) if notes else "Fără note înregistrate",
                    "Evidență Absențe": abs_str_formatted,
                    "Medie Semestrială": media_str
                })
            st.dataframe(rows_display, use_container_width=True, hide_index=True)
        wb.close()
    except Exception as ex:
        st.error(f"Eroare la încărcare fișă elev: {ex}")

st.divider()
st.caption("**© Prof. Ec. Gherman Octavian-Theodor** | Sistem Securizat de Consultare Catalog Școlar")
