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

# Lista celor 32 de elevi
ELEVI = [
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

DISCIPLINE_CG_V15 = [
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

MODULE_TH_V15 = [
    ("M1: Bazele contabilității", 8),
    ("M2: Etică și comunicare", 61),
    ("M3: Structuri de primire turistică", 114),
    ("M4: Procese și calitate în HoReCa", 167),
    ("M5: CDEOȘ (IP) - Instruire Practică", 220),
    ("M6: Curriculum de aprofundare și inserție profesională", 273)
]

DISCIPLINE_CG_V14 = [
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

MODULE_TH_V14 = [
    ("M1: Bazele contabilității", 8),
    ("M2: Etică și comunicare", 29),
    ("M3: Structuri de primire turistică", 50),
    ("M4: Procese și calitate în HoReCa", 71),
    ("M5: CDEOȘ (IP) - Instruire Practică", 92),
    ("M6: Curriculum de aprofundare și inserție profesională", 113)
]

JSONBIN_URL = "https://api.jsonbin.io/v3/b/68d50fe2301f22312bd31d27"

def get_cloud_data():
    try:
        req = urllib.request.Request(JSONBIN_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res.get('record', {'grades': [], 'absences': []})
    except Exception:
        return {'grades': [], 'absences': []}

def find_excel_file():
    candidates = [
        "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "CATALOG/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "catalog_scolar_clasa_IX_TH_Turda-v14.xlsx",
        "CATALOG/catalog_scolar_clasa_IX_TH_Turda-v14.xlsx",
        "/workspace/artifacts/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

excel_path = find_excel_file()

st.title("🏫 Colegiul 'Emil Negruțiu' Turda")
st.subheader("👨‍👩‍👧‍👦 Portal Părinți — Vizualizare Fișă Școlară Elev (IX TH)")
st.info("🔒 Acces securizat pentru părinți. Vă rugăm să vă autentificați mai jos cu Numărul Matricol al elevului pentru a consulta situația școlară.")

# Zona de Autentificare
col_auth1, col_auth2 = st.columns([2, 1])

with col_auth1:
    nr_matricol_input = st.text_input(
        "🔑 Introduceți Numărul Matricol al elevului (ex: 126/76 sau numărul simplu 13):",
        value="",
        placeholder="Exemplu: 126/76",
        help="Numărul matricol se găsește pe carnetul de elev sau adeverința de înscriere."
    ).strip()

matched_student = None
if nr_matricol_input:
    for student in ELEVI:
        if nr_matricol_input.lower() == str(student[2]).lower() or nr_matricol_input.lower() == str(student[3]).lower():
            matched_student = student
            break

if not nr_matricol_input:
    st.warning("👉 Vă rugăm să introduceți Numărul Matricol în caseta de mai sus pentru a afișa fișa elevului.")
elif matched_student is None:
    st.error("❌ Numărul Matricol introdus nu a fost găsit în baza de date a clasei a IX-a TH! Vă rugăm să verificați carnetul elevului.")
else:
    idx_elev = matched_student[0] - 1
    st.success(f"✅ Autentificare reușită pentru elevul: **{matched_student[1]}** (Nr. Matricol: {matched_student[3]})")
    
    # Preia datele live din Cloud
    cloud_data = get_cloud_data()
    c_grades = cloud_data.get('grades', [])
    c_absences = cloud_data.get('absences', [])
    
    if os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            
            # Detectează dacă fișierul este v15 (53 col / materie) sau v14 (21 col / materie)
            ws_check = wb["Cultură Generală"]
            is_v15 = (ws_check.cell(row=7, column=28).value == "MEDIE" or ws_check.cell(row=7, column=18).value == "N6" or "v15" in excel_path)
            
            if is_v15:
                disc_cg = DISCIPLINE_CG_V15
                mod_th = MODULE_TH_V15
                max_notes = 10
                abs_offset = 21
                max_abs = 30
            else:
                disc_cg = DISCIPLINE_CG_V14
                mod_th = MODULE_TH_V14
                max_notes = 5
                abs_offset = 11
                max_abs = 8

            # Preluare date de sinteză din sheet-ul Absențe & Purtare
            abs_sheet = wb["Absențe & Purtare"]
            student_row_abs = 9 + idx_elev
            abs_nem = abs_sheet.cell(row=student_row_abs, column=5).value or 0
            abs_mot = abs_sheet.cell(row=student_row_abs, column=6).value or 0
            abs_tot = abs_sheet.cell(row=student_row_abs, column=7).value or 0
            purtare = abs_sheet.cell(row=student_row_abs, column=8).value or 10

            # Preluare medii din Centralizator
            cent_sheet = wb["Centralizator Medii"]
            student_row_cent = 9 + idx_elev
            med_cg = cent_sheet.cell(row=student_row_cent, column=5).value
            med_th = cent_sheet.cell(row=student_row_cent, column=6).value
            med_gen = cent_sheet.cell(row=student_row_cent, column=7).value

            def fmt_val(v):
                if isinstance(v, (int, float)):
                    return f"{float(v):.2f}"
                return str(v) if v else "-"

            # Carduri cu indicatori principali
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            m_col1.metric("Media Cultură Gen.", fmt_val(med_cg))
            m_col2.metric("Media Module TH", fmt_val(med_th))
            m_col3.metric("Media Generală", fmt_val(med_gen))
            m_col4.metric("Notă Purtare", f"{purtare:.0f}" if isinstance(purtare, (int, float)) else str(purtare))
            m_col5.metric("Total Absențe", f"{abs_tot} ({abs_nem} nem. / {abs_mot} mot.)")

            st.markdown("---")

            # Situația detaliată pe discipline și module
            tab_cg, tab_th = st.tabs(["📚 Cultură Generală", "🛠️ Module Tehnologice"])

            for tab_obj, cat_title, sheet_n, sub_list in [
                (tab_cg, "Cultură Generală", "Cultură Generală", disc_cg),
                (tab_th, "Module Tehnologice", "Module Tehnologice", mod_th)
            ]:
                with tab_obj:
                    ws = wb[sheet_n]
                    s_row = 9 + idx_elev
                    rows_data = []

                    for mat_idx, (s_name, start_col) in enumerate(sub_list):
                        notes = []
                        for k in range(max_notes):
                            n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                            d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                            if n_val is not None and str(n_val).strip() != "":
                                d_str = f" ({d_val})" if d_val else ""
                                notes.append(f"{n_val}{d_str}")
                        
                        # Adaugă notele noi transmise din Catalog în Cloud
                        for cg in c_grades:
                            if cg.get('student_idx') == idx_elev and cg.get('cat') == cat_title and cg.get('mat_idx') == mat_idx:
                                notes.append(f"{cg.get('nota')} ({cg.get('data')})")

                        absences = []
                        for k in range(max_abs):
                            a_val = ws.cell(row=s_row, column=start_col + abs_offset + k).value
                            if a_val is not None and str(a_val).strip() != "":
                                absences.append(str(a_val).strip())
                        
                        # Adaugă absențele noi transmise din Catalog în Cloud
                        for ca in c_absences:
                            if ca.get('student_idx') == idx_elev and ca.get('cat') == cat_title and ca.get('mat_idx') == mat_idx:
                                a_str = f"{ca.get('data')}{'m' if ca.get('is_mot') else ''}"
                                if a_str not in absences:
                                    absences.append(a_str)

                        media_val = ws.cell(row=s_row, column=start_col + (20 if is_v15 else 19)).value
                        media_str = fmt_val(media_val)

                        rows_data.append({
                            "Disciplină / Modul": s_name,
                            "Note Obtinute": ", ".join(notes) if notes else "Fără note înregistrate",
                            "Absențe Înregistrate": ", ".join(absences) if absences else "Fără absențe",
                            "Medie Actuală": media_str
                        })

                    st.dataframe(rows_data, use_container_width=True, hide_index=True)

            wb.close()
        except Exception as ex:
            st.error(f"Eroare la încărcarea datelor elevului: {ex}")
    else:
        st.warning("⚠️ Baza de date a catalogului este momentan indisponibilă.")

st.markdown("---")
st.caption("🏫 Colegiul 'Emil Negruțiu' Turda — Sistem Școlar Securizat pentru Părinți | Date actualizate în timp real.")
