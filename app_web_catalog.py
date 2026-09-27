import datetime
import os
import openpyxl
import streamlit as st
import urllib.request
import urllib.parse
import json
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

st.set_page_config(
    page_title="Catalog Școlar Online IX TH",
    page_icon="🏫",
    layout="wide"
)

PAROLA_PROFESORI = "profesori2026"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown("## 🔒 Conectare Catalog Profesori")
    st.caption("Colegiul 'Emil Negruțiu' Turda — Clasa a IX-a TH Turism")
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        parola_input = st.text_input("🔑 Introduceți Parola de Acces:", type="password", key="pass_input")
        if st.button("🔓 Autentificare", type="primary", use_container_width=True):
            if parola_input == PAROLA_PROFESORI:
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("❌ Parolă incorectă! Vă rugăm să încercați din nou.")
    st.stop()

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

JSONBIN_URL = "https://api.jsonbin.io/v3/b/68d50fe2301f22312bd31d27"

def get_cloud_data():
    try:
        req = urllib.request.Request(JSONBIN_URL, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            return res.get('record', {'grades': [], 'absences': []})
    except Exception:
        return {'grades': [], 'absences': []}

def save_cloud_data(data):
    try:
        req_data = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(JSONBIN_URL, data=req_data, headers={'Content-Type': 'application/json', 'User-Agent': 'Mozilla/5.0'}, method='PUT')
        with urllib.request.urlopen(req, timeout=3) as resp:
            return True
    except Exception:
        return False

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

st.title("🏫 Colegiul 'Emil Negruțiu' Turda — Catalog Școlar Online (IX TH Turism)")
st.caption("Aplicație Web Streamlit pentru gestionare note și absențe")

if not os.path.exists(excel_path):
    st.warning(f"⚠️ Fișierul catalog '{excel_path}' nu a fost găsit în directorul curent. Vă rugăm să îl încărcați pe GitHub în același folder.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "📊 Fișă Elev",
    "📈 Centralizator Clasă",
    "📋 Raport Diriginte"
])

elev_options = [f"{e[0]}. {e[1]} (Matr. {e[3]})" for e in ELEVI]

with st.sidebar:
    st.header("⚙️ Opțiuni Catalog")
    selected_file = st.text_input("Fișier Excel:", value=excel_path)
    st.info("Fișierul este salvat automat local + live în Cloud pentru părinți.")
    if os.path.exists(selected_file):
        try:
            with open(selected_file, "rb") as f:
                st.download_button(
                    label="📥 Descarcă Catalog Excel (.xlsx)",
                    data=f.read(),
                    file_name=os.path.basename(selected_file),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
        except Exception:
            pass
    st.divider()
    if st.button("🚪 Deconectare", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

# --- TAB 1: NOTĂ ---
with tab1:
    st.subheader("Adăugare Notă Nouă (Format v15 - 10 Note)")
    col1, col2 = st.columns(2)
    with col1:
        elev_idx_n = st.selectbox("Selectează Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_n")
        cat_n = st.radio("Categorie Disciplină:", ["Cultură Generală", "Module Tehnologice"], key="cat_n")
    with col2:
        materii = [d[0] for d in DISCIPLINE_CG] if cat_n == "Cultură Generală" else [m[0] for m in MODULE_TH]
        mat_idx_n = st.selectbox("Selectează Disciplina / Modulul:", range(len(materii)), format_func=lambda i: materii[i], key="mat_n")
        nota_val = st.number_input("Notă (1 - 10):", min_value=1, max_value=10, value=10, step=1)
        data_nota = st.text_input("Data Notei (DD.MM):", value=datetime.datetime.now().strftime("%d.%m"), key="data_n")
        
    if st.button("💾 Salvează Nota în Catalog", type="primary", use_container_width=True):
        if not os.path.exists(selected_file):
            st.error(f"Fișierul {selected_file} nu există!")
        else:
            try:
                wb = openpyxl.load_workbook(selected_file)
                sheet_name = "Cultură Generală" if cat_n == "Cultură Generală" else "Module Tehnologice"
                ws = wb[sheet_name]
                student_row = 9 + elev_idx_n
                start_col = DISCIPLINE_CG[mat_idx_n][1] if cat_n == "Cultură Generală" else MODULE_TH[mat_idx_n][1]
                
                slot_found = False
                for k in range(10):
                    n_col = start_col + (k * 2)
                    d_col = n_col + 1
                    cell_n = ws.cell(row=student_row, column=n_col)
                    cell_d = ws.cell(row=student_row, column=d_col)
                    if cell_n.value is None or str(cell_n.value).strip() == "":
                        cell_n.value = int(nota_val)
                        cell_d.value = str(data_nota)
                        cell_d.number_format = '@'
                        slot_found = True
                        slot_num = k + 1
                        break
                if slot_found:
                    wb.save(selected_file)
                    c_data = get_cloud_data()
                    c_data.setdefault('grades', []).append({
                        'student_idx': elev_idx_n,
                        'cat': cat_n,
                        'mat_idx': mat_idx_n,
                        'nota': int(nota_val),
                        'data': str(data_nota),
                        'ts': datetime.datetime.now().isoformat()
                    })
                    save_cloud_data(c_data)
                    st.success(f"✅ Notă salvată local + transmisă instant la Părinți: {nota_val} pe {data_nota} la {materii[mat_idx_n]} (Slot N{slot_num}) pentru {ELEVI[elev_idx_n][1]}")
                    st.rerun()
                else:
                    st.error("❌ Toate cele 10 sloturi de note sunt pline pentru această disciplină!")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare la salvare: {ex}")

# --- TAB 2: ABSENȚĂ ---
with tab2:
    st.subheader("Adăugare Absență (Format v15 - 30 Absențe)")
    col1, col2 = st.columns(2)
    with col1:
        elev_idx_a = st.selectbox("Selectează Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_a")
        cat_a = st.radio("Categorie Disciplină:", ["Cultură Generală", "Module Tehnologice"], key="cat_a")
    with col2:
        materii_a = [d[0] for d in DISCIPLINE_CG] if cat_a == "Cultură Generală" else [m[0] for m in MODULE_TH]
        mat_idx_a = st.selectbox("Selectează Disciplina / Modulul:", range(len(materii_a)), format_func=lambda i: materii_a[i], key="mat_a")
        data_abs = st.text_input("Data Absenței (DD.MM):", value=datetime.datetime.now().strftime("%d.%m"), key="data_a")
        is_mot = st.checkbox("Absență Motivată (adaugă 'm')", value=False)
        
    if st.button("💾 Salvează Absența în Catalog", type="primary", use_container_width=True):
        if not os.path.exists(selected_file):
            st.error(f"Fișierul {selected_file} nu există!")
        else:
            try:
                wb = openpyxl.load_workbook(selected_file)
                sheet_name = "Cultură Generală" if cat_a == "Cultură Generală" else "Module Tehnologice"
                ws = wb[sheet_name]
                student_row = 9 + elev_idx_a
                start_col = DISCIPLINE_CG[mat_idx_a][1] if cat_a == "Cultură Generală" else MODULE_TH[mat_idx_a][1]
                
                abs_val = f"{data_abs.strip()}m" if is_mot else data_abs.strip()
                
                slot_found = False
                for k in range(30):
                    a_col = start_col + 21 + k
                    cell_a = ws.cell(row=student_row, column=a_col)
                    if cell_a.value is None or str(cell_a.value).strip() == "":
                        cell_a.value = abs_val
                        cell_a.number_format = '@'
                        slot_found = True
                        slot_num = k + 1
                        break
                if slot_found:
                    wb.save(selected_file)
                    c_data = get_cloud_data()
                    c_data.setdefault('absences', []).append({
                        'student_idx': elev_idx_a,
                        'cat': cat_a,
                        'mat_idx': mat_idx_a,
                        'data': str(data_abs.strip()),
                        'is_mot': is_mot,
                        'ts': datetime.datetime.now().isoformat()
                    })
                    save_cloud_data(c_data)
                    st.success(f"✅ Absență salvată local + transmisă instant la Părinți: '{abs_val}' la {materii_a[mat_idx_a]} (Slot A{slot_num}) pentru {ELEVI[elev_idx_a][1]}")
                    st.rerun()
                else:
                    st.error("❌ Toate cele 30 de sloturi de absențe sunt pline pentru această disciplină!")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare la salvare: {ex}")

# --- TAB 3: MOTIVARE ---
with tab3:
    st.subheader("Motivare Absență Existentă")
    col1, col2 = st.columns(2)
    with col1:
        elev_idx_m = st.selectbox("Selectează Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_m")
        cat_m = st.radio("Categorie Disciplină:", ["Cultură Generală", "Module Tehnologice"], key="cat_m")
    with col2:
        materii_m = [d[0] for d in DISCIPLINE_CG] if cat_m == "Cultură Generală" else [m[0] for m in MODULE_TH]
        mat_idx_m = st.selectbox("Selectează Disciplina / Modulul:", range(len(materii_m)), format_func=lambda i: materii_m[i], key="mat_m")
        data_mot = st.text_input("Data de motivat (ex: 21.09):", key="data_mot")
        
    if st.button("✅ Motivează Absența", type="primary", use_container_width=True):
        if not os.path.exists(selected_file):
            st.error(f"Fișierul {selected_file} nu există!")
        elif not data_mot.strip():
            st.warning("Vă rugăm să introduceți data absenței!")
        else:
            try:
                wb = openpyxl.load_workbook(selected_file)
                sheet_name = "Cultură Generală" if cat_m == "Cultură Generală" else "Module Tehnologice"
                ws = wb[sheet_name]
                student_row = 9 + elev_idx_m
                start_col = DISCIPLINE_CG[mat_idx_m][1] if cat_m == "Cultură Generală" else MODULE_TH[mat_idx_m][1]
                
                target_d = data_mot.strip()
                found = False
                for k in range(30):
                    a_col = start_col + 21 + k
                    cell_a = ws.cell(row=student_row, column=a_col)
                    val = str(cell_a.value).strip() if cell_a.value else ""
                    if val == target_d:
                        cell_a.value = f"{target_d}m"
                        cell_a.number_format = '@'
                        found = True
                        break
                    elif val == f"{target_d}m":
                        st.info(f"Absența din {target_d} este deja motivată!")
                        wb.close()
                        found = True
                        break
                        
                if found and cell_a.value == f"{target_d}m":
                    wb.save(selected_file)
                    c_data = get_cloud_data()
                    for ca in c_data.get('absences', []):
                        if ca.get('student_idx') == elev_idx_m and ca.get('cat') == cat_m and ca.get('mat_idx') == mat_idx_m and ca.get('data') == target_d:
                            ca['is_mot'] = True
                    save_cloud_data(c_data)
                    st.success(f"✅ Absență motivată ('{target_d}m') pentru {ELEVI[elev_idx_m][1]} la {materii_m[mat_idx_m]}")
                    st.rerun()
                elif not found:
                    st.warning(f"Nu s-a găsit nicio absență nemotivată cu data '{target_d}'.")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare: {ex}")

# --- TAB 4: FIȘĂ ELEV ---
with tab4:
    st.subheader("Fișă Elev & Rezumat")
    elev_idx_v = st.selectbox("Alege Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_v")
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            e_info = ELEVI[elev_idx_v]
            st.markdown(f"### 👤 {e_info[1]} (Matricol {e_info[3]})")
            
            c_data = get_cloud_data()
            c_grades = c_data.get('grades', [])
            c_absences = c_data.get('absences', [])

            for cat_title, sheet_n, sub_list in [("Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"#### {cat_title}")
                ws = wb[sheet_n]
                s_row = 9 + elev_idx_v
                
                rows_data = []
                for mat_idx, (s_name, start_col) in enumerate(sub_list):
                    notes = []
                    for k in range(10):
                        n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                        if n_val is not None and str(n_val).strip() != "":
                            d_str = f" ({d_val})" if d_val else ""
                            notes.append(f"{n_val}{d_str}")
                    for cg in c_grades:
                        if cg.get('student_idx') == elev_idx_v and cg.get('cat') == cat_title and cg.get('mat_idx') == mat_idx:
                            notes.append(f"{cg.get('nota')} ({cg.get('data')})")

                    absences = []
                    for k in range(30):
                        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            absences.append(str(a_val))
                    for ca in c_absences:
                        if ca.get('student_idx') == elev_idx_v and ca.get('cat') == cat_title and ca.get('mat_idx') == mat_idx:
                            a_str = f"{ca.get('data')}{'m' if ca.get('is_mot') else ''}"
                            if a_str not in absences:
                                absences.append(a_str)

                    media_val = ws.cell(row=s_row, column=start_col + 20).value
                    media_str = f"{float(media_val):.2f}" if isinstance(media_val, (int, float)) else (str(media_val) if media_val else "-")
                    
                    rows_data.append({
                        "Disciplină / Modul": s_name,
                        "Note & Date": ", ".join(notes) if notes else "Fără note",
                        "Absențe": ", ".join(absences) if absences else "Fără absențe",
                        "Medie": media_str
                    })
                st.dataframe(rows_data, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire fișă: {ex}")

# --- TAB 5: CENTRALIZATOR CLASĂ ---
with tab5:
    st.subheader("📈 Centralizator General Clasă")
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_c = wb["Centralizator Medii"]
            c_data = []
            for idx in range(len(ELEVI)):
                r = 9 + idx
                c_data.append({
                    "Nr.": str(ws_c.cell(row=r, column=1).value or ""),
                    "Nume și Prenume": str(ws_c.cell(row=r, column=2).value or ""),
                    "Matricol": str(ws_c.cell(row=r, column=4).value or ""),
                    "Media CG": str(ws_c.cell(row=r, column=5).value or "-"),
                    "Media TH": str(ws_c.cell(row=r, column=6).value or "-"),
                    "Media Generală": str(ws_c.cell(row=r, column=7).value or "-"),
                    "Purtare": str(ws_c.cell(row=r, column=8).value or "10"),
                    "Total Absențe": str(ws_c.cell(row=r, column=10).value or "0")
                })
            st.dataframe(c_data, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire centralizator: {ex}")

# --- TAB 6: RAPORT DIRIGINTE ---
with tab6:
    st.subheader("📋 Raport Diriginte")
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_r = wb["Raport Diriginte"]
            st.metric("Total Elevi", str(ws_r.cell(row=6, column=1).value or "32"))
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire raport: {ex}")
