import datetime
import os
import openpyxl
import streamlit as st

st.set_page_config(
    page_title="Portal Părinți - Catalog IX TH",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

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
        "/workspace/scratch/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

excel_path = find_excel_file()

def safe_str(val):
    if val is None:
        return ""
    return str(val).strip()

def safe_float_str(val):
    if val is None or str(val).strip() == "" or str(val).strip() == "-":
        return "-"
    try:
        return f"{float(val):.2f}"
    except Exception:
        return str(val).strip()

st.title("🏫 Colegiul 'Emil Negruțiu' Turda")
st.subheader("👨‍👩‍👧‍👦 Portal Părinți — Vizualizare Fișă Școlară Elev (IX TH)")
st.info("🔒 Acces securizat pentru părinți. Vă rugăm să vă autentificați mai jos cu Numărul Matricol al elevului pentru a consulta situația școlară.")

col_auth1, col_auth2 = st.columns([2, 1])

with col_auth1:
    nr_matricol_input = st.text_input(
        "🔑 Introduceți Numărul Matricol al elevului (ex: 126/76 sau numărul simplu 13):",
        value="",
        placeholder="Exemplu: 126/76",
        help="Numărul matricol se găsește pe carnetul de elev sau adeverința de înscriere."
    ).strip()

elev_gasit = None
elev_idx = -1

if nr_matricol_input:
    for idx, (e_id, nume, matr_simplu, matr_complet) in enumerate(ELEVI):
        if nr_matricol_input in (str(e_id), str(matr_simplu), str(matr_complet), f"Matr. {matr_simplu}"):
            elev_gasit = (e_id, nume, matr_simplu, matr_complet)
            elev_idx = idx
            break

if not nr_matricol_input:
    st.info("💡 Introduceți Numărul Matricol pentru a afișa situația școlară a copilului dumneavoastră.")
elif elev_gasit is None:
    st.error(f"❌ Numărul Matricol '{nr_matricol_input}' nu a fost găsit în baza de date a clasei a IX-a TH.")
else:
    st.success(f"✅ Autentificare reușită pentru elevul: **{elev_gasit[1]}** (Matricol {elev_gasit[3]})")
    
    if os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            s_row = 9 + elev_idx
            
            ws_c = wb["Centralizator Medii"]
            medie_cg = safe_float_str(ws_c.cell(row=s_row, column=5).value)
            medie_th = safe_float_str(ws_c.cell(row=s_row, column=6).value)
            medie_gen = safe_float_str(ws_c.cell(row=s_row, column=7).value)
            nota_purtare = safe_str(ws_c.cell(row=s_row, column=8).value)
            
            ws_abs = wb["Absențe & Purtare"]
            abs_nem = safe_str(ws_abs.cell(row=s_row, column=5).value)
            abs_mot = safe_str(ws_abs.cell(row=s_row, column=6).value)
            tot_abs = safe_str(ws_abs.cell(row=s_row, column=7).value)
            
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Media Cultură Gen.", medie_cg)
            m2.metric("Media Module TH.", medie_th)
            m3.metric("Media Generală", medie_gen)
            m4.metric("Notă Purtare", nota_purtare if nota_purtare else "10")
            m5.metric("Total Absențe", tot_abs if tot_abs else "0", delta=f"{abs_nem if abs_nem else '0'} nemotivate")
            
            st.divider()
            
            for cat_title, sheet_n, sub_list in [("📚 Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("⚙️ Module Tehnologice (HoReCa)", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"### {cat_title}")
                ws = wb[sheet_n]
                
                rows_data = []
                for s_name, start_col in sub_list:
                    notes = []
                    for k in range(10):
                        n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        if safe_str(n_val):
                            notes.append(safe_str(n_val))
                    absences = []
                    for k in range(30):
                        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                        if safe_str(a_val):
                            absences.append(safe_str(a_val))
                    media_val = ws.cell(row=s_row, column=start_col + 20).value
                    media_str = safe_float_str(media_val)
                    
                    rows_data.append({
                        "Disciplină / Modul": s_name,
                        "Note Obținute": ", ".join(notes) if notes else "Fără note",
                        "Absențe Înregistrate": ", ".join(absences) if absences else "Fără absențe",
                        "Medie Actuală": media_str
                    })
                st.dataframe(rows_data, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citirea fișei elevului: {ex}")
    else:
        st.warning("⚠️ Baza de date a catalogului este momentan indisponibilă.")
