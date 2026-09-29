
# --- MOCUL GESTIUNE ELEVI & EVIDENȚĂ (PERSISTENȚĂ ȘI SINCRONIZARE) ---
GESTIUNE_FILE = "gestiune_elevi.json"

DEFAULT_ELEVI = [
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

DEFAULT_PINS = ['2951', '6234', '9233', '9385', '2681', '4658', '7891', '9975', '9042', '8226', '4931', '1041', '2322', '2814', '5706', '2606', '8367', '1188', '9032', '6148', '4444', '7508', '5120', '6696', '6843', '7166', '9414', '2250', '6577', '2469', '9815', '5786']

def sync_gestiune_from_github():
    filename = GESTIUNE_FILE
    ts = int(datetime.datetime.now().timestamp())
    raw_url = f"https://raw.githubusercontent.com/profudeconta-sketch/catalog-online/main/{filename}?t={ts}"
    token = os.environ.get("GITHUB_TOKEN") or st.secrets.get("GITHUB_TOKEN", "")
    headers = {"User-Agent": "StreamlitApp", "Cache-Control": "no-cache"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(raw_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                content = resp.read()
                if len(content) > 10:
                    with open(filename, "wb") as f:
                        f.write(content)
                    return filename
    except Exception:
        pass
    return filename

def parse_student_name_parts(nume_complet):
    parts = nume_complet.strip().split()
    if not parts:
        return "", "", ""
    if len(parts) == 1:
        return parts[0], "", ""
    nume = parts[0]
    if len(parts) >= 3 and (parts[1].endswith('.') or len(parts[1]) <= 4):
        initiala = parts[1]
        prenume = " ".join(parts[2:])
    else:
        initiala = ""
        prenume = " ".join(parts[1:])
    return nume, initiala, prenume

def init_gestiune_data():
    data = []
    for idx, (e_id, full_name, r_ex, matr) in enumerate(DEFAULT_ELEVI):
        nume, init, prenume = parse_student_name_parts(full_name)
        pin = DEFAULT_PINS[idx] if idx < len(DEFAULT_PINS) else "1234"
        data.append({
            'id': e_id,
            'rand_excel': r_ex,
            'matricol': matr,
            'pin': pin,
            'nume': nume,
            'initiala': init,
            'prenume': prenume,
            'nume_complet': full_name,
            'cnp': '',
            'telefon': '',
            'localitate': 'Turda',
            'judet': 'Cluj',
            'strada': '',
            'numar_strada': '',
            'bloc': '',
            'apartament': '',
            'nume_mama': '',
            'telefon_mama': '',
            'mama_plecata': False,
            'tara_mama': '',
            'nume_tata': '',
            'telefon_tata': '',
            'tata_plecat': False,
            'tara_tata': '',
            'nationalitate': 'Română',
            'etnie': 'Română',
            'ces': False,
            'orfan': False,
            'plasament': False,
            'bursa_medicala': False,
            'bursa_venit': False
        })
    with open(GESTIUNE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data

def load_gestiune_data():
    sync_gestiune_from_github()
    if os.path.exists(GESTIUNE_FILE):
        try:
            with open(GESTIUNE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data and isinstance(data, list):
                    return data
        except Exception:
            pass
    return init_gestiune_data()

def save_gestiune_data(data):
    with open(GESTIUNE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    push_to_github(GESTIUNE_FILE)

def get_current_elevi_and_pins():
    data = load_gestiune_data()
    elevi_list = []
    pins_list = []
    for d in data:
        full = d.get('nume_complet', f"{d.get('nume','')} {d.get('initiala','')} {d.get('prenume','')}".strip())
        full = " ".join(full.split())
        elevi_list.append((d['id'], full, d.get('rand_excel', 12 + d['id']), d['matricol']))
        pins_list.append(str(d.get('pin', '1234')))
    return elevi_list, pins_list

def get_student_sex(st_dict):
    cnp = str(st_dict.get('cnp', '')).strip()
    if len(cnp) == 13 and cnp.isdigit():
        s = int(cnp[0])
        return 'Băiat' if s in [1, 3, 5, 7] else 'Fată'
    prenume = str(st_dict.get('prenume', '')).strip().upper()
    if not prenume:
        prenume = str(st_dict.get('nume_complet', '')).strip().upper()
    words = prenume.split()
    first_p = words[-1] if words else ''
    if first_p.endswith('A') and first_p not in ['LUCA', 'HORA']:
        return 'Fată'
    return 'Băiat'

def get_student_age(st_dict):
    cnp = str(st_dict.get('cnp', '')).strip()
    if len(cnp) == 13 and cnp.isdigit():
        s = int(cnp[0])
        yy = int(cnp[1:3])
        year = (1900 + yy) if s in [1, 2] else (2000 + yy if s in [5, 6] else 2000 + yy)
        return 2026 - year
    return 15

def generate_excel_registru_elevi(data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registru Elevi"
    ws.views.sheetView[0].showGridLines = True
    
    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1A365D")
    sub_font = Font(name="Calibri", size=10, italic=True, color="4A5568")
    data_font = Font(name="Calibri", size=10)
    
    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    
    ws.append(["COLEGIUL 'EMIL NEGRUȚIU' TURDA — CLASA a IX-a TH"])
    ws.append(["REGISTRUL GENERAL DE EVIDENȚĂ ȘI GESTIUNE A ELEVILOR"])
    ws.append([])
    
    ws.cell(row=1, column=1).font = title_font
    ws.cell(row=2, column=1).font = sub_font
    
    headers = [
        "Nr.", "Nr. Matricol", "PIN Părinte", "Nume de Familie", "Inițială", "Prenume Elev",
        "Nume Complet", "CNP", "Telefon Elev", "Localitate", "Județ", "Stradă",
        "Nr. Stradă", "Bloc", "Ap.", "Nume Mamă", "Tel. Mamă", "Mamă Plecată?", "Țară Mamă",
        "Nume Tată", "Tel. Tată", "Tată Plecat?", "Țară Tată", "Naționalitate", "Etnie",
        "CES", "Orfan", "Plasament", "Bursă Medicală", "Bursă Venit"
    ]
    
    ws.append(headers)
    header_row = 4
    for col_num, h in enumerate(headers, 1):
        cell = ws.cell(row=header_row, column=col_num)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = thin_border
        
    ws.row_dimensions[header_row].height = 28
    
    for idx, d in enumerate(data, 1):
        row = [
            idx,
            d.get('matricol', ''),
            d.get('pin', ''),
            d.get('nume', ''),
            d.get('initiala', ''),
            d.get('prenume', ''),
            d.get('nume_complet', ''),
            f"'{d.get('cnp', '')}",
            d.get('telefon', ''),
            d.get('localitate', ''),
            d.get('judet', ''),
            d.get('strada', ''),
            d.get('numar_strada', ''),
            d.get('bloc', ''),
            d.get('apartament', ''),
            d.get('nume_mama', ''),
            d.get('telefon_mama', ''),
            "DA" if d.get('mama_plecata') else "NU",
            d.get('tara_mama', ''),
            d.get('nume_tata', ''),
            d.get('telefon_tata', ''),
            "DA" if d.get('tata_plecat') else "NU",
            d.get('tara_tata', ''),
            d.get('nationalitate', 'Română'),
            d.get('etnie', 'Română'),
            "DA" if d.get('ces') else "NU",
            "DA" if d.get('orfan') else "NU",
            "DA" if d.get('plasament') else "NU",
            "DA" if d.get('bursa_medicala') else "NU",
            "DA" if d.get('bursa_venit') else "NU"
        ]
        ws.append(row)
        r_idx = header_row + idx
        for col_num in range(1, len(headers) + 1):
            cell = ws.cell(row=r_idx, column=col_num)
            cell.font = data_font
            cell.border = thin_border
            if col_num in [1, 2, 3, 8, 18, 22, 26, 27, 28, 29, 30]:
                cell.alignment = Alignment(horizontal="center", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
                
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()

def generate_excel_statistica_clasa(data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Statistică Clasă"
    ws.views.sheetView[0].showGridLines = True
    
    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    section_fill = PatternFill(start_color="EDF2F7", end_color="EDF2F7", fill_type="solid")
    
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    title_font = Font(name="Calibri", size=14, bold=True, color="1A365D")
    sec_title_font = Font(name="Calibri", size=11, bold=True, color="1A365D")
    data_font = Font(name="Calibri", size=10)
    bold_font = Font(name="Calibri", size=10, bold=True)
    
    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    
    ws.append(["COLEGIUL 'EMIL NEGRUȚIU' TURDA — CLASA a IX-a TH"])
    ws.append(["RAPORT STATISTIC SINTETIC ȘI INDICATORI CLASĂ"])
    ws.append([])
    
    ws.cell(row=1, column=1).font = title_font
    ws.cell(row=2, column=1).font = Font(name="Calibri", size=10, italic=True, color="4A5568")
    
    tot_elevi = len(data)
    boys = [s for s in data if get_student_sex(s) == 'Băiat']
    girls = [s for s in data if get_student_sex(s) == 'Fată']
    nr_b = len(boys)
    nr_f = len(girls)
    
    def add_section_header(title):
        row_idx = ws.max_row + 1
        ws.cell(row=row_idx, column=1, value=title).font = sec_title_font
        ws.cell(row=row_idx, column=1).fill = section_fill
        ws.row_dimensions[row_idx].height = 24
        
    def add_table_headers(headers):
        r_idx = ws.max_row + 1
        for c_idx, h in enumerate(headers, 1):
            cell = ws.cell(row=r_idx, column=c_idx, value=h)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            cell.border = thin_border
        ws.row_dimensions[r_idx].height = 24

    # 1. Repartizarea pe sex
    add_section_header("1. REPARTIZAREA ELEVILOR PE SEX")
    add_table_headers(["Categorie Sex", "Număr Elevi", "Pondere (%)"])
    ws.append(["Băieți", nr_b, f"{(nr_b/tot_elevi*100):.1f}%" if tot_elevi else "0%"])
    ws.append(["Fete", nr_f, f"{(nr_f/tot_elevi*100):.1f}%" if tot_elevi else "0%"])
    ws.append(["TOTAL CLASĂ", tot_elevi, "100.0%"])
    for r in range(ws.max_row - 2, ws.max_row + 1):
        for c in range(1, 4):
            cell = ws.cell(row=r, column=c)
            cell.border = thin_border
            cell.font = bold_font if r == ws.max_row else data_font
            cell.alignment = Alignment(horizontal="center" if c > 1 else "left", vertical="center")
    ws.append([])

    # 2. Gruparea pe vârstă și sex
    add_section_header("2. GRUPAREA ELEVILOR PE VÂRSTĂ ȘI SEX")
    add_table_headers(["Vârstă (Ani)", "Total Elevi", "Fete", "Băieți"])
    ages_dict = {}
    for s in data:
        a = get_student_age(s)
        sx = get_student_sex(s)
        if a not in ages_dict: ages_dict[a] = {'f': 0, 'b': 0, 'tot': 0}
        ages_dict[a]['tot'] += 1
        if sx == 'Fată': ages_dict[a]['f'] += 1
        else: ages_dict[a]['b'] += 1
        
    for age_k in sorted(ages_dict.keys()):
        info = ages_dict[age_k]
        ws.append([f"{age_k} ani", info['tot'], info['f'], info['b']])
        r = ws.max_row
        for c in range(1, 5):
            cell = ws.cell(row=r, column=c)
            cell.border = thin_border
            cell.font = data_font
            cell.alignment = Alignment(horizontal="center" if c > 1 else "left", vertical="center")
    ws.append([])

    # 3. Etnie & Naționalitate
    add_section_header("3. ETNIE ȘI NAȚIONALITATE")
    add_table_headers(["Etnie / Naționalitate", "Total Elevi", "Fete", "Băieți"])
    etn_dict = {}
    for s in data:
        e = str(s.get('etnie', 'Română')).strip() or 'Română'
        sx = get_student_sex(s)
        if e not in etn_dict: etn_dict[e] = {'f': 0, 'b': 0, 'tot': 0}
        etn_dict[e]['tot'] += 1
        if sx == 'Fată': etn_dict[e]['f'] += 1
        else: etn_dict[e]['b'] += 1
        
    for etn_k, info in etn_dict.items():
        ws.append([etn_k, info['tot'], info['f'], info['b']])
        r = ws.max_row
        for c in range(1, 5):
            cell = ws.cell(row=r, column=c)
            cell.border = thin_border
            cell.font = data_font
            cell.alignment = Alignment(horizontal="center" if c > 1 else "left", vertical="center")
    ws.append([])

    # 4. Burse Sociale & CES
    add_section_header("4. ELEVI CU BURSE SOCIALE ȘI CES")
    add_table_headers(["Tip Sprijin / Bursă / CES", "Total Elevi", "Fete", "Băieți"])
    
    b_med = [s for s in data if s.get('bursa_medicala')]
    b_ven = [s for s in data if s.get('bursa_venit')]
    ces_el = [s for s in data if s.get('ces')]
    
    b_med_f = sum(1 for s in b_med if get_student_sex(s) == 'Fată')
    b_med_b = sum(1 for s in b_med if get_student_sex(s) == 'Băiat')
    
    b_ven_f = sum(1 for s in b_ven if get_student_sex(s) == 'Fată')
    b_ven_b = sum(1 for s in b_ven if get_student_sex(s) == 'Băiat')
    
    ces_f = sum(1 for s in ces_el if get_student_sex(s) == 'Fată')
    ces_b = sum(1 for s in ces_el if get_student_sex(s) == 'Băiat')
    
    ws.append(["Bursă Socială Medicală", len(b_med), b_med_f, b_med_b])
    ws.append(["Bursă Socială pe Bază de Venit", len(b_ven), b_ven_f, b_ven_b])
    ws.append(["Cerințe Educaționale Speciale (CES)", len(ces_el), ces_f, ces_b])
    
    for r in range(ws.max_row - 2, ws.max_row + 1):
        for c in range(1, 5):
            cell = ws.cell(row=r, column=c)
            cell.border = thin_border
            cell.font = data_font
            cell.alignment = Alignment(horizontal="center" if c > 1 else "left", vertical="center")
    ws.append([])

    # 5. Situații Sociale Speciale (Orfani & Plasament)
    add_section_header("5. SITUAȚII SOCIALE SPECIALE (ORFANI ȘI PLASAMENT)")
    add_table_headers(["Categorie Socială", "Total Elevi", "Fete", "Băieți"])
    
    orf = [s for s in data if s.get('orfan')]
    plas = [s for s in data if s.get('plasament')]
    
    orf_f = sum(1 for s in orf if get_student_sex(s) == 'Fată')
    orf_b = sum(1 for s in orf if get_student_sex(s) == 'Băiat')
    
    plas_f = sum(1 for s in plas if get_student_sex(s) == 'Fată')
    plas_b = sum(1 for s in plas if get_student_sex(s) == 'Băiat')
    
    ws.append(["Elevi Orfani", len(orf), orf_f, orf_b])
    ws.append(["Elevi aflați în Plasament", len(plas), plas_f, plas_b])
    
    for r in range(ws.max_row - 1, ws.max_row + 1):
        for c in range(1, 5):
            cell = ws.cell(row=r, column=c)
            cell.border = thin_border
            cell.font = data_font
            cell.alignment = Alignment(horizontal="center" if c > 1 else "left", vertical="center")
    ws.append([])

    # 6. Părinți plecați în străinătate
    add_section_header("6. ELEVI CU PĂRINȚI PLECAȚI ÎN STRĂINĂTATE")
    add_table_headers(["Țară Destinație", "Mamă Plecată", "Tată Plecat", "Amândoi Plecați", "Total Elevi", "Fete", "Băieți"])
    
    countries_dict = {}
    for s in data:
        m_p = bool(s.get('mama_plecata'))
        t_p = bool(s.get('tata_plecat'))
        c_m = str(s.get('tara_mama', '')).strip() if m_p else ''
        c_t = str(s.get('tara_tata', '')).strip() if t_p else ''
        
        all_c = set([c for c in [c_m, c_t] if c])
        if not all_c: continue
        
        sx = get_student_sex(s)
        for c_item in all_c:
            if c_item not in countries_dict:
                countries_dict[c_item] = {'m': 0, 't': 0, 'both': 0, 'tot': 0, 'f': 0, 'b': 0}
            if c_m == c_item and c_t == c_item:
                countries_dict[c_item]['both'] += 1
            elif c_m == c_item:
                countries_dict[c_item]['m'] += 1
            elif c_t == c_item:
                countries_dict[c_item]['t'] += 1
            countries_dict[c_item]['tot'] += 1
            if sx == 'Fată': countries_dict[c_item]['f'] += 1
            else: countries_dict[c_item]['b'] += 1
            
    if countries_dict:
        for c_k, info in countries_dict.items():
            ws.append([c_k, info['m'], info['t'], info['both'], info['tot'], info['f'], info['b']])
            r = ws.max_row
            for c in range(1, 8):
                cell = ws.cell(row=r, column=c)
                cell.border = thin_border
                cell.font = data_font
                cell.alignment = Alignment(horizontal="center" if c > 1 else "left", vertical="center")
    else:
        ws.append(["Niciun părinte plecat înregistrat", 0, 0, 0, 0, 0, 0])
        r = ws.max_row
        for c in range(1, 8):
            cell = ws.cell(row=r, column=c)
            cell.border = thin_border
            cell.font = data_font
            cell.alignment = Alignment(horizontal="center" if c > 1 else "left", vertical="center")
            
    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 14)
        
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


ELEVI, PINS = get_current_elevi_and_pins()import datetime
import os
import openpyxl
import streamlit as st
import urllib.request
import urllib.parse
import json
import base64
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

def clean_pdf_text(text):
    if PDF_FONT == "Helvetica":
        rep = {'ă':'a', 'Ă':'A', 'â':'a', 'Â':'A', 'î':'i', 'Î':'I', 'ș':'s', 'Ș':'S', 'ț':'t', 'Ț':'T'}
        for k, v in rep.items():
            text = text.replace(k, v)
    return text

def render_copyright_footer():
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #4A5568; font-size: 0.83rem; line-height: 1.6; padding: 16px 12px; background-color: #F7FAFC; border-radius: 8px; border: 1px solid #E2E8F0; margin-top: 25px; margin-bottom: 10px;">
            <div style="font-size: 0.95rem; font-weight: bold; color: #1A365D; margin-bottom: 4px;">
                © Software Creat și Deținut de Prof. Ec. Gherman Octavian-Theodor
            </div>
            <div>
                Acest program este protejat de legea privind drepturile de autor (Legea nr. 8/1996) și legislația internațională aplicabilă.<br/>
                Orice descărcare, multiplicare, distribuire sau utilizare neautorizată se pedepsește conform legii.<br/>
                <span style="color: #C53030; font-weight: bold;">🚫 ESTE STRICT INTERZISĂ COMERCIALIZAREA ACESTUI PRODUS!</span><br/>
                Acest produs se utilizează în mod gratuit exclusiv de către persoanele cărora autorul le conferă în mod explicit acest drept.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def render_sidebar_copyright():
    st.sidebar.divider()
    st.sidebar.markdown(
        """
        <div style='font-size: 0.78rem; color: #718096; line-height: 1.4;'>
            <b>© Prof. Ec. Gherman Octavian-Theodor</b><br/>
            Drepturi de autor rezervate.<br/>
            <span style='color: #E53E3E; font-weight: bold;'>Comercializarea interzisă.</span><br/>
            Utilizare gratuită doar cu acordul autorului.
        </div>
        """,
        unsafe_allow_html=True
    )

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

# Lista celor 32 de elevi (ID, Nume, RM/PG, Nr. Matr., PIN)
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

# --- RECALCULARE ȘI SCRIERE ÎN EXCEL (PENTRU PERSISTENȚĂ STRUCTURATĂ) ---
def update_excel_computed_values(file_path):
    if not os.path.exists(file_path):
        return
    try:
        wb = openpyxl.load_workbook(file_path)
        ws_cg = wb['Cultură Generală']
        ws_th = wb['Module Tehnologice']
        ws_abs = wb['Absențe & Purtare']
        ws_cent = wb['Centralizator Medii']
        
        student_stats = []
        
        for idx, e in enumerate(ELEVI):
            s_row = 9 + idx
            cg_avgs = []
            cg_tot_nem = 0
            cg_tot_mot = 0
            
            for _, col in DISCIPLINE_CG:
                notes = []
                for k in range(10):
                    v = ws_cg.cell(row=s_row, column=col + k*2).value
                    if v is not None and str(v).strip() != '':
                        try: notes.append(float(v))
                        except Exception: pass
                if notes:
                    s_avg = round(sum(notes)/len(notes), 2)
                    ws_cg.cell(row=s_row, column=col+20).value = s_avg
                    cg_avgs.append(s_avg)
                else:
                    ws_cg.cell(row=s_row, column=col+20).value = None
                    
                for k in range(30):
                    av = ws_cg.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != '':
                        s = str(av).strip()
                        if s.endswith('m') or s.endswith('M'): cg_tot_mot += 1
                        else: cg_tot_nem += 1
                        
            mcg = round(sum(cg_avgs)/len(cg_avgs), 2) if cg_avgs else None
            ws_cg.cell(row=s_row, column=5).value = mcg
            ws_cg.cell(row=s_row, column=6).value = cg_tot_nem if cg_tot_nem > 0 else None
            ws_cg.cell(row=s_row, column=7).value = cg_tot_mot if cg_tot_mot > 0 else None

            th_avgs = []
            th_tot_nem = 0
            th_tot_mot = 0
            for _, col in MODULE_TH:
                notes = []
                for k in range(10):
                    v = ws_th.cell(row=s_row, column=col + k*2).value
                    if v is not None and str(v).strip() != '':
                        try: notes.append(float(v))
                        except Exception: pass
                if notes:
                    s_avg = round(sum(notes)/len(notes), 2)
                    ws_th.cell(row=s_row, column=col+20).value = s_avg
                    th_avgs.append(s_avg)
                else:
                    ws_th.cell(row=s_row, column=col+20).value = None
                    
                for k in range(30):
                    av = ws_th.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != '':
                        s = str(av).strip()
                        if s.endswith('m') or s.endswith('M'): th_tot_mot += 1
                        else: th_tot_nem += 1

            mth = round(sum(th_avgs)/len(th_avgs), 2) if th_avgs else None
            ws_th.cell(row=s_row, column=5).value = mth
            ws_th.cell(row=s_row, column=6).value = th_tot_nem if th_tot_nem > 0 else None
            ws_th.cell(row=s_row, column=7).value = th_tot_mot if th_tot_mot > 0 else None

            tot_nem = cg_tot_nem + th_tot_nem
            tot_mot = cg_tot_mot + th_tot_mot
            tot_abs = tot_nem + tot_mot
            purtare = max(1, 10 - int(tot_nem / 20))

            ws_abs.cell(row=s_row, column=5).value = tot_nem if tot_nem > 0 else None
            ws_abs.cell(row=s_row, column=6).value = tot_mot if tot_mot > 0 else None
            ws_abs.cell(row=s_row, column=7).value = tot_abs if tot_abs > 0 else None
            ws_abs.cell(row=s_row, column=8).value = purtare

            if mcg is not None and mth is not None: mg = round((mcg + mth)/2.0, 2)
            elif mcg is not None: mg = mcg
            elif mth is not None: mg = mth
            else: mg = None

            ws_cent.cell(row=s_row, column=5).value = mcg
            ws_cent.cell(row=s_row, column=6).value = mth
            ws_cent.cell(row=s_row, column=7).value = mg
            ws_cent.cell(row=s_row, column=8).value = purtare
            ws_cent.cell(row=s_row, column=10).value = tot_abs if tot_abs > 0 else None

            statut = '-'
            if mcg is not None or mth is not None:
                if (mcg is None or mcg >= 5) and (mth is None or mth >= 5) and purtare >= 5:
                    statut = 'Promovat'
                else:
                    statut = 'Corigent / Repetent'
            ws_cent.cell(row=s_row, column=9).value = statut

            student_stats.append({
                'idx': idx,
                'row': s_row,
                'mg': mg,
                'tot_abs': tot_abs,
                'statut': statut,
                'purtare': purtare
            })

        valid_mgs = sorted([s['mg'] for s in student_stats if s['mg'] is not None], reverse=True)
        for s in student_stats:
            if s['mg'] is not None:
                rang = valid_mgs.index(s['mg']) + 1
                ws_cent.cell(row=s['row'], column=11).value = rang
                if rang == 1: premiu = 'Premiul I'
                elif rang == 2: premiu = 'Premiul II'
                elif rang == 3: premiu = 'Premiul III'
                elif rang <= 7: premiu = 'Mențiune'
                else: premiu = 'Membru'
                ws_cent.cell(row=s['row'], column=12).value = premiu
            else:
                ws_cent.cell(row=s['row'], column=11).value = None
                ws_cent.cell(row=s['row'], column=12).value = None

        wb.save(file_path)
        wb.close()
    except Exception:
        pass

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

    except Exception:
        pass

    return students_data, subject_totals

def find_excel_file():
    candidates = [
        "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "CATALOG/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "/workspace/artifacts/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
        "/workspace/out/catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
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
        with open(selected_file, "rb") as f_ex:
            st.download_button(
                "📥 Descarcă Catalog Excel (.xlsx)",
                data=f_ex.read(),
                file_name="catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
    st.divider()
    if st.button("🚪 Deconectare (Logout)", use_container_width=True):
        st.session_state["authenticated"] = False
        st.rerun()
        
    render_sidebar_copyright()

if not os.path.exists(selected_file):
    st.warning(f"⚠️ Fișierul catalog '{selected_file}' nu a fost găsit în directorul curent.")

tab1, tab2, tab3, tab_del, tab4, tab5, tab6, tab_gest = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "🗑️ Ștergere Notă / Absență",
    "📊 Fișă Elev",
    "📈 Centralizator Clasă",
    "📋 Raport Diriginte",
    "👥 Gestiune Elevi"
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
    
    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA"), title_style))
    story.append(Paragraph(clean_pdf_text("FIȘĂ INDIVIDUALĂ DE EVALUARE ȘI FRECVENȚĂ ȘCOLARĂ"), title_style))
    story.append(Paragraph(clean_pdf_text("Clasa a IX-a TH — Turism și Alimentație | An școlar 2026-2027"), subtitle_style))
    story.append(Spacer(1, 10))
    
    meta_data = [
        [Paragraph(clean_pdf_text(f"<b>Nume și Prenume:</b> {e_info[1]}"), cell_style), Paragraph(clean_pdf_text(f"<b>Nr. Matricol:</b> {e_info[3]}"), cell_style), Paragraph(clean_pdf_text(f"<b>RM/PG:</b> {e_info[2]}"), cell_style)]
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
            story.append(Paragraph(clean_pdf_text(cat_title), heading_style))
            ws = wb[sheet_n]
            
            table_data = [[
                Paragraph(clean_pdf_text("<b>Disciplină / Modul</b>"), cell_bold),
                Paragraph(clean_pdf_text("<b>Note & Date</b>"), cell_bold),
                Paragraph(clean_pdf_text("<b>Medie</b>"), cell_bold),
                Paragraph(clean_pdf_text("<b>Absențe Total (Nem / Mot)</b>"), cell_bold)
            ]]
            
            for s_name, start_col in sub_list:
                notes_list = []
                for k in range(10):
                    n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                    d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                    if n_val is not None and str(n_val).strip() != "":
                        d_str = f" ({d_val})" if d_val else ""
                        notes_list.append(f"{n_val}{d_str}")
                        
                abs_list = []
                sub_nem = 0
                sub_mot = 0
                for k in range(30):
                    a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                    if a_val is not None and str(a_val).strip() != "":
                        s_a = str(a_val).strip()
                        abs_list.append(s_a)
                        if s_a.endswith('m') or s_a.endswith('M'): sub_mot += 1
                        else: sub_nem += 1
                        
                sub_tot = sub_nem + sub_mot
                abs_summary = f"{sub_tot} tot ({sub_nem} nem. / {sub_mot} mot.)" if sub_tot > 0 else "-"
                if abs_list:
                    abs_summary += f" — {', '.join(abs_list)}"
                    
                m_val = ws.cell(row=s_row, column=start_col + 20).value
                m_str = safe_float_str(m_val)
                
                table_data.append([
                    Paragraph(clean_pdf_text(s_name), cell_style),
                    Paragraph(clean_pdf_text(", ".join(notes_list) if notes_list else "-"), cell_style),
                    Paragraph(clean_pdf_text(m_str), cell_bold),
                    Paragraph(clean_pdf_text(abs_summary), cell_style)
                ])
                
            t_sub = Table(table_data, colWidths=[150, 180, 45, 145])
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
    story.append(Paragraph(clean_pdf_text("<b>Profesor Diriginte:</b> ___________________________   |   <b>Semnătură:</b> ___________"), cell_style))

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

    story.append(Paragraph(clean_pdf_text("COLEGIUL 'EMIL NEGRUȚIU' TURDA — CENTRALIZATOR GENERAL CLASĂ (IX TH)"), title_style))
    story.append(Spacer(1, 8))
    
    table_data = [[
        Paragraph(clean_pdf_text("<b>Nr.</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Nume și Prenume</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Matr.</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Med. CG</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Med. TH</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Med. Gen.</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Purtare</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Statut</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Tot. Abs.</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Rang</b>"), cell_bold),
        Paragraph(clean_pdf_text("<b>Premiu</b>"), cell_bold)
    ]]
    
    stats, _ = calculate_all_class_stats(file_path)
    for s in stats:
        table_data.append([
            Paragraph(clean_pdf_text(str(s['nr'])), cell_style),
            Paragraph(clean_pdf_text(s['nume']), cell_style),
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

    t_cent = Table(table_data, colWidths=[25, 200, 50, 50, 50, 55, 45, 80, 50, 40, 70])
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
            Paragraph(clean_pdf_text(f"<b>{e[4]}</b>"), cell_bold)
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
            st.markdown(f"### 👤 {e_info[1]} (Matricol {e_info[3]}) | Cod PIN Părinți: `{e_info[4]}`")
            
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
            st.subheader("📊 Centralizator Absențe pe Discipline și Module")
            st.caption("Generează raportul sintetic al absențelor defalcat pe fiecare disciplină în parte cu totalurile la nivel de clasă.")
            
            show_abs_cent = st.checkbox("Afișează Centralizator Absențe pe Discipline", value=True, key="chk_show_abs_cent")
            
            if show_abs_cent:
                abs_by_sub_rows = []
                tot_class_nem = 0
                tot_class_mot = 0
                
                for cat_name, sub_list in [("Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", MODULE_TH)]:
                    for s_name, _ in sub_list:
                        s_info = sub_totals.get((cat_name, s_name), {'nem': 0, 'mot': 0, 'tot': 0})
                        tot_class_nem += s_info['nem']
                        tot_class_mot += s_info['mot']
                        abs_by_sub_rows.append({
                            "Categorie": cat_name,
                            "Disciplină / Modul": s_name,
                            "Absențe Nemotivate Clasă": s_info['nem'],
                            "Absențe Motivate Clasă": s_info['mot'],
                            "Total Absențe Clasă": s_info['tot']
                        })
                
                tot_class_all = tot_class_nem + tot_class_mot
                abs_by_sub_rows.append({
                    "Categorie": "TOTAL CLASĂ",
                    "Disciplină / Modul": "TOTAL GENERAL CLASĂ",
                    "Absențe Nemotivate Clasă": tot_class_nem,
                    "Absențe Motivate Clasă": tot_class_mot,
                    "Total Absențe Clasă": tot_class_all
                })
                
                st.dataframe(abs_by_sub_rows, use_container_width=True, hide_index=True)
            
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
                    "COD PIN ACCES PĂRINTE": e[4]
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


# --- TAB 8: GESTIUNE ELEVI (EVIDENȚĂ, DATE PERSONALE & STATISTICĂ) ---
with tab_gest:
    st.subheader("👥 Gestiune Elevi — Evidență, Date Personale & Statistica Clasă")
    st.caption("Gestionați lista elevilor din clasă, datele de identificare, adresa, părinții, plecările în străinătate, bursele și situațiile speciale (CES, orfani, plasament).")
    
    gest_data = load_gestiune_data()
    
    op_gest = st.radio(
        "Selectează Operațiunea:",
        ["✏️ Modificare Date Elev Existent", "➕ Adăugare Elev Nou în Clasă", "🗑️ Ștergere Elev din Clasă"],
        horizontal=True,
        key="op_gest_radio_btn"
    )
    
    st.divider()
    
    if op_gest == "✏️ Modificare Date Elev Existent":
        if not gest_data:
            st.info("ℹ️ Nu există elevi înregistrați în baza de date.")
        else:
            g_sel_idx = st.selectbox(
                "Selectează Elevul pentru Modificare Date:",
                range(len(gest_data)),
                format_func=lambda i: f"{gest_data[i]['id']}. {gest_data[i].get('nume_complet','')} (Matricol {gest_data[i]['matricol']})",
                key="sel_student_edit"
            )
            st_curr = gest_data[g_sel_idx]
            
            st.markdown(f"#### 📝 Editare Date pentru: **{st_curr.get('nume_complet','')}**")
            
            st.markdown("##### 1. 🆔 Date Identificare & Școlar")
            c1, c2 = st.columns(2)
            with c1:
                g_matr = st.text_input("Număr Matricol:", value=st_curr.get("matricol", ""), key=f"gm_{g_sel_idx}")
                g_cnp = st.text_input("Cod Numeric Personal (CNP - 13 cifre):", value=st_curr.get("cnp", ""), key=f"gc_{g_sel_idx}")
                g_nume = st.text_input("Nume de Familie:", value=st_curr.get("nume", ""), key=f"gn_{g_sel_idx}")
                g_init = st.text_input("Inițiala Tatălui (ex: V. sau I.M.):", value=st_curr.get("initiala", ""), key=f"gi_{g_sel_idx}")
            with c2:
                g_prenume = st.text_input("Prenume Elev:", value=st_curr.get("prenume", ""), key=f"gp_{g_sel_idx}")
                g_tel = st.text_input("Număr Telefon Elev:", value=st_curr.get("telefon", ""), key=f"gt_{g_sel_idx}")
                g_nat = st.text_input("Naționalitate:", value=st_curr.get("nationalitate", "Română"), key=f"gnat_{g_sel_idx}")
                g_etnie = st.text_input("Etnie:", value=st_curr.get("etnie", "Română"), key=f"get_{g_sel_idx}")
                
            st.markdown("##### 2. 🏠 Adresă Domiciliu")
            ca1, ca2 = st.columns(2)
            with ca1:
                g_loc = st.text_input("Localitate:", value=st_curr.get("localitate", "Turda"), key=f"gloc_{g_sel_idx}")
                g_jud = st.text_input("Județ:", value=st_curr.get("judet", "Cluj"), key=f"gjud_{g_sel_idx}")
                g_strada = st.text_input("Stradă:", value=st_curr.get("strada", ""), key=f"gstr_{g_sel_idx}")
            with ca2:
                g_nr_strada = st.text_input("Număr Stradă:", value=st_curr.get("numar_strada", ""), key=f"gnr_{g_sel_idx}")
                g_bloc = st.text_input("Bloc:", value=st_curr.get("bloc", ""), key=f"gbl_{g_sel_idx}")
                g_ap = st.text_input("Apartament:", value=st_curr.get("apartament", ""), key=f"gap_{g_sel_idx}")
                
            st.markdown("##### 3. 👨‍👩‍👧 Informații Părinți & Plecări în Străinătate")
            cp1, cp2 = st.columns(2)
            with cp1:
                g_nmama = st.text_input("Nume și Prenume Mamă:", value=st_curr.get("nume_mama", ""), key=f"gnm_{g_sel_idx}")
                g_tmama = st.text_input("Telefon Mamă:", value=st_curr.get("telefon_mama", ""), key=f"gtm_{g_sel_idx}")
                g_mplecata = st.checkbox("Mamă plecată în străinătate", value=bool(st_curr.get("mama_plecata")), key=f"gmp_{g_sel_idx}")
                g_taramama = st.text_input("Țara unde este plecată mama:", value=st_curr.get("tara_mama", ""), key=f"gtaram_{g_sel_idx}") if g_mplecata else ""
            with cp2:
                g_ntata = st.text_input("Nume și Prenume Tată:", value=st_curr.get("nume_tata", ""), key=f"gnt_{g_sel_idx}")
                g_ttata = st.text_input("Telefon Tată:", value=st_curr.get("telefon_tata", ""), key=f"gtt_{g_sel_idx}")
                g_tplecat = st.checkbox("Tată plecat în străinătate", value=bool(st_curr.get("tata_plecat")), key=f"gtp_{g_sel_idx}")
                g_taratata = st.text_input("Țara unde este plecat tatăl:", value=st_curr.get("tara_tata", ""), key=f"gtarat_{g_sel_idx}") if g_tplecat else ""
                
            st.markdown("##### 4. 🩺 Situații Speciale, Burse & CES (Bife)")
            cs1, cs2 = st.columns(2)
            with cs1:
                g_ces = st.checkbox("Elev cu Cerințe Educaționale Speciale (CES)", value=bool(st_curr.get("ces")), key=f"gces_{g_sel_idx}")
                g_orfan = st.checkbox("Elev Orfan", value=bool(st_curr.get("orfan")), key=f"gorf_{g_sel_idx}")
                g_plasament = st.checkbox("Elev aflat în Plasament", value=bool(st_curr.get("plasament")), key=f"gplas_{g_sel_idx}")
            with cs2:
                g_bursa_med = st.checkbox("Elev cu Bursă Socială Medicală", value=bool(st_curr.get("bursa_medicala")), key=f"gbmed_{g_sel_idx}")
                g_bursa_ven = st.checkbox("Elev cu Bursă Socială pe Bază de Venit", value=bool(st_curr.get("bursa_venit")), key=f"gbven_{g_sel_idx}")
                
            st.write("")
            if st.button("💾 Salvează Date Elev", type="primary", use_container_width=True, key=f"btn_save_edit_{g_sel_idx}"):
                gest_data[g_sel_idx]['matricol'] = g_matr.strip()
                gest_data[g_sel_idx]['cnp'] = g_cnp.strip()
                gest_data[g_sel_idx]['nume'] = g_nume.strip().upper()
                gest_data[g_sel_idx]['initiala'] = g_init.strip().upper()
                gest_data[g_sel_idx]['prenume'] = g_prenume.strip().upper()
                gest_data[g_sel_idx]['nume_complet'] = f"{g_nume.strip().upper()} {g_init.strip().upper()} {g_prenume.strip().upper()}".replace("  ", " ").strip()
                gest_data[g_sel_idx]['telefon'] = g_tel.strip()
                gest_data[g_sel_idx]['nationalitate'] = g_nat.strip()
                gest_data[g_sel_idx]['etnie'] = g_etnie.strip()
                
                gest_data[g_sel_idx]['localitate'] = g_loc.strip()
                gest_data[g_sel_idx]['judet'] = g_jud.strip()
                gest_data[g_sel_idx]['strada'] = g_strada.strip()
                gest_data[g_sel_idx]['numar_strada'] = g_nr_strada.strip()
                gest_data[g_sel_idx]['bloc'] = g_bloc.strip()
                gest_data[g_sel_idx]['apartament'] = g_ap.strip()
                
                gest_data[g_sel_idx]['nume_mama'] = g_nmama.strip()
                gest_data[g_sel_idx]['telefon_mama'] = g_tmama.strip()
                gest_data[g_sel_idx]['mama_plecata'] = g_mplecata
                gest_data[g_sel_idx]['tara_mama'] = g_taramama.strip() if g_mplecata else ""
                
                gest_data[g_sel_idx]['nume_tata'] = g_ntata.strip()
                gest_data[g_sel_idx]['telefon_tata'] = g_ttata.strip()
                gest_data[g_sel_idx]['tata_plecat'] = g_tplecat
                gest_data[g_sel_idx]['tara_tata'] = g_taratata.strip() if g_tplecat else ""
                
                gest_data[g_sel_idx]['ces'] = g_ces
                gest_data[g_sel_idx]['orfan'] = g_orfan
                gest_data[g_sel_idx]['plasament'] = g_plasament
                gest_data[g_sel_idx]['bursa_medicala'] = g_bursa_med
                gest_data[g_sel_idx]['bursa_venit'] = g_bursa_ven
                
                save_gestiune_data(gest_data)
                st.success(f"✅ Datele pentru {gest_data[g_sel_idx]['nume_complet']} au fost salvate și actualizate în tot catalogul!")
                st.rerun()

    elif op_gest == "➕ Adăugare Elev Nou în Clasă":
        st.markdown("#### ➕ Formular Adăugare Elev Nou")
        
        new_id = (max([d['id'] for d in gest_data]) + 1) if gest_data else 1
        new_r_ex = 12 + new_id
        
        st.info(f"💡 Noul elev va primi automat ID-ul {new_id} și rândul {new_r_ex} în catalog.")
        
        st.markdown("##### 1. 🆔 Date Identificare & Școlar")
        c1, c2 = st.columns(2)
        with c1:
            add_matr = st.text_input("Număr Matricol:", value=f"128/{new_id}", key="add_matr")
            add_cnp = st.text_input("Cod Numeric Personal (CNP - 13 cifre):", value="", key="add_cnp")
            add_nume = st.text_input("Nume de Familie:", value="", key="add_nume")
            add_init = st.text_input("Inițiala Tatălui (ex: V. sau I.M.):", value="", key="add_init")
        with c2:
            add_prenume = st.text_input("Prenume Elev:", value="", key="add_prenume")
            add_tel = st.text_input("Număr Telefon Elev:", value="", key="add_tel")
            add_nat = st.text_input("Naționalitate:", value="Română", key="add_nat")
            add_etnie = st.text_input("Etnie:", value="Română", key="add_etnie")
            add_pin = st.text_input("Cod PIN Confidențial Părinte (4 cifre):", value=str(1000 + new_id * 17 % 8999), key="add_pin")
            
        st.markdown("##### 2. 🏠 Adresă Domiciliu")
        ca1, ca2 = st.columns(2)
        with ca1:
            add_loc = st.text_input("Localitate:", value="Turda", key="add_loc")
            add_jud = st.text_input("Județ:", value="Cluj", key="add_jud")
            add_strada = st.text_input("Stradă:", value="", key="add_strada")
        with ca2:
            add_nr_strada = st.text_input("Număr Stradă:", value="", key="add_nr_strada")
            add_bloc = st.text_input("Bloc:", value="", key="add_bloc")
            add_ap = st.text_input("Apartament:", value="", key="add_ap")
            
        st.markdown("##### 3. 👨‍👩‍👧 Informații Părinți & Plecări în Străinătate")
        cp1, cp2 = st.columns(2)
        with cp1:
            add_nmama = st.text_input("Nume și Prenume Mamă:", value="", key="add_nmama")
            add_tmama = st.text_input("Telefon Mamă:", value="", key="add_tmama")
            add_mplecata = st.checkbox("Mamă plecată în străinătate", value=False, key="add_mplecata")
            add_taramama = st.text_input("Țara unde este plecată mama:", value="", key="add_taramama") if add_mplecata else ""
        with cp2:
            add_ntata = st.text_input("Nume și Prenume Tată:", value="", key="add_ntata")
            add_ttata = st.text_input("Telefon Tată:", value="", key="add_ttata")
            add_tplecat = st.checkbox("Tată plecat în străinătate", value=False, key="add_tplecat")
            add_taratata = st.text_input("Țara unde este plecat tatăl:", value="", key="add_taratata") if add_tplecat else ""
            
        st.markdown("##### 4. 🩺 Situații Speciale, Burse & CES (Bife)")
        cs1, cs2 = st.columns(2)
        with cs1:
            add_ces = st.checkbox("Elev cu Cerințe Educaționale Speciale (CES)", value=False, key="add_ces")
            add_orfan = st.checkbox("Elev Orfan", value=False, key="add_orfan")
            add_plasament = st.checkbox("Elev aflat în Plasament", value=False, key="add_plasament")
        with cs2:
            add_bursa_med = st.checkbox("Elev cu Bursă Socială Medicală", value=False, key="add_bursa_med")
            add_bursa_ven = st.checkbox("Elev cu Bursă Socială pe Bază de Venit", value=False, key="add_bursa_ven")
            
        st.write("")
        if st.button("➕ Adaugă Elevul în Baza de Date", type="primary", use_container_width=True, key="btn_add_new_student"):
            if not add_nume.strip() or not add_prenume.strip():
                st.error("❌ Vă rugăm să introduceți cel puțin numele și prenumele elevului!")
            else:
                full_n = f"{add_nume.strip().upper()} {add_init.strip().upper()} {add_prenume.strip().upper()}".replace("  ", " ").strip()
                new_st_dict = {
                    'id': new_id,
                    'rand_excel': new_r_ex,
                    'matricol': add_matr.strip() or f"128/{new_id}",
                    'pin': add_pin.strip() or "1234",
                    'nume': add_nume.strip().upper(),
                    'initiala': add_init.strip().upper(),
                    'prenume': add_prenume.strip().upper(),
                    'nume_complet': full_n,
                    'cnp': add_cnp.strip(),
                    'telefon': add_tel.strip(),
                    'localitate': add_loc.strip(),
                    'judet': add_jud.strip(),
                    'strada': add_strada.strip(),
                    'numar_strada': add_nr_strada.strip(),
                    'bloc': add_bloc.strip(),
                    'apartament': add_ap.strip(),
                    'nume_mama': add_nmama.strip(),
                    'telefon_mama': add_tmama.strip(),
                    'mama_plecata': add_mplecata,
                    'tara_mama': add_taramama.strip() if add_mplecata else "",
                    'nume_tata': add_ntata.strip(),
                    'telefon_tata': add_ttata.strip(),
                    'tata_plecat': add_tplecat,
                    'tara_tata': add_taratata.strip() if add_tplecat else "",
                    'nationalitate': add_nat.strip(),
                    'etnie': add_etnie.strip(),
                    'ces': add_ces,
                    'orfan': add_orfan,
                    'plasament': add_plasament,
                    'bursa_medicala': add_bursa_med,
                    'bursa_venit': add_bursa_ven
                }
                gest_data.append(new_st_dict)
                save_gestiune_data(gest_data)
                st.success(f"✅ Elevul {full_n} a fost adăugat cu succes în catalog!")
                st.rerun()

    elif op_gest == "🗑️ Ștergere Elev din Clasă":
        st.markdown("#### 🗑️ Ștergere Elev din Baza de Date")
        if not gest_data:
            st.info("ℹ️ Nu există elevi în baza de date.")
        else:
            del_sel_idx = st.selectbox(
                "Selectează Elevul de Șters:",
                range(len(gest_data)),
                format_func=lambda i: f"{gest_data[i]['id']}. {gest_data[i].get('nume_complet','')} (Matricol {gest_data[i]['matricol']})",
                key="sel_student_delete"
            )
            st_del = gest_data[del_sel_idx]
            st.warning(f"⚠️ Atenție! Sunteți pe cale să ștergeți elevul: **{st_del.get('nume_complet','')}** (Matricol {st_del.get('matricol','')}).")
            
            if st.button("🗑️ Confirmă Ștergerea Definitivă", type="primary", use_container_width=True, key="btn_confirm_del_student"):
                deleted_name = gest_data[del_sel_idx].get('nume_complet', '')
                gest_data.pop(del_sel_idx)
                # Re-index IDs cleanly
                for idx_i, d_item in enumerate(gest_data, 1):
                    d_item['id'] = idx_i
                    d_item['rand_excel'] = 12 + idx_i
                save_gestiune_data(gest_data)
                st.success(f"✅ Elevul {deleted_name} a fost eliminat din clasă!")
                st.rerun()

    st.divider()
    st.markdown("### 📥 Generare și Descărcare Rapoarte Gestiune & Statistică Excel")
    st.caption("Descărcați Registrul complet al datelor de gestiune sau Raportul Statistic Sintetic al clasei.")
    
    col_ex_g1, col_ex_g2 = st.columns(2)
    
    with col_ex_g1:
        try:
            excel_reg_bytes = generate_excel_registru_elevi(gest_data)
            st.download_button(
                "📊 Descarcă Registru Date Elevi (.xlsx)",
                data=excel_reg_bytes,
                file_name="Registru_Date_Elevi_Clasa_IX_TH.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_dl_registru_excel"
            )
        except Exception as ex:
            st.error(f"Eroare la generare Registru Excel: {ex}")
            
    with col_ex_g2:
        try:
            excel_stat_bytes = generate_excel_statistica_clasa(gest_data)
            st.download_button(
                "📊 Descarcă Statistica Clasa (.xlsx)",
                data=excel_stat_bytes,
                file_name="Statistica_Clasa_IX_TH.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                key="btn_dl_statistica_excel"
            )
        except Exception as ex:
            st.error(f"Eroare la generare Statistică Excel: {ex}")


render_copyright_footer()
