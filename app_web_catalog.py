import datetime
import io
import os
import openpyxl
import streamlit as st

from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

st.set_page_config(
    page_title="Catalog Școlar Online IX TH",
    page_icon="🏫",
    layout="wide"
)

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

# --- PDF GENERATION HELPERS ---
def generate_student_pdf(excel_p, elev_idx):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm
    )
    usable_w = A4[0] - 30*mm
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=14, leading=18, alignment=TA_CENTER, textColor=HexColor('#1B365D'))
    sub_style = ParagraphStyle('S', fontName='Helvetica', fontSize=10, leading=14, alignment=TA_CENTER, textColor=HexColor('#4B6B94'))
    h2_style = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=HexColor('#1B365D'), spaceBefore=10, spaceAfter=4)
    tbl_hdr = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=HexColor('#FFFFFF'))
    tbl_bdy = ParagraphStyle('TB', fontName='Helvetica', fontSize=8.5, leading=11, textColor=HexColor('#222222'))
    tbl_bdy_b = ParagraphStyle('TBB', fontName='Helvetica-Bold', fontSize=8.5, leading=11, textColor=HexColor('#1B365D'))
    
    e_info = ELEVI[elev_idx]
    
    story.append(Paragraph("COLEGIUL 'EMIL NEGRUȚIU' TURDA", title_style))
    story.append(Paragraph("FIȘĂ INDIVIDUALĂ DE EVALUARE ȘI FRECVENȚĂ — AN ȘCOLAR 2026-2027", sub_style))
    story.append(Spacer(1, 10))
    
    info_data = [
        [Paragraph(f"<b>ELEV:</b> {e_info[1]}", tbl_bdy), Paragraph(f"<b>CLASA:</b> a IX-a TH", tbl_bdy)],
        [Paragraph(f"<b>NR. MATRICOL:</b> {e_info[2]}", tbl_bdy), Paragraph(f"<b>REG. MATRICOL:</b> {e_info[3]}", tbl_bdy)]
    ]
    t_info = Table(info_data, colWidths=[usable_w*0.5, usable_w*0.5])
    t_info.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor('#F0F4F8')),
        ('BOX', (0,0), (-1,-1), 1, HexColor('#D0DCE5')),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_info)
    story.append(Spacer(1, 12))
    
    wb = openpyxl.load_workbook(excel_p, data_only=True)
    s_row = 9 + elev_idx
    
    for cat_title, sheet_n, sub_list in [("DISCIPLINE CULTURĂ GENERALĂ", "Cultură Generală", DISCIPLINE_CG), ("MODULE TEHNOLOGICE (HORECA / TURISM)", "Module Tehnologice", MODULE_TH)]:
        story.append(Paragraph(cat_title, h2_style))
        ws = wb[sheet_n]
        
        table_rows = [[
            Paragraph("DISCIPLINĂ / MODUL", tbl_hdr),
            Paragraph("NOTE OBȚINUTE", tbl_hdr),
            Paragraph("ABSENȚE", tbl_hdr),
            Paragraph("MEDIE", tbl_hdr)
        ]]
        
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
            
            table_rows.append([
                Paragraph(s_name, tbl_bdy),
                Paragraph(", ".join(notes) if notes else "-", tbl_bdy),
                Paragraph(", ".join(absences) if absences else "-", tbl_bdy),
                Paragraph(media_str, tbl_bdy_b)
            ])
            
        t_sec = Table(table_rows, colWidths=[usable_w*0.4, usable_w*0.25, usable_w*0.23, usable_w*0.12])
        t_sec.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), HexColor('#1B365D')),
            ('GRID', (0,0), (-1,-1), 0.5, HexColor('#CBD5E1')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#FFFFFF'), HexColor('#F8FAFC')]),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 4),
            ('ALIGN', (3,1), (3,-1), 'CENTER')
        ]))
        story.append(t_sec)
        story.append(Spacer(1, 10))
        
    wb.close()
    
    story.append(Spacer(1, 15))
    sig_data = [
        [Paragraph("<b>Profesor Diriginte,</b>", tbl_bdy), Paragraph("<b>Director / Conducere,</b>", tbl_bdy)],
        [Paragraph("_______________________", tbl_bdy), Paragraph("_______________________", tbl_bdy)]
    ]
    t_sig = Table(sig_data, colWidths=[usable_w*0.5, usable_w*0.5])
    t_sig.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_sig)
    
    doc.build(story)
    return buffer.getvalue()

def generate_centralizator_pdf(excel_p):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=10*mm, rightMargin=10*mm, topMargin=10*mm, bottomMargin=10*mm
    )
    usable_w = landscape(A4)[0] - 20*mm
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=13, leading=16, alignment=TA_CENTER, textColor=HexColor('#1B365D'))
    sub_style = ParagraphStyle('S', fontName='Helvetica', fontSize=9, leading=12, alignment=TA_CENTER, textColor=HexColor('#4B6B94'))
    tbl_hdr = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=8, leading=10, textColor=HexColor('#FFFFFF'), alignment=TA_CENTER)
    tbl_bdy = ParagraphStyle('TB', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=HexColor('#222222'))
    tbl_bdy_c = ParagraphStyle('TBC', fontName='Helvetica', fontSize=7.5, leading=9.5, textColor=HexColor('#222222'), alignment=TA_CENTER)
    
    story.append(Paragraph("COLEGIUL 'EMIL NEGRUȚIU' TURDA — CENTRALIZATOR MEDII ȘI SITUAȚIE ȘCOLARĂ", title_style))
    story.append(Paragraph("Clasa a IX-a TH (Turism și Alimentație) | An Școlar 2026-2027", sub_style))
    story.append(Spacer(1, 8))
    
    table_rows = [[
        Paragraph("<b>Nr.</b>", tbl_hdr),
        Paragraph("<b>Nume și Prenume Elev</b>", tbl_hdr),
        Paragraph("<b>Matr.</b>", tbl_hdr),
        Paragraph("<b>Media CG</b>", tbl_hdr),
        Paragraph("<b>Media TH</b>", tbl_hdr),
        Paragraph("<b>Media Gen.</b>", tbl_hdr),
        Paragraph("<b>Purtare</b>", tbl_hdr),
        Paragraph("<b>Abs. Nem.</b>", tbl_hdr),
        Paragraph("<b>Abs. Mot.</b>", tbl_hdr),
        Paragraph("<b>Tot. Abs.</b>", tbl_hdr)
    ]]
    
    wb = openpyxl.load_workbook(excel_p, data_only=True)
    ws_cg = wb["Cultură Generală"]
    ws_th = wb["Module Tehnologice"]
    
    for idx, e in enumerate(ELEVI):
        s_row = 9 + idx
        cg_medias, th_medias = [], []
        tot_abs_nem, tot_abs_mot = 0, 0
        
        for s_name, start_col in DISCIPLINE_CG:
            m_val = ws_cg.cell(row=s_row, column=start_col + 19).value
            if isinstance(m_val, (int, float)):
                cg_medias.append(float(m_val))
            for k in range(8):
                a_val = ws_cg.cell(row=s_row, column=start_col + 11 + k).value
                if a_val is not None and str(a_val).strip() != "":
                    if str(a_val).strip().endswith('m'):
                        tot_abs_mot += 1
                    else:
                        tot_abs_nem += 1
                        
        for s_name, start_col in MODULE_TH:
            m_val = ws_th.cell(row=s_row, column=start_col + 19).value
            if isinstance(m_val, (int, float)):
                th_medias.append(float(m_val))
            for k in range(8):
                a_val = ws_th.cell(row=s_row, column=start_col + 11 + k).value
                if a_val is not None and str(a_val).strip() != "":
                    if str(a_val).strip().endswith('m'):
                        tot_abs_mot += 1
                    else:
                        tot_abs_nem += 1
                        
        avg_cg = sum(cg_medias)/len(cg_medias) if cg_medias else None
        avg_th = sum(th_medias)/len(th_medias) if th_medias else None
        all_m = cg_medias + th_medias
        avg_gen = sum(all_m)/len(all_m) if all_m else None
        purtare = max(1, 10 - (tot_abs_nem // 20))
        
        table_rows.append([
            Paragraph(str(e[0]), tbl_bdy_c),
            Paragraph(e[1], tbl_bdy),
            Paragraph(str(e[2]), tbl_bdy_c),
            Paragraph(f"{avg_cg:.2f}" if avg_cg else "-", tbl_bdy_c),
            Paragraph(f"{avg_th:.2f}" if avg_th else "-", tbl_bdy_c),
            Paragraph(f"{avg_gen:.2f}" if avg_gen else "-", tbl_bdy_c),
            Paragraph(str(purtare), tbl_bdy_c),
            Paragraph(str(tot_abs_nem), tbl_bdy_c),
            Paragraph(str(tot_abs_mot), tbl_bdy_c),
            Paragraph(str(tot_abs_nem + tot_abs_mot), tbl_bdy_c)
        ])
        
    wb.close()
    
    col_w = [usable_w*0.04, usable_w*0.34, usable_w*0.06, usable_w*0.08, usable_w*0.08, usable_w*0.08, usable_w*0.08, usable_w*0.08, usable_w*0.08, usable_w*0.08]
    t_cent = Table(table_rows, colWidths=col_w, repeatRows=1)
    t_cent.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#1B365D')),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#FFFFFF'), HexColor('#F8FAFC')]),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('PADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t_cent)
    
    doc.build(story)
    return buffer.getvalue()

def generate_raport_diriginte_pdf(excel_p):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=15*mm, rightMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm
    )
    usable_w = A4[0] - 30*mm
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', fontName='Helvetica-Bold', fontSize=14, leading=18, alignment=TA_CENTER, textColor=HexColor('#1B365D'))
    sub_style = ParagraphStyle('S', fontName='Helvetica', fontSize=10, leading=14, alignment=TA_CENTER, textColor=HexColor('#4B6B94'))
    h2_style = ParagraphStyle('H2', fontName='Helvetica-Bold', fontSize=11, leading=15, textColor=HexColor('#1B365D'), spaceBefore=12, spaceAfter=6)
    tbl_hdr = ParagraphStyle('TH', fontName='Helvetica-Bold', fontSize=9, leading=11, textColor=HexColor('#FFFFFF'))
    tbl_bdy = ParagraphStyle('TB', fontName='Helvetica', fontSize=9, leading=12, textColor=HexColor('#222222'))
    tbl_bdy_c = ParagraphStyle('TBC', fontName='Helvetica-Bold', fontSize=9, leading=12, textColor=HexColor('#1B365D'), alignment=TA_CENTER)
    
    story.append(Paragraph("COLEGIUL 'EMIL NEGRUȚIU' TURDA", title_style))
    story.append(Paragraph("RAPORT SEMESTRIAL / ANUAL AL DIRIGINTELUI — CLASA A IX-A TH", sub_style))
    story.append(Spacer(1, 12))
    
    wb = openpyxl.load_workbook(excel_p, data_only=True)
    ws_cg, ws_th = wb["Cultură Generală"], wb["Module Tehnologice"]
    tot_nem, tot_mot = 0, 0
    all_student_medias = []
    
    for idx in range(len(ELEVI)):
        s_row = 9 + idx
        s_medias = []
        for s_name, start_col in DISCIPLINE_CG:
            m_val = ws_cg.cell(row=s_row, column=start_col + 19).value
            if isinstance(m_val, (int, float)):
                s_medias.append(float(m_val))
            for k in range(8):
                a_val = ws_cg.cell(row=s_row, column=start_col + 11 + k).value
                if a_val is not None and str(a_val).strip() != "":
                    if str(a_val).strip().endswith('m'):
                        tot_mot += 1
                    else:
                        tot_nem += 1
        for s_name, start_col in MODULE_TH:
            m_val = ws_th.cell(row=s_row, column=start_col + 19).value
            if isinstance(m_val, (int, float)):
                s_medias.append(float(m_val))
            for k in range(8):
                a_val = ws_th.cell(row=s_row, column=start_col + 11 + k).value
                if a_val is not None and str(a_val).strip() != "":
                    if str(a_val).strip().endswith('m'):
                        tot_mot += 1
                    else:
                        tot_nem += 1
        if s_medias:
            all_student_medias.append(sum(s_medias)/len(s_medias))
            
    wb.close()
    
    avg_class = sum(all_student_medias)/len(all_student_medias) if all_student_medias else 0
    tot_abs = tot_nem + tot_mot
    avg_abs_per_student = tot_abs / len(ELEVI)
    
    story.append(Paragraph("I. INDICATORI CHEIE AI CLASEI", h2_style))
    stat_rows = [
        [Paragraph("<b>INDICATOR</b>", tbl_hdr), Paragraph("<b>VALOARE</b>", tbl_hdr)],
        [Paragraph("Total Elevi Înscriși", tbl_bdy), Paragraph(str(len(ELEVI)), tbl_bdy_c)],
        [Paragraph("Media Generală a Clasei", tbl_bdy), Paragraph(f"{avg_class:.2f}" if avg_class else "-", tbl_bdy_c)],
        [Paragraph("Total Absențe Nemotivate", tbl_bdy), Paragraph(str(tot_nem), tbl_bdy_c)],
        [Paragraph("Total Absențe Motivate", tbl_bdy), Paragraph(str(tot_mot), tbl_bdy_c)],
        [Paragraph("Total General Absențe", tbl_bdy), Paragraph(str(tot_abs), tbl_bdy_c)],
        [Paragraph("Media Absențelor per Elev", tbl_bdy), Paragraph(f"{avg_abs_per_student:.1f}", tbl_bdy_c)]
    ]
    t_stat = Table(stat_rows, colWidths=[usable_w*0.7, usable_w*0.3])
    t_stat.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), HexColor('#1B365D')),
        ('GRID', (0,0), (-1,-1), 0.5, HexColor('#CBD5E1')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [HexColor('#FFFFFF'), HexColor('#F8FAFC')]),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t_stat)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("II. CONCLUZII ȘI MĂSURI PROPUSE", h2_style))
    p_text = Paragraph("Frecvența și situația școlară sunt monitorizate săptămânal. Pentru elevii cu absențe nemotivate se vor transmite înștiințări scrise părinților și se vor stabili ore de consiliere cu dirigintele și psihologul școlar.", tbl_bdy)
    story.append(p_text)
    story.append(Spacer(1, 20))
    
    sig_data = [
        [Paragraph("<b>Profesor Diriginte,</b>", tbl_bdy), Paragraph("<b>Director / Conducere,</b>", tbl_bdy)],
        [Paragraph("_______________________", tbl_bdy), Paragraph("_______________________", tbl_bdy)]
    ]
    t_sig = Table(sig_data, colWidths=[usable_w*0.5, usable_w*0.5])
    t_sig.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t_sig)
    
    doc.build(story)
    return buffer.getvalue()


# --- STREAMLIT UI SECURITY & CHECK ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 Autentificare Profesori — Catalog IX TH")
    parola_input = st.text_input("Introduceți parola de acces:", type="password")
    if st.button("🔓 Conectare", type="primary"):
        if parola_input == PAROLA_PROFESORI:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Parolă incorectă!")
    st.stop()

# --- MAIN APP UI ---
st.title("🏫 Colegiul 'Emil Negruțiu' Turda — Catalog Școlar Online (IX TH Turism)")
st.caption("Aplicație Web Streamlit pentru gestionare note, absențe și generare rapoarte PDF")

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
        st.session_state.authenticated = False
        st.rerun()

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
                abs_val = f"{data_abs.strip()}m" if is_mot else data_abs.strip()
                
                slot_found = False
                for k in range(8):
                    a_col = start_col + 11 + k
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
    col_v1, col_v2 = st.columns([3, 1])
    with col_v1:
        elev_idx_v = st.selectbox("Alege Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_v")
    with col_v2:
        st.write("")
        st.write("")
        if os.path.exists(selected_file):
            try:
                pdf_fisa = generate_student_pdf(selected_file, elev_idx_v)
                st.download_button(
                    label="🖨️ Descarcă Fișă PDF",
                    data=pdf_fisa,
                    file_name=f"Fisa_Elev_{ELEVI[elev_idx_v][1].replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as ex:
                st.error(f"Eroare PDF: {ex}")
                
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            e_info = ELEVI[elev_idx_v]
            st.markdown(f"### 👤 {e_info[1]} (Matricol {e_info[2]})")
            
            for cat_title, sheet_n, sub_list in [("Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"#### {cat_title}")
                ws = wb[sheet_n]
                s_row = 9 + elev_idx_v
                
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
                        "Note": ", ".join(notes) if notes else "Fără note",
                        "Absențe": ", ".join(absences) if absences else "Fără absențe",
                        "Medie": media_str
                    })
                st.dataframe(rows_data, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire fișă: {ex}")

# --- TAB 5: CENTRALIZATOR CLASĂ ---
with tab5:
    st.subheader("📋 Centralizator Clasă (Situație Generală)")
    if os.path.exists(selected_file):
        col_c1, col_c2 = st.columns([3, 1])
        with col_c1:
            st.info("Centralizatorul general include mediile la Cultură Generală, Module Tehnologice, Media Generală, Nota la Purtare și Absențele.")
        with col_c2:
            try:
                pdf_cent = generate_centralizator_pdf(selected_file)
                st.download_button(
                    label="🖨️ Descarcă Centralizator PDF",
                    data=pdf_cent,
                    file_name="Centralizator_Clasa_IX_TH.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as ex:
                st.error(f"Eroare PDF: {ex}")
                
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_cg, ws_th = wb["Cultură Generală"], wb["Module Tehnologice"]
            
            cent_rows = []
            for idx, e in enumerate(ELEVI):
                s_row = 9 + idx
                cg_medias, th_medias = [], []
                tot_abs_nem, tot_abs_mot = 0, 0
                
                for s_name, start_col in DISCIPLINE_CG:
                    m_val = ws_cg.cell(row=s_row, column=start_col + 19).value
                    if isinstance(m_val, (int, float)):
                        cg_medias.append(float(m_val))
                    for k in range(8):
                        a_val = ws_cg.cell(row=s_row, column=start_col + 11 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            if str(a_val).strip().endswith('m'):
                                tot_abs_mot += 1
                            else:
                                tot_abs_nem += 1
                                
                for s_name, start_col in MODULE_TH:
                    m_val = ws_th.cell(row=s_row, column=start_col + 19).value
                    if isinstance(m_val, (int, float)):
                        th_medias.append(float(m_val))
                    for k in range(8):
                        a_val = ws_th.cell(row=s_row, column=start_col + 11 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            if str(a_val).strip().endswith('m'):
                                tot_abs_mot += 1
                            else:
                                tot_abs_nem += 1
                                
                avg_cg = sum(cg_medias)/len(cg_medias) if cg_medias else None
                avg_th = sum(th_medias)/len(th_medias) if th_medias else None
                all_m = cg_medias + th_medias
                avg_gen = sum(all_m)/len(all_m) if all_m else None
                purtare = max(1, 10 - (tot_abs_nem // 20))
                
                cent_rows.append({
                    "Nr.": e[0],
                    "Nume și Prenume": e[1],
                    "Matricol": e[2],
                    "Media CG": f"{avg_cg:.2f}" if avg_cg else "-",
                    "Media TH": f"{avg_th:.2f}" if avg_th else "-",
                    "Media Generală": f"{avg_gen:.2f}" if avg_gen else "-",
                    "Purtare": purtare,
                    "Abs. Nem.": tot_abs_nem,
                    "Abs. Mot.": tot_abs_mot,
                    "Total Abs.": tot_abs_nem + tot_abs_mot
                })
            wb.close()
            st.dataframe(cent_rows, use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare centralizator: {ex}")

# --- TAB 6: RAPORT DIRIGINTE ---
with tab6:
    st.subheader("📈 Raport Diriginte & Indicatori Clasă")
    if os.path.exists(selected_file):
        col_r1, col_r2 = st.columns([3, 1])
        with col_r1:
            st.info("Raportul conține sinteza de performanță, frecvență și indicatorii generali ai clasei.")
        with col_r2:
            try:
                pdf_rap = generate_raport_diriginte_pdf(selected_file)
                st.download_button(
                    label="🖨️ Descarcă Raport PDF",
                    data=pdf_rap,
                    file_name="Raport_Diriginte_IX_TH.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as ex:
                st.error(f"Eroare PDF: {ex}")
                
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_cg, ws_th = wb["Cultură Generală"], wb["Module Tehnologice"]
            tot_nem, tot_mot = 0, 0
            all_student_medias = []
            
            for idx in range(len(ELEVI)):
                s_row = 9 + idx
                s_medias = []
                for s_name, start_col in DISCIPLINE_CG:
                    m_val = ws_cg.cell(row=s_row, column=start_col + 19).value
                    if isinstance(m_val, (int, float)):
                        s_medias.append(float(m_val))
                    for k in range(8):
                        a_val = ws_cg.cell(row=s_row, column=start_col + 11 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            if str(a_val).strip().endswith('m'):
                                tot_mot += 1
                            else:
                                tot_nem += 1
                for s_name, start_col in MODULE_TH:
                    m_val = ws_th.cell(row=s_row, column=start_col + 19).value
                    if isinstance(m_val, (int, float)):
                        s_medias.append(float(m_val))
                    for k in range(8):
                        a_val = ws_th.cell(row=s_row, column=start_col + 11 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            if str(a_val).strip().endswith('m'):
                                tot_mot += 1
                            else:
                                tot_nem += 1
                if s_medias:
                    all_student_medias.append(sum(s_medias)/len(s_medias))
            wb.close()
            
            avg_class = sum(all_student_medias)/len(all_student_medias) if all_student_medias else 0
            tot_abs = tot_nem + tot_mot
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Elevi", len(ELEVI))
            c2.metric("Media Clasei", f"{avg_class:.2f}" if avg_class else "-")
            c3.metric("Absențe Nemotivate", tot_nem)
            c4.metric("Absențe Motivate", tot_mot)
        except Exception as ex:
            st.error(f"Eroare raport: {ex}")
