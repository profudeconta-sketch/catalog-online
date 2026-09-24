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

PINS = ['2951', '6234', '9233', '9385', '2681', '4658', '7891', '9975', '9042', '8226', '4931', '1041', '2322', '2814', '5706', '2606', '8367', '1188', '9032', '6148', '4444', '7508', '5120', '6696', '6843', '7166', '9414', '2250', '6577', '2469', '9815', '5786']

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
st.info("🔒 Acces securizat pentru părinți. Vă rugăm să vă autentificați mai jos cu Numărul Matricol și Codul PIN al elevului.")

# Zona de Autentificare
col_auth1, col_auth2 = st.columns(2)

with col_auth1:
    nr_matricol_input = st.text_input(
        "🔑 Număr Matricol (ex: 126/76 sau 13):",
        value="",
        placeholder="Exemplu: 126/76",
        help="Numărul matricol se găsește pe fișa de acces primită."
    ).strip()

with col_auth2:
    pin_input = st.text_input(
        "🔒 Cod PIN Confidențial (4 cifre):",
        value="",
        type="password",
        placeholder="Exemplu: 2951",
        help="Codul PIN de 4 cifre aflat pe biletul individual de acces."
    ).strip()

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

# Verificare elev pe bază de număr matricol și PIN
student_found = None
student_idx_found = -1

if nr_matricol_input:
    for idx, e in enumerate(ELEVI):
        if nr_matricol_input == str(e[2]) or nr_matricol_input == str(e[3]) or nr_matricol_input.lower() == str(e[3]).lower():
            # Verificare PIN dacă a fost introdus
            correct_pin = PINS[idx]
            if not pin_input:
                st.info("👉 Vă rugăm să introduceți și Codul PIN de 4 cifre.")
            elif pin_input == correct_pin:
                student_found = e
                student_idx_found = idx
            else:
                st.error("❌ Codul PIN introdus este incorect! Verificați biletul de acces.")
            break

if not nr_matricol_input:
    st.warning("👈 Vă rugăm să introduceți Numărul Matricol și Codul PIN mai sus.")
elif student_found:
    # Jurnalizare autentificare în Streamlit Logs (Metoda 1)
    log_key = f"logged_{student_found[3]}"
    if log_key not in st.session_state:
        st.session_state[log_key] = True
        now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        print(f"[{now_str}] 👨‍👩‍👧‍👦 LOGARE PĂRINTE REUȘITĂ: Elev: {student_found[1]} | Matricol: {student_found[3]}", flush=True)

    st.success(f"✅ Autentificare reușită pentru elevul: **{student_found[1]}** (Matricol {student_found[3]})")
    st.divider()

    if not os.path.exists(excel_path):
        st.error(f"Fișierul catalog '{excel_path}' nu a fost găsit.")
    else:
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            s_row = 9 + student_idx_found

            # Preluare sumare din Centralizator și Absențe
            ws_c = wb["Centralizator Medii"]
            ws_a = wb["Absențe & Purtare"]

            media_cg = safe_float_str(ws_c.cell(row=s_row, column=5).value)
            media_th = safe_float_str(ws_c.cell(row=s_row, column=6).value)
            media_gen = safe_float_str(ws_c.cell(row=s_row, column=7).value)
            nota_purtare = safe_str(ws_a.cell(row=s_row, column=8).value)
            abs_nem = safe_str(ws_a.cell(row=s_row, column=5).value)
            abs_mot = safe_str(ws_a.cell(row=s_row, column=6).value)
            abs_tot = safe_str(ws_a.cell(row=s_row, column=7).value)

            col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
            col_kpi1.metric("Media Cultură Gen.", media_cg)
            col_kpi2.metric("Media Module TH.", media_th)
            col_kpi3.metric("Media Generală", media_gen)
            col_kpi4.metric("Nota la Purtare", nota_purtare if nota_purtare else "10")
            col_kpi5.metric("Total Absențe", f"{abs_tot if abs_tot else '0'} ({abs_nem if abs_nem else '0'} nem.)")

            st.divider()

            # Tabel detaliat pe discipline
            for cat_title, sheet_n, sub_list in [("📚 DISCIPLINE CULTURĂ GENERALĂ", "Cultură Generală", DISCIPLINE_CG), ("⚙️ MODULE TEHNOLOGICE", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"#### {cat_title}")
                ws = wb[sheet_n]

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
                    for k in range(30):
                        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            absences.append(str(a_val))
                    media_val = ws.cell(row=s_row, column=start_col + 20).value
                    media_str = safe_float_str(media_val)

                    rows_data.append({
                        "Disciplină / Modul": s_name,
                        "Note & Date": ", ".join(notes) if notes else "Fără note",
                        "Absențe": ", ".join(absences) if absences else "Fără absențe",
                        "Medie": media_str
                    })
                st.dataframe(rows_data, use_container_width=True)

            wb.close()
        except Exception as ex:
            st.error(f"Eroare la încărcarea fișei elevului: {ex}")

st.markdown("---")
st.caption("🏫 Colegiul 'Emil Negruțiu' Turda — Sistem Școlar Securizat pentru Părinți | Date actualizate în timp real.")
