import datetime
import os
import openpyxl
import streamlit as st

st.set_page_config(
    page_title="Portal Părinți - Catalog IX TH",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# Lista celor 32 de elevi (ID, Nume, Nr. Matr. Simplu, Nr. Matr. Registru/Complet)
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

def find_excel_file():
    candidates = [
        "catalog_scolar_clasa_IX_TH_Turda-v14.xlsx",
        "CATALOG/catalog_scolar_clasa_IX_TH_Turda-v14.xlsx",
        "/workspace/artifacts/catalog_scolar_clasa_IX_TH_Turda-v14.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "catalog_scolar_clasa_IX_TH_Turda-v14.xlsx"

excel_path = find_excel_file()

st.title("🏫 Colegiul 'Emil Negruțiu' Turda")
st.headline = st.subheader("👨‍👩‍👧‍👦 Portal Părinți — Vizualizare Fișă Școlară Elev (IX TH)")
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
        # Verificare potrivire nr. matricol complet (ex: 126/76) sau simplu (ex: 13)
        if nr_matricol_input.lower() == str(student[2]).lower() or nr_matricol_input.lower() == str(student[3]).lower():
            matched_student = student
            break

if not nr_matricol_input:
    st.warning("👉 Vă rugăm să introduceți Numărul Matricol în caseta de mai sus pentru a afișa fișa elevului.")
elif matched_student is None:
    st.error("❌ Numărul Matricol introdus nu a fost găsit în baza de date a clasei a IX-a TH! Vă rugăm să verificați carnetul elevului.")
else:
    # Elevul a fost identificat cu succes
    idx_elev = matched_student[0] - 1
    st.success(f"✅ Autentificare reușită pentru elevul: **{matched_student[1]}** (Nr. Matricol: {matched_student[3]})")
    
    if os.path.exists(excel_path):
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            
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
                (tab_cg, "Cultură Generală", "Cultură Generală", DISCIPLINE_CG),
                (tab_th, "Module Tehnologice", "Module Tehnologice", MODULE_TH)
            ]:
                with tab_obj:
                    ws = wb[sheet_n]
                    s_row = 9 + idx_elev
                    rows_data = []

                    for s_name, start_col in sub_list:
                        notes = []
                        for k in range(5):
                            n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                            if n_val is not None and str(n_val).strip() != "":
                                notes.append(str(n_val))
                        absences = []
                        for k in range(8):
                            a_val = ws.cell(row=s_row, column=start_col + 11 + k).value
                            if a_val is not None and str(a_val).strip() != "":
                                absences.append(str(a_val))
                        media_val = ws.cell(row=s_row, column=start_col + 19).value
                        media_str = f"{float(media_val):.2f}" if isinstance(media_val, (int, float)) else (str(media_val) if media_val else "-")

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
        st.warning("⚠️ Baza de date a catalogului este momentan indisponibilă. Vă rugăm să reîncercați mai târziu.")

st.markdown("---")
st.caption("🏫 Colegiul 'Emil Negruțiu' Turda — Sistem Școlar Securizat pentru Părinți | Date actualizate în timp real.")
