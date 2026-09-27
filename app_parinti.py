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

# CLOUD SYNC & LOGGING CONFIGURATION
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxZTSWP9ciRZ-gsFRzxFyLZ4TN-v4eeyNDAhIY8_bBi9z9y9fXI6TQBUIGNHINDhGYF/exec"
JSONBIN_URL = "https://api.jsonbin.io/v3/b/68d50fe2301f22312bd31d27"

def get_cloud_data():
    try:
        req = urllib.request.Request(JSONBIN_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res.get('record', {'grades': [], 'absences': []})
    except Exception:
        return {'grades': [], 'absences': []}

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

def render_copyright_footer():
    st.markdown("---")
    st.markdown(
        """**© Software Creat și Deținut de Prof. Ec. Gherman Octavian-Theodor**  
*Acest program este protejat de legea privind drepturile de autor (Legea nr. 8/1996) și legislația internațională aplicabilă.*  
*Orice descărcare, multiplicare, distribuire sau utilizare neautorizată se pedepsește conform legii.*  
**🚫 ESTE STRICT INTERZISĂ COMERCIALIZAREA ACESTUI PRODUS!**  
*Acest produs se utilizează în mod gratuit exclusiv de către persoanele cărora autorul le conferă în mod explicit acest drept.*""",
        unsafe_allow_html=True
    )

def render_sidebar_copyright():
    st.sidebar.divider()
    st.sidebar.markdown(
        """**© Prof. Ec. Gherman Octavian-Theodor**  
Drepturi de autor rezervate.  
Comercializarea interzisă.  
Utilizare gratuită doar cu acordul autorului.""",
        unsafe_allow_html=True
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
        "/workspace/artifacts/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

excel_path = find_excel_file()

st.title("🏫 Colegiul 'Emil Negruțiu' Turda")
st.subheader("👨‍👩‍👧‍👦 Portal Părinți — Vizualizare Fișă Școlară Elev (IX TH)")
st.info("🔒 Acces securizat pentru părinți. Vă rugăm să vă autentificați mai jos cu Numărul Matricol și Codul PIN confidențial al elevului.")

with st.sidebar:
    st.header("ℹ️ Portal Părinți")
    st.info("Accesul este securizat și individualizat pentru fiecare elev.")
    render_sidebar_copyright()

# Formular Autentificare Părinte
col_auth1, col_auth2 = st.columns(2)

with col_auth1:
    nr_matricol_input = st.text_input(
        "🔑 Număr Matricol Elev (ex: 126/76 sau 13):",
        value="",
        placeholder="Exemplu: 126/76",
        help="Numărul matricol se găsește pe carnetul de elev sau adeverința de înscriere."
    ).strip()

with col_auth2:
    pin_input = st.text_input(
        "🔐 Cod PIN Confidențial (4 cifre):",
        value="",
        type="password",
        placeholder="Exemplu: 2951",
        help="Codul PIN confidențial transmis de către diriginte."
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

def compute_student_subject_data(ws, s_row, start_col, cat_title, mat_idx, s_idx, c_grades, c_absences):
    notes = []
    notes_num = []
    for k in range(10):
        n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
        d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
        if n_val is not None and str(n_val).strip() != "":
            d_str = f" ({d_val})" if d_val else ""
            notes.append(f"{n_val}{d_str}")
            try:
                notes_num.append(float(n_val))
            except Exception:
                pass

    for cg in c_grades:
        if cg.get('student_idx') == s_idx and cg.get('cat') == cat_title and cg.get('mat_idx') == mat_idx:
            n_item = f"{cg.get('nota')} ({cg.get('data')})"
            if n_item not in notes:
                notes.append(n_item)
                try:
                    notes_num.append(float(cg.get('nota')))
                except Exception:
                    pass

    absences = []
    for k in range(30):
        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
        if a_val is not None and str(a_val).strip() != "":
            absences.append(str(a_val).strip())

    for ca in c_absences:
        if ca.get('student_idx') == s_idx and ca.get('cat') == cat_title and ca.get('mat_idx') == mat_idx:
            a_str = f"{ca.get('data')}{'m' if ca.get('is_mot') else ''}"
            if a_str not in absences:
                absences.append(a_str)

    avg = (sum(notes_num) / len(notes_num)) if notes_num else None

    if avg is None:
        m_excel = ws.cell(row=s_row, column=start_col + 20).value
        if m_excel is not None and str(m_excel).strip() != "":
            try:
                avg = float(m_excel)
            except Exception:
                pass

    return notes, absences, avg

def compute_all_student_summary(wb, s_idx, c_grades, c_absences):
    s_row = 9 + s_idx
    ws_cg = wb["Cultură Generală"]
    ws_th = wb["Module Tehnologice"]
    ws_abs = wb["Absențe & Purtare"]
    ws_cent = wb["Centralizator Medii"]

    cg_avgs = []
    all_absences = []

    for mat_idx, (s_name, start_col) in enumerate(DISCIPLINE_CG):
        _, abs_list, avg = compute_student_subject_data(ws_cg, s_row, start_col, "Cultură Generală", mat_idx, s_idx, c_grades, c_absences)
        if avg is not None:
            cg_avgs.append(avg)
        all_absences.extend(abs_list)

    th_avgs = []
    for mat_idx, (s_name, start_col) in enumerate(MODULE_TH):
        _, abs_list, avg = compute_student_subject_data(ws_th, s_row, start_col, "Module Tehnologice", mat_idx, s_idx, c_grades, c_absences)
        if avg is not None:
            th_avgs.append(avg)
        all_absences.extend(abs_list)

    med_cg = (sum(cg_avgs) / len(cg_avgs)) if cg_avgs else None
    med_th = (sum(th_avgs) / len(th_avgs)) if th_avgs else None

    if med_cg is not None and med_th is not None:
        med_gen = (med_cg + med_th) / 2.0
    elif med_cg is not None:
        med_gen = med_cg
    elif med_th is not None:
        med_gen = med_th
    else:
        med_gen = None

    purtare = ws_abs.cell(row=s_row, column=8).value
    if purtare is None or str(purtare).strip() == "":
        purtare = 10

    total_abs = len(all_absences)
    mot_abs = sum(1 for a in all_absences if str(a).endswith('m'))
    nem_abs = total_abs - mot_abs

    if total_abs == 0:
        a_nem_ex = ws_abs.cell(row=s_row, column=5).value or 0
        a_mot_ex = ws_abs.cell(row=s_row, column=6).value or 0
        a_tot_ex = ws_abs.cell(row=s_row, column=7).value or 0
        try:
            total_abs = int(a_tot_ex)
            nem_abs = int(a_nem_ex)
            mot_abs = int(a_mot_ex)
        except Exception:
            pass

    if med_cg is None:
        m_cg_ex = ws_cent.cell(row=s_row, column=5).value
        if m_cg_ex is not None:
            try: med_cg = float(m_cg_ex)
            except Exception: pass

    if med_th is None:
        m_th_ex = ws_cent.cell(row=s_row, column=6).value
        if m_th_ex is not None:
            try: med_th = float(m_th_ex)
            except Exception: pass

    if med_gen is None:
        m_gen_ex = ws_cent.cell(row=s_row, column=7).value
        if m_gen_ex is not None:
            try: med_gen = float(m_gen_ex)
            except Exception: pass

    return {
        'med_cg': med_cg,
        'med_th': med_th,
        'med_gen': med_gen,
        'purtare': purtare,
        'total_abs': total_abs,
        'nem_abs': nem_abs,
        'mot_abs': mot_abs
    }

# Verificare elev și PIN
student_found = None
s_idx_matched = None
expected_pin = None

if nr_matricol_input:
    for idx, e in enumerate(ELEVI):
        if nr_matricol_input == str(e[0]) or nr_matricol_input == str(e[2]) or nr_matricol_input.lower() == str(e[3]).lower():
            student_found = e
            s_idx_matched = idx
            expected_pin = PINS[idx]
            break

if not nr_matricol_input or not pin_input:
    st.warning("👈 Vă rugăm să completați atât Numărul Matricol, cât și Codul PIN confidențial de mai sus.")
    render_copyright_footer()
elif not student_found:
    st.error("❌ Nu s-a găsit niciun elev cu acest Număr Matricol. Verificați carnetul elevului și încercați din nou.")
    render_copyright_footer()
elif pin_input != expected_pin:
    st.error("❌ Codul PIN introdus este incorect pentru acest elev! Vă rugăm să verificați codul transmis de diriginte.")
    render_copyright_footer()
else:
    st.success(f"✅ Autentificare reușită pentru elevul: **{student_found[1]}** (Matricol {student_found[3]})")
    log_parent_access(student_found[1], student_found[3])
    st.divider()

    if not os.path.exists(excel_path):
        st.error(f"Fișierul catalog '{excel_path}' nu a fost găsit.")
    else:
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            
            # Cloud data live sync
            cloud_data = get_cloud_data()
            c_grades = cloud_data.get('grades', [])
            c_absences = cloud_data.get('absences', [])

            sum_d = compute_all_student_summary(wb, s_idx_matched, c_grades, c_absences)

            media_cg = safe_float_str(sum_d['med_cg'])
            media_th = safe_float_str(sum_d['med_th'])
            media_gen = safe_float_str(sum_d['med_gen'])
            nota_purtare = str(sum_d['purtare'])
            abs_tot = f"{sum_d['total_abs']} ({sum_d['nem_abs']} nem. / {sum_d['mot_abs']} mot.)"

            col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
            col_kpi1.metric("Media Cultură Gen.", media_cg)
            col_kpi2.metric("Media Module TH.", media_th)
            col_kpi3.metric("Media Generală", media_gen)
            col_kpi4.metric("Nota la Purtare", nota_purtare)
            col_kpi5.metric("Total Absențe", abs_tot)

            st.divider()

            # Tabel detaliat pe discipline
            for cat_title, sheet_n, sub_list in [("📚 DISCIPLINE CULTURĂ GENERALĂ", "Cultură Generală", DISCIPLINE_CG), ("⚙️ MODULE TEHNOLOGICE", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"#### {cat_title}")
                ws = wb[sheet_n]
                rows_data = []
                
                cat_clean = "Cultură Generală" if "CULTURĂ" in cat_title else "Module Tehnologice"
                for mat_idx, (s_name, start_col) in enumerate(sub_list):
                    notes, absences, avg_val = compute_student_subject_data(ws, 9 + s_idx_matched, start_col, cat_clean, mat_idx, s_idx_matched, c_grades, c_absences)
                    media_str = safe_float_str(avg_val)

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

    render_copyright_footer()
