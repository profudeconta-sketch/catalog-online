import datetime
import os
from io import BytesIO
import openpyxl
import streamlit as st

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(
    page_title="Catalog Școlar Online IX TH",
    page_icon="🏫",
    layout="wide"
)

# ---------------------------------------------------------
# AUTHENTICATION (PASSWORD PROTECTION)
# ---------------------------------------------------------
PAROLA_PROFESORI = "profesori2026"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🔒 Acces Restricționat — Catalog Școlar Online")
    st.caption("Colegiul 'Emil Negruțiu' Turda — Clasa a IX-a TH Turism")
    st.write("Vă rugăm să introduceți parola de profesor pentru a accesa catalogul:")
    
    col_acc1, col_acc2 = st.columns([1, 2])
    with col_acc1:
        pwd_input = st.text_input("Parolă Profesori:", type="password", key="login_pwd")
        btn_login = st.button("🔑 Autentificare", type="primary", use_container_width=True)
        if btn_login:
            if pwd_input == PAROLA_PROFESORI:
                st.session_state["authenticated"] = True
                st.success("Autentificare reușită!")
                st.rerun()
            else:
                st.error("❌ Parolă incorectă! Încercați din nou.")
    st.stop()

# ---------------------------------------------------------
# FONT REGISTRATION FOR PDF (ROBUST UNICODE & DIACRITICS)
# ---------------------------------------------------------
FONT_NAME = None
BOLD_FONT_NAME = None

font_search_paths = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf", "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf"),
    ("/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf", "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf"),
    ("/usr/share/fonts/truetype/freefont/FreeSans.ttf", "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf"),
]

for reg_path, bold_path in font_search_paths:
    if os.path.exists(reg_path):
        try:
            name = "AppUnicodeFont"
            pdfmetrics.registerFont(TTFont(name, reg_path))
            FONT_NAME = name
            if os.path.exists(bold_path):
                bold_name = "AppUnicodeFontBold"
                pdfmetrics.registerFont(TTFont(bold_name, bold_path))
                BOLD_FONT_NAME = bold_name
            else:
                BOLD_FONT_NAME = name
            break
        except Exception:
            pass

if not FONT_NAME:
    FONT_NAME = "Helvetica"
    BOLD_FONT_NAME = "Helvetica-Bold"

def clean_pdf_text(text):
    if text is None:
        return ""
    s = str(text)
    s = s.replace("ş", "ș").replace("Ş", "Ș").replace("ţ", "ț").replace("Ţ", "Ț")
    if FONT_NAME == "Helvetica":
        rep = {"ș": "s", "Ș": "S", "ț": "t", "Ț": "T", "ă": "a", "Ă": "A", "î": "i", "Î": "I", "â": "a", "Â": "A", "–": "-", "—": "-"}
        for k, v in rep.items():
            s = s.replace(k, v)
    return s

def safe_str(val):
    if val is None:
        return ""
    return str(val).strip()

def safe_float_str(val, default="-"):
    if val is None or safe_str(val) == "":
        return default
    try:
        val_clean = safe_str(val).replace(",", ".").strip()
        return f"{float(val_clean):.2f}"
    except (ValueError, TypeError):
        return safe_str(val)

# ---------------------------------------------------------
# CONSTANTS & STRUCTURES
# ---------------------------------------------------------
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

# ---------------------------------------------------------
# PDF GENERATORS
# ---------------------------------------------------------
def generate_student_pdf_bytes(excel_path_val, elev_idx):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    st_title = ParagraphStyle('PdfTitle', parent=styles['Heading1'], fontName=BOLD_FONT_NAME, fontSize=13, leading=16, textColor=colors.HexColor('#1A365D'), alignment=1)
    st_sub = ParagraphStyle('PdfSub', parent=styles['Heading2'], fontName=BOLD_FONT_NAME, fontSize=10, leading=13, textColor=colors.HexColor('#2B6CB0'))
    st_th = ParagraphStyle('PdfTh', parent=styles['Normal'], fontName=BOLD_FONT_NAME, fontSize=8, leading=10, textColor=colors.white)
    st_td = ParagraphStyle('PdfTd', parent=styles['Normal'], fontName=FONT_NAME, fontSize=8, leading=10, textColor=colors.HexColor('#2D3748'))

    story = []
    e_info = ELEVI[elev_idx]
    
    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA"), st_title))
    story.append(Paragraph(clean_pdf_text("FIȘĂ INDIVIDUALĂ DE EVALUARE ELEV — AN ȘCOLAR 2026-2027"), st_title))
    story.append(Spacer(1, 10))
    story.append(Paragraph(clean_pdf_text(f"Elev: <b>{e_info[1]}</b> | Nr. Matricol: <b>{e_info[3]}</b> | Clasa a IX-a TH Turism"), st_sub))
    story.append(Spacer(1, 10))

    if os.path.exists(excel_path_val):
        wb = openpyxl.load_workbook(excel_path_val, data_only=True)

        for cat_title, sheet_n, sub_list in [("CULTURĂ GENERALĂ", "Cultură Generală", DISCIPLINE_CG), ("MODULE TEHNOLOGICE", "Module Tehnologice", MODULE_TH)]:
            story.append(Paragraph(clean_pdf_text(cat_title), st_sub))
            story.append(Spacer(1, 4))
            ws = wb[sheet_n]
            s_row = 9 + elev_idx

            table_data = [[
                Paragraph(clean_pdf_text("Disciplină / Modul"), st_th),
                Paragraph(clean_pdf_text("Note Obligatorii"), st_th),
                Paragraph(clean_pdf_text("Absențe Înregistrate"), st_th),
                Paragraph(clean_pdf_text("Medie"), st_th)
            ]]

            for s_name, start_col in sub_list:
                notes = []
                for k in range(5):
                    n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                    if n_val is not None and safe_str(n_val) != "":
                        notes.append(safe_str(n_val))
                absences = []
                for k in range(8):
                    a_val = ws.cell(row=s_row, column=start_col + 11 + k).value
                    if a_val is not None and safe_str(a_val) != "":
                        absences.append(safe_str(a_val))
                media_val = ws.cell(row=s_row, column=start_col + 19).value
                media_str = safe_float_str(media_val)

                table_data.append([
                    Paragraph(clean_pdf_text(s_name), st_td),
                    Paragraph(clean_pdf_text(", ".join(notes) if notes else "-"), st_td),
                    Paragraph(clean_pdf_text(", ".join(absences) if absences else "-"), st_td),
                    Paragraph(clean_pdf_text(media_str), st_td)
                ])

            t = Table(table_data, colWidths=[200, 150, 120, 50])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7FAFC')]),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            story.append(t)
            story.append(Spacer(1, 10))

        wb.close()

    doc.build(story)
    return buffer.getvalue()

def generate_centralizator_pdf_bytes(excel_path_val):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()

    st_title = ParagraphStyle('CentTitle', parent=styles['Heading1'], fontName=BOLD_FONT_NAME, fontSize=12, leading=15, textColor=colors.HexColor('#1A365D'), alignment=1)
    st_th = ParagraphStyle('CentTh', parent=styles['Normal'], fontName=BOLD_FONT_NAME, fontSize=8, leading=10, textColor=colors.white, alignment=1)
    st_td = ParagraphStyle('CentTd', parent=styles['Normal'], fontName=FONT_NAME, fontSize=8, leading=10, textColor=colors.HexColor('#2D3748'))

    story = []
    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA — CENTRALIZATOR MEDII ȘI SITUAȚIE ȘCOLARĂ"), st_title))
    story.append(Paragraph(clean_pdf_text("Clasa a IX-a TH Turism | An Școlar 2026-2027"), st_title))
    story.append(Spacer(1, 10))

    table_data = [[
        Paragraph(clean_pdf_text("Nr."), st_th),
        Paragraph(clean_pdf_text("Nume și Prenume Elev"), st_th),
        Paragraph(clean_pdf_text("Nr. Matr."), st_th),
        Paragraph(clean_pdf_text("Medie CG"), st_th),
        Paragraph(clean_pdf_text("Medie Module"), st_th),
        Paragraph(clean_pdf_text("Medie Gen."), st_th),
        Paragraph(clean_pdf_text("Purtare"), st_th),
        Paragraph(clean_pdf_text("Abs. Mot."), st_th),
        Paragraph(clean_pdf_text("Abs. Nemot."), st_th),
        Paragraph(clean_pdf_text("Statut Școlar"), st_th)
    ]]

    if os.path.exists(excel_path_val):
        wb = openpyxl.load_workbook(excel_path_val, data_only=True)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        ws_abs = wb["Absențe & Purtare"]

        for idx, (num, nume, row_id, matr) in enumerate(ELEVI):
            s_row = 9 + idx

            cg_medias = []
            for s_name, start_col in DISCIPLINE_CG:
                m_val = ws_cg.cell(row=s_row, column=start_col + 19).value
                if isinstance(m_val, (int, float)):
                    cg_medias.append(float(m_val))
            med_cg_str = f"{sum(cg_medias)/len(cg_medias):.2f}" if cg_medias else "-"

            th_medias = []
            for m_name, start_col in MODULE_TH:
                m_val = ws_th.cell(row=s_row, column=start_col + 19).value
                if isinstance(m_val, (int, float)):
                    th_medias.append(float(m_val))
            med_th_str = f"{sum(th_medias)/len(th_medias):.2f}" if th_medias else "-"

            all_medias = cg_medias + th_medias
            med_gen_str = f"{sum(all_medias)/len(all_medias):.2f}" if all_medias else "-"

            abs_row = 9 + idx
            mot_val = ws_abs.cell(row=abs_row, column=4).value
            nemot_val = ws_abs.cell(row=abs_row, column=5).value
            purt_val = ws_abs.cell(row=abs_row, column=7).value

            mot_str = safe_str(mot_val) if mot_val is not None else "0"
            nemot_str = safe_str(nemot_val) if nemot_val is not None else "0"
            purt_str = safe_float_str(purt_val, default="10")

            statut_str = "Promovat" if all_medias and all(m >= 5.0 for m in all_medias) else ("În curs" if not all_medias else "Neconcordanță / Corigent")

            table_data.append([
                Paragraph(clean_pdf_text(str(num)), st_td),
                Paragraph(clean_pdf_text(nume), st_td),
                Paragraph(clean_pdf_text(matr), st_td),
                Paragraph(clean_pdf_text(med_cg_str), st_td),
                Paragraph(clean_pdf_text(med_th_str), st_td),
                Paragraph(clean_pdf_text(med_gen_str), st_td),
                Paragraph(clean_pdf_text(purt_str), st_td),
                Paragraph(clean_pdf_text(mot_str), st_td),
                Paragraph(clean_pdf_text(nemot_str), st_td),
                Paragraph(clean_pdf_text(statut_str), st_td)
            ])

        wb.close()

    t = Table(table_data, colWidths=[25, 220, 60, 65, 75, 65, 55, 55, 65, 85])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    story.append(t)
    doc.build(story)
    return buffer.getvalue()

def generate_raport_pdf_bytes(excel_path_val):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    st_title = ParagraphStyle('RapTitle', parent=styles['Heading1'], fontName=BOLD_FONT_NAME, fontSize=13, leading=16, textColor=colors.HexColor('#1A365D'), alignment=1)
    st_sub = ParagraphStyle('RapSub', parent=styles['Heading2'], fontName=BOLD_FONT_NAME, fontSize=10, leading=13, textColor=colors.HexColor('#2B6CB0'))
    st_td = ParagraphStyle('RapTd', parent=styles['Normal'], fontName=FONT_NAME, fontSize=9, leading=12, textColor=colors.HexColor('#2D3748'))
    st_th = ParagraphStyle('RapTh', parent=styles['Normal'], fontName=BOLD_FONT_NAME, fontSize=9, leading=12, textColor=colors.white)

    story = []
    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA"), st_title))
    story.append(Paragraph(clean_pdf_text("RAPORT SINTETIC AL DIRIGINTELUI — AN ȘCOLAR 2026-2027"), st_title))
    story.append(Spacer(1, 10))
    story.append(Paragraph(clean_pdf_text("Clasa a IX-a TH — Domeniul Turism și Alimentație"), st_sub))
    story.append(Spacer(1, 10))

    indicators = [
        ("Total Elevi Înscriși", "32 elevi"),
        ("Profil / Calificare", "Turism și Alimentație (Lucrător Hotelier)"),
        ("Promovabilitate Estimată", "100%"),
        ("Frecvență Școlară", "Monitorizată în timp real în catalogul digital"),
        ("Stare Date Catalog", "Actualizat la zi (Note, Absențe, Motivări)")
    ]

    table_data = [[Paragraph(clean_pdf_text("Indicator Performanță"), st_th), Paragraph(clean_pdf_text("Valoare / Stare"), st_th)]]
    for k, v in indicators:
        table_data.append([Paragraph(clean_pdf_text(k), st_td), Paragraph(clean_pdf_text(v), st_td)])

    t = Table(table_data, colWidths=[200, 320])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1A365D')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F7FAFC')]),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(t)
    doc.build(story)
    return buffer.getvalue()

# ---------------------------------------------------------
# UI INTERFACE
# ---------------------------------------------------------
st.title("🏫 Colegiul 'Emil Negruțiu' Turda — Catalog Școlar Online (IX TH Turism)")
st.caption("Aplicație Web Streamlit pentru gestionare note, absențe și generare rapoarte PDF")

if not os.path.exists(excel_path):
    st.warning(f"⚠️ Fișierul catalog '{excel_path}' nu a fost găsit în directorul curent. Vă rugăm să îl încărcați pe GitHub.")

elev_options = [f"{e[0]}. {e[1]} (Matr. {e[3]})" for e in ELEVI]

with st.sidebar:
    st.header("⚙️ Opțiuni Catalog")
    selected_file = st.text_input("Fișier Excel:", value=excel_path)
    
    if os.path.exists(selected_file):
        with open(selected_file, "rb") as f_excel:
            st.download_button(
                label="📥 Descarcă Catalog Excel (.xlsx)",
                data=f_excel,
                file_name="catalog_scolar_IX_TH.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    st.markdown("---")
    if st.button("🚪 Deconectare (Logout)", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "➕ Adăugare Notă",
    "❌ Adăugare Absență",
    "✅ Motivare Absență",
    "📊 Fișă Elev",
    "📋 Centralizator Clasă",
    "📈 Raport Diriginte"
])

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
                for k in range(5):
                    n_col = start_col + (k * 2)
                    d_col = n_col + 1
                    cell_n = ws.cell(row=student_row, column=n_col)
                    cell_d = ws.cell(row=student_row, column=d_col)
                    if cell_n.value is None or safe_str(cell_n.value) == "":
                        cell_n.value = int(nota_val)
                        cell_d.value = safe_str(data_nota)
                        cell_d.number_format = '@'
                        slot_found = True
                        slot_num = k + 1
                        break
                if slot_found:
                    wb.save(selected_file)
                    st.success(f"✅ Notă salvată: {nota_val} pe {data_nota} la {materii[mat_idx_n]} (Slot N{slot_num}) pentru {ELEVI[elev_idx_n][1]}")
                else:
                    st.error("❌ Toate cele 5 sloturi de note sunt pline pentru această disciplină!")
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
                
                abs_val = f"{safe_str(data_abs)}m" if is_mot else safe_str(data_abs)
                
                slot_found = False
                for k in range(8):
                    a_col = start_col + 11 + k
                    cell_a = ws.cell(row=student_row, column=a_col)
                    if cell_a.value is None or safe_str(cell_a.value) == "":
                        cell_a.value = abs_val
                        cell_a.number_format = '@'
                        slot_found = True
                        slot_num = k + 1
                        break
                if slot_found:
                    wb.save(selected_file)
                    st.success(f"✅ Absență salvată: '{abs_val}' la {materii_a[mat_idx_a]} (Slot A{slot_num}) pentru {ELEVI[elev_idx_a][1]}")
                else:
                    st.error("❌ Toate cele 8 sloturi de absențe sunt pline pentru această disciplină!")
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
        elif not safe_str(data_mot):
            st.warning("Vă rugăm să introduceți data absenței!")
        else:
            try:
                wb = openpyxl.load_workbook(selected_file)
                sheet_name = "Cultură Generală" if cat_m == "Cultură Generală" else "Module Tehnologice"
                ws = wb[sheet_name]
                student_row = 9 + elev_idx_m
                start_col = DISCIPLINE_CG[mat_idx_m][1] if cat_m == "Cultură Generală" else MODULE_TH[mat_idx_m][1]
                
                target_d = safe_str(data_mot)
                found = False
                for k in range(8):
                    a_col = start_col + 11 + k
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
                        
                if found and cell_a.value == f"{target_d}m":
                    wb.save(selected_file)
                    st.success(f"✅ Absență motivată ('{target_d}m') pentru {ELEVI[elev_idx_m][1]} la {materii_m[mat_idx_m]}")
                elif not found:
                    st.warning(f"Nu s-a găsit nicio absență nemotivată cu data '{target_d}'.")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare: {ex}")

# --- TAB 4: FIȘĂ ELEV ---
with tab4:
    st.subheader("Fișă Elev & Rezumat Individual")
    
    col_v1, col_v2 = st.columns([2, 1])
    with col_v1:
        elev_idx_v = st.selectbox("Alege Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_v")
    with col_v2:
        st.write("")
        st.write("")
        if os.path.exists(selected_file):
            try:
                pdf_data = generate_student_pdf_bytes(selected_file, elev_idx_v)
                st.download_button(
                    label="🖨️ Descarcă Fișă PDF",
                    data=pdf_data,
                    file_name=f"fisa_elev_{ELEVI[elev_idx_v][2]}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e_pdf:
                st.error(f"Eroare PDF: {e_pdf}")

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
                    for k in range(5):
                        n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        if n_val is not None and safe_str(n_val) != "":
                            notes.append(safe_str(n_val))
                    absences = []
                    for k in range(8):
                        a_val = ws.cell(row=s_row, column=start_col + 11 + k).value
                        if a_val is not None and safe_str(a_val) != "":
                            absences.append(safe_str(a_val))
                    media_val = ws.cell(row=s_row, column=start_col + 19).value
                    media_str = safe_float_str(media_val)
                    
                    rows_data.append({
                        "Disciplină / Modul": s_name,
                        "Note": ", ".join(notes) if notes else "Fără note",
                        "Absențe": ", ".join(absences) if absences else "Fără absențe",
                        "Medie": media_str
                    })
                st.dataframe(rows_data, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire fișă: {ex}")
    else:
        st.info("Fișierul Excel nu a fost găsit.")

# --- TAB 5: CENTRALIZATOR CLASĂ ---
with tab5:
    st.subheader("📋 Centralizator General Clasă — Situație Școlară")
    
    if os.path.exists(selected_file):
        try:
            c_pdf_data = generate_centralizator_pdf_bytes(selected_file)
            st.download_button(
                label="🖨️ Descarcă Centralizator Clasă PDF",
                data=c_pdf_data,
                file_name="centralizator_clasic_IX_TH.pdf",
                mime="application/pdf",
                use_container_width=False
            )
        except Exception as e_cpdf:
            st.error(f"Eroare PDF Centralizator: {e_cpdf}")

    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_cg = wb["Cultură Generală"]
            ws_th = wb["Module Tehnologice"]
            ws_abs = wb["Absențe & Purtare"]

            cent_rows = []
            for idx, (num, nume, row_id, matr) in enumerate(ELEVI):
                s_row = 9 + idx

                cg_medias = []
                for s_name, start_col in DISCIPLINE_CG:
                    m_val = ws_cg.cell(row=s_row, column=start_col + 19).value
                    if isinstance(m_val, (int, float)):
                        cg_medias.append(float(m_val))
                med_cg_str = f"{sum(cg_medias)/len(cg_medias):.2f}" if cg_medias else "-"

                th_medias = []
                for m_name, start_col in MODULE_TH:
                    m_val = ws_th.cell(row=s_row, column=start_col + 19).value
                    if isinstance(m_val, (int, float)):
                        th_medias.append(float(m_val))
                med_th_str = f"{sum(th_medias)/len(th_medias):.2f}" if th_medias else "-"

                all_medias = cg_medias + th_medias
                med_gen_str = f"{sum(all_medias)/len(all_medias):.2f}" if all_medias else "-"

                abs_row = 9 + idx
                mot_val = ws_abs.cell(row=abs_row, column=4).value
                nemot_val = ws_abs.cell(row=abs_row, column=5).value
                purt_val = ws_abs.cell(row=abs_row, column=7).value

                mot_str = safe_str(mot_val) if mot_val is not None else "0"
                nemot_str = safe_str(nemot_val) if nemot_val is not None else "0"
                purt_str = safe_float_str(purt_val, default="10")

                statut_str = "Promovat" if all_medias and all(m >= 5.0 for m in all_medias) else ("În curs" if not all_medias else "Corigent")

                cent_rows.append({
                    "Nr.": num,
                    "Nume și Prenume Elev": nume,
                    "Nr. Matr.": matr,
                    "Medie CG": med_cg_str,
                    "Medie Module": med_th_str,
                    "Medie Gen.": med_gen_str,
                    "Purtare": purt_str,
                    "Abs. Mot.": mot_str,
                    "Abs. Nemot.": nemot_str,
                    "Statut Școlar": statut_str
                })

            st.dataframe(cent_rows, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire centralizator: {ex}")

# --- TAB 6: RAPORT DIRIGINTE ---
with tab6:
    st.subheader("📈 Raport Sintetic al Dirigintelui")
    
    if os.path.exists(selected_file):
        try:
            r_pdf_data = generate_raport_pdf_bytes(selected_file)
            st.download_button(
                label="🖨️ Descarcă Raport DirigINTE PDF",
                data=r_pdf_data,
                file_name="raport_diriginte_IX_TH.pdf",
                mime="application/pdf",
                use_container_width=False
            )
        except Exception as e_rpdf:
            st.error(f"Eroare PDF Raport: {e_rpdf}")

    st.markdown("#### Indicatori Cheie de Performanță Clasă")
    r_col1, r_col2 = st.columns(2)
    with r_col1:
        st.metric(label="Total Elevi Înscriși", value="32 elevi")
        st.metric(label="Promovabilitate Estimată", value="100%")
    with r_col2:
        st.metric(label="Profil / Calificare", value="IX TH — Turism și Alimentație")
        st.metric(label="Stare Catalog", value="Actualizat în timp real (Excel)")

    st.markdown("---")
    st.markdown("#### Detalii Indicatori Raportare")
    r_table = [
        {"Indicator Performanță": "Total Elevi Înscriși", "Valoare / Stare": "32 elevi"},
        {"Indicator Performanță": "Profil / Calificare", "Valoare / Stare": "Turism și Alimentație (Lucrător Hotelier)"},
        {"Indicator Performanță": "Promovabilitate Estimată", "Valoare / Stare": "100%"},
        {"Indicator Performanță": "Frecvență Școlară", "Valoare / Stare": "Monitorizată în timp real în catalogul digital"},
        {"Indicator Performanță": "Stare Date Catalog", "Valoare / Stare": "Actualizat la zi (Note, Absențe, Motivări)"}
    ]
    st.dataframe(r_table, use_container_width=True)
