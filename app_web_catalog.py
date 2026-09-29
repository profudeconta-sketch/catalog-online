import datetime
import os
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
import streamlit as st
import urllib.request
import urllib.parse
import json
import base64
import random
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
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
            except Exception: pass
                
    for fbp in font_bold_paths:
        if os.path.exists(fbp):
            try:
                pdfmetrics.registerFont(TTFont("CustomUnicodeBold", fbp))
                font_bold_name = "CustomUnicodeBold"
                break
            except Exception: pass
                
    return font_name, font_bold_name

PDF_FONT, PDF_FONT_BOLD = get_pdf_font()

def safe_str(val):
    if val is None: return ""
    return str(val).strip()

def safe_float_str(val):
    if val is None or val == "": return "-"
    try: return f"{float(val):.2f}"
    except Exception: return str(val)

def clean_pdf_text(text):
    if not text: return ""
    t = str(text)
    replacements = {'ș': 'ș', 'Ș': 'Ș', 'ț': 'ț', 'Ț': 'Ț', 'ă': 'ă', 'Ă': 'Ă', 'î': 'î', 'Î': 'Î', 'â': 'â', 'Â': 'Â'}
    for k, v in replacements.items(): t = t.replace(k, v)
    return t

def render_copyright_footer():
    st.markdown("---")
    st.markdown("""
    **© Software Creat și Deținut de Prof. Ec. Gherman Octavian-Theodor**  
    *Acest program este protejat de legea privind drepturile de autor (Legea nr. 8/1996) și legislația internațională aplicabilă.*  
    *Orice descărcare, multiplicare, distribuire sau utilizare neautorizată se pedepsește conform legii.*  
    **🚫 ESTE STRICT INTERZISĂ COMERCIALIZAREA ACESTUI PRODUS!**  
    *Acest produs se utilizează în mod gratuit exclusiv de către persoanele cărora autorul le conferă în mod explicit acest drept.*
    """)

def render_sidebar_copyright():
    st.caption("---")
    st.caption("**© Prof. Ec. Gherman Octavian-Theodor**\nDrepturi de autor rezervate.\nComercializarea interzisă.\nUtilizare gratuită acordată de autor.")

# --- LISTA DEFAULT A ELEVILOR DIN CLASĂ ---
ELEVI_DEFAULT = [
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

PINS_DEFAULT = ['2951', '6234', '9233', '9385', '2681', '4658', '7891', '9975', '9042', '8226', '4931', '1041', '2322', '2814', '5706', '2606', '8367', '1188', '9032', '6148', '4444', '7508', '5120', '6696', '6843', '7166', '9414', '2250', '6577', '2469', '9815', '5786']

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

# --- HELPER PARSARE NUME COMPLET ---
def parse_nume_complet(nume_complet):
    parts = nume_complet.strip().split()
    if not parts:
        return "", "", ""
    nume = parts[0]
    initiala = ""
    prenume = ""
    
    if len(parts) > 1 and (parts[1].endswith('.') or '.' in parts[1]):
        initiala = parts[1]
        prenume = " ".join(parts[2:])
    elif len(parts) > 1:
        prenume = " ".join(parts[1:])
        
    return nume, initiala, prenume

# --- HELPER INITIALIZARE/INCARCARE DATA GESTIUNE ELEVI ---
def init_default_gestiune_data():
    data = []
    for idx, e in enumerate(ELEVI_DEFAULT):
        nume, initiala, prenume = parse_nume_complet(e[1])
        pin_val = PINS_DEFAULT[idx] if idx < len(PINS_DEFAULT) else "0000"
        data.append({
            "id": e[0],
            "rand_excel": e[2],
            "matricol": e[3],
            "pin": pin_val,
            "nume": nume,
            "initiala": initiala,
            "prenume": prenume,
            "nume_complet": e[1],
            "cnp": "",
            "telefon": "",
            "localitate": "Turda",
            "judet": "Cluj",
            "strada": "",
            "numar_strada": "",
            "bloc": "",
            "apartament": "",
            "nume_mama": "",
            "telefon_mama": "",
            "mama_plecata": False,
            "tara_mama": "",
            "nume_tata": "",
            "telefon_tata": "",
            "tata_plecat": False,
            "tara_tata": "",
            "nationalitate": "Română",
            "etnie": "Română",
            "ces": False,
            "orfan": False,
            "plasament": False,
            "bursa_medicala": False,
            "bursa_venit": False
        })
    return data

def load_gestiune_data():
    candidates = ["gestiune_elevi.json", "/workspace/artifacts/gestiune_elevi.json"]
    for c in candidates:
        if os.path.exists(c):
            try:
                with open(c, "r", encoding="utf-8") as f:
                    d = json.load(f)
                if d:
                    return d
            except Exception: pass
    return init_default_gestiune_data()

def save_gestiune_data(data):
    file_path = "gestiune_elevi.json"
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        push_to_github(file_path)
        return True
    except Exception:
        return False

# --- DYNAMIC ELEVI AND PINS INITIALIZATION ---
students_gestiune = load_gestiune_data()

ELEVI = [(s["id"], s["nume_complet"], s["rand_excel"], s["matricol"]) for s in students_gestiune]
PINS = [s.get("pin", "0000") for s in students_gestiune]
elev_options = [f"{e[0]}. {e[1]} (Matr. {e[3]})" for e in ELEVI]

# --- PARSARE CNP ȘI SEX ---
def parse_cnp(cnp):
    cnp_str = str(cnp).strip()
    if len(cnp_str) != 13 or not cnp_str.isdigit():
        return {'sex': 'Necunoscut', 'age': 'N/A', 'birth_date': 'N/A'}
    
    first_digit = int(cnp_str[0])
    sex = 'Băiat' if first_digit in [1, 3, 5, 7] else 'Fată'
    
    year_prefix = '19'
    if first_digit in [5, 6]:
        year_prefix = '20'
    elif first_digit in [1, 2]:
        year_prefix = '19'
    elif first_digit in [3, 4]:
        year_prefix = '18'
        
    yy = year_prefix + cnp_str[1:3]
    mm = cnp_str[3:5]
    dd = cnp_str[5:7]
    
    try:
        birth_dt = datetime.datetime.strptime(f'{yy}-{mm}-{dd}', '%Y-%m-%d')
        today = datetime.datetime.now()
        age = today.year - birth_dt.year - ((today.month, today.day) < (birth_dt.month, birth_dt.day))
        return {'sex': sex, 'age': age, 'birth_date': f'{dd}.{mm}.{yy}'}
    except Exception:
        return {'sex': sex, 'age': 'N/A', 'birth_date': 'N/A'}

def get_student_sex(student):
    cnp_info = parse_cnp(student.get('cnp', ''))
    if cnp_info['sex'] in ['Băiat', 'Fată']:
        return cnp_info['sex']
    
    prenume = student.get('prenume', '').strip().split()
    if prenume:
        first_p = prenume[0].lower()
        if (first_p.endswith('a') and first_p not in ['luca', 'minea', 'horia', 'toma']) or first_p in ['carmen', 'iris', 'medea']:
            return 'Fată'
    return 'Băiat'

# --- RECALCULARE ȘI SCRIERE ÎN EXCEL (PENTRU PERSISTENȚĂ STRUCTURATĂ) ---
def update_excel_computed_values(file_path):
    if not os.path.exists(file_path):
        return
    try:
        wb = openpyxl.load_workbook(file_path)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        ws_cent = wb["Centralizator Medii"]
        
        valid_mgs = []
        students_calculated = []

        for idx in range(len(ELEVI)):
            s_row = 9 + idx
            
            cg_avgs = []
            tot_abs_nem = 0
            tot_abs_mot = 0
            
            for s_name, start_col in DISCIPLINE_CG:
                notes = []
                for k in range(10):
                    val = ws_cg.cell(row=s_row, column=start_col + (k * 2)).value
                    if val is not None and str(val).strip() != "":
                        try: notes.append(float(val))
                        except Exception: pass
                
                avg_col = start_col + 20
                if notes:
                    sub_avg = round(sum(notes) / len(notes), 2)
                    ws_cg.cell(row=s_row, column=avg_col).value = sub_avg
                    cg_avgs.append(sub_avg)
                else:
                    ws_cg.cell(row=s_row, column=avg_col).value = None

                for k in range(30):
                    a_val = ws_cg.cell(row=s_row, column=start_col + 21 + k).value
                    if a_val is not None and str(a_val).strip() != "":
                        s_a = str(a_val).strip()
                        if s_a.endswith('m') or s_a.endswith('M'): tot_abs_mot += 1
                        else: tot_abs_nem += 1

            th_avgs = []
            for s_name, start_col in MODULE_TH:
                notes = []
                for k in range(10):
                    val = ws_th.cell(row=s_row, column=start_col + (k * 2)).value
                    if val is not None and str(val).strip() != "":
                        try: notes.append(float(val))
                        except Exception: pass
                
                avg_col = start_col + 20
                if notes:
                    sub_avg = round(sum(notes) / len(notes), 2)
                    ws_th.cell(row=s_row, column=avg_col).value = sub_avg
                    th_avgs.append(sub_avg)
                else:
                    ws_th.cell(row=s_row, column=avg_col).value = None

                for k in range(30):
                    a_val = ws_th.cell(row=s_row, column=start_col + 21 + k).value
                    if a_val is not None and str(a_val).strip() != "":
                        s_a = str(a_val).strip()
                        if s_a.endswith('m') or s_a.endswith('M'): tot_abs_mot += 1
                        else: tot_abs_nem += 1

            mcg = round(sum(cg_avgs) / len(cg_avgs), 2) if cg_avgs else None
            mth = round(sum(th_avgs) / len(th_avgs), 2) if th_avgs else None
            
            if mcg is not None and mth is not None: mg = round((mcg + mth) / 2.0, 2)
            elif mcg is not None: mg = mcg
            elif mth is not None: mg = mth
            else: mg = None

            tot_abs = tot_abs_nem + tot_abs_mot
            purtare = max(1, 10 - int(tot_abs_nem / 20))
            
            statut = "-"
            if mcg is not None or mth is not None:
                if (mcg is None or mcg >= 5) and (mth is None or mth >= 5) and purtare >= 5:
                    statut = "Promovat"
                else:
                    statut = "Corigent / Repetent"

            ws_cent.cell(row=s_row, column=5).value = mcg
            ws_cent.cell(row=s_row, column=6).value = mth
            ws_cent.cell(row=s_row, column=7).value = mg
            ws_cent.cell(row=s_row, column=8).value = purtare
            ws_cent.cell(row=s_row, column=9).value = statut
            ws_cent.cell(row=s_row, column=10).value = tot_abs

            if mg is not None: valid_mgs.append(mg)
            students_calculated.append((s_row, mg))

        valid_mgs_sorted = sorted(valid_mgs, reverse=True)
        for s_row, mg in students_calculated:
            if mg is not None:
                rang = valid_mgs_sorted.index(mg) + 1
                if rang == 1: premiu = "Premiul I"
                elif rang == 2: premiu = "Premiul II"
                elif rang == 3: premiu = "Premiul III"
                elif rang <= 7: premiu = "Mențiune"
                else: premiu = "Membru"
                ws_cent.cell(row=s_row, column=11).value = rang
                ws_cent.cell(row=s_row, column=12).value = premiu
            else:
                ws_cent.cell(row=s_row, column=11).value = None
                ws_cent.cell(row=s_row, column=12).value = None

        wb.save(file_path)
        wb.close()
    except Exception: pass

# --- PARSARE ABSENȚE LUNARE (LUNILE SEPTEMBRIE 2026 - IUNIE 2027) ---
MONTH_DEFS = [
    ("Septembrie 2026", "09"),
    ("Octombrie 2026", "10"),
    ("Noiembrie 2026", "11"),
    ("Decembrie 2026", "12"),
    ("Ianuarie 2027", "01"),
    ("Februarie 2027", "02"),
    ("Martie 2027", "03"),
    ("Aprilie 2027", "04"),
    ("Mai 2027", "05"),
    ("Iunie 2027", "06")
]

def parse_absence_month(abs_str):
    if not abs_str: return None, False
    s = str(abs_str).strip()
    is_mot = False
    if s.endswith('m') or s.endswith('M'):
        is_mot = True
        s = s[:-1].strip()
    
    parts = s.replace('-', '.').replace('/', '.').split('.')
    if len(parts) >= 2:
        m_str = parts[1].zfill(2)
        return m_str, is_mot
    return None, False

def generate_excel_bytes(rows_data, sheet_name="Raport Excel"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name[:31]
    
    if not rows_data:
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
        
    headers = list(rows_data[0].keys())
    ws.append(headers)
    
    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        
    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    
    for r_idx, r_dict in enumerate(rows_data, 2):
        row_vals = [r_dict[h] for h in headers]
        ws.append(row_vals)
        for c_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=r_idx, column=c_idx)
            cell.border = thin_border
            if isinstance(cell.value, (int, float)):
                cell.alignment = Alignment(horizontal="center", vertical="center")
                
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def generate_excel_registru_elevi(students_data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registru Date Elevi"
    
    headers = [
        "Nr. Crt.", "Număr Matricol", "Nume", "Inițiala Tatălui", "Prenume", "Nume Complet",
        "CNP", "Telefon Elev", "Localitate", "Județ", "Stradă", "Număr Stradă", "Bloc", "Apartament",
        "Nume Mamă", "Telefon Mamă", "Mamă Plecată Străinătate", "Țară Mamă",
        "Nume Tată", "Telefon Tată", "Tată Plecat Străinătate", "Țară Tată",
        "Naționalitate", "Etnie", "CES", "Orfan", "Plasament", "Bursă Socială Medicală", "Bursă Socială Venit"
    ]
    
    ws.append(headers)
    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    center_align = Alignment(horizontal="center", vertical="center", wrap_text=True)
    
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        
    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    
    for idx, s in enumerate(students_data, 1):
        row = [
            idx,
            s.get('matricol', ''),
            s.get('nume', ''),
            s.get('initiala', ''),
            s.get('prenume', ''),
            s.get('nume_complet', ''),
            s.get('cnp', ''),
            s.get('telefon', ''),
            s.get('localitate', ''),
            s.get('judet', ''),
            s.get('strada', ''),
            s.get('numar_strada', ''),
            s.get('bloc', ''),
            s.get('apartament', ''),
            s.get('nume_mama', ''),
            s.get('telefon_mama', ''),
            'DA' if s.get('mama_plecata') else 'NU',
            s.get('tara_mama', ''),
            s.get('nume_tata', ''),
            s.get('telefon_tata', ''),
            'DA' if s.get('tata_plecat') else 'NU',
            s.get('tara_tata', ''),
            s.get('nationalitate', 'Română'),
            s.get('etnie', 'Română'),
            'DA' if s.get('ces') else 'NU',
            'DA' if s.get('orfan') else 'NU',
            'DA' if s.get('plasament') else 'NU',
            'DA' if s.get('bursa_medicala') else 'NU',
            'DA' if s.get('bursa_venit') else 'NU'
        ]
        ws.append(row)
        for c_idx in range(1, len(row) + 1):
            c = ws.cell(row=idx+1, column=c_idx)
            c.border = thin_border
            if c_idx in [1, 2, 7, 8, 16, 17, 20, 21, 25, 26, 27, 28, 29]:
                c.alignment = Alignment(horizontal='center', vertical='center')

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def generate_excel_statistica_clasa(students_data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Statistică Clasă"
    
    title_fill = PatternFill(start_color='1A365D', end_color='1A365D', fill_type='solid')
    title_font = Font(name='Calibri', size=14, bold=True, color='FFFFFF')
    section_fill = PatternFill(start_color='2B6CB0', end_color='2B6CB0', fill_type='solid')
    section_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(start_color='EDF2F7', end_color='EDF2F7', fill_type='solid')
    header_font = Font(name='Calibri', size=10, bold=True, color='1A365D')
    
    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    center_align = Alignment(horizontal='center', vertical='center')
    
    ws.merge_cells('A1:E1')
    ws['A1'] = "RAPORT STATISTIC SINTETIC CLASĂ (IX TH TURISM)"
    ws['A1'].fill = title_fill
    ws['A1'].font = title_font
    ws['A1'].alignment = center_align
    ws.row_dimensions[1].height = 30
    
    curr_row = 3
    
    # 1. Repartizare Sex
    boys = sum(1 for s in students_data if get_student_sex(s) == 'Băiat')
    girls = sum(1 for s in students_data if get_student_sex(s) == 'Fată')
    total_el = len(students_data) or 1
    
    ws.cell(row=curr_row, column=1, value="1. REPARTIZAREA ELEVILOR PE SEX").font = section_font
    ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=4)
    for c in range(1, 5): ws.cell(row=curr_row, column=c).fill = section_fill
    curr_row += 1
    
    headers_1 = ["Gen / Sex", "Număr Elevi", "Pondere (%)", "Observații"]
    for c_idx, h in enumerate(headers_1, 1):
        cell = ws.cell(row=curr_row, column=c_idx, value=h)
        cell.fill = header_fill; cell.font = header_font; cell.border = thin_border
    curr_row += 1
    
    rows_1 = [
        ["Băieți", boys, f"{(boys/total_el*100):.1f}%", "Elevi de sex masculin"],
        ["Fete", girls, f"{(girls/total_el*100):.1f}%", "Elevi de sex feminin"],
        ["TOTAL CLASĂ", len(students_data), "100.0%", "Efectiv total elevi"]
    ]
    for r in rows_1:
        for c_idx, val in enumerate(r, 1):
            cell = ws.cell(row=curr_row, column=c_idx, value=val)
            cell.border = thin_border
            if c_idx in [2, 3]: cell.alignment = center_align
        curr_row += 1
        
    curr_row += 1
    
    # 2. Varsta
    ws.cell(row=curr_row, column=1, value="2. GRUPAREA ELEVILOR PE VÂRSTĂ ȘI SEX").font = section_font
    ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=4)
    for c in range(1, 5): ws.cell(row=curr_row, column=c).fill = section_fill
    curr_row += 1
    
    headers_2 = ["Categorie Vârstă", "Total Elevi", "din care Băieți", "din care Fete"]
    for c_idx, h in enumerate(headers_2, 1):
        cell = ws.cell(row=curr_row, column=c_idx, value=h)
        cell.fill = header_fill; cell.font = header_font; cell.border = thin_border
    curr_row += 1
    
    age_groups = {'14 ani': {'b': 0, 'f': 0}, '15 ani': {'b': 0, 'f': 0}, '16 ani': {'b': 0, 'f': 0}, '17+ ani': {'b': 0, 'f': 0}, 'Fără CNP / Neconfirmat': {'b': 0, 'f': 0}}
    for s in students_data:
        sex = get_student_sex(s)
        cnp_info = parse_cnp(s.get('cnp', ''))
        age = cnp_info['age']
        if age == 14: key = '14 ani'
        elif age == 15: key = '15 ani'
        elif age == 16: key = '16 ani'
        elif isinstance(age, int) and age >= 17: key = '17+ ani'
        else: key = 'Fără CNP / Neconfirmat'
        
        if sex == 'Băiat': age_groups[key]['b'] += 1
        else: age_groups[key]['f'] += 1
        
    for k, v in age_groups.items():
        tot = v['b'] + v['f']
        row = [k, tot, v['b'], v['f']]
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=curr_row, column=c_idx, value=val)
            cell.border = thin_border
            if c_idx in [2, 3, 4]: cell.alignment = center_align
        curr_row += 1
        
    curr_row += 1
    
    # 3. Etnie si Nationalitate
    ws.cell(row=curr_row, column=1, value="3. ETNIE ȘI NAȚIONALITATE").font = section_font
    ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=4)
    for c in range(1, 5): ws.cell(row=curr_row, column=c).fill = section_fill
    curr_row += 1
    
    headers_3 = ["Etnie / Naționalitate", "Total Elevi", "din care Băieți", "din care Fete"]
    for c_idx, h in enumerate(headers_3, 1):
        cell = ws.cell(row=curr_row, column=c_idx, value=h)
        cell.fill = header_fill; cell.font = header_font; cell.border = thin_border
    curr_row += 1
    
    etnie_groups = {}
    for s in students_data:
        et = s.get('etnie', '').strip() or s.get('nationalitate', '').strip() or 'Română'
        sex = get_student_sex(s)
        if et not in etnie_groups: etnie_groups[et] = {'b': 0, 'f': 0}
        if sex == 'Băiat': etnie_groups[et]['b'] += 1
        else: etnie_groups[et]['f'] += 1
        
    for k, v in etnie_groups.items():
        tot = v['b'] + v['f']
        row = [k, tot, v['b'], v['f']]
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=curr_row, column=c_idx, value=val)
            cell.border = thin_border
            if c_idx in [2, 3, 4]: cell.alignment = center_align
        curr_row += 1
        
    curr_row += 1
    
    # 4. Burse si CES
    ws.cell(row=curr_row, column=1, value="4. BURSE SOCIALE ȘI CES").font = section_font
    ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=4)
    for c in range(1, 5): ws.cell(row=curr_row, column=c).fill = section_fill
    curr_row += 1
    
    headers_4 = ["Tip Bursă / Sprijin", "Total Elevi", "din care Băieți", "din care Fete"]
    for c_idx, h in enumerate(headers_4, 1):
        cell = ws.cell(row=curr_row, column=c_idx, value=h)
        cell.fill = header_fill; cell.font = header_font; cell.border = thin_border
    curr_row += 1
    
    b_med = {'b': sum(1 for s in students_data if s.get('bursa_medicala') and get_student_sex(s)=='Băiat'), 'f': sum(1 for s in students_data if s.get('bursa_medicala') and get_student_sex(s)=='Fată')}
    b_ven = {'b': sum(1 for s in students_data if s.get('bursa_venit') and get_student_sex(s)=='Băiat'), 'f': sum(1 for s in students_data if s.get('bursa_venit') and get_student_sex(s)=='Fată')}
    e_ces = {'b': sum(1 for s in students_data if s.get('ces') and get_student_sex(s)=='Băiat'), 'f': sum(1 for s in students_data if s.get('ces') and get_student_sex(s)=='Fată')}
    
    rows_4 = [
        ["Bursă Socială Medicală", b_med['b']+b_med['f'], b_med['b'], b_med['f']],
        ["Bursă Socială (Venit Mic)", b_ven['b']+b_ven['f'], b_ven['b'], b_ven['f']],
        ["Cerințe Educaționale Speciale (CES)", e_ces['b']+e_ces['f'], e_ces['b'], e_ces['f']],
    ]
    for r in rows_4:
        for c_idx, val in enumerate(r, 1):
            cell = ws.cell(row=curr_row, column=c_idx, value=val)
            cell.border = thin_border
            if c_idx in [2, 3, 4]: cell.alignment = center_align
        curr_row += 1
        
    curr_row += 1
    
    # 5. Situatii Sociale Speciale
    ws.cell(row=curr_row, column=1, value="5. SITUAȚII SOCIALE SPECIALE").font = section_font
    ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=4)
    for c in range(1, 5): ws.cell(row=curr_row, column=c).fill = section_fill
    curr_row += 1
    
    headers_5 = ["Categorie Specială", "Total Elevi", "din care Băieți", "din care Fete"]
    for c_idx, h in enumerate(headers_5, 1):
        cell = ws.cell(row=curr_row, column=c_idx, value=h)
        cell.fill = header_fill; cell.font = header_font; cell.border = thin_border
    curr_row += 1
    
    e_orf = {'b': sum(1 for s in students_data if s.get('orfan') and get_student_sex(s)=='Băiat'), 'f': sum(1 for s in students_data if s.get('orfan') and get_student_sex(s)=='Fată')}
    e_plas = {'b': sum(1 for s in students_data if s.get('plasament') and get_student_sex(s)=='Băiat'), 'f': sum(1 for s in students_data if s.get('plasament') and get_student_sex(s)=='Fată')}
    
    rows_5 = [
        ["Elevi Orfani", e_orf['b']+e_orf['f'], e_orf['b'], e_orf['f']],
        ["Elevi în Plasament", e_plas['b']+e_plas['f'], e_plas['b'], e_plas['f']],
    ]
    for r in rows_5:
        for c_idx, val in enumerate(r, 1):
            cell = ws.cell(row=curr_row, column=c_idx, value=val)
            cell.border = thin_border
            if c_idx in [2, 3, 4]: cell.alignment = center_align
        curr_row += 1

    curr_row += 1
    
    # 6. Parinti plecati in strainatate
    ws.cell(row=curr_row, column=1, value="6. PĂRINȚI PLECAȚI ÎN STRĂINĂTATE PE ȚĂRI").font = section_font
    ws.merge_cells(start_row=curr_row, start_column=1, end_row=curr_row, end_column=5)
    for c in range(1, 6): ws.cell(row=curr_row, column=c).fill = section_fill
    curr_row += 1
    
    headers_6 = ["Țară Destinație", "Mamă Plecată", "Tată Plecat", "Total Elevi Afectați", "din care Băieți / Fete"]
    for c_idx, h in enumerate(headers_6, 1):
        cell = ws.cell(row=curr_row, column=c_idx, value=h)
        cell.fill = header_fill; cell.font = header_font; cell.border = thin_border
    curr_row += 1
    
    tari_map = {}
    for s in students_data:
        m_plec = s.get('mama_plecata')
        t_plec = s.get('tata_plecat')
        tara_m = s.get('tara_mama', '').strip()
        tara_t = s.get('tara_tata', '').strip()
        sex = get_student_sex(s)
        
        tari = set()
        if m_plec and tara_m: tari.add(tara_m)
        if t_plec and tara_t: tari.add(tara_t)
        
        for tr in tari:
            if tr not in tari_map: tari_map[tr] = {'mama': 0, 'tata': 0, 'tot': 0, 'b': 0, 'f': 0}
            if m_plec and (s.get('tara_mama', '').strip() == tr): tari_map[tr]['mama'] += 1
            if t_plec and (s.get('tara_tata', '').strip() == tr): tari_map[tr]['tata'] += 1
            tari_map[tr]['tot'] += 1
            if sex == 'Băiat': tari_map[tr]['b'] += 1
            else: tari_map[tr]['f'] += 1
            
    if not tari_map:
        row = ["Nicio înregistrare", 0, 0, 0, "0 Băieți / 0 Fete"]
        for c_idx, val in enumerate(row, 1):
            cell = ws.cell(row=curr_row, column=c_idx, value=val)
            cell.border = thin_border
            if c_idx in [2, 3, 4, 5]: cell.alignment = center_align
        curr_row += 1
    else:
        for tr_k, tr_v in tari_map.items():
            row = [tr_k, tr_v['mama'], tr_v['tata'], tr_v['tot'], f"{tr_v['b']} Băieți / {tr_v['f']} Fete"]
            for c_idx, val in enumerate(row, 1):
                cell = ws.cell(row=curr_row, column=c_idx, value=val)
                cell.border = thin_border
                if c_idx in [2, 3, 4, 5]: cell.alignment = center_align
            curr_row += 1

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)

    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def calculate_lunar_student_absences(file_path):
    student_lunar_rows = []
    if not os.path.exists(file_path):
        return student_lunar_rows
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        
        for idx, e in enumerate(ELEVI):
            s_row = 9 + idx
            m_stats = {m_code: {'nem': 0, 'mot': 0, 'tot': 0} for _, m_code in MONTH_DEFS}
            
            for s_name, col in DISCIPLINE_CG:
                for k in range(30):
                    av = ws_cg.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != "":
                        m_code, is_mot = parse_absence_month(av)
                        if m_code in m_stats:
                            if is_mot: m_stats[m_code]['mot'] += 1
                            else: m_stats[m_code]['nem'] += 1
                            m_stats[m_code]['tot'] += 1

            for s_name, col in MODULE_TH:
                for k in range(30):
                    av = ws_th.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != "":
                        m_code, is_mot = parse_absence_month(av)
                        if m_code in m_stats:
                            if is_mot: m_stats[m_code]['mot'] += 1
                            else: m_stats[m_code]['nem'] += 1
                            m_stats[m_code]['tot'] += 1

            row_dict = {
                "Nr.": idx + 1,
                "Nume și Prenume Elev": e[1],
                "Matricol": e[3]
            }
            
            tot_an_nem = 0
            tot_an_mot = 0
            
            for m_label, m_code in MONTH_DEFS:
                st_m = m_stats[m_code]
                tot_an_nem += st_m['nem']
                tot_an_mot += st_m['mot']
                row_dict[f"{m_label} - Nemotivate"] = st_m['nem']
                row_dict[f"{m_label} - Motivate"] = st_m['mot']
                row_dict[f"{m_label} - Total"] = st_m['tot']

            row_dict["TOTAL ANUAL - Nemotivate"] = tot_an_nem
            row_dict["TOTAL ANUAL - Motivate"] = tot_an_mot
            row_dict["TOTAL ANUAL - General Absențe"] = tot_an_nem + tot_an_mot
            
            student_lunar_rows.append(row_dict)

        wb.close()
    except Exception: pass
    return student_lunar_rows

def calculate_lunar_subject_absences(file_path):
    subject_lunar_rows = []
    if not os.path.exists(file_path):
        return subject_lunar_rows
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        
        tot_class_lunar = {m_code: {'nem': 0, 'mot': 0, 'tot': 0} for _, m_code in MONTH_DEFS}

        for cat_name, ws_obj, sub_list in [("Cultură Generală", ws_cg, DISCIPLINE_CG), ("Module Tehnologice", ws_th, MODULE_TH)]:
            for s_name, col in sub_list:
                s_m_stats = {m_code: {'nem': 0, 'mot': 0, 'tot': 0} for _, m_code in MONTH_DEFS}
                
                for idx in range(len(ELEVI)):
                    s_row = 9 + idx
                    for k in range(30):
                        av = ws_obj.cell(row=s_row, column=col + 21 + k).value
                        if av is not None and str(av).strip() != "":
                            m_code, is_mot = parse_absence_month(av)
                            if m_code in s_m_stats:
                                if is_mot:
                                    s_m_stats[m_code]['mot'] += 1
                                    tot_class_lunar[m_code]['mot'] += 1
                                else:
                                    s_m_stats[m_code]['nem'] += 1
                                    tot_class_lunar[m_code]['nem'] += 1
                                s_m_stats[m_code]['tot'] += 1
                                tot_class_lunar[m_code]['tot'] += 1

                row_dict = {
                    "Categorie": cat_name,
                    "Disciplină / Modul": s_name
                }
                
                tot_sub_nem = 0
                tot_sub_mot = 0
                
                for m_label, m_code in MONTH_DEFS:
                    st_m = s_m_stats[m_code]
                    tot_sub_nem += st_m['nem']
                    tot_sub_mot += st_m['mot']
                    row_dict[f"{m_label} - Nemotivate Clasă"] = st_m['nem']
                    row_dict[f"{m_label} - Motivate Clasă"] = st_m['mot']
                    row_dict[f"{m_label} - Total Clasă"] = st_m['tot']

                row_dict["TOTAL ANUAL - Nemotivate Clasă"] = tot_sub_nem
                row_dict["TOTAL ANUAL - Motivate Clasă"] = tot_sub_mot
                row_dict["TOTAL ANUAL - General Clasă"] = tot_sub_nem + tot_sub_mot
                
                subject_lunar_rows.append(row_dict)

        tot_row_dict = {
            "Categorie": "TOTAL CLASĂ",
            "Disciplină / Modul": "TOTAL GENERAL CLASĂ"
        }
        tot_gen_class_nem = 0
        tot_gen_class_mot = 0
        
        for m_label, m_code in MONTH_DEFS:
            st_m = tot_class_lunar[m_code]
            tot_gen_class_nem += st_m['nem']
            tot_gen_class_mot += st_m['mot']
            tot_row_dict[f"{m_label} - Nemotivate Clasă"] = st_m['nem']
            tot_row_dict[f"{m_label} - Motivate Clasă"] = st_m['mot']
            tot_row_dict[f"{m_label} - Total Clasă"] = st_m['tot']

        tot_row_dict["TOTAL ANUAL - Nemotivate Clasă"] = tot_gen_class_nem
        tot_row_dict["TOTAL ANUAL - Motivate Clasă"] = tot_gen_class_mot
        tot_row_dict["TOTAL ANUAL - General Clasă"] = tot_gen_class_nem + tot_gen_class_mot
        
        subject_lunar_rows.append(tot_row_dict)

        wb.close()
    except Exception: pass
    return subject_lunar_rows

# --- CALCUL DINAMIC ÎN TIMP REAL PENTRU VIZUALIZĂRI ȘI RAPOARTE ---
def calculate_all_class_stats(file_path):
    students_data = []
    subject_totals = {}
    
    for cat_name, sub_list in [("Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", MODULE_TH)]:
        for s_name, _ in sub_list:
            subject_totals[(cat_name, s_name)] = {'nem': 0, 'mot': 0, 'tot': 0}
            
    if not os.path.exists(file_path):
        return students_data, subject_totals

    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        
        for idx, e in enumerate(ELEVI):
            s_row = 9 + idx
            cg_avgs = []
            tot_abs_nem = 0
            tot_abs_mot = 0
            student_subject_abs = {}
            
            for s_name, col in DISCIPLINE_CG:
                notes = []
                for k in range(10):
                    v = ws_cg.cell(row=s_row, column=col + k*2).value
                    if v is not None and str(v).strip() != "":
                        try: notes.append(float(v))
                        except Exception: pass
                if notes:
                    cg_avgs.append(round(sum(notes)/len(notes), 2))
                    
                sub_nem = 0
                sub_mot = 0
                for k in range(30):
                    av = ws_cg.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != "":
                        s = str(av).strip()
                        if s.endswith('m') or s.endswith('M'): sub_mot += 1
                        else: sub_nem += 1
                        
                tot_abs_nem += sub_nem
                tot_abs_mot += sub_mot
                sub_tot = sub_nem + sub_mot
                student_subject_abs[s_name] = {'cat': "Cultură Generală", 'nem': sub_nem, 'mot': sub_mot, 'tot': sub_tot}
                
                subject_totals[("Cultură Generală", s_name)]['nem'] += sub_nem
                subject_totals[("Cultură Generală", s_name)]['mot'] += sub_mot
                subject_totals[("Cultură Generală", s_name)]['tot'] += sub_tot

            th_avgs = []
            for s_name, col in MODULE_TH:
                notes = []
                for k in range(10):
                    v = ws_th.cell(row=s_row, column=col + k*2).value
                    if v is not None and str(v).strip() != "":
                        try: notes.append(float(v))
                        except Exception: pass
                if notes:
                    th_avgs.append(round(sum(notes)/len(notes), 2))
                    
                sub_nem = 0
                sub_mot = 0
                for k in range(30):
                    av = ws_th.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != "":
                        s = str(av).strip()
                        if s.endswith('m') or s.endswith('M'): sub_mot += 1
                        else: sub_nem += 1
                        
                tot_abs_nem += sub_nem
                tot_abs_mot += sub_mot
                sub_tot = sub_nem + sub_mot
                student_subject_abs[s_name] = {'cat': "Module Tehnologice", 'nem': sub_nem, 'mot': sub_mot, 'tot': sub_tot}
                
                subject_totals[("Module Tehnologice", s_name)]['nem'] += sub_nem
                subject_totals[("Module Tehnologice", s_name)]['mot'] += sub_mot
                subject_totals[("Module Tehnologice", s_name)]['tot'] += sub_tot

            mcg = round(sum(cg_avgs)/len(cg_avgs), 2) if cg_avgs else None
            mth = round(sum(th_avgs)/len(th_avgs), 2) if th_avgs else None
            
            if mcg is not None and mth is not None: mg = round((mcg + mth)/2.0, 2)
            elif mcg is not None: mg = mcg
            elif mth is not None: mg = mth
            else: mg = None
                
            tot_abs = tot_abs_nem + tot_abs_mot
            purtare = max(1, 10 - int(tot_abs_nem / 20))
            
            statut = "-"
            if mcg is not None or mth is not None:
                if (mcg is None or mcg >= 5) and (mth is None or mth >= 5) and purtare >= 5:
                    statut = "Promovat"
                else:
                    statut = "Corigent / Repetent"

            max_sub = "Nicio absență"
            max_sub_info = {'nem': 0, 'mot': 0, 'tot': 0}
            max_val = -1
            for s_name, s_info in student_subject_abs.items():
                if s_info['tot'] > max_val and s_info['tot'] > 0:
                    max_val = s_info['tot']
                    max_sub = s_name
                    max_sub_info = s_info

            students_data.append({
                'idx': idx,
                'nr': idx + 1,
                'nume': e[1],
                'rm_pg': e[2],
                'matr': e[3],
                'mcg': mcg,
                'mth': mth,
                'mg': mg,
                'purtare': purtare,
                'statut': statut,
                'tot_abs': tot_abs,
                'abs_nem': tot_abs_nem,
                'abs_mot': tot_abs_mot,
                'max_sub': max_sub,
                'max_sub_info': max_sub_info,
                'subject_abs': student_subject_abs
            })
            
        wb.close()
        
        valid_mgs = sorted([s['mg'] for s in students_data if s['mg'] is not None], reverse=True)
        for s in students_data:
            if s['mg'] is not None:
                rang = valid_mgs.index(s['mg']) + 1
                s['rang'] = str(rang)
                if rang == 1: s['premiu'] = "Premiul I"
                elif rang == 2: s['premiu'] = "Premiul II"
                elif rang == 3: s['premiu'] = "Premiul III"
                elif rang <= 7: s['premiu'] = "Mențiune"
                else: s['premiu'] = "Membru"
            else:
                s['rang'] = "-"
                s['premiu'] = "-"

        sorted_tot_abs = sorted([s['tot_abs'] for s in students_data], reverse=True)
        sorted_nem_abs = sorted([s['abs_nem'] for s in students_data], reverse=True)
        for s in students_data:
            s['abs_tot_rank'] = sorted_tot_abs.index(s['tot_abs']) + 1
            s['abs_nem_rank'] = sorted_nem_abs.index(s['abs_nem']) + 1

    except Exception: pass

    return students_data, subject_totals

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
    
    render_copyright_footer()
    st.stop()

# --- APLICAȚIA PRINCIPALA PENTRU PROFESORI ---

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
        except Exception: pass

    st.divider()
    if st.button("🚪 Deconectare (Logout)", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
        
    render_sidebar_copyright()

if not os.path.exists(selected_file):
    st.warning(f"⚠️ Fișierul catalog '{selected_file}' nu a fost găsit în directorul curent.")

tab1, tab2, tab3, tab_del, tab4, tab5, tab6, tab_gestiune = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "🗑️ Ștergere Notă/Absență",
    "📊 Fișă Elev",
    "📈 Centralizator Clasă",
    "📋 Raport Diriginte",
    "👥 Gestiune Elevi"
])

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

    e = ELEVI[student_idx]
    
    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA"), title_style))
    story.append(Paragraph(clean_pdf_text("FIȘĂ ȘCOLARĂ INDIVIDUALĂ ELEV"), title_style))
    story.append(Paragraph(clean_pdf_text(f"Clasa a IX-a TH — Turism și Alimentație | An Școlar 2026–2027"), subtitle_style))
    story.append(Spacer(1, 10))
    
    info_text = f"<b>Elev:</b> {e[1]} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Matricol:</b> {e[3]} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Cod PIN Părinți:</b> {PINS[student_idx]}"
    story.append(Paragraph(clean_pdf_text(info_text), heading_style))
    story.append(Spacer(1, 6))

    if os.path.exists(file_path):
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            for cat_title, sheet_n, sub_list in [("CULTURĂ GENERALĂ", "Cultură Generală", DISCIPLINE_CG), ("MODULE TEHNOLOGICE", "Module Tehnologice", MODULE_TH)]:
                story.append(Paragraph(clean_pdf_text(cat_title), heading_style))
                ws = wb[sheet_n]
                s_row = 9 + student_idx
                
                t_data = [[
                    Paragraph(clean_pdf_text("<b>Disciplină / Modul</b>"), cell_bold),
                    Paragraph(clean_pdf_text("<b>Note & Date</b>"), cell_bold),
                    Paragraph(clean_pdf_text("<b>Absențe (Tot/Nem/Mot) & Date</b>"), cell_bold),
                    Paragraph(clean_pdf_text("<b>Medie</b>"), cell_bold)
                ]]
                
                for s_name, start_col in sub_list:
                    notes = []
                    for k in range(10):
                        n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                        if n_val is not None and str(n_val).strip() != "":
                            d_str = f" ({d_val})" if d_val else ""
                            notes.append(f"{n_val}{d_str}")
                    
                    absences = []
                    sub_nem = 0
                    sub_mot = 0
                    for k in range(30):
                        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            s_a = str(a_val).strip()
                            absences.append(s_a)
                            if s_a.endswith('m') or s_a.endswith('M'): sub_mot += 1
                            else: sub_nem += 1
                            
                    sub_tot = sub_nem + sub_mot
                    abs_str_formatted = f"{sub_tot} tot ({sub_nem} nem / {sub_mot} mot) - {', '.join(absences)}" if sub_tot > 0 else "0"
                    
                    media_val = ws.cell(row=s_row, column=start_col + 20).value
                    media_str = safe_float_str(media_val)
                    
                    t_data.append([
                        Paragraph(clean_pdf_text(s_name), cell_style),
                        Paragraph(clean_pdf_text(", ".join(notes) if notes else "-"), cell_style),
                        Paragraph(clean_pdf_text(abs_str_formatted), cell_style),
                        Paragraph(clean_pdf_text(media_str), cell_bold)
                    ])
                    
                table = Table(t_data, colWidths=[160, 160, 150, 50])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
                    ('PADDING', (0,0), (-1,-1), 4),
                    ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
                ]))
                story.append(table)
                story.append(Spacer(1, 8))
            wb.close()
        except Exception: pass

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_pdf_centralizator(file_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=PDF_FONT_BOLD, fontSize=13, leading=16, alignment=1, textColor=colors.HexColor("#1A365D"))
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontName=PDF_FONT, fontSize=7, leading=9)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=7, leading=9)

    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA — CENTRALIZATOR GENERAL CLASĂ IX TH"), title_style))
    story.append(Spacer(1, 8))
    
    stats, _ = calculate_all_class_stats(file_path)
    
    t_data = [[
        Paragraph(clean_pdf_text("<b>Nr.</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Nume și Prenume Elev</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Matricol</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Medie CG</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Medie TH</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Medie Gen.</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Purtare</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Statut</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Absențe</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Rang</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Premiu</b>"), cell_bold)
    ]]
    
    for s in stats:
        t_data.append([
            Paragraph(clean_pdf_text(str(s['nr'])), cell_style),
            Paragraph(clean_pdf_text(s['nume']), cell_bold),
            Paragraph(clean_pdf_text(s['matr']), cell_style),
            Paragraph(clean_pdf_text(safe_float_str(s['mcg'])), cell_style),
            Paragraph(clean_pdf_text(safe_float_str(s['mth'])), cell_style),
            Paragraph(clean_pdf_text(safe_float_str(s['mg'])), cell_bold),
            Paragraph(clean_pdf_text(str(s['purtare'])), cell_style),
            Paragraph(clean_pdf_text(s['statut']), cell_style),
            Paragraph(clean_pdf_text(str(s['tot_abs'])), cell_style),
            Paragraph(clean_pdf_text(s['rang']), cell_style),
            Paragraph(clean_pdf_text(s['premiu']), cell_style)
        ])
        
    table = Table(t_data, colWidths=[25, 200, 60, 55, 55, 60, 45, 80, 50, 40, 80])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 3),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE')
    ]))
    story.append(table)
    
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

    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA"), title_style))
    story.append(Paragraph(clean_pdf_text("RAPORT SEMESTRIAL / ANUAL AL DIRIGINTELUI"), title_style))
    story.append(Spacer(1, 10))
    
    stats, _ = calculate_all_class_stats(file_path)
    tot_el = len(stats)
    promovati = [s for s in stats if s['statut'] == "Promovat"]
    promov_str = f"{len(promovati)}/{tot_el} ({(len(promovati)/tot_el*100):.1f}%)" if tot_el else "-"
    
    valid_mgs = [s['mg'] for s in stats if s['mg'] is not None]
    med_clasa = f"{(sum(valid_mgs)/len(valid_mgs)):.2f}" if valid_mgs else "-"
    med_purt = f"{(sum(s['purtare'] for s in stats)/tot_el):.2f}" if tot_el else "10.00"
    tot_abs_sum = sum(s['tot_abs'] for s in stats)
    tot_abs_str = f"{tot_abs_sum}"
    
    kpi_data = [
        [Paragraph(clean_pdf_text("<b>Total Elevi</b>"), cell_bold), Paragraph(clean_pdf_text("<b>Promovabilitate</b>"), cell_bold), Paragraph(clean_pdf_text("<b>Media Clasei</b>"), cell_bold), Paragraph(clean_pdf_text("<b>Media Purtare</b>"), cell_bold), Paragraph(clean_pdf_text("<b>Total Absențe</b>"), cell_bold)],
        [Paragraph(clean_pdf_text(str(tot_el)), cell_style), Paragraph(clean_pdf_text(promov_str), cell_style), Paragraph(clean_pdf_text(med_clasa), cell_style), Paragraph(clean_pdf_text(med_purt), cell_style), Paragraph(clean_pdf_text(tot_abs_str), cell_style)]
    ]
    t_kpi = Table(kpi_data, colWidths=[100, 100, 100, 100, 120])
    t_kpi.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2B6CB0")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    story.append(t_kpi)
    story.append(Spacer(1, 10))
    
    story.append(Paragraph(clean_pdf_text("DISTRIBUȚIA MEDIILOR ȘI FRECVENȚA"), heading_style))
    dist_data = [[Paragraph(clean_pdf_text("<b>Tranșă Medie</b>"), cell_bold), Paragraph(clean_pdf_text("<b>Nr. Elevi</b>"), cell_bold), Paragraph(clean_pdf_text("<b>Pondere</b>"), cell_bold)]]
    
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
        dist_data.append([Paragraph(clean_pdf_text(label), cell_style), Paragraph(clean_pdf_text(str(cnt)), cell_style), Paragraph(clean_pdf_text(pond), cell_style)])
        
    t_dist = Table(dist_data, colWidths=[250, 120, 150])
    t_dist.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 4)
    ]))
    story.append(t_dist)

    doc.build(story)
    buffer.seek(0)
    return buffer

def generate_pdf_pins(file_path):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    story = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontName=PDF_FONT_BOLD, fontSize=13, leading=16, alignment=1, textColor=colors.HexColor("#1A365D"))
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Normal'], fontName=PDF_FONT, fontSize=9, leading=12, alignment=1, textColor=colors.HexColor("#4A5568"))
    cell_style = ParagraphStyle('Cell', parent=styles['Normal'], fontName=PDF_FONT, fontSize=8, leading=11)
    cell_bold = ParagraphStyle('CellBold', parent=styles['Normal'], fontName=PDF_FONT_BOLD, fontSize=8, leading=11)

    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA"), title_style))
    story.append(Paragraph(clean_pdf_text("LISTA CODURILOR PIN CONFIDENȚIALE PENTRU PORTALUL PĂRINȚILOR"), title_style))
    story.append(Paragraph(clean_pdf_text("Clasa a IX-a TH — Turism și Alimentație | Document Confidențial (Diriginte)"), subtitle_style))
    story.append(Spacer(1, 12))
    
    pin_table_data = [[
        Paragraph(clean_pdf_text("<b>Nr.</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Nume și Prenume Elev</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Nr. Matricol</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>COD PIN ACCES PĂRINTE</b>"), cell_bold)
    ]]
    
    for idx, e in enumerate(ELEVI):
        pin_table_data.append([
            Paragraph(clean_pdf_text(str(e[0])), cell_style),
            Paragraph(clean_pdf_text(e[1]), cell_style),
            Paragraph(clean_pdf_text(e[3]), cell_style),
            Paragraph(clean_pdf_text(f"<b>{PINS[idx]}</b>"), cell_bold)
        ])
        
    t_pin = Table(pin_table_data, colWidths=[30, 240, 100, 150])
    t_pin.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E0")),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (3,0), (3,-1), 'CENTER')
    ]))
    story.append(t_pin)
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
                    st.success(f"✅ Notă salvată: {nota_val} pe {data_nota} la {materii[mat_idx_n]} (Slot N{slot_num}) pentru {ELEVI[elev_idx_n][1]}")
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

# --- TAB 4: ȘTERGERE NOTĂ / ABSENȚĂ ---
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
                        if n_val is not None and str(n_val).strip() != "":
                            d_str = f" din data {d_val}" if d_val else ""
                            existing_items.append(f"Slot N{k+1}: Notă {n_val}{d_str}")
                            item_coords.append((n_col, d_col))
                else:
                    for k in range(30):
                        a_col = start_col + 21 + k
                        a_val = ws.cell(row=student_row, column=a_col).value
                        if a_val is not None and str(a_val).strip() != "":
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

# --- TAB 5: FIȘĂ ELEV ---
with tab4:
    st.subheader("Fișă Elev & Rezumat")
    col_v1, col_v2 = st.columns([3, 1])
    with col_v1:
        elev_idx_v = st.selectbox("Alege Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_v")
    with col_v2:
        st.write("")
        st.write("")
        try:
            pdf_bytes = generate_pdf_student(elev_idx_v, selected_file)
            st.download_button("🖨️ Descarcă Fișă PDF", data=pdf_bytes, file_name=f"Fisa_Elev_{ELEVI[elev_idx_v][1].replace(' ', '_')}.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare PDF: {ex}")

    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            e_info = ELEVI[elev_idx_v]
            st.markdown(f"### 👤 {e_info[1]} (Matricol {e_info[3]}) | Cod PIN Părinți: `{PINS[elev_idx_v]}`")
            
            for cat_title, sheet_n, sub_list in [("Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"#### {cat_title}")
                ws = wb[sheet_n]
                s_row = 9 + elev_idx_v
                
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
                    sub_nem = 0
                    sub_mot = 0
                    for k in range(30):
                        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            s_a = str(a_val).strip()
                            absences.append(s_a)
                            if s_a.endswith('m') or s_a.endswith('M'): sub_mot += 1
                            else: sub_nem += 1
                            
                    sub_tot = sub_nem + sub_mot
                    abs_str_formatted = f"{sub_tot} total ({sub_nem} nem. / {sub_mot} mot.) — Date: {', '.join(absences)}" if sub_tot > 0 else "Fără absențe (0)"
                    
                    media_val = ws.cell(row=s_row, column=start_col + 20).value
                    media_str = safe_float_str(media_val)
                    
                    rows_data.append({
                        "Disciplină / Modul": s_name,
                        "Note & Date": ", ".join(notes) if notes else "Fără note",
                        "Absențe Detaliate (Total / Nem / Mot)": abs_str_formatted,
                        "Medie": media_str
                    })
                st.dataframe(rows_data, use_container_width=True, hide_index=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire fișă: {ex}")

# --- TAB 6: CENTRALIZATOR CLASĂ ---
with tab5:
    st.subheader("📈 Centralizator General Clasă (Situție Școlară & Premii)")
    col_c1, col_c2 = st.columns([2, 1])
    with col_c2:
        try:
            pdf_cent_bytes = generate_pdf_centralizator(selected_file)
            st.download_button("🖨️ Descarcă Centralizator PDF", data=pdf_cent_bytes, file_name="Centralizator_General_IX_TH.pdf", mime="application/pdf", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare PDF Centralizator: {ex}")
            
    if os.path.exists(selected_file):
        try:
            stats, sub_totals = calculate_all_class_stats(selected_file)
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
            st.dataframe(c_data, use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("📊 Centralizator Absențe Lunare pe Elevi și pe Discipline")
            st.caption("Afișează și permite descărcarea în format Excel a situației lunare a absențelor (Septembrie 2026 - Iunie 2027).")
            
            col_l1, col_l2 = st.columns(2)
            with col_l1:
                try:
                    lunar_stud_rows = calculate_lunar_student_absences(selected_file)
                    if lunar_stud_rows:
                        ex_lunar_stud_bytes = generate_excel_bytes(lunar_stud_rows, sheet_name="Absente Lunare Elevi")
                        st.download_button("📊 Descarcă Absențe Lunare pe Elevi (.xlsx)", data=ex_lunar_stud_bytes, file_name="Absente_Lunare_Elevi_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except Exception as ex:
                    st.error(f"Eroare Excel Lunare Elevi: {ex}")
                    
            with col_l2:
                try:
                    lunar_sub_rows = calculate_lunar_subject_absences(selected_file)
                    if lunar_sub_rows:
                        ex_lunar_sub_bytes = generate_excel_bytes(lunar_sub_rows, sheet_name="Absente Lunare Discipline")
                        st.download_button("📊 Descarcă Absențe Lunare pe Discipline (.xlsx)", data=ex_lunar_sub_bytes, file_name="Absente_Lunare_Discipline_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except Exception as ex:
                    st.error(f"Eroare Excel Lunare Discipline: {ex}")
            
            st.divider()
            st.subheader("🔐 Coduri PIN Confidențiale Părinți")
            st.caption("Fișierul cu codurile de acces necesare părinților pentru autentificare în portalul lor.")
            
            col_p1, col_p2 = st.columns([3, 1])
            with col_p2:
                try:
                    pdf_pins_bytes = generate_pdf_pins(selected_file)
                    st.download_button("🖨️ Descarcă Listă PIN-uri (PDF)", data=pdf_pins_bytes, file_name="Lista_Coduri_PIN_Parinti_IX_TH.pdf", mime="application/pdf", use_container_width=True)
                except Exception as ex:
                    st.error(f"Eroare PDF PIN-uri: {ex}")
            
            pin_display_data = []
            for idx, e in enumerate(ELEVI):
                pin_display_data.append({
                    "Nr.": str(e[0]),
                    "Nume și Prenume Elev": e[1],
                    "Număr Matricol": e[3],
                    "COD PIN ACCES PĂRINTE": PINS[idx]
                })
            st.dataframe(pin_display_data, use_container_width=True, hide_index=True)
        except Exception as ex:
            st.error(f"Eroare la citire centralizator: {ex}")

# --- TAB 7: RAPORT DIRIGINTE ---
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
            stats, sub_totals = calculate_all_class_stats(selected_file)
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
            
            st.divider()
            st.markdown("#### 📊 Raport Centralizat al Absențelor pe Discipline (Include Ultimul Rând - Total Clasă)")
            abs_rap_rows = []
            tot_class_nem = 0
            tot_class_mot = 0
            
            for cat_name, sub_list in [("Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", MODULE_TH)]:
                for s_name, _ in sub_list:
                    s_info = sub_totals.get((cat_name, s_name), {'nem': 0, 'mot': 0, 'tot': 0})
                    tot_class_nem += s_info['nem']
                    tot_class_mot += s_info['mot']
                    abs_rap_rows.append({
                        "Categorie": cat_name,
                        "Disciplină / Modul": s_name,
                        "Absențe Nemotivate Clasă": s_info['nem'],
                        "Absențe Motivate Clasă": s_info['mot'],
                        "Total Absențe Clasă": s_info['tot']
                    })
            
            tot_class_all = tot_class_nem + tot_class_mot
            abs_rap_rows.append({
                "Categorie": "TOTAL CLASĂ",
                "Disciplină / Modul": "TOTAL GENERAL CLASĂ",
                "Absențe Nemotivate Clasă": tot_class_nem,
                "Absențe Motivate Clasă": tot_class_mot,
                "Total Absențe Clasă": tot_class_all
            })
            st.dataframe(abs_rap_rows, use_container_width=True, hide_index=True)
            try:
                excel_abs_bytes = generate_excel_bytes(abs_rap_rows, sheet_name="Absente Discipline")
                st.download_button("📊 Descarcă Raport Centralizat Absențe (.xlsx)", data=excel_abs_bytes, file_name="Raport_Centralizat_Absente_Discipline_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
            except Exception as ex:
                st.error(f"Eroare la generare Excel: {ex}")
            
            st.divider()
            st.markdown("#### 🏆 Clasament Complet Elevi în Funcție de Absențe (32 Elevi)")
            
            sort_criterion = st.radio("Criteriu Sortare Clasament Absențe:", ["După Total Absențe (Descrescător)", "După Absențe Nemotivate (Descrescător)"], horizontal=True, key="sort_crit_abs")
            
            if "Nemotivate" in sort_criterion:
                sorted_abs_stats = sorted(stats, key=lambda x: (x['abs_nem'], x['tot_abs']), reverse=True)
            else:
                sorted_abs_stats = sorted(stats, key=lambda x: (x['tot_abs'], x['abs_nem']), reverse=True)
                
            rank_abs_rows = []
            for r_idx, s in enumerate(sorted_abs_stats):
                max_sub_str = f"{s['max_sub']}"
                max_sub_det = f"{s['max_sub_info']['tot']} tot ({s['max_sub_info']['nem']} nem. / {s['max_sub_info']['mot']} mot.)" if s['max_sub_info']['tot'] > 0 else "0 absențe"
                rank_abs_rows.append({
                    "Loc Absențe": r_idx + 1,
                    "Nume și Prenume Elev": s['nume'],
                    "Matricol": s['matr'],
                    "Total Absențe": s['tot_abs'],
                    "Absențe Nemotivate": s['abs_nem'],
                    "Absențe Motivate": s['abs_mot'],
                    "Disciplina cu Cele Mai Multe Absențe": max_sub_str,
                    "Absențe la Disciplina Maximă": max_sub_det
                })
            st.dataframe(rank_abs_rows, use_container_width=True, hide_index=True)
            
            sorted_tot_stats = sorted(stats, key=lambda x: (x['tot_abs'], x['abs_nem']), reverse=True)
            rank_tot_rows = []
            for r_idx, s in enumerate(sorted_tot_stats):
                max_sub_str = f"{s['max_sub']}"
                max_sub_det = f"{s['max_sub_info']['tot']} tot ({s['max_sub_info']['nem']} nem. / {s['max_sub_info']['mot']} mot.)" if s['max_sub_info']['tot'] > 0 else "0 absențe"
                rank_tot_rows.append({
                    "Loc Absențe": r_idx + 1,
                    "Nume și Prenume Elev": s['nume'],
                    "Matricol": s['matr'],
                    "Total Absențe": s['tot_abs'],
                    "Absențe Nemotivate": s['abs_nem'],
                    "Absențe Motivate": s['abs_mot'],
                    "Disciplina cu Cele Mai Multe Absențe": max_sub_str,
                    "Absențe la Disciplina Maximă": max_sub_det
                })

            sorted_nem_stats = sorted(stats, key=lambda x: (x['abs_nem'], x['tot_abs']), reverse=True)
            rank_nem_rows = []
            for r_idx, s in enumerate(sorted_nem_stats):
                max_sub_str = f"{s['max_sub']}"
                max_sub_det = f"{s['max_sub_info']['tot']} tot ({s['max_sub_info']['nem']} nem. / {s['max_sub_info']['mot']} mot.)" if s['max_sub_info']['tot'] > 0 else "0 absențe"
                rank_nem_rows.append({
                    "Loc Absențe": r_idx + 1,
                    "Nume și Prenume Elev": s['nume'],
                    "Matricol": s['matr'],
                    "Total Absențe": s['tot_abs'],
                    "Absențe Nemotivate": s['abs_nem'],
                    "Absențe Motivate": s['abs_mot'],
                    "Disciplina cu Cele Mai Multe Absențe": max_sub_str,
                    "Absențe la Disciplina Maximă": max_sub_det
                })

            col_ex1, col_ex2 = st.columns(2)
            with col_ex1:
                try:
                    excel_tot_bytes = generate_excel_bytes(rank_tot_rows, sheet_name="Clasament Total Absente")
                    st.download_button("📊 Descarcă Clasament după Total Absențe (.xlsx)", data=excel_tot_bytes, file_name="Clasament_Elevi_Dupa_Total_Absente_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except Exception as ex:
                    st.error(f"Eroare la generare Excel: {ex}")

            with col_ex2:
                try:
                    excel_nem_bytes = generate_excel_bytes(rank_nem_rows, sheet_name="Clasament Absente Nemotivate")
                    st.download_button("📊 Descarcă Clasament după Absențe Nemotivate (.xlsx)", data=excel_nem_bytes, file_name="Clasament_Elevi_Dupa_Absente_Nemotivate_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except Exception as ex:
                    st.error(f"Eroare la generare Excel: {ex}")

            st.divider()
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
            st.dataframe(d_rows, use_container_width=True, hide_index=True)
            
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
                st.dataframe(top_rows, use_container_width=True, hide_index=True)
            else:
                st.info("ℹ️ Nu există încă elevi cu medii calculate pentru afișarea clasamentului.")
        except Exception as ex:
            st.error(f"Eroare la citire raport: {ex}")

# --- TAB 8: GESTIUNE ELEVI ---
with tab_gestiune:
    st.subheader("👥 Gestiune Bază de Date Elevi (Înregistrare & Statistică)")
    
    op_gest = st.radio(
        "Selectați operațiunea pe clasa de elevi:",
        ["✏️ Modificare Date Elev Existent", "➕ Adăugare Elev Nou în Clasă", "🗑️ Ștergere Elev din Clasă"],
        horizontal=True,
        key="op_gest_rad"
    )
    
    students_gest = load_gestiune_data()
    
    if op_gest == "✏️ Modificare Date Elev Existent":
        if not students_gest:
            st.warning("Nu există elevi în baza de date.")
        else:
            sel_idx = st.selectbox(
                "Alege Elevul pentru Editare Completa:",
                range(len(students_gest)),
                format_func=lambda i: f"{students_gest[i]['id']}. {students_gest[i]['nume_complet']} (Matr. {students_gest[i]['matricol']})",
                key="sel_edit_stud"
            )
            s = students_gest[sel_idx]
            
            with st.form("edit_student_form"):
                st.markdown("#### 1. 🆔 Identificare & Școlar")
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    f_matr = st.text_input("Număr Matricol:", value=s.get("matricol", ""), key="f_matr")
                    f_cnp = st.text_input("Cod Numeric Personal (CNP):", value=s.get("cnp", ""), key="f_cnp")
                with c2:
                    f_nume = st.text_input("Nume:", value=s.get("nume", ""), key="f_nume")
                    f_tel_elev = st.text_input("Telefon Elev:", value=s.get("telefon", ""), key="f_tel_e")
                with c3:
                    f_init = st.text_input("Inițiala Tatălui:", value=s.get("initiala", ""), key="f_init")
                    f_nat = st.text_input("Naționalitate:", value=s.get("nationalitate", "Română"), key="f_nat")
                with c4:
                    f_prenume = st.text_input("Prenume:", value=s.get("prenume", ""), key="f_prenume")
                    f_etnie = st.text_input("Etnie:", value=s.get("etnie", "Română"), key="f_etnie")
                    
                st.markdown("#### 2. 🏠 Adresă Domiciliu")
                a1, a2, a3, a4, a5, a6 = st.columns(6)
                with a1: f_loc = st.text_input("Localitate:", value=s.get("localitate", "Turda"), key="f_loc")
                with a2: f_jud = st.text_input("Județ:", value=s.get("judet", "Cluj"), key="f_jud")
                with a3: f_str = st.text_input("Stradă:", value=s.get("strada", ""), key="f_str")
                with a4: f_nr_str = st.text_input("Număr Stradă:", value=s.get("numar_strada", ""), key="f_nr_str")
                with a5: f_bloc = st.text_input("Bloc:", value=s.get("bloc", ""), key="f_bloc")
                with a6: f_ap = st.text_input("Apartament:", value=s.get("apartament", ""), key="f_ap")
                
                st.markdown("#### 3. 👨‍👩‍👧 Informații Părinți & Plecări Străinătate")
                p1, p2, p3, p4 = st.columns(4)
                with p1:
                    f_nume_m = st.text_input("Nume și Prenume Mamă:", value=s.get("nume_mama", ""), key="f_nume_m")
                    f_tel_m = st.text_input("Telefon Mamă:", value=s.get("telefon_mama", ""), key="f_tel_m")
                with p2:
                    f_m_plec = st.checkbox("Mamă plecată în străinătate", value=s.get("mama_plecata", False), key="f_m_plec")
                    f_tara_m = st.text_input("Țară unde este plecată mama:", value=s.get("tara_mama", ""), key="f_tara_m")
                with p3:
                    f_nume_t = st.text_input("Nume și Prenume Tată:", value=s.get("nume_tata", ""), key="f_nume_t")
                    f_tel_t = st.text_input("Telefon Tată:", value=s.get("telefon_tata", ""), key="f_tel_t")
                with p4:
                    f_t_plec = st.checkbox("Tată plecat în străinătate", value=s.get("tata_plecat", False), key="f_t_plec")
                    f_tara_t = st.text_input("Țară unde este plecat tatăl:", value=s.get("tara_tata", ""), key="f_tara_t")
                    
                st.markdown("#### 4. 🩺 Situații Speciale, Burse & CES (Bife)")
                b1, b2, b3, b4, b5 = st.columns(5)
                with b1: f_ces = st.checkbox("Elev cu CES", value=s.get("ces", False), key="f_ces")
                with b2: f_orfan = st.checkbox("Elev Orfan", value=s.get("orfan", False), key="f_orfan")
                with b3: f_plas = st.checkbox("Elev în Plasament", value=s.get("plasament", False), key="f_plas")
                with b4: f_b_med = st.checkbox("Bursă Socială Medicală", value=s.get("bursa_medicala", False), key="f_b_med")
                with b5: f_b_ven = st.checkbox("Bursă Socială (Venit)", value=s.get("bursa_venit", False), key="f_b_ven")
                
                submit_save = st.form_submit_button("💾 Salvează Date Elev", type="primary", use_container_width=True)
                
                if submit_save:
                    nume_c = f"{f_nume.strip()} {f_init.strip()} {f_prenume.strip()}".strip()
                    students_gest[sel_idx].update({
                        "matricol": f_matr.strip(),
                        "nume": f_nume.strip(),
                        "initiala": f_init.strip(),
                        "prenume": f_prenume.strip(),
                        "nume_complet": nume_c,
                        "cnp": f_cnp.strip(),
                        "telefon": f_tel_elev.strip(),
                        "localitate": f_loc.strip(),
                        "judet": f_jud.strip(),
                        "strada": f_str.strip(),
                        "numar_strada": f_nr_str.strip(),
                        "bloc": f_bloc.strip(),
                        "apartament": f_ap.strip(),
                        "nume_mama": f_nume_m.strip(),
                        "telefon_mama": f_tel_m.strip(),
                        "mama_plecata": f_m_plec,
                        "tara_mama": f_tara_m.strip(),
                        "nume_tata": f_nume_t.strip(),
                        "telefon_tata": f_tel_t.strip(),
                        "tata_plecat": f_t_plec,
                        "tara_tata": f_tara_t.strip(),
                        "nationalitate": f_nat.strip(),
                        "etnie": f_etnie.strip(),
                        "ces": f_ces,
                        "orfan": f_orfan,
                        "plasament": f_plas,
                        "bursa_medicala": f_b_med,
                        "bursa_venit": f_b_ven
                    })
                    if save_gestiune_data(students_gest):
                        st.success(f"✅ Datele pentru {nume_c} au fost salvate și actualizate în toate taburile!")
                        st.rerun()
                    else:
                        st.error("❌ Eroare la salvarea datelor pe disk.")

    elif op_gest == "➕ Adăugare Elev Nou în Clasă":
        st.markdown("#### ➕ Adăugare Elev Nou în Catalog")
        with st.form("add_new_student_form"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                n_matr = st.text_input("Număr Matricol Nou:", key="n_matr")
                n_cnp = st.text_input("Cod Numeric Personal (CNP):", key="n_cnp")
            with c2:
                n_nume = st.text_input("Nume Elev:", key="n_nume")
                n_tel = st.text_input("Telefon Elev:", key="n_tel")
            with c3:
                n_init = st.text_input("Inițiala Tatălui:", key="n_init")
                n_nat = st.text_input("Naționalitate:", value="Română", key="n_nat")
            with c4:
                n_prenume = st.text_input("Prenume Elev:", key="n_prenume")
                n_etnie = st.text_input("Etnie:", value="Română", key="n_etnie")
                
            submit_add = st.form_submit_button("➕ Adaugă Elev în Baza de Date", type="primary", use_container_width=True)
            
            if submit_add:
                if not n_nume.strip() or not n_prenume.strip() or not n_matr.strip():
                    st.warning("Completati cel putin Nume, Prenume si Numar Matricol!")
                else:
                    new_id = len(students_gest) + 1
                    new_rand = 12 + new_id
                    new_pin = str(random.randint(1000, 9999))
                    nume_c = f"{n_nume.strip()} {n_init.strip()} {n_prenume.strip()}".strip()
                    
                    new_stud = {
                        "id": new_id,
                        "rand_excel": new_rand,
                        "matricol": n_matr.strip(),
                        "pin": new_pin,
                        "nume": n_nume.strip(),
                        "initiala": n_init.strip(),
                        "prenume": n_prenume.strip(),
                        "nume_complet": nume_c,
                        "cnp": n_cnp.strip(),
                        "telefon": n_tel.strip(),
                        "localitate": "Turda",
                        "judet": "Cluj",
                        "strada": "", "numar_strada": "", "bloc": "", "apartament": "",
                        "nume_mama": "", "telefon_mama": "", "mama_plecata": False, "tara_mama": "",
                        "nume_tata": "", "telefon_tata": "", "tata_plecat": False, "tara_tata": "",
                        "nationalitate": n_nat.strip(),
                        "etnie": n_etnie.strip(),
                        "ces": False, "orfan": False, "plasament": False,
                        "bursa_medicala": False, "bursa_venit": False
                    }
                    students_gest.append(new_stud)
                    if save_gestiune_data(students_gest):
                        st.success(f"✅ Elevul {nume_c} a fost adăugat cu succes cu codul PIN {new_pin}!")
                        st.rerun()

    elif op_gest == "🗑️ Ștergere Elev din Clasă":
        st.markdown("#### 🗑️ Eliminare Elev din Baza de Date")
        if not students_gest:
            st.warning("Nu există elevi în baza de date.")
        else:
            del_idx = st.selectbox(
                "Alege Elevul de Șters:",
                range(len(students_gest)),
                format_func=lambda i: f"{students_gest[i]['id']}. {students_gest[i]['nume_complet']} (Matr. {students_gest[i]['matricol']})",
                key="sel_del_stud"
            )
            
            if st.button("🗑️ Confirmă Ștergerea Elevului Selectat", type="primary", use_container_width=True):
                removed = students_gest.pop(del_idx)
                for idx_idx, st_item in enumerate(students_gest, 1):
                    st_item['id'] = idx_idx
                    st_item['rand_excel'] = 12 + idx_idx
                    
                if save_gestiune_data(students_gest):
                    st.success(f"✅ Elevul {removed['nume_complet']} a fost eliminat din baza de date!")
                    st.rerun()

    st.divider()
    st.markdown("#### 📊 Export Registru Elevi & Raport Statistic Clasă")
    col_exp1, col_exp2 = st.columns(2)
    
    with col_exp1:
        try:
            ex_reg_bytes = generate_excel_registru_elevi(students_gest)
            st.download_button("📊 Descarcă Registru Date Elevi (.xlsx)", data=ex_reg_bytes, file_name="Registru_Date_Elevi_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare Registru Excel: {ex}")
            
    with col_exp2:
        try:
            ex_stat_bytes = generate_excel_statistica_clasa(students_gest)
            st.download_button("📊 Descarcă Statistica Clasa (.xlsx)", data=ex_stat_bytes, file_name="Statistica_Clasa_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        except Exception as ex:
            st.error(f"Eroare Statistică Excel: {ex}")

render_copyright_footer()
