import datetime
import os
import openpyxl
import streamlit as st
import urllib.request
import urllib.parse
import json
import base64
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io

st.set_page_config(
    page_title="Catalog Școlar Online IX TH",
    page_icon="🏫",
    layout="wide"
)

# --- SINCRONIZARE AUTOMATĂ PE GITHUB VIA API ---
def push_to_github(file_path):
    token = os.environ.get("GITHUB_TOKEN") or st.secrets.get("GITHUB_TOKEN", "")
    if not token:
        return
    try:
        repo = "profudeconta-sketch/catalog-online"
        filename = os.path.basename(file_path)
        url = f"https://api.github.com/repos/{repo}/contents/{filename}"
        
        req_get = urllib.request.Request(
            url, 
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "StreamlitApp"
            }
        )
        sha = None
        try:
            with urllib.request.urlopen(req_get, timeout=5) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                sha = data.get('sha')
        except Exception:
            pass

        with open(file_path, "rb") as f:
            content_b64 = base64.b64encode(f.read()).decode('utf-8')

        payload = {
            "message": f"Update automat catalog: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
            "content": content_b64
        }
        if sha:
            payload["sha"] = sha

        req_put = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "StreamlitApp"
            },
            method="PUT"
        )
        with urllib.request.urlopen(req_put, timeout=5) as resp:
            if 200 <= resp.status <= 299:
                st.toast("☁️ Modificările s-au sincronizat automat pe GitHub!")
    except Exception:
        pass

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
    
    font_name = "Helvetica"
    font_bold_name = "Helvetica-Bold"
    
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
    st.markdown("---")
    st.info("""
    **© Software Creat și Deținut de Prof. Ec. Gherman Octavian-Theodor**
    *Acest program este protejat de legea privind drepturile de autor (Legea nr. 8/1996) și legislația internațională aplicabilă.*
    *Orice descărcare, multiplicare, distribuire sau utilizare neautorizată se pedepsește conform legii.*
    **🚫 ESTE STRICT INTERZISĂ COMERCIALIZAREA ACESTUI PRODUS!**
    *Acest produs se utilizează în mod gratuit exclusiv de către persoanele cărora autorul le conferă în mod explicit acest drept.*
    """)
    st.stop()

# Lista celor 32 de elevi
ELEVI = [
    (1, "ALBAC V. ALEXANDRU ANDREI", 13, "126/76", "2951"),
    (2, "BARA D. ADRIAN DANIEL", 14, "126/77", "6234"),
    (3, "BUDACĂ I. MARIA MADALINA", 15, "126/78", "9233"),
    (4, "BUDULĂU I.M. VLAD IOAN", 16, "126/79", "9385"),
    (5, "CHESZOVAN D.E. IRINA JULIETA", 17, "126/80", "2681"),
    (6, "CIURCUI V. DIANA", 18, "126/81", "4658"),
    (7, "CORDIȘ M.C. EDUARD IONUȚ", 19, "126/82", "7891"),
    (8, "DEMETER D.C. DENIS RĂZVAN", 20, "126/83", "9975"),
    (9, "FERENCZI E.C. MEDEA MARICARMEN", 21, "126/84", "9042"),
    (10, "FLOREA V. FLAVIU CRISTIAN", 22, "126/85", "8226"),
    (11, "GHERMAN M.I. DAVID MARIUS", 23, "126/86", "4931"),
    (12, "LOBONȚ M. MIHNEA", 24, "126/87", "1041"),
    (13, "LUKACS A.L. LORENA DENISA", 25, "126/88", "2322"),
    (14, "MAGYARI A.M. ANDREI", 26, "126/89", "2814"),
    (15, "MARCOVICI L.S. IOANA DENISA", 27, "126/90", "5706"),
    (16, "MARIAN M.I. MIHAELA DARIA", 28, "126/91", "2606"),
    (17, "MATEI V.C. ROXANA MIHAELA", 29, "126/92", "8367"),
    (18, "MENCU R.R. DIANA OLIVIA", 30, "126/93", "1188"),
    (19, "MUNTEANU V.N. ELENA", 31, "126/94", "9032"),
    (20, "NAP A.C. ALEXANDRA MARIA", 32, "126/95", "6148"),
    (21, "PETELEU C.A. CLAUDIA MARIA", 33, "126/96", "4444"),
    (22, "POP D. ANDRA MARIA", 34, "126/97", "7508"),
    (23, "POP M.V. LARISA ANDREEA", 35, "126/98", "5120"),
    (24, "POP I.C. ROBERT EUGEN", 36, "126/99", "6696"),
    (25, "POPA C.F. ILINCA", 37, "126/100", "6843"),
    (26, "PUICA G. GEORGE ROBERT", 38, "126/101", "7166"),
    (27, "RĂDUȚ I.M. ADELINA IOANA", 39, "128/1", "9414"),
    (28, "ȘIPOȘ T.R. DAVID ADRIAN", 40, "128/2", "2250"),
    (29, "TRIF S.D. TUȘA DANIEL", 41, "128/3", "6577"),
    (30, "TUȘINEAN S.V. IRINA", 42, "128/4", "2469"),
    (31, "ȚANDEA M. LUCAS MIHAI", 43, "128/5", "9815"),
    (32, "VRÎNCIANU M.G. DELIA MARIA", 44, "128/6", "5786")
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

def update_excel_computed_values(file_path):
    if not os.path.exists(file_path):
        return
    try:
        wb = openpyxl.load_workbook(file_path)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        ws_c = wb["Centralizator Medii"] if "Centralizator Medii" in wb.sheetnames else None
        ws_a = wb["Absențe & Purtare"] if "Absențe & Purtare" in wb.sheetnames else None

        for idx in range(len(ELEVI)):
            s_row = 9 + idx
            
            cg_avgs = []
            tot_abs_nem_cg = 0
            tot_abs_mot_cg = 0
            for _, start_col in DISCIPLINE_CG:
                notes = []
                for k in range(10):
                    v = ws_cg.cell(row=s_row, column=start_col + k*2).value
                    if v is not None and str(v).strip() != "" and not str(v).startswith("="):
                        try:
                            notes.append(float(v))
                        except Exception:
                            pass
                if notes:
                    avg = round(sum(notes)/len(notes), 2)
                    cg_avgs.append(avg)
                    ws_cg.cell(row=s_row, column=start_col + 20).value = avg
                else:
                    ws_cg.cell(row=s_row, column=start_col + 20).value = None

                for k in range(30):
                    av = ws_cg.cell(row=s_row, column=start_col + 21 + k).value
                    if av is not None and str(av).strip() != "" and not str(av).startswith("="):
                        s_a = str(av).strip()
                        if s_a.endswith('m') or s_a.endswith('M'):
                            tot_abs_mot_cg += 1
                        else:
                            tot_abs_nem_cg += 1

            th_avgs = []
            tot_abs_nem_th = 0
            tot_abs_mot_th = 0
            for _, start_col in MODULE_TH:
                notes = []
                for k in range(10):
                    v = ws_th.cell(row=s_row, column=start_col + k*2).value
                    if v is not None and str(v).strip() != "" and not str(v).startswith("="):
                        try:
                            notes.append(float(v))
                        except Exception:
                            pass
                if notes:
                    avg = round(sum(notes)/len(notes), 2)
                    th_avgs.append(avg)
                    ws_th.cell(row=s_row, column=start_col + 20).value = avg
                else:
                    ws_th.cell(row=s_row, column=start_col + 20).value = None

                for k in range(30):
                    av = ws_th.cell(row=s_row, column=start_col + 21 + k).value
                    if av is not None and str(av).strip() != "" and not str(av).startswith("="):
                        s_a = str(av).strip()
                        if s_a.endswith('m') or s_a.endswith('M'):
                            tot_abs_mot_th += 1
                        else:
                            tot_abs_nem_th += 1

            mcg = round(sum(cg_avgs)/len(cg_avgs), 2) if cg_avgs else None
            mth = round(sum(th_avgs)/len(th_avgs), 2) if th_avgs else None
            
            ws_cg.cell(row=s_row, column=5).value = mcg if mcg is not None else None
            ws_th.cell(row=s_row, column=5).value = mth if mth is not None else None

            tot_abs_nem = tot_abs_nem_cg + tot_abs_nem_th
            tot_abs_mot = tot_abs_mot_cg + tot_abs_mot_th
            tot_abs = tot_abs_nem + tot_abs_mot
            purtare = max(1, 10 - int(tot_abs_nem / 20))

            if ws_a:
                ws_a.cell(row=s_row, column=5).value = tot_abs_nem if tot_abs_nem > 0 else None
                ws_a.cell(row=s_row, column=6).value = tot_abs_mot if tot_abs_mot > 0 else None
                ws_a.cell(row=s_row, column=7).value = tot_abs if tot_abs > 0 else None
                ws_a.cell(row=s_row, column=8).value = purtare

            if ws_c:
                ws_c.cell(row=s_row, column=5).value = mcg if mcg is not None else None
                ws_c.cell(row=s_row, column=6).value = mth if mth is not None else None
                if mcg is not None and mth is not None:
                    mg = round((mcg + mth)/2.0, 2)
                elif mcg is not None:
                    mg = mcg
                elif mth is not None:
                    mg = mth
                else:
                    mg = None
                ws_c.cell(row=s_row, column=7).value = mg if mg is not None else None
                ws_c.cell(row=s_row, column=8).value = purtare
                
                if mcg is not None or mth is not None:
                    statut = "Promovat" if (mcg is None or mcg >= 5) and (mth is None or mth >= 5) and purtare >= 5 else "Corigent / Repetent"
                else:
                    statut = "-"
                ws_c.cell(row=s_row, column=9).value = statut
                ws_c.cell(row=s_row, column=10).value = tot_abs if tot_abs > 0 else None

        wb.save(file_path)
    except Exception:
        pass

def calculate_all_class_stats(file_path):
    students_data = []
    if not os.path.exists(file_path):
        return students_data
        
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        
        for idx, e in enumerate(ELEVI):
            s_row = 9 + idx
            
            cg_avgs = []
            tot_abs_nem = 0
            tot_abs_mot = 0
            
            for _, col in DISCIPLINE_CG:
                notes = []
                for k in range(10):
                    v = ws_cg.cell(row=s_row, column=col + k*2).value
                    if v is not None and str(v).strip() != "" and not str(v).startswith("="):
                        try:
                            notes.append(float(v))
                        except Exception:
                            pass
                if notes:
                    cg_avgs.append(round(sum(notes)/len(notes), 2))
                    
                for k in range(30):
                    av = ws_cg.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != "" and not str(av).startswith("="):
                        s = str(av).strip()
                        if s.endswith('m') or s.endswith('M'):
                            tot_abs_mot += 1
                        else:
                            tot_abs_nem += 1
                            
            th_avgs = []
            for _, col in MODULE_TH:
                notes = []
                for k in range(10):
                    v = ws_th.cell(row=s_row, column=col + k*2).value
                    if v is not None and str(v).strip() != "" and not str(v).startswith("="):
                        try:
                            notes.append(float(v))
                        except Exception:
                            pass
                if notes:
                    th_avgs.append(round(sum(notes)/len(notes), 2))
                    
                for k in range(30):
                    av = ws_th.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != "" and not str(av).startswith("="):
                        s = str(av).strip()
                        if s.endswith('m') or s.endswith('M'):
                            tot_abs_mot += 1
                        else:
                            tot_abs_nem += 1
                            
            mcg = round(sum(cg_avgs)/len(cg_avgs), 2) if cg_avgs else None
            mth = round(sum(th_avgs)/len(th_avgs), 2) if th_avgs else None
            
            if mcg is not None and mth is not None:
                mg = round((mcg + mth)/2.0, 2)
            elif mcg is not None:
                mg = mcg
            elif mth is not None:
                mg = mth
            else:
                mg = None
                
            purtare = max(1, 10 - int(tot_abs_nem / 20))
            tot_abs = tot_abs_nem + tot_abs_mot
            
            statut = "-"
            if mcg is not None or mth is not None:
                if (mcg is None or mcg >= 5) and (mth is None or mth >= 5) and purtare >= 5:
                    statut = "Promovat"
                else:
                    statut = "Corigent / Repetent"
                    
            students_data.append({
                'nr': e[0],
                'nume': e[1],
                'matr': e[3],
                'pin': e[4],
                'mcg': mcg,
                'mth': mth,
                'mg': mg,
                'purtare': purtare,
                'statut': statut,
                'tot_abs': tot_abs,
                'abs_nem': tot_abs_nem,
                'abs_mot': tot_abs_mot
            })
            
        wb.close()
        
        valid_mgs = sorted([s['mg'] for s in students_data if s['mg'] is not None], reverse=True)
        for s in students_data:
            if s['mg'] is not None:
                rang = valid_mgs.index(s['mg']) + 1
                s['rang'] = str(rang)
                if rang == 1:
                    s['premiu'] = "Premiul I"
                elif rang == 2:
                    s['premiu'] = "Premiul II"
                elif rang == 3:
                    s['premiu'] = "Premiul III"
                elif rang <= 7:
                    s['premiu'] = "Mențiune"
                else:
                    s['premiu'] = "Membru"
            else:
                s['rang'] = "-"
                s['premiu'] = "-"
    except Exception:
        pass
        
    return students_data

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

st.title("🏫 Colegiul 'Emil Negruțiu' Turda — Catalog Școlar Online (IX TH Turism)")
st.caption("Sistem Informatizat de Gestionare Note, Absențe și Generare Documente Oficiale")

with st.sidebar:
    st.header("⚙️ Opțiuni Catalog")
    selected_file = st.text_input("Fișier Excel Sursă:", value=excel_path)
    st.info("💡 Fișierul se salvează automat la fiecare modificare.")
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
    if st.button("🚪 Deconectare (Logout)", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
    st.caption("---")
    st.caption("**© Prof. Ec. Gherman Octavian-Theodor**\nDrepturi de autor rezervate.\nComercializarea interzisă.\nUtilizare gratuită acordată de autor.")

if not os.path.exists(selected_file):
    st.warning(f"⚠️ Fișierul catalog '{selected_file}' nu a fost găsit în directorul curent.")

tab1, tab2, tab3, tab_del, tab4, tab5, tab6 = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "🗑️ Ștergere Notă / Absență",
    "📊 Fișă Elev",
    "📈 Centralizator Clasă",
    "📋 Raport Diriginte"
])

elev_options = [f"{e[0]}. {e[1]} (Matr. {e[3]})" for e in ELEVI]

# --- GENERATOARE PDF ---
def generate_pdf_ticket_student(student_idx, file_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=25,
        leftMargin=25,
        topMargin=20,
        bottomMargin=20
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'SchoolHeader',
        parent=styles['Heading1'],
        fontName=PDF_FONT_BOLD,
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#1A365D")
    )
    sub_title_style = ParagraphStyle(
        'SubHeader',
        parent=styles['Normal'],
        fontName=PDF_FONT,
        fontSize=8,
        leading=11,
        alignment=1,
        textColor=colors.HexColor("#4A5568")
    )
    ticket_title = ParagraphStyle(
        'TicketTitle',
        parent=styles['Heading2'],
        fontName=PDF_FONT_BOLD,
        fontSize=11,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#2B6CB0"),
        spaceBefore=4,
        spaceAfter=4
    )
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontName=PDF_FONT_BOLD,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#2D3748")
    )
    val_style = ParagraphStyle(
        'Val',
        parent=styles['Normal'],
        fontName=PDF_FONT_BOLD,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#1A365D")
    )
    pin_val_style = ParagraphStyle(
        'PinVal',
        parent=styles['Normal'],
        fontName=PDF_FONT_BOLD,
        fontSize=11,
        leading=13,
        textColor=colors.HexColor("#C53030")
    )
    instr_head = ParagraphStyle(
        'InstrHead',
        parent=styles['Heading3'],
        fontName=PDF_FONT_BOLD,
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1A365D"),
        spaceBefore=4,
        spaceAfter=2
    )
    instr_body = ParagraphStyle(
        'InstrBody',
        parent=styles['Normal'],
        fontName=PDF_FONT,
        fontSize=7.5,
        leading=10.5,
        textColor=colors.HexColor("#2D3748")
    )
    img_label = ParagraphStyle(
        'ImgLabel',
        parent=styles['Normal'],
        fontName=PDF_FONT_BOLD,
        fontSize=7.5,
        leading=10,
        alignment=1,
        textColor=colors.HexColor("#2B6CB0")
    )
    footer_style = ParagraphStyle(
        'FooterText',
        parent=styles['Normal'],
        fontName=PDF_FONT,
        fontSize=6.5,
        leading=8.5,
        alignment=1,
        textColor=colors.HexColor("#718096")
    )

    android_img_path = "/workspace/artifacts/ghid_shortcut_android.png"
    iphone_img_path = "/workspace/artifacts/ghid_shortcut_iphone.png"

    e = ELEVI[student_idx]
    pin = e[4]

    story = []
    story.append(Paragraph("COLEGIUL „EMIL NEGRUȚIU” TURDA", title_style))
    story.append(Paragraph("AN ȘCOLAR 2026–2027 | CLASA a IX-a TH (TURISM ȘI ALIMENTAȚIE)", sub_title_style))
    story.append(Paragraph("Prof. Diriginte: Prof. Ec. Gherman Octavian-Theodor", sub_title_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph("BILET INDIVIDUAL DE ACCES — PORTAL PĂRINȚI", ticket_title))
    story.append(Spacer(1, 4))

    cred_data = [
        [
            Paragraph("ELEV / ELEVĂ:", label_style),
            Paragraph(f"{e[1]}", val_style)
        ],
        [
            Paragraph("NUMĂR MATRICOL (UTILIZATOR):", label_style),
            Paragraph(f"{e[3]} (sau numărul simplu: {e[2]})", val_style)
        ],
        [
            Paragraph("COD PIN CONFIDENȚIAL (PAROLĂ):", label_style),
            Paragraph(f"{pin}", pin_val_style)
        ],
        [
            Paragraph("ADRESĂ WEB PORTAL:", label_style),
            Paragraph("https://catalog-online-5482kppsbvvl6nffpe332g.streamlit.app/", val_style)
        ]
    ]

    t_cred = Table(cred_data, colWidths=[180, 320])
    t_cred.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EDF2F7")),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(t_cred)
    story.append(Spacer(1, 6))

    story.append(Paragraph("INSTRUCȚIUNI DE CONECTARE ȘI ADĂUGARE PE ECRANUL TELEFONULUI:", instr_head))
    instr_text = (
        "1. Autentificare: Accesați adresa https://catalog-online-5482kppsbvvl6nffpe332g.streamlit.app/ și introduceți Numărul Matricol și Codul PIN de mai sus. "
        "2. Telefoane Android (Samsung, Xiaomi, Motorola etc.): Deschideți în Google Chrome ➔ apăsați pe cele 3 puncte (dreapta sus) ➔ Selectați opțiunea „Adaugă pe ecranul de pornire” (sau „Instalează aplicația”). "
        "3. Telefoane iPhone (Apple iOS): Deschideți în Safari ➔ apăsați pe butonul Partajare ➔ Selectați opțiunea „Adaugă pe ecranul principal”."
    )
    story.append(Paragraph(instr_text, instr_body))
    story.append(Spacer(1, 6))

    img_w = 170
    img_h = 227
    if os.path.exists(android_img_path) and os.path.exists(iphone_img_path):
        img_android = RLImage(android_img_path, width=img_w, height=img_h)
        img_iphone = RLImage(iphone_img_path, width=img_w, height=img_h)
        img_table_data = [
            [
                Paragraph("Ghid Adăugare Android (Google Chrome)", img_label),
                Paragraph("Ghid Adăugare iPhone / iOS (Safari)", img_label)
            ],
            [
                img_android,
                img_iphone
            ]
        ]
        t_img = Table(img_table_data, colWidths=[250, 250])
        t_img.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('PADDING', (0,0), (-1,-1), 2),
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#F7FAFC")),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0"))
        ]))
        story.append(t_img)
        story.append(Spacer(1, 6))

    footer_text = (
        "© Software Creat și Deținut de Prof. Ec. Gherman Octavian-Theodor | Protejat de Legea nr. 8/1996 privind drepturile de autor. "
        "Comercializarea este interzisă! Produs utilizat gratuit exclusiv de persoanele autorizate de autor."
    )
    story.append(Paragraph(footer_text, footer_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

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
    
    meta_data = [
        [Paragraph(f"<b>Nume și Prenume:</b> {e_info[1]}", cell_style), Paragraph(f"<b>Nr. Matricol:</b> {e_info[3]}", cell_style), Paragraph(f"<b>RM/PG:</b> {e_info[2]}", cell_style)]
    ]
    t_meta = Table(meta_data, colWidths=[240, 150, 130])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor("#EDF2F7")),
        ('PADDING', (0,0), (-1,-1), 6),
        ('BOX', (0,0), (-1,-1), 1, colors.HexColor("#CBD5E0"))
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    if os.path.exists(file_path):
        wb = openpyxl.load_workbook(file_path, data_only=True)
        s_row = 9 + student_idx
        
        for cat_title, sheet_n, sub_list in [("DISCIPLINE CULTURĂ GENERALĂ", "Cultură Generală", DISCIPLINE_CG), ("MODULE TEHNOLOGICE", "Module Tehnologice", MODULE_TH)]:
            story.append(Paragraph(cat_title, heading_style))
            ws = wb[sheet_n]
            
            table_data = [[
                Paragraph("<b>Disciplină / Modul</b>", cell_bold),
                Paragraph("<b>Note & Date</b>", cell_bold),
                Paragraph("<b>Medie</b>", cell_bold),
                Paragraph("<b>Absențe</b>", cell_bold)
            ]]
            
            for s_name, start_col in sub_list:
                notes_list = []
                notes_num = []
                for k in range(10):
                    n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                    d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                    if n_val is not None and str(n_val).strip() != "" and not str(n_val).startswith("="):
                        d_str = f" ({d_val})" if d_val else ""
                        notes_list.append(f"{n_val}{d_str}")
                        try:
                            notes_num.append(float(n_val))
                        except Exception:
                            pass
                        
                abs_list = []
                for k in range(30):
                    a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                    if a_val is not None and str(a_val).strip() != "" and not str(a_val).startswith("="):
                        abs_list.append(str(a_val).strip())
                        
                m_str = f"{(sum(notes_num)/len(notes_num)):.2f}" if notes_num else "-"
                
                table_data.append([
                    Paragraph(s_name, cell_style),
                    Paragraph(", ".join(notes_list) if notes_list else "-", cell_style),
                    Paragraph(m_str, cell_bold),
                    Paragraph(", ".join(abs_list) if abs_list else "-", cell_style)
                ])
                
            t_sub = Table(table_data, colWidths=[180, 180, 60, 100])
            t_sub.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
                ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
                ('PADDING', (0,0), (-1,-1), 4),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
            ]))
            story.append(t_sub)
            story.append(Spacer(1, 8))
            
        wb.close()

    story.append(Spacer(1, 15))
    story.append(Paragraph("Profesor Diriginte: Prof. Ec. Gherman Octavian-Theodor | Semnătură: ___________", cell_style))

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
    
    table_data = [[
        Paragraph("<b>Nr.</b>", cell_bold),
        Paragraph("<b>Nume și Prenume</b>", cell_bold),
        Paragraph("<b>Matr.</b>", cell_bold),
        Paragraph("<b>Med. CG</b>", cell_bold),
        Paragraph("<b>Med. TH</b>", cell_bold),
        Paragraph("<b>Med. Gen.</b>", cell_bold),
        Paragraph("<b>Purtare</b>", cell_bold),
        Paragraph("<b>Statut</b>", cell_bold),
        Paragraph("<b>Tot. Abs.</b>", cell_bold),
        Paragraph("<b>Rang</b>", cell_bold),
        Paragraph("<b>Premiu</b>", cell_bold)
    ]]
    
    stats = calculate_all_class_stats(file_path)
    for s in stats:
        table_data.append([
            Paragraph(str(s['nr']), cell_style),
            Paragraph(s['nume'], cell_style),
            Paragraph(s['matr'], cell_style),
            Paragraph(safe_float_str(s['mcg']), cell_style),
            Paragraph(safe_float_str(s['mth']), cell_style),
            Paragraph(safe_float_str(s['mg']), cell_bold),
            Paragraph(str(s['purtare']), cell_style),
            Paragraph(s['statut'], cell_style),
            Paragraph(str(s['tot_abs']), cell_style),
            Paragraph(s['rang'], cell_style),
            Paragraph(s['premiu'], cell_style)
        ])

    t_cent = Table(table_data, colWidths=[25, 180, 50, 50, 50, 55, 45, 80, 50, 35, 70])
    t_cent.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
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
    story.append(Paragraph("Prof. Diriginte: Prof. Ec. Gherman Octavian-Theodor", title_style))
    story.append(Spacer(1, 10))
    
    stats = calculate_all_class_stats(file_path)
    tot_el = len(stats)
    promovati = [s for s in stats if s['statut'] == "Promovat"]
    promov_str = f"{len(promovati)}/{tot_el} ({(len(promovati)/tot_el*100):.1f}%)" if tot_el else "-"
    
    valid_mgs = [s['mg'] for s in stats if s['mg'] is not None]
    med_clasa = f"{(sum(valid_mgs)/len(valid_mgs)):.2f}" if valid_mgs else "-"
    med_purt = f"{(sum(s['purtare'] for s in stats)/tot_el):.2f}" if tot_el else "10.00"
    tot_abs_sum = sum(s['tot_abs'] for s in stats)
    tot_abs_str = f"{tot_abs_sum}"
    
    kpi_data = [
        [Paragraph("<b>Total Elevi</b>", cell_bold), Paragraph("<b>Promovabilitate</b>", cell_bold), Paragraph("<b>Media Clasei</b>", cell_bold), Paragraph("<b>Media Purtare</b>", cell_bold), Paragraph("<b>Total Absențe</b>", cell_bold)],
        [Paragraph(str(tot_el), cell_style), Paragraph(promov_str, cell_style), Paragraph(med_clasa, cell_style), Paragraph(med_purt, cell_style), Paragraph(tot_abs_str, cell_style)]
    ]
    t_kpi = Table(kpi_data, colWidths=[100, 110, 100, 100, 110])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("DISTRIBUȚIA MEDIILOR ȘI FRECVENȚA", heading_style))
    dist_data = [[Paragraph("<b>Tranșă Medie</b>", cell_bold), Paragraph("<b>Nr. Elevi</b>", cell_bold), Paragraph("<b>Pondere</b>", cell_bold)]]
    
    transe = [
        ("Medii = 10.00", lambda m: m == 10.0),
        ("Medii 9.00 - 9.99", lambda m: 9.0 <= m < 10.0),
        ("Medii 8.00 - 8.99", lambda m: 8.0 <= m < 9.0),
        ("Medii 7.00 - 7.99", lambda m: 7.0 <= m < 8.0),
        ("Medii 6.00 - 6.99", lambda m: 6.0 <= m < 7.0),
        ("Medii 5.00 - 5.99", lambda m: 5.0 <= m < 6.0),
        ("Medii sub 5.00", lambda m: m < 5.0)
    ]
    
    for label, cond in transe:
        cnt = sum(1 for m in valid_mgs if cond(m))
        pond = f"{(cnt/len(valid_mgs)*100):.1f}%" if valid_mgs else "0%"
        dist_data.append([Paragraph(label, cell_style), Paragraph(str(cnt), cell_style), Paragraph(pond, cell_style)])
        
    t_dist = Table(dist_data, colWidths=[220, 150, 150])
    t_dist.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(t_dist)

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_pdf_pins_list(file_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=PDF_FONT_BOLD, fontSize=13, leading=16, alignment=1, textColor=colors.HexColor("#1A365D"))
    subtitle_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontName=PDF_FONT, fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#4A5568"))
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontName=PDF_FONT, fontSize=8, leading=11)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=8, leading=11)

    story.append(Paragraph("COLEGIUL 'EMIL NEGRUȚIU' TURDA", title_style))
    story.append(Paragraph("LISTĂ CODURI PIN CONFIDENȚIALE - PORTAL PĂRINȚI (IX TH)", title_style))
    story.append(Paragraph("Prof. Diriginte: Prof. Ec. Gherman Octavian-Theodor | CONFIDENȚIAL", subtitle_style))
    story.append(Spacer(1, 10))

    table_data = [[
        Paragraph("<b>Nr.</b>", cell_bold),
        Paragraph("<b>Nume și Prenume Elev</b>", cell_bold),
        Paragraph("<b>Nr. Matricol</b>", cell_bold),
        Paragraph("<b>Cod PIN Părinte</b>", cell_bold)
    ]]
    
    for idx, e in enumerate(ELEVI):
        table_data.append([
            Paragraph(str(e[0]), cell_style),
            Paragraph(e[1], cell_style),
            Paragraph(e[3], cell_style),
            Paragraph(f"<b>{e[4]}</b>", cell_bold)
        ])
        
    t_pins = Table(table_data, colWidths=[40, 240, 120, 120])
    t_pins.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 4),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(t_pins)
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
        materii_n = [d[0] for d in DISCIPLINE_CG] if cat_n == "Cultură Generală" else [m[0] for m in MODULE_TH]
        mat_idx_n = st.selectbox("Selectează Disciplina / Modulul:", range(len(materii_n)), format_func=lambda i: materii_n[i], key="mat_n")
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
                    update_excel_computed_values(selected_file)
                    push_to_github(selected_file)
                    st.success(f"✅ Notă salvată: {nota_val} pe {data_nota} la {materii_n[mat_idx_n]} (Slot N{slot_num}) pentru {ELEVI[elev_idx_n][1]}")
                    st.rerun()
                else:
                    st.error("❌ Toate cele 10 sloturi de note sunt pline pentru această disciplină!")
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
                    update_excel_computed_values(selected_file)
                    push_to_github(selected_file)
                    st.success(f"✅ Absență salvată: '{abs_val}' la {materii_a[mat_idx_a]} (Slot A{slot_num}) pentru {ELEVI[elev_idx_a][1]}")
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
                    update_excel_computed_values(selected_file)
                    push_to_github(selected_file)
                    st.success(f"✅ Absență motivată ('{target_d}m') pentru {ELEVI[elev_idx_m][1]} la {materii_m[mat_idx_m]}")
                    st.rerun()
                elif not found:
                    st.warning(f"Nu s-a găsit nicio absență nemotivată cu data '{target_d}'.")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare: {ex}")

# --- TAB NOU: ȘTERGERE NOTĂ / ABSENȚĂ ---
with tab_del:
    st.subheader("🗑️ Ștergere Notă sau Absență Introduse")
    col1, col2 = st.columns(2)
    
    with col1:
        elev_idx_del = st.selectbox("Selectează Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_del")
        cat_del = st.radio("Categorie Disciplină:", ["Cultură Generală", "Module Tehnologice"], key="cat_del")
        tip_del = st.radio("Ce doriți să ștergeți?", ["Notă", "Absență"], key="tip_del")
        
    with col2:
        materii_del = [d[0] for d in DISCIPLINE_CG] if cat_del == "Cultură Generală" else [m[0] for m in MODULE_TH]
        mat_idx_del = st.selectbox("Selectează Disciplina / Modulul:", range(len(materii_del)), format_func=lambda i: materii_del[i], key="mat_del")
        
        existing_items = []
        item_coords = []
        
        if os.path.exists(selected_file):
            try:
                wb = openpyxl.load_workbook(selected_file, data_only=True)
                sheet_name = "Cultură Generală" if cat_del == "Cultură Generală" else "Module Tehnologice"
                ws = wb[sheet_name]
                student_row = 9 + elev_idx_del
                start_col = DISCIPLINE_CG[mat_idx_del][1] if cat_del == "Cultură Generală" else MODULE_TH[mat_idx_del][1]
                
                if tip_del == "Notă":
                    for k in range(10):
                        n_col = start_col + (k * 2)
                        d_col = n_col + 1
                        n_val = ws.cell(row=student_row, column=n_col).value
                        d_val = ws.cell(row=student_row, column=d_col).value
                        if n_val is not None and str(n_val).strip() != "" and not str(n_val).startswith("="):
                            d_str = f" din data {d_val}" if d_val else ""
                            existing_items.append(f"Slot N{k+1}: Notă {n_val}{d_str}")
                            item_coords.append((n_col, d_col))
                else:
                    for k in range(30):
                        a_col = start_col + 21 + k
                        a_val = ws.cell(row=student_row, column=a_col).value
                        if a_val is not None and str(a_val).strip() != "" and not str(a_val).startswith("="):
                            existing_items.append(f"Slot A{k+1}: Absență '{a_val}'")
                            item_coords.append((a_col, None))
                wb.close()
            except Exception as ex:
                st.error(f"Eroare la citire: {ex}")

        if existing_items:
            item_selected_idx = st.selectbox(f"Selectează {tip_del} de șters:", range(len(existing_items)), format_func=lambda i: existing_items[i], key="item_del_sel")
            
            if st.button(f"🗑️ Șterge {tip_del} Selectată", type="primary", use_container_width=True):
                try:
                    wb = openpyxl.load_workbook(selected_file)
                    sheet_name = "Cultură Generală" if cat_del == "Cultură Generală" else "Module Tehnologice"
                    ws = wb[sheet_name]
                    student_row = 9 + elev_idx_del
                    
                    c1, c2 = item_coords[item_selected_idx]
                    ws.cell(row=student_row, column=c1).value = None
                    if c2 is not None:
                        ws.cell(row=student_row, column=c2).value = None
                        
                    wb.save(selected_file)
                    update_excel_computed_values(selected_file)
                    push_to_github(selected_file)
                    st.success(f"✅ {existing_items[item_selected_idx]} a fost ștersă cu succes din catalog!")
                    wb.close()
                    st.rerun()
                except Exception as ex:
                    st.error(f"Eroare la ștergere: {ex}")
        else:
            st.info(f"ℹ️ Nu există nicio {tip_del.lower()} înregistrată pentru elevul selectat la {materii_del[mat_idx_del]}.")

# --- TAB 4: FIȘĂ ELEV ---
with tab4:
    st.subheader("Fișă Elev & Rezumat")
    col_v1, col_v2, col_v3 = st.columns(3)
    with col_v1:
        elev_idx_v = st.selectbox("Alege Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_v")
    with col_v2:
        st.write("")
        st.write("")
        try:
            pdf_bytes = generate_pdf_student(elev_idx_v, selected_file)
            st.download_button("🖨️ Descarcă Fișă Școlară PDF", data=pdf_bytes, file_name=f"Fisa_Elev_{ELEVI[elev_idx_v][1].replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare PDF Fișă: {ex}")
    with col_v3:
        st.write("")
        st.write("")
        try:
            ticket_bytes = generate_pdf_ticket_student(elev_idx_v, selected_file)
            st.download_button("🔑 Descarcă Bilet Acces Părinte PDF", data=ticket_bytes, file_name=f"Bilet_Acces_Parinte_{ELEVI[elev_idx_v][0]:02d}_{ELEVI[elev_idx_v][1].replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare PDF Bilet: {ex}")

    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            e_info = ELEVI[elev_idx_v]
            st.markdown(f"### 👤 {e_info[1]} (Matricol {e_info[3]}) | Cod PIN Părinți: `{e_info[4]}`")
            
            for cat_title, sheet_n, sub_list in [("Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"#### {cat_title}")
                ws = wb[sheet_n]
                s_row = 9 + elev_idx_v
                
                rows_data = []
                for s_name, start_col in sub_list:
                    notes = []
                    notes_num = []
                    for k in range(10):
                        n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                        if n_val is not None and str(n_val).strip() != "" and not str(n_val).startswith("="):
                            d_str = f" ({d_val})" if d_val else ""
                            notes.append(f"{n_val}{d_str}")
                            try:
                                notes_num.append(float(n_val))
                            except Exception:
                                pass
                    absences = []
                    for k in range(30):
                        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                        if a_val is not None and str(a_val).strip() != "" and not str(a_val).startswith("="):
                            absences.append(str(a_val).strip())
                            
                    media_str = f"{(sum(notes_num)/len(notes_num)):.2f}" if notes_num else "-"
                    
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
    st.subheader("📈 Centralizator General Clasă (Situție Școlară & Premii)")
    col_c1, col_c2 = st.columns([3, 1])
    with col_c2:
        try:
            pdf_cent_bytes = generate_pdf_centralizator(selected_file)
            st.download_button("🖨️ Descarcă Centralizator PDF", data=pdf_cent_bytes, file_name="Centralizator_General_IX_TH.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare PDF Centralizator: {ex}")
            
    if os.path.exists(selected_file):
        try:
            stats = calculate_all_class_stats(selected_file)
            c_data = []
            for s in stats:
                c_data.append({
                    "Nr.": str(s['nr']),
                    "Nume și Prenume": s['nume'],
                    "Matricol": s['matr'],
                    "Media CG": safe_float_str(s['mcg']),
                    "Media TH": safe_float_str(s['mth']),
                    "Media Generală": safe_float_str(s['mg']),
                    "Nota Purtare": str(s['purtare']),
                    "Statut Școlar": s['statut'],
                    "Total Absențe": str(s['tot_abs']),
                    "Rang": s['rang'],
                    "Premiu": s['premiu']
                })
            st.dataframe(c_data, use_container_width=True)
            
            st.divider()
            with st.expander("🔐 Gestionare Coduri PIN Confidențiale Părinți", expanded=False):
                col_p1, col_p2 = st.columns([3, 1])
                with col_p1:
                    st.info("💡 Fiecare elev are atribuit un cod PIN unic de 4 cifre necesar părinților pentru autentificare în portal.")
                with col_p2:
                    try:
                        pdf_pins_bytes = generate_pdf_pins_list(selected_file)
                        st.download_button("🖨️ Descarcă Listă PIN-uri (PDF)", data=pdf_pins_bytes, file_name="Lista_PIN_Parinti_IX_TH.pdf", mime="application/pdf", use_container_width=True)
                    except Exception as ex:
                        st.error(f"Eroare PDF PIN-uri: {ex}")
                        
                pin_rows = []
                for e in ELEVI:
                    pin_rows.append({
                        "Nr. Crt.": e[0],
                        "Nume și Prenume Elev": e[1],
                        "Nr. Matricol": e[3],
                        "Cod PIN Confidențial": e[4]
                    })
                st.dataframe(pin_rows, use_container_width=True)
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
            st.error(f"Eroare PDF Raport: {ex}")
            
    if os.path.exists(selected_file):
        try:
            stats = calculate_all_class_stats(selected_file)
            tot_el = len(stats)
            promovati = [s for s in stats if s['statut'] == "Promovat"]
            promov_str = f"{len(promovati)}/{tot_el} ({(len(promovati)/tot_el*100):.1f}%)" if tot_el else "-"
            
            valid_mgs = [s['mg'] for s in stats if s['mg'] is not None]
            med_clasa = f"{(sum(valid_mgs)/len(valid_mgs)):.2f}" if valid_mgs else "-"
            med_purt = f"{(sum(s['purtare'] for s in stats)/tot_el):.2f}" if tot_el else "10.00"
            tot_abs_sum = sum(s['tot_abs'] for s in stats)
            tot_abs_str = f"{tot_abs_sum}"

            st.markdown("#### 📊 Indicatori Cheie de Performanță Clasă")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Elevi", str(tot_el))
            m2.metric("Promovabilitate", promov_str)
            m3.metric("Media Clasei", med_clasa)
            m4.metric("Media Purtare", med_purt)
            m5.metric("Total Absențe", tot_abs_str)
            
            st.markdown("#### 📈 Distribuția Mediilor Generale")
            transe = [
                ("Medii = 10.00", lambda m: m == 10.0),
                ("Medii 9.00 - 9.99", lambda m: 9.0 <= m < 10.0),
                ("Medii 8.00 - 8.99", lambda m: 8.0 <= m < 9.0),
                ("Medii 7.00 - 7.99", lambda m: 7.0 <= m < 8.0),
                ("Medii 6.00 - 6.99", lambda m: 6.0 <= m < 7.0),
                ("Medii 5.00 - 5.99", lambda m: 5.0 <= m < 6.0),
                ("Medii sub 5.00", lambda m: m < 5.0)
            ]
            
            d_rows = []
            for label, cond in transe:
                cnt = sum(1 for m in valid_mgs if cond(m))
                pond = f"{(cnt/len(valid_mgs)*100):.1f}%" if valid_mgs else "0%"
                d_rows.append({
                    "Tranșă Medie": label,
                    "Număr Elevi": str(cnt),
                    "Pondere (%)": pond
                })
            st.dataframe(d_rows, use_container_width=True)
            
            st.markdown("#### 🏆 Top 5 Elevi ai Clasei")
            top_students = sorted([s for s in stats if s['mg'] is not None], key=lambda x: x['mg'], reverse=True)[:5]
            top_rows = []
            for r_idx, s in enumerate(top_students):
                top_rows.append({
                    "Loc": r_idx + 1,
                    "Nume și Prenume": s['nume'],
                    "Matricol": s['matr'],
                    "Media CG": safe_float_str(s['mcg']),
                    "Media TH": safe_float_str(s['mth']),
                    "Media Generală": safe_float_str(s['mg']),
                    "Distincție": s['premiu']
                })
            if top_rows:
                st.dataframe(top_rows, use_container_width=True)
            else:
                st.info("ℹ️ Nu există încă elevi cu medii calculate pentru afișarea clasamentului.")
        except Exception as ex:
            st.error(f"Eroare la citire raport: {ex}")

st.markdown("---")
st.info("""
**© Software Creat și Deținut de Prof. Ec. Gherman Octavian-Theodor**
*Acest program este protejat de legea privind drepturile de autor (Legea nr. 8/1996) și legislația internațională aplicabilă.*
*Orice descărcare, multiplicare, distribuire sau utilizare neautorizată se pedepsește conform legii.*
**🚫 ESTE STRICT INTERZISĂ COMERCIALIZAREA ACESTUI PRODUS!**
*Acest produs se utilizează în mod gratuit exclusiv de către persoanele cărora autorul le conferă în mod explicit acest drept.*
""")
