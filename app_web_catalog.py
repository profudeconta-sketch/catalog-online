import datetime
import os
import openpyxl
import streamlit as st
import urllib.request
import urllib.parse
import json
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

st.set_page_config(
    page_title="Catalog Școlar Online IX TH",
    page_icon="🏫",
    layout="wide"
)

# --- CONFIGURARE FONT UNICODE PENTRU DIACRITICE (PDF) ---
def get_pdf_font():
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf"
    ]
    font_bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf"
    ]
    font_name, font_bold_name = "Helvetica", "Helvetica-Bold"
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont("CustomUnicode", fp))
                font_name = "CustomUnicode"
                break
            except Exception:
                pass
    for fbp in font_bold_paths:
        if os.path.exists(fbp):
            try:
                pdfmetrics.registerFont(TTFont("CustomUnicodeBold", fbp))
                font_bold_name = "CustomUnicodeBold"
                break
            except Exception:
                pass
    return font_name, font_bold_name

PDF_FONT, PDF_FONT_BOLD = get_pdf_font()

def safe_str(val):
    return "" if val is None else str(val).strip()

def safe_float_str(val):
    if val is None or val == "": return "-"
    try: return f"{float(val):.2f}"
    except Exception: return str(val)

# AUTENTIFICARE PROFESORI
PAROLA_PROFESORI = "profesori2026"
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Conectare Catalog Profesori")
    st.caption("Colegiul 'Emil Negruțiu' Turda — Clasa a IX-a TH")
    with st.form("login_form"):
        pwd_input = st.text_input("🔑 Introduceți Parola de Acces Profesori:", type="password")
        submit_btn = st.form_submit_button("🔓 Conectare", type="primary", use_container_width=True)
        if submit_btn:
            if pwd_input == PAROLA_PROFESORI:
                st.session_state["authenticated"] = True
                st.success("✅ Autentificare reușită!")
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

# CLOUD SYNC CONFIGURATION
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
        "catalog_scolar_clasa_IX_TH_Turda-v14.xlsx",
        "CATALOG/catalog_scolar_clasa_IX_TH_Turda-v14.xlsx",
        "catalog_scolar_clasa_IX_TH_Turda.xlsx"
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

excel_path = find_excel_file()

st.title("🏫 Colegiul 'Emil Negruțiu' Turda — Catalog Școlar Online (IX TH Turism)")
st.caption("Sistem Informatizat de Gestionare Note, Absențe și Generare Documente Oficiale")

with st.sidebar:
    st.header("⚙️ Opțiuni Catalog")
    selected_file = st.text_input("Fișier Excel Sursă:", value=excel_path)
    if os.path.exists(selected_file):
        with open(selected_file, "rb") as f:
            st.download_button(
                "📥 Descarcă Catalog Excel (.xlsx)",
                data=f.read(),
                file_name=os.path.basename(selected_file),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    st.info("💡 Salvare automata activa local + sincronizare live in Cloud pentru parinti.")
    st.caption("© 2026 Prof. Ec. Gherman Octavian-Theodor. Toate drepturile de autor rezervate.")
    st.divider()
    if st.button("🚪 Deconectare (Logout)", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "📊 Fișă Elev",
    "📈 Centralizator Clasă",
    "📋 Raport Diriginte"
])

elev_options = [f"{e[0]}. {e[1]} (Matr. {e[3]})" for e in ELEVI]

# --- GENERATOARE PDF ---
def generate_pdf_student(student_idx, file_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=PDF_FONT_BOLD, fontSize=14, leading=18, alignment=1, textColor=colors.HexColor("#1A365D"))
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontName=PDF_FONT, fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#4A5568"))
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontName=PDF_FONT_BOLD, fontSize=11, leading=14, textColor=colors.HexColor("#1A365D"), spaceBefore=10, spaceAfter=4)
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontName=PDF_FONT, fontSize=8, leading=11)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=8, leading=11)

    e_info = ELEVI[student_idx]
    story.append(Paragraph("COLEGIUL 'EMIL NEGRUȚIU' TURDA", title_style))
    story.append(Paragraph("FIȘĂ INDIVIDUALĂ DE EVALUARE ȘI FRECVENȚĂ ȘCOLARĂ", title_style))
    story.append(Paragraph("Clasa a IX-a TH — Turism și Alimentație | An școlar 2026-2027", subtitle_style))
    story.append(Spacer(1, 10))
    
    t_meta = Table([[Paragraph(f"<b>Nume și Prenume:</b> {e_info[1]}", cell_style), Paragraph(f"<b>Nr. Matricol:</b> {e_info[3]}", cell_style), Paragraph(f"<b>RM/PG:</b> {e_info[2]}", cell_style)]], colWidths=[240, 150, 130])
    t_meta.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EDF2F7")), ('PADDING', (0,0), (-1,-1), 6), ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0"))]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    if os.path.exists(file_path):
        wb = openpyxl.load_workbook(file_path, data_only=True)
        s_row = 9 + student_idx
        for cat_title, sheet_n, sub_list in [("DISCIPLINE CULTURĂ GENERALĂ", "Cultură Generală", DISCIPLINE_CG), ("MODULE TEHNOLOGICE", "Module Tehnologice", MODULE_TH)]:
            story.append(Paragraph(cat_title, heading_style))
            ws = wb[sheet_n]
            table_data = [[Paragraph("<b>Disciplină / Modul</b>", cell_bold), Paragraph("<b>Note & Date</b>", cell_bold), Paragraph("<b>Medie</b>", cell_bold), Paragraph("<b>Absențe</b>", cell_bold)]]
            for s_name, start_col in sub_list:
                notes_list, abs_list = [], []
                for k in range(10):
                    n_val, d_val = ws.cell(row=s_row, column=start_col + (k * 2)).value, ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                    if n_val is not None and str(n_val).strip() != "":
                        notes_list.append(f"{n_val}{f' ({d_val})' if d_val else ''}")
                for k in range(30):
                    a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                    if a_val is not None and str(a_val).strip() != "": abs_list.append(str(a_val))
                m_val = ws.cell(row=s_row, column=start_col + 20).value
                table_data.append([Paragraph(s_name, cell_style), Paragraph(", ".join(notes_list) if notes_list else "-", cell_style), Paragraph(safe_float_str(m_val), cell_bold), Paragraph(", ".join(abs_list) if abs_list else "-", cell_style)])
            t_sub = Table(table_data, colWidths=[160, 200, 50, 110])
            t_sub.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 4), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
            story.append(t_sub)
            story.append(Spacer(1, 8))
        wb.close()
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Profesor Diriginte:</b> ___________________________   |   <b>Semnătură:</b> ___________", cell_style))
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_pdf_centralizator(file_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=PDF_FONT_BOLD, fontSize=12, leading=15, alignment=1, textColor=colors.HexColor("#1A365D"))
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontName=PDF_FONT, fontSize=7, leading=9)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=7, leading=9)

    story.append(Paragraph("COLEGIUL 'EMIL NEGRUȚIU' TURDA — CENTRALIZATOR GENERAL CLASĂ (IX TH)", title_style))
    story.append(Spacer(1, 8))
    table_data = [[Paragraph("<b>Nr.</b>", cell_bold), Paragraph("<b>Nume și Prenume</b>", cell_bold), Paragraph("<b>Matr.</b>", cell_bold), Paragraph("<b>Med. CG</b>", cell_bold), Paragraph("<b>Med. TH</b>", cell_bold), Paragraph("<b>Med. Gen.</b>", cell_bold), Paragraph("<b>Purtare</b>", cell_bold), Paragraph("<b>Statut</b>", cell_bold), Paragraph("<b>Tot. Abs.</b>", cell_bold), Paragraph("<b>Rang</b>", cell_bold), Paragraph("<b>Premiu</b>", cell_bold)]]
    if os.path.exists(file_path):
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws = wb["Centralizator Medii"]
        for idx in range(len(ELEVI)):
            r = 9 + idx
            table_data.append([
                Paragraph(safe_str(ws.cell(row=r, column=1).value), cell_style), Paragraph(safe_str(ws.cell(row=r, column=2).value), cell_style),
                Paragraph(safe_str(ws.cell(row=r, column=4).value), cell_style), Paragraph(safe_float_str(ws.cell(row=r, column=5).value), cell_style),
                Paragraph(safe_float_str(ws.cell(row=r, column=6).value), cell_style), Paragraph(safe_float_str(ws.cell(row=r, column=7).value), cell_bold),
                Paragraph(safe_str(ws.cell(row=r, column=8).value), cell_style), Paragraph(safe_str(ws.cell(row=r, column=9).value), cell_style),
                Paragraph(safe_str(ws.cell(row=r, column=10).value), cell_style), Paragraph(safe_str(ws.cell(row=r, column=11).value), cell_style),
                Paragraph(safe_str(ws.cell(row=r, column=12).value), cell_style)
            ])
        wb.close()
    t_cent = Table(table_data, colWidths=[25, 200, 50, 50, 50, 55, 45, 80, 50, 40, 70])
    t_cent.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 3), ('VALIGN', (0,0), (-1,-1), 'MIDDLE')]))
    story.append(t_cent)
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_pdf_raport(file_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=PDF_FONT_BOLD, fontSize=13, leading=16, alignment=1, textColor=colors.HexColor("#1A365D"))
    heading_style = ParagraphStyle('HeadingStyle', parent=styles['Heading2'], fontName=PDF_FONT_BOLD, fontSize=10, leading=13, textColor=colors.HexColor("#1A365D"), spaceBefore=10, spaceAfter=4)
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontName=PDF_FONT, fontSize=8, leading=11)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=8, leading=11)

    story.append(Paragraph("COLEGIUL 'EMIL NEGRUȚIU' TURDA", title_style))
    story.append(Paragraph("RAPORT SEMESTRIAL / ANUAL AL DIRIGINTELUI", title_style))
    story.append(Spacer(1, 10))
    if os.path.exists(file_path):
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws_r = wb["Raport Diriginte"]
        t_kpi = Table([
            [Paragraph("<b>Total Elevi</b>", cell_bold), Paragraph("<b>Promovabilitate</b>", cell_bold), Paragraph("<b>Media Clasei</b>", cell_bold), Paragraph("<b>Media Purtare</b>", cell_bold), Paragraph("<b>Total Absențe</b>", cell_bold)],
            [Paragraph(safe_str(ws_r.cell(row=6, column=1).value), cell_style), Paragraph(safe_str(ws_r.cell(row=6, column=3).value), cell_style), Paragraph(safe_float_str(ws_r.cell(row=6, column=5).value), cell_style), Paragraph(safe_float_str(ws_r.cell(row=6, column=7).value), cell_style), Paragraph(safe_str(ws_r.cell(row=6, column=9).value), cell_style)]
        ], colWidths=[100, 100, 100, 100, 120])
        t_kpi.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")), ('TEXTCOLOR', (0,0), (-1,0), colors.white), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 5), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
        story.append(t_kpi)
        story.append(Spacer(1, 10))
        story.append(Paragraph("DISTRIBUȚIA MEDIILOR ȘI FRECVENȚA", heading_style))
        dist_data = [[Paragraph("<b>Tranșă Medie</b>", cell_bold), Paragraph("<b>Nr. Elevi</b>", cell_bold), Paragraph("<b>Pondere</b>", cell_bold)]]
        for row_idx in range(11, 17):
            dist_data.append([Paragraph(safe_str(ws_r.cell(row=row_idx, column=1).value), cell_style), Paragraph(safe_str(ws_r.cell(row=row_idx, column=2).value), cell_style), Paragraph(safe_str(ws_r.cell(row=row_idx, column=4).value), cell_style)])
        t_dist = Table(dist_data, colWidths=[250, 120, 150])
        t_dist.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")), ('PADDING', (0,0), (-1,-1), 4)]))
        story.append(t_dist)
        wb.close()
    doc.build(story)
    buffer.seek(0)
    return buffer

# --- TAB 1: NOTĂ ---
with tab1:
    st.subheader("Adăugare Notă Nouă (Sloturi N1 - N10)")
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
                    cell_n, cell_d = ws.cell(row=student_row, column=n_col), ws.cell(row=student_row, column=d_col)
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
                    c_data.setdefault('grades', []).append({'student_idx': elev_idx_n, 'cat': cat_n, 'mat_idx': mat_idx_n, 'nota': int(nota_val), 'data': str(data_nota), 'ts': datetime.datetime.now().isoformat()})
                    save_cloud_data(c_data)
                    st.success(f"✅ Notă salvată local + Cloud Live: {nota_val} pe {data_nota} la {materii[mat_idx_n]} pentru {ELEVI[elev_idx_n][1]}")
                    st.rerun()
                else:
                    st.error("❌ Toate sloturile de note sunt pline!")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare la salvare: {ex}")

# --- TAB 2: ABSENȚĂ ---
with tab2:
    st.subheader("Adăugare Absență (Sloturi A1 - A30)")
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
                    c_data.setdefault('absences', []).append({'student_idx': elev_idx_a, 'cat': cat_a, 'mat_idx': mat_idx_a, 'data': str(data_abs.strip()), 'is_mot': is_mot, 'ts': datetime.datetime.now().isoformat()})
                    save_cloud_data(c_data)
                    st.success(f"✅ Absență salvată local + Cloud Live: '{abs_val}' la {materii_a[mat_idx_a]} pentru {ELEVI[elev_idx_a][1]}")
                    st.rerun()
                else:
                    st.error("❌ Toate sloturile de absențe sunt pline!")
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
                if found:
                    wb.save(selected_file)
                    c_data = get_cloud_data()
                    for ca in c_data.get('absences', []):
                        if ca.get('student_idx') == elev_idx_m and ca.get('cat') == cat_m and ca.get('mat_idx') == mat_idx_m and ca.get('data') == target_d:
                            ca['is_mot'] = True
                    save_cloud_data(c_data)
                    st.success(f"✅ Absență motivată ('{target_d}m') pentru {ELEVI[elev_idx_m][1]}")
                    st.rerun()
                else:
                    st.warning(f"Nu s-a găsit nicio absență nemotivată cu data '{target_d}'.")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare: {ex}")

# --- TAB 4: FIȘĂ ELEV ---
with tab4:
    st.subheader("Fișă Elev & Rezumat")
    col_v1, col_v2 = st.columns([3, 1])
    with col_v1:
        elev_idx_v = st.selectbox("Alege Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_v")
    with col_v2:
        st.write(""); st.write("")
        try:
            pdf_bytes = generate_pdf_student(elev_idx_v, selected_file)
            st.download_button("🖨️ Descarcă Fișă PDF", data=pdf_bytes, file_name=f"Fisa_Elev_{ELEVI[elev_idx_v][1].replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare PDF: {ex}")

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
                        n_val, d_val = ws.cell(row=s_row, column=start_col + (k * 2)).value, ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                        if n_val is not None and str(n_val).strip() != "":
                            notes.append(f"{n_val}{f' ({d_val})' if d_val else ''}")
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
                            if a_str not in absences: absences.append(a_str)
                            
                    media_val = ws.cell(row=s_row, column=start_col + 20).value
                    rows_data.append({"Disciplină / Modul": s_name, "Note & Date": ", ".join(notes) if notes else "Fără note", "Absențe": ", ".join(absences) if absences else "Fără absențe", "Medie": safe_float_str(media_val)})
                st.dataframe(rows_data, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire fișă: {ex}")

# --- TAB 5: CENTRALIZATOR CLASĂ ---
with tab5:
    st.subheader("📈 Centralizator General Clasă")
    col_c1, col_c2 = st.columns([3, 1])
    with col_c2:
        try:
            pdf_cent_bytes = generate_pdf_centralizator(selected_file)
            st.download_button("🖨️ Descarcă Centralizator PDF", data=pdf_cent_bytes, file_name="Centralizator_General_IX_TH.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare PDF: {ex}")
            
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_c = wb["Centralizator Medii"]
            c_data = []
            for idx in range(len(ELEVI)):
                r = 9 + idx
                c_data.append({
                    "Nr.": safe_str(ws_c.cell(row=r, column=1).value), "Nume și Prenume": safe_str(ws_c.cell(row=r, column=2).value),
                    "Matricol": safe_str(ws_c.cell(row=r, column=4).value), "Media CG": safe_float_str(ws_c.cell(row=r, column=5).value),
                    "Media TH": safe_float_str(ws_c.cell(row=r, column=6).value), "Media Generală": safe_float_str(ws_c.cell(row=r, column=7).value),
                    "Nota Purtare": safe_str(ws_c.cell(row=r, column=8).value), "Statut Școlar": safe_str(ws_c.cell(row=r, column=9).value),
                    "Total Absențe": safe_str(ws_c.cell(row=r, column=10).value), "Rang": safe_str(ws_c.cell(row=r, column=11).value),
                    "Premiu": safe_str(ws_c.cell(row=r, column=12).value)
                })
            st.dataframe(c_data, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire centralizator: {ex}")

# --- TAB 6: RAPORT DIRIGINTE ---
with tab6:
    st.subheader("📋 Raport Sintetic al Dirigintelui")
    col_r1, col_r2 = st.columns([3, 1])
    with col_r2:
        try:
            pdf_rap_bytes = generate_pdf_raport(selected_file)
            st.download_button("🖨️ Descarcă Raport PDF", data=pdf_rap_bytes, file_name="Raport_Diriginte_IX_TH.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare PDF: {ex}")
            
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_r = wb["Raport Diriginte"]
            st.markdown("#### 📊 Indicatori Cheie de Performanță Clasă")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Elevi", safe_str(ws_r.cell(row=6, column=1).value))
            m2.metric("Promovabilitate", safe_str(ws_r.cell(row=6, column=3).value))
            m3.metric("Media Clasei", safe_float_str(ws_r.cell(row=6, column=5).value))
            m4.metric("Media Purtare", safe_float_str(ws_r.cell(row=6, column=7).value))
            m5.metric("Total Absențe", safe_str(ws_r.cell(row=6, column=9).value))
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire raport: {ex}")
