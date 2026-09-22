import datetime
import os
import openpyxl
import streamlit as st

st.set_page_config(
    page_title="Portal Părinți — Catalog IX TH",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# Safe string conversion helpers
def safe_str(val):
    if val is None:
        return ""
    return str(val).strip()

def safe_float_str(val):
    if val is None or val == "":
        return "-"
    try:
        return f"{float(val):.2f}"
    except Exception:
        return str(val)

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
        "catalog_scolar_clasa_IX_TH_Turda-v14.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

excel_path = find_excel_file()

st.title("🏫 Colegiul 'Emil Negruțiu' Turda")
st.subheader("👨‍👩‍👧‍👦 Portal Părinți — Vizualizare Fișă Școlară Elev (IX TH)")
st.info("🔒 Acces securizat pentru părinți. Vă rugăm să vă autentificați cu Numărul Matricol al elevului pentru a consulta situația școlară.")

col_auth1, col_auth2 = st.columns([2, 1])

with col_auth1:
    nr_matricol_input = st.text_input(
        "🔑 Introduceți Numărul Matricol al elevului (ex: 126/76 sau numărul simplu 13):",
        value="",
        placeholder="Exemplu: 126/76",
        help="Numărul matricol se găsește pe carnetul de elev sau adeverința de înscriere."
    ).strip()

found_student = None
student_idx = -1

if nr_matricol_input:
    for idx, (nr_ord, nume, nr_matr_s, nr_matr_reg) in enumerate(ELEVI):
        if (nr_matricol_input.lower() == safe_str(nr_matr_reg).lower() or 
            nr_matricol_input == safe_str(nr_matr_s) or 
            nr_matricol_input == safe_str(nr_ord)):
            found_student = ELEVI[idx]
            student_idx = idx
            break

if not nr_matricol_input:
    st.warning("👈 Introduceți numărul matricol mai sus pentru a vizualiza datele elevului.")
    st.stop()

if not found_student:
    st.error("❌ Nu s-a găsit niciun elev cu acest număr matricol! Verificați numărul și încercați din nou.")
    st.stop()

st.success(f"✅ Autentificat cu succes pentru elevul: **{found_student[1]}** (Matricol: {found_student[3]})")
st.divider()

if not os.path.exists(excel_path):
    st.warning(f"⚠️ Fișierul catalog '{excel_path}' nu a fost găsit.")
    st.stop()

try:
    wb = openpyxl.load_workbook(excel_path, data_only=True)
    s_row = 9 + student_idx
    
    # 1. Preluare indicatori din Centralizator Medii
    ws_cent = wb["Centralizator Medii"]
    med_cg = safe_float_str(ws_cent.cell(row=s_row, column=5).value)
    med_th = safe_float_str(ws_cent.cell(row=s_row, column=6).value)
    med_gen = safe_float_str(ws_cent.cell(row=s_row, column=7).value)
    nota_purtare = safe_str(ws_cent.cell(row=s_row, column=8).value) or "10"
    statut = safe_str(ws_cent.cell(row=s_row, column=9).value) or "Promovat"
    
    ws_abs = wb["Absențe & Purtare"]
    abs_nem = safe_str(ws_abs.cell(row=s_row, column=5).value) or "0"
    abs_mot = safe_str(ws_abs.cell(row=s_row, column=6).value) or "0"
    abs_tot = safe_str(ws_abs.cell(row=s_row, column=7).value) or "0"
    
    # Carduri Vizuale sintetice
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Media Cultură Gen.", med_cg)
    m2.metric("Media Module TH", med_th)
    m3.metric("Media Generală", med_gen)
    m4.metric("Notă Purtare", nota_purtare)
    m5.metric("Total Absențe", f"{abs_tot} ({abs_nem} nemot / {abs_mot} mot)")
    
    st.divider()
    
    # Tabele detaliate per categorie
    for cat_title, sheet_n, sub_list in [
        ("📚 DISCIPLINE CULTURĂ GENERALĂ", "Cultură Generală", DISCIPLINE_CG),
        ("🏨 MODULE TEHNOLOGICE (HORECA / TURISM)", "Module Tehnologice", MODULE_TH)
    ]:
        st.subheader(cat_title)
        ws = wb[sheet_n]
        
        rows_data = []
        for s_name, start_col in sub_list:
            notes_with_dates = []
            for k in range(10):
                n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                if n_val is not None and safe_str(n_val) != "":
                    d_str = f" ({safe_str(d_val)})" if d_val else ""
                    notes_with_dates.append(f"{safe_str(n_val)}{d_str}")
            
            absences_list = []
            for k in range(30):
                a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                if a_val is not None and safe_str(a_val) != "":
                    absences_list.append(safe_str(a_val))
            
            media_val = ws.cell(row=s_row, column=start_col + 20).value
            media_str = safe_float_str(media_val)
            
            rows_data.append({
                "Disciplină / Modul": s_name,
                "Note Acoardate (Data)": ", ".join(notes_with_dates) if notes_with_dates else "Fără note",
                "Absențe Înregistrate": ", ".join(absences_list) if absences_list else "Fără absențe",
                "Medie Semestrială / Anuală": media_str
            })
        st.dataframe(rows_data, use_container_width=True)
        
    wb.close()
except Exception as ex:
    st.error(f"Eroare la citirea datelor elevului: {ex}")
