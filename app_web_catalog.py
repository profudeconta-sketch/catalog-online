import datetime
import os
import openpyxl
import streamlit as st
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
    "📋 Centralizator Clasă",
    "📈 Raport Diriginte"
])

elev_options = [f"{e[0]}. {e[1]} (Matr. {e[2]})" for e in ELEVI]

with st.sidebar:
    st.header("⚙️ Opțiuni Catalog")
    selected_file = st.text_input("Fișier Excel:", value=excel_path)
    st.info("Fișierul este salvat automat la fiecare modificare.")
    if st.button("🚪 Deconectare (Logout)", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

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

def setup_pdf_font():
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]
    bold_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]
    font_name = "Helvetica"
    font_bold_name = "Helvetica-Bold"
    for fp, bp in zip(font_paths, bold_paths):
        if os.path.exists(fp) and os.path.exists(bp):
            try:
                pdfmetrics.registerFont(TTFont('DejaVuSans', fp))
                pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', bp))
                font_name = 'DejaVuSans'
                font_bold_name = 'DejaVuSans-Bold'
                break
            except Exception:
                pass
    return font_name, font_bold_name

def clean_pdf_text(text):
    return str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# --- TAB 1: NOTĂ ---
with tab1:
    st.subheader("Adăugare Notă Nouă")
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
                    st.success(f"✅ Notă salvată: {nota_val} pe {data_nota} la {materii[mat_idx_n]} (Slot N{slot_num}) pentru {ELEVI[elev_idx_n][1]}")
                else:
                    st.error("❌ Toate cele 10 sloturi de note sunt pline pentru această disciplină!")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare la salvare: {ex}")

# --- TAB 2: ABSENȚĂ ---
with tab2:
    st.subheader("Adăugare Absență")
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
                    st.success(f"✅ Absență salvată: '{abs_val}' la {materii_a[mat_idx_a]} (Slot A{slot_num}) pentru {ELEVI[elev_idx_a][1]}")
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
                    val = safe_str(cell_a.value)
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
                        
                if found and safe_str(cell_a.value) == f"{target_d}m":
                    wb.save(selected_file)
                    st.success(f"✅ Absență motivată ('{target_d}m') pentru {ELEVI[elev_idx_m][1]} la {materii_m[mat_idx_m]}")
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
            
            for cat_title, sheet_n, sub_list in [("Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"#### {cat_title}")
                ws = wb[sheet_n]
                s_row = 9 + elev_idx_v
                
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
                        "Note": ", ".join(notes) if notes else "Fără note",
                        "Absențe": ", ".join(absences) if absences else "Fără absențe",
                        "Medie": media_str
                    })
                st.dataframe(rows_data, use_container_width=True)
            wb.close()

            # --- GENERARE PDF FIȘĂ ELEV ---
            if st.button("🖨️ Descarcă Fișă PDF (Format Oficial Print)", type="primary"):
                try:
                    pdf_filename = f"Fisa_Elev_{e_info[1].replace(' ', '_')}.pdf"
                    font_name, font_bold_name = setup_pdf_font()
                    
                    doc = SimpleDocTemplate(
                        pdf_filename,
                        pagesize=A4,
                        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
                    )
                    styles = getSampleStyleSheet()
                    
                    title_style = ParagraphStyle('TStyle', parent=styles['Heading1'], fontName=font_bold_name, fontSize=14, alignment=TA_CENTER, leading=18)
                    sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontName=font_bold_name, fontSize=10, alignment=TA_CENTER, leading=14)
                    body_style = ParagraphStyle('BStyle', parent=styles['Normal'], fontName=font_name, fontSize=8, leading=10)
                    body_center = ParagraphStyle('BCStyle', parent=styles['Normal'], fontName=font_name, fontSize=8, alignment=TA_CENTER, leading=10)
                    head_style = ParagraphStyle('HStyle', parent=styles['Normal'], fontName=font_bold_name, fontSize=8, alignment=TA_CENTER, leading=10)
                    
                    story = []
                    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA"), title_style))
                    story.append(Paragraph(clean_pdf_text("FIȘĂ INDIVIDUALĂ DE EVALUARE ȘI FRECVENȚĂ ȘCOLARĂ"), sub_style))
                    story.append(Spacer(1, 10))
                    
                    info_text = f"<b>Elev:</b> {clean_pdf_text(e_info[1])} | <b>Nr. Matricol:</b> {clean_pdf_text(e_info[3])} | <b>Clasa:</b> a IX-a TH (Turism)"
                    story.append(Paragraph(info_text, ParagraphStyle('Info', parent=body_style, fontSize=9, leading=12)))
                    story.append(Spacer(1, 10))
                    
                    wb_data = openpyxl.load_workbook(selected_file, data_only=True)
                    table_data = [[
                        Paragraph("<b>Disciplină / Modul</b>", head_style),
                        Paragraph("<b>Note (1-10)</b>", head_style),
                        Paragraph("<b>Absențe</b>", head_style),
                        Paragraph("<b>Medie</b>", head_style)
                    ]]
                    
                    for cat_title, sheet_n, sub_list in [("Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", "Module Tehnologice", MODULE_TH)]:
                        ws = wb_data[sheet_n]
                        s_row = 9 + elev_idx_v
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
                            
                            table_data.append([
                                Paragraph(clean_pdf_text(s_name), body_style),
                                Paragraph(clean_pdf_text(", ".join(notes) if notes else "-"), body_style),
                                Paragraph(clean_pdf_text(", ".join(absences) if absences else "-"), body_style),
                                Paragraph(clean_pdf_text(media_str), body_center)
                            ])
                    wb_data.close()
                    
                    t = Table(table_data, colWidths=[180, 160, 130, 50])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#DCE6F1')),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('TOPPADDING', (0,0), (-1,-1), 4),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                    ]))
                    story.append(t)
                    story.append(Spacer(1, 20))
                    story.append(Paragraph("<b>Diriginte:</b> ___________________________   |   <b>Data eliberării:</b> " + datetime.datetime.now().strftime("%d.%m.%Y"), body_style))
                    
                    doc.build(story)
                    
                    with open(pdf_filename, "rb") as f_pdf:
                        st.download_button(
                            label="⬇️ Apasă aici pentru a descărca Fișa PDF",
                            data=f_pdf.read(),
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )
                except Exception as ex_pdf:
                    st.error(f"Eroare la generare PDF: {ex_pdf}")
        except Exception as ex:
            st.error(f"Eroare la citire fișă: {ex}")

# --- TAB 5: CENTRALIZATOR ---
with tab5:
    st.subheader("📋 Centralizator General Clasă (Medii, Purtare & Absențe)")
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_c = wb["Centralizator Medii"]
            
            c_rows = []
            for idx in range(len(ELEVI)):
                r = 9 + idx
                c_rows.append({
                    "Nr.": safe_str(ws_c.cell(row=r, column=1).value),
                    "Nume și Prenume": safe_str(ws_c.cell(row=r, column=2).value),
                    "Matricol": safe_str(ws_c.cell(row=r, column=4).value),
                    "Media CG": safe_float_str(ws_c.cell(row=r, column=5).value),
                    "Media Module": safe_float_str(ws_c.cell(row=r, column=6).value),
                    "Media Generală": safe_float_str(ws_c.cell(row=r, column=7).value),
                    "Notă Purtare": safe_str(ws_c.cell(row=r, column=8).value),
                    "Statut Școlar": safe_str(ws_c.cell(row=r, column=9).value),
                    "Total Absențe": safe_str(ws_c.cell(row=r, column=10).value)
                })
            wb.close()
            st.dataframe(c_rows, use_container_width=True)
            
            if st.button("🖨️ Descarcă Centralizator PDF (Format A4 Landscape)", type="primary"):
                try:
                    pdf_filename = "Centralizator_Clasa_IX_TH.pdf"
                    font_name, font_bold_name = setup_pdf_font()
                    
                    doc = SimpleDocTemplate(
                        pdf_filename,
                        pagesize=landscape(A4),
                        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
                    )
                    styles = getSampleStyleSheet()
                    
                    title_style = ParagraphStyle('TStyle', parent=styles['Heading1'], fontName=font_bold_name, fontSize=13, alignment=TA_CENTER, leading=16)
                    body_style = ParagraphStyle('BStyle', parent=styles['Normal'], fontName=font_name, fontSize=8, leading=10)
                    body_center = ParagraphStyle('BCStyle', parent=styles['Normal'], fontName=font_name, fontSize=8, alignment=TA_CENTER, leading=10)
                    head_style = ParagraphStyle('HStyle', parent=styles['Normal'], fontName=font_bold_name, fontSize=8, alignment=TA_CENTER, leading=10)
                    
                    story = []
                    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA — CENTRALIZATOR MEDII & FRECVENȚĂ"), title_style))
                    story.append(Paragraph(clean_pdf_text("Clasa a IX-a TH (Turism și Alimentație) | An Școlar 2026-2027"), ParagraphStyle('Sub', parent=title_style, fontSize=10, leading=12)))
                    story.append(Spacer(1, 10))
                    
                    table_data = [[
                        Paragraph("<b>Nr.</b>", head_style),
                        Paragraph("<b>Nume și Prenume Elev</b>", head_style),
                        Paragraph("<b>Matricol</b>", head_style),
                        Paragraph("<b>Media CG</b>", head_style),
                        Paragraph("<b>Media Mod.</b>", head_style),
                        Paragraph("<b>Media Gen.</b>", head_style),
                        Paragraph("<b>Purtare</b>", head_style),
                        Paragraph("<b>Statut</b>", head_style),
                        Paragraph("<b>Absențe</b>", head_style)
                    ]]
                    
                    for row in c_rows:
                        table_data.append([
                            Paragraph(clean_pdf_text(row["Nr."]), body_center),
                            Paragraph(clean_pdf_text(row["Nume și Prenume"]), body_style),
                            Paragraph(clean_pdf_text(row["Matricol"]), body_center),
                            Paragraph(clean_pdf_text(row["Media CG"]), body_center),
                            Paragraph(clean_pdf_text(row["Media Module"]), body_center),
                            Paragraph(clean_pdf_text(row["Media Generală"]), body_center),
                            Paragraph(clean_pdf_text(row["Notă Purtare"]), body_center),
                            Paragraph(clean_pdf_text(row["Statut Școlar"]), body_center),
                            Paragraph(clean_pdf_text(row["Total Absențe"]), body_center)
                        ])
                        
                    t = Table(table_data, colWidths=[30, 220, 60, 60, 60, 60, 50, 90, 60])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('TOPPADDING', (0,0), (-1,-1), 3),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
                    ]))
                    story.append(t)
                    doc.build(story)
                    
                    with open(pdf_filename, "rb") as f_pdf:
                        st.download_button("⬇️ Apasă aici pentru a descărca Centralizatorul PDF", data=f_pdf.read(), file_name=pdf_filename, mime="application/pdf")
                except Exception as ex_pdf:
                    st.error(f"Eroare PDF: {ex_pdf}")
        except Exception as ex:
            st.error(f"Eroare la citire centralizator: {ex}")

# --- TAB 6: RAPORT DIRIGINTE ---
with tab6:
    st.subheader("📈 Raport Sintetic al Dirigintelui")
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_r = wb["Raport Diriginte"]
            
            tot_elevi = safe_str(ws_r.cell(row=6, column=1).value)
            promovabilitate = safe_str(ws_r.cell(row=6, column=3).value)
            medie_clasa = safe_float_str(ws_r.cell(row=6, column=5).value)
            medie_purtare = safe_float_str(ws_r.cell(row=6, column=7).value)
            tot_abs = safe_str(ws_r.cell(row=6, column=9).value)
            wb.close()
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Elevi", tot_elevi if tot_elevi else "32")
            c2.metric("Promovabilitate", f"{float(promovabilitate)*100:.0f}%" if promovabilitate and promovabilitate != "-" else "100%")
            c3.metric("Media Clasei", medie_clasa)
            c4.metric("Media Purtare", medie_purtare)
            c5.metric("Total Absențe", tot_abs if tot_abs else "0")
            
            if st.button("🖨️ Descarcă Raport Diriginte PDF", type="primary"):
                try:
                    pdf_filename = "Raport_Diriginte_IX_TH.pdf"
                    font_name, font_bold_name = setup_pdf_font()
                    
                    doc = SimpleDocTemplate(
                        pdf_filename,
                        pagesize=A4,
                        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36
                    )
                    styles = getSampleStyleSheet()
                    
                    title_style = ParagraphStyle('TStyle', parent=styles['Heading1'], fontName=font_bold_name, fontSize=13, alignment=TA_CENTER, leading=16)
                    body_style = ParagraphStyle('BStyle', parent=styles['Normal'], fontName=font_name, fontSize=9, leading=12)
                    head_style = ParagraphStyle('HStyle', parent=styles['Normal'], fontName=font_bold_name, fontSize=9, alignment=TA_CENTER, leading=12)
                    
                    story = []
                    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA — RAPORT DIRIGINTE"), title_style))
                    story.append(Paragraph(clean_pdf_text("Clasa a IX-a TH (Turism și Alimentație) | An Școlar 2026-2027"), ParagraphStyle('Sub', parent=title_style, fontSize=10, leading=12)))
                    story.append(Spacer(1, 15))
                    
                    table_data = [
                        [Paragraph("<b>Indicator Performanță / Frecvență</b>", head_style), Paragraph("<b>Valoare Înregistrată</b>", head_style)],
                        [Paragraph("Total Elevi Înscriși", body_style), Paragraph(clean_pdf_text(tot_elevi if tot_elevi else "32"), body_style)],
                        [Paragraph("Promovabilitate Estimată", body_style), Paragraph(clean_pdf_text(f"{float(promovabilitate)*100:.0f}%" if promovabilitate and promovabilitate != "-" else "100%"), body_style)],
                        [Paragraph("Media Generală a Clasei", body_style), Paragraph(clean_pdf_text(medie_clasa), body_style)],
                        [Paragraph("Media Clasei la Purtare", body_style), Paragraph(clean_pdf_text(medie_purtare), body_style)],
                        [Paragraph("Total Absențe Înregistrate", body_style), Paragraph(clean_pdf_text(tot_abs if tot_abs else "0"), body_style)]
                    ]
                    
                    t = Table(table_data, colWidths=[300, 200])
                    t.setStyle(TableStyle([
                        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1F497D')),
                        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#D9D9D9')),
                        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
                        ('TOPPADDING', (0,0), (-1,-1), 6),
                        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
                    ]))
                    story.append(t)
                    doc.build(story)
                    
                    with open(pdf_filename, "rb") as f_pdf:
                        st.download_button("⬇️ Apasă aici pentru a descărca Raportul PDF", data=f_pdf.read(), file_name=pdf_filename, mime="application/pdf")
                except Exception as ex_pdf:
                    st.error(f"Eroare PDF: {ex_pdf}")
        except Exception as ex:
            st.error(f"Eroare la citire raport: {ex}")
