import datetime
import io
import os
import openpyxl
import streamlit as st

from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor

st.set_page_config(
    page_title="Catalog Școlar Online IX TH",
    page_icon="🏫",
    layout="wide"
)

# --- CONFIGURARE FONTS UNICODE PENTRU DIACRITICE (ă, â, î, ș, ț) ---
def setup_unicode_fonts():
    font_name = "Helvetica"
    font_bold = "Helvetica-Bold"
    
    candidates = [
        ("DejaVuSans", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
        ("LiberationSans", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        ("Roboto", "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Regular.ttf", "/usr/share/fonts/truetype/roboto/unhinted/RobotoTTF/Roboto-Bold.ttf"),
    ]
    
    for fname, regular_path, bold_path in candidates:
        if os.path.exists(regular_path) and os.path.exists(bold_path):
            try:
                pdfmetrics.registerFont(TTFont(fname, regular_path))
                pdfmetrics.registerFont(TTFont(f"{fname}-Bold", bold_path))
                font_name = fname
                font_bold = f"{fname}-Bold"
                break
            except Exception:
                pass
                
    if font_name == "Helvetica":
        reg_found, bold_found = None, None
        for root, dirs, files in os.walk("/usr/share/fonts"):
            for f in files:
                fl = f.lower()
                if fl in ["dejavusans.ttf", "liberationsans-regular.ttf", "free-sans.ttf"]:
                    reg_found = os.path.join(root, f)
                elif fl in ["dejavusans-bold.ttf", "liberationsans-bold.ttf", "free-sansbold.ttf"]:
                    bold_found = os.path.join(root, f)
        if reg_found and bold_found:
            try:
                pdfmetrics.registerFont(TTFont("DynSans", reg_found))
                pdfmetrics.registerFont(TTFont("DynSans-Bold", bold_found))
                font_name = "DynSans"
                font_bold = "DynSans-Bold"
            except Exception:
                pass
            
    return font_name, font_bold

FONT_NORM, FONT_BOLD = setup_unicode_fonts()

PAROLA_PROFESORI = "profesori2026"

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

# --- VERIFICARE AUTENTIFICARE ---
if "autentificat" not in st.session_state:
    st.session_state.autentificat = False

if not st.session_state.autentificat:
    st.title("🔒 Catalog Școlar Online — Conectare Profesori")
    st.caption("Colegiul 'Emil Negruțiu' Turda — Clasa a IX-a TH Turism")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Autentificare Cadre Didactice")
        parola_introduse = st.text_input("Introduceți Parola de Acces:", type="password", key="pass_input")
        if st.button("🔑 Conectare în Catalog", type="primary", use_container_width=True):
            if parola_introduse == PAROLA_PROFESORI:
                st.session_state.autentificat = True
                st.success("✅ Conectare reușită!")
                st.rerun()
            else:
                st.error("❌ Parolă incorectă! Vă rugăm să încercați din nou.")
    st.stop()

# --- INTERFAȚĂ PRINCIPALĂ PROFESORI ---
st.title("🏫 Colegiul 'Emil Negruțiu' Turda — Catalog Școlar Online (IX TH Turism)")
st.caption("Aplicație Web securizată pentru gestionare note, absențe și rapoarte")

if not os.path.exists(excel_path):
    st.warning(f"⚠️ Fișierul catalog '{excel_path}' nu a fost găsit în directorul curent. Vă rugăm să îl încărcați pe GitHub în același folder.")

elev_options = [f"{e[0]}. {e[1]} (Matr. {e[2]})" for e in ELEVI]

with st.sidebar:
    st.header("⚙️ Opțiuni Catalog")
    st.success("🔓 Conectat ca Profesor")
    selected_file = st.text_input("Fișier Excel:", value=excel_path)
    
    if os.path.exists(selected_file):
        with open(selected_file, "rb") as f:
            st.download_button(
                label="📥 Descarcă Catalog Excel (.xlsx)",
                data=f,
                file_name=os.path.basename(selected_file),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
    if st.button("🚪 Deconectare (Logout)", use_container_width=True):
        st.session_state.autentificat = False
        st.rerun()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "📊 Fișă Elev", 
    "📋 Centralizator Clasă",
    "📈 Raport Diriginte"
])

# --- GENERARE PDF-URI PENTRU DESCĂRCARE ---
def generate_fisa_elev_pdf(e_info, rows_cg, rows_th):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('TitleStyle', fontName=FONT_BOLD, fontSize=14, leading=18, alignment=1, textColor=HexColor('#1A237E'))
    sub_style = ParagraphStyle('SubStyle', fontName=FONT_BOLD, fontSize=11, leading=15, textColor=HexColor('#0D47A1'))
    body_style = ParagraphStyle('BodyStyle', fontName=FONT_NORM, fontSize=9, leading=12)
    head_style = ParagraphStyle('HeadStyle', fontName=FONT_BOLD, fontSize=9, leading=12, textColor=HexColor('#FFFFFF'))
    
    story = [
        Paragraph("COLEGIUL „EMIL NEGRUȚIU” TURDA", title_style),
        Paragraph("FIȘĂ INDIVIDUALĂ DE EVALUARE ȘI FRECVENȚĂ ȘCOLARĂ", title_style),
        Spacer(1, 10),
        Paragraph(f"<b>Elev:</b> {e_info[1]} | <b>Nr. Matricol:</b> {e_info[2]} | <b>Clasa:</b> a IX-a TH (Turism)", sub_style),
        Spacer(1, 10)
    ]
    
    for title_cat, r_data in [("DISCIPLINE CULTURĂ GENERALĂ", rows_cg), ("MODULE TEHNOLOGICE & PREGĂTIRE PRACTICĂ", rows_th)]:
        story.append(Paragraph(title_cat, sub_style))
        story.append(Spacer(1, 4))
        
        table_data = [[
            Paragraph("<b>Disciplină / Modul</b>", head_style),
            Paragraph("<b>Note</b>", head_style),
            Paragraph("<b>Absențe</b>", head_style),
            Paragraph("<b>Medie</b>", head_style)
        ]]
        for r in r_data:
            table_data.append([
                Paragraph(r["Disciplină / Modul"], body_style),
                Paragraph(r["Note"], body_style),
                Paragraph(r["Absențe"], body_style),
                Paragraph(r["Medie"], body_style)
            ])
            
        t = Table(table_data, colWidths=[200, 160, 110, 50])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1A237E')),
            ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#B0BEC5')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F5F5F5')])
        ]))
        story.append(t)
        story.append(Spacer(1, 12))
        
    story.append(Spacer(1, 15))
    sign_data = [
        [Paragraph("<b>Profesor Diriginte:</b> ____________________", body_style), Paragraph("<b>Director / Conducere:</b> ____________________", body_style)]
    ]
    st_sign = Table(sign_data, colWidths=[260, 260])
    st_sign.setStyle(TableStyle([('VALIGN', (0, 0), (-1, -1), 'MIDDLE')]))
    story.append(st_sign)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_centralizator_pdf(excel_f):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('CTitleStyle', fontName=FONT_BOLD, fontSize=14, leading=18, alignment=1, textColor=HexColor('#1A237E'))
    sub_style = ParagraphStyle('CSubStyle', fontName=FONT_NORM, fontSize=10, leading=13, alignment=1)
    body_style = ParagraphStyle('CBodyStyle', fontName=FONT_NORM, fontSize=8, leading=10)
    head_style = ParagraphStyle('CHeadStyle', fontName=FONT_BOLD, fontSize=8, leading=10, textColor=HexColor('#FFFFFF'))
    
    story = [
        Paragraph("COLEGIUL „EMIL NEGRUȚIU” TURDA — CENTRALIZATOR MEDII & SITUAȚIE ȘCOLARĂ", title_style),
        Paragraph("Clasa a IX-a TH (Domeniul Turism și Alimentație) | An școlar 2026-2027", sub_style),
        Spacer(1, 10)
    ]
    
    table_data = [[
        Paragraph("<b>Nr.</b>", head_style),
        Paragraph("<b>Nume și Prenume</b>", head_style),
        Paragraph("<b>Nr. Matr.</b>", head_style),
        Paragraph("<b>Media CG</b>", head_style),
        Paragraph("<b>Media Mod.</b>", head_style),
        Paragraph("<b>Media Gen.</b>", head_style),
        Paragraph("<b>Purtare</b>", head_style),
        Paragraph("<b>Abs. Nem.</b>", head_style),
        Paragraph("<b>Abs. Mot.</b>", head_style),
        Paragraph("<b>Total Abs.</b>", head_style)
    ]]
    
    if os.path.exists(excel_f):
        try:
            wb = openpyxl.load_workbook(excel_f, data_only=True)
            ws_cen = wb["Centralizator Medii"] if "Centralizator Medii" in wb.sheetnames else None
            ws_abs = wb["Absențe & Purtare"] if "Absențe & Purtare" in wb.sheetnames else None
            
            for idx, e in enumerate(ELEVI):
                s_row = 9 + idx
                mcg = ws_cen.cell(row=s_row, column=5).value if ws_cen else "-"
                mth = ws_cen.cell(row=s_row, column=6).value if ws_cen else "-"
                mgen = ws_cen.cell(row=s_row, column=7).value if ws_cen else "-"
                purt = ws_cen.cell(row=s_row, column=8).value if ws_cen else "10"
                
                abs_nem = ws_abs.cell(row=s_row, column=5).value if ws_abs else "-"
                abs_mot = ws_abs.cell(row=s_row, column=6).value if ws_abs else "-"
                abs_tot = ws_abs.cell(row=s_row, column=7).value if ws_abs else "-"
                
                table_data.append([
                    Paragraph(str(e[0]), body_style),
                    Paragraph(e[1], body_style),
                    Paragraph(str(e[2]), body_style),
                    Paragraph(f"{float(mcg):.2f}" if isinstance(mcg, (int, float)) else str(mcg or "-"), body_style),
                    Paragraph(f"{float(mth):.2f}" if isinstance(mth, (int, float)) else str(mth or "-"), body_style),
                    Paragraph(f"{float(mgen):.2f}" if isinstance(mgen, (int, float)) else str(mgen or "-"), body_style),
                    Paragraph(str(purt or "10"), body_style),
                    Paragraph(str(abs_nem or "0"), body_style),
                    Paragraph(str(abs_mot or "0"), body_style),
                    Paragraph(str(abs_tot or "0"), body_style)
                ])
            wb.close()
        except Exception:
            pass
            
    t = Table(table_data, colWidths=[25, 220, 65, 60, 60, 60, 50, 55, 55, 55])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1A237E')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#B0BEC5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [HexColor('#FFFFFF'), HexColor('#F5F5F5')])
    ]))
    story.append(t)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_raport_pdf(excel_f):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('RTitleStyle', fontName=FONT_BOLD, fontSize=14, leading=18, alignment=1, textColor=HexColor('#1A237E'))
    sub_style = ParagraphStyle('RSubStyle', fontName=FONT_BOLD, fontSize=11, leading=15, textColor=HexColor('#0D47A1'))
    body_style = ParagraphStyle('RBodyStyle', fontName=FONT_NORM, fontSize=10, leading=14)
    head_style = ParagraphStyle('RHeadStyle', fontName=FONT_BOLD, fontSize=10, leading=13, textColor=HexColor('#FFFFFF'))
    
    story = [
        Paragraph("COLEGIUL „EMIL NEGRUȚIU” TURDA", title_style),
        Paragraph("RAPORT EVALUATIV AL DIRIGINTELUI — CLASA a IX-a TH", title_style),
        Spacer(1, 10),
        Paragraph("<b>An școlar:</b> 2026-2027 | <b>Especialitatea:</b> Turism și Alimentație (Lucrător Hotelier)", body_style),
        Spacer(1, 10),
        Paragraph("I. SITUAȚIA GENERALĂ A CLASEI", sub_style),
        Spacer(1, 4)
    ]
    
    info_data = [
        [Paragraph("<b>Indicator</b>", head_style), Paragraph("<b>Valoare / Stare</b>", head_style)],
        [Paragraph("Total Elevi Înscriși", body_style), Paragraph("32 elevi", body_style)],
        [Paragraph("Clasă / Profil", body_style), Paragraph("a IX-a TH — Turism și Alimentație", body_style)],
        [Paragraph("Stare Salvări Catalog", body_style), Paragraph("Actualizat la zi în baza de date Excel", body_style)],
        [Paragraph("Promovabilitate Estimată", body_style), Paragraph("100%", body_style)]
    ]
    t = Table(info_data, colWidths=[260, 260])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), HexColor('#1A237E')),
        ('GRID', (0, 0), (-1, -1), 0.5, HexColor('#B0BEC5')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
    ]))
    story.append(t)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("II. OBSERVAȚII ȘI MĂSURI DISCIPLINARE / FRECVENȚĂ", sub_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("• Frecvența elevilor este monitorizată zilnic și actualizată în catalogul electronic.", body_style))
    story.append(Paragraph("• Pentru elevii care acumulează absențe nemotivate se aplică scăderea notei la purtare (-1 punct la 20 de absențe nemotivate).", body_style))
    story.append(Paragraph("• Se menține legătura permanentă cu părinții/reprezentanții legali prin portalul securizat online.", body_style))
    
    story.append(Spacer(1, 30))
    sign_data = [
        [Paragraph("<b>Profesor Diriginte:</b> ____________________", body_style), Paragraph("<b>Data:</b> _____________", body_style)]
    ]
    st_sign = Table(sign_data, colWidths=[320, 200])
    story.append(st_sign)
    
    doc.build(story)
    buffer.seek(0)
    return buffer

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
                    if cell_n.value is None or str(cell_n.value).strip() == "":
                        cell_n.value = int(nota_val)
                        cell_d.value = str(data_nota)
                        cell_d.number_format = '@'
                        slot_found = True
                        slot_num = k + 1
                        break
                if slot_found:
                    wb.save(selected_file)
                    st.success(f"✅ Notă salvată: {nota_val} pe {data_nota} la {materii[mat_idx_n]} pentru {ELEVI[elev_idx_n][1]}")
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
                
                abs_val = f"{data_abs.strip()}m" if is_mot else data_abs.strip()
                
                slot_found = False
                for k in range(8):
                    a_col = start_col + 11 + k
                    cell_a = ws.cell(row=student_row, column=a_col)
                    if cell_a.value is None or str(cell_a.value).strip() == "":
                        cell_a.value = abs_val
                        cell_a.number_format = '@'
                        slot_found = True
                        break
                if slot_found:
                    wb.save(selected_file)
                    st.success(f"✅ Absență salvată: '{abs_val}' la {materii_a[mat_idx_a]} pentru {ELEVI[elev_idx_a][1]}")
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
                for k in range(8):
                    a_col = start_col + 11 + k
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
                    st.success(f"✅ Absență motivată ('{target_d}m') pentru {ELEVI[elev_idx_m][1]} la {materii_m[mat_idx_m]}")
                elif not found:
                    st.warning(f"Nu s-a găsit nicio absență nemotivată cu data '{target_d}'.")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare: {ex}")

# --- TAB 4: FIȘĂ ELEV ---
with tab4:
    st.subheader("Fișă Elev & Rezumat")
    col_e1, col_e2 = st.columns([3, 1])
    with col_e1:
        elev_idx_v = st.selectbox("Alege Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_v")
        
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            e_info = ELEVI[elev_idx_v]
            
            rows_cg, rows_th = [], []
            for cat_title, sheet_n, sub_list, r_list in [("Cultură Generală", "Cultură Generală", DISCIPLINE_CG, rows_cg), ("Module Tehnologice", "Module Tehnologice", MODULE_TH, rows_th)]:
                ws = wb[sheet_n]
                s_row = 9 + elev_idx_v
                for s_name, start_col in sub_list:
                    notes = [str(ws.cell(row=s_row, column=start_col + (k * 2)).value) for k in range(5) if ws.cell(row=s_row, column=start_col + (k * 2)).value is not None and str(ws.cell(row=s_row, column=start_col + (k * 2)).value).strip() != ""]
                    absences = [str(ws.cell(row=s_row, column=start_col + 11 + k).value) for k in range(8) if ws.cell(row=s_row, column=start_col + 11 + k).value is not None and str(ws.cell(row=s_row, column=start_col + 11 + k).value).strip() != ""]
                    media_val = ws.cell(row=s_row, column=start_col + 19).value
                    media_str = f"{float(media_val):.2f}" if isinstance(media_val, (int, float)) else (str(media_val) if media_val else "-")
                    
                    r_list.append({
                        "Disciplină / Modul": s_name,
                        "Note": ", ".join(notes) if notes else "Fără note",
                        "Absențe": ", ".join(absences) if absences else "Fără absențe",
                        "Medie": media_str
                    })
            wb.close()
            
            with col_e2:
                st.write("")
                st.write("")
                pdf_bytes_fisa = generate_fisa_elev_pdf(e_info, rows_cg, rows_th)
                st.download_button(
                    label="🖨️ Descarcă Fișă PDF",
                    data=pdf_bytes_fisa,
                    file_name=f"Fisa_Elev_{e_info[2].replace('/', '_')}.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True
                )
                
            st.markdown(f"### 👤 {e_info[1]} (Matricol {e_info[2]})")
            st.markdown("#### Cultură Generală")
            st.dataframe(rows_cg, use_container_width=True)
            st.markdown("#### Module Tehnologice")
            st.dataframe(rows_th, use_container_width=True)
            
        except Exception as ex:
            st.error(f"Eroare la citire fișă: {ex}")
    else:
        st.info("Fișierul Excel nu a fost încărcat încă.")

# --- TAB 5: CENTRALIZATOR CLASĂ ---
with tab5:
    st.subheader("📋 Centralizator Medii & Situație Școlară Clasă")
    col_c1, col_c2 = st.columns([3, 1])
    with col_c2:
        if os.path.exists(selected_file):
            pdf_bytes_cen = generate_centralizator_pdf(selected_file)
            st.download_button(
                label="🖨️ Descarcă Centralizator PDF",
                data=pdf_bytes_cen,
                file_name="Centralizator_Clasa_IX_TH.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_cen = wb["Centralizator Medii"] if "Centralizator Medii" in wb.sheetnames else None
            ws_abs = wb["Absențe & Purtare"] if "Absențe & Purtare" in wb.sheetnames else None
            
            cen_data = []
            for idx, e in enumerate(ELEVI):
                s_row = 9 + idx
                mcg = ws_cen.cell(row=s_row, column=5).value if ws_cen else "-"
                mth = ws_cen.cell(row=s_row, column=6).value if ws_cen else "-"
                mgen = ws_cen.cell(row=s_row, column=7).value if ws_cen else "-"
                purt = ws_cen.cell(row=s_row, column=8).value if ws_cen else "10"
                abs_tot = ws_abs.cell(row=s_row, column=7).value if ws_abs else "-"
                
                cen_data.append({
                    "Nr.": e[0],
                    "Nume și Prenume": e[1],
                    "Matricol": e[2],
                    "Media CG": f"{float(mcg):.2f}" if isinstance(mcg, (int, float)) else str(mcg or "-"),
                    "Media Module": f"{float(mth):.2f}" if isinstance(mth, (int, float)) else str(mth or "-"),
                    "Media Generală": f"{float(mgen):.2f}" if isinstance(mgen, (int, float)) else str(mgen or "-"),
                    "Purtare": str(purt or "10"),
                    "Total Absențe": str(abs_tot or "0")
                })
            wb.close()
            st.dataframe(cen_data, use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare la citire centralizator: {ex}")

# --- TAB 6: RAPORT DIRIGINTE ---
with tab6:
    st.subheader("📈 Raport Sintetic al Dirigintelui")
    col_r1, col_r2 = st.columns([3, 1])
    with col_r2:
        if os.path.exists(selected_file):
            pdf_bytes_rap = generate_raport_pdf(selected_file)
            st.download_button(
                label="🖨️ Descarcă Raport PDF",
                data=pdf_bytes_rap,
                file_name="Raport_Diriginte_IX_TH.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )
            
    st.markdown("#### Indicatori Cheie de Performanță Clasă")
    st.json({
        "Total Elevi Înscriși": 32,
        "Profil / Calificare": "Clasa a IX-a TH — Turism și Alimentație",
        "Promovabilitate Estimată": "100%",
        "Stare Catalog": "Actualizat în timp real (Excel & Bază de date)"
    })
