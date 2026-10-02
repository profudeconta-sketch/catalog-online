import datetime
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

tab1, tab2, tab3, tab_del, tab4, tab5, tab6, tab_com = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "🗑️ Ștergere Notă / Absență",
    "📊 Fișă Elev",
    "📈 Centralizator Clasă",
    "📋 Raport Diriginte",
    "📩 Comunicare / Documente Părinți"
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

render_copyright_footer()


# --- TAB 8: COMUNICARE / DOCUMENTE PĂRINȚI ---
with tab_com:
    st.subheader("📩 Comunicare și Gestiune Documente Părinți")
    st.info("Secțiune dedicată comunicării bidirecționale: primirea scutirilor și adeverințelor de la părinți, transmiterea de documente oficiale și monitorizarea automată a confirmărilor de descărcare.")
    
    tab_doc_in, tab_doc_out, tab_doc_conf = st.tabs([
        "📥 Documente Primite de la Părinți", 
        "📤 Transmitere Documente Oficiale", 
        "⏱️ Stare Confirmări Descărcări Părinți"
    ])
    
    with tab_doc_in:
        st.subheader("📥 Scutiri, Adeverințe și Dosare Primite de la Părinți")
        
        filter_student = st.selectbox(
            "Filtrează după elev:",
            ["Toți Elevii"] + [f"{e[1]} (Matricol {e[3]})" for e in ELEVI],
            key="filter_parent_docs_select"
        )
        
        if os.path.exists("documente_parinti_meta.json"):
            try:
                with open("documente_parinti_meta.json", "r", encoding="utf-8") as f_p:
                    p_meta = json.load(f_p)
                
                if filter_student != "Toți Elevii":
                    matr_filter = filter_student.split("Matricol ")[1].replace(")", "").strip()
                    p_meta = [d for d in p_meta if str(d.get("matricol")) == matr_filter]
                
                if p_meta:
                    for idx_p, p_doc in enumerate(reversed(p_meta)):
                        col_p1, col_p2 = st.columns([3, 1])
                        with col_p1:
                            st.markdown(f"**{p_doc.get('nume_elev')}** (Matricol {p_doc.get('matricol')})")
                            st.caption(f"📌 **{p_doc.get('tip_document')}** | Data încărcării: {p_doc.get('data_incarcare')} | Fișier: {p_doc.get('nume_fisier_original')}")
                        with col_p2:
                            filepath = p_doc.get("cale", "")
                            if os.path.exists(filepath):
                                with open(filepath, "rb") as f_b:
                                    st.download_button(
                                        "📥 Deschide / Descarcă",
                                        data=f_b.read(),
                                        file_name=p_doc.get("nume_fisier_original", "document.pdf"),
                                        mime="application/pdf" if filepath.endswith(".pdf") else "image/png",
                                        key=f"dl_parent_doc_{idx_p}",
                                        use_container_width=True
                                    )
                            else:
                                st.warning("Fișier negăsit pe disc")
                        st.divider()
                else:
                    st.info("ℹ️ Nu există documente încărcate de părinți conform filtrului selectat.")
            except Exception as ex_p:
                st.error(f"Eroare la citire documente părinți: {ex_p}")
        else:
            st.info("ℹ️ Nu există înregistrat niciun document transmis de părinți.")
            
    with tab_doc_out:
        st.subheader("📤 Emitere / Transmitere Document Oficial către Părinți")
        st.info("Atașați un document oficial (mustrare, preaviz, decizie de scădere a mediei la purtare, înștiințare de absențe) și transmiteți-l către părintele elevului selectat.")
        
        col_o1, col_o2 = st.columns([2, 1])
        with col_o1:
            elev_idx_of = st.selectbox(
                "Selectează Elevul Destinatar:",
                range(len(ELEVI)),
                format_func=lambda i: f"{ELEVI[i][0]}. {ELEVI[i][1]} (Matricol {ELEVI[i][3]})",
                key="elev_idx_of_select"
            )
            tip_doc_of = st.selectbox(
                "Tipul Documentului Oficial:",
                [
                    "⚠️ Mustrare Scrisă",
                    "📉 Decizie de Scădere a Mediei la Purtare",
                    "🚨 Preaviz de Exmatriculare",
                    "📑 Înștiințare Absențe Acumulate",
                    "ℹ️ Informare / Adresă Oficială"
                ],
                key="tip_doc_of_select"
            )
            titlu_doc_of = st.text_input(
                "Titlu / Număr Înregistrare Document (ex: Mustrare Scrisă Nr. 14 / 02.10.2026):",
                value=f"{tip_doc_of.split(' ')[1]} Nr. 1 / {datetime.datetime.now().strftime('%d.%m.%Y')}",
                key="titlu_doc_of_input"
            )
            file_up_of = st.file_uploader("Atașați Fișierul Documentului (PDF, JPG, PNG):", type=["pdf", "jpg", "jpeg", "png"], key="file_up_of_input")
            
        with col_o2:
            st.write("")
            st.write("")
            if file_up_of is not None and titlu_doc_of:
                if st.button("🚀 Transmite Documentul Oficial către Părinte", use_container_width=True, type="primary"):
                    try:
                        selected_student = ELEVI[elev_idx_of]
                        clean_matr = str(selected_student[3]).replace('/', '_')
                        
                        ext = file_up_of.name.split('.')[-1] if '.' in file_up_of.name else 'pdf'
                        ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        new_fname = f"DocOficial_{clean_matr}_{ts_str}.{ext}"
                        
                        student_dir = os.path.join("documente_oficiale", f"Matricol_{clean_matr}")
                        os.makedirs(student_dir, exist_ok=True)
                        save_path = os.path.join(student_dir, new_fname)
                        
                        with open(save_path, "wb") as f_out:
                            f_out.write(file_up_of.getbuffer())
                            
                        docs_of_meta = []
                        if os.path.exists("documente_oficiale_meta.json"):
                            try:
                                with open("documente_oficiale_meta.json", "r", encoding="utf-8") as f_o:
                                    docs_of_meta = json.load(f_o)
                            except Exception: pass
                            
                        docs_of_meta.append({
                            "matricol": str(selected_student[3]),
                            "nume_elev": selected_student[1],
                            "tip_document": tip_doc_of,
                            "nume_document": titlu_doc_of,
                            "nume_fisier_original": file_up_of.name,
                            "cale": save_path,
                            "data_emitere": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                        })
                        
                        with open("documente_oficiale_meta.json", "w", encoding="utf-8") as f_o:
                            json.dump(docs_of_meta, f_o, ensure_ascii=False, indent=2)
                            
                        push_to_github(save_path)
                        push_to_github("documente_oficiale_meta.json")
                        
                        st.success(f"✅ Documentul oficial a fost transmis cu succes pentru elevul **{selected_student[1]}**!")
                        st.rerun()
                    except Exception as ex_of_send:
                        st.error(f"Eroare la transmiterea documentului: {ex_of_send}")
                        
    with tab_doc_conf:
        st.subheader("⏱️ Monitorizare Real-Time Confirmări Descărcare Părinți")
        st.info("Înregistrare automată ca dovadă digitală de luare la cunoștință. Se afișează data și ora exactă la care părintele a descărcat/vizualizat documentul oficial.")
        
        if os.path.exists("documente_oficiale_meta.json"):
            try:
                with open("documente_oficiale_meta.json", "r", encoding="utf-8") as f_o:
                    all_emitted = json.load(f_o)
                    
                all_confirmari = []
                if os.path.exists("confirmari_documente.json"):
                    with open("confirmari_documente.json", "r", encoding="utf-8") as f_c:
                        all_confirmari = json.load(f_c)
                        
                if all_emitted:
                    conf_table_data = []
                    for doc_item in reversed(all_emitted):
                        e_matr = str(doc_item.get("matricol"))
                        doc_title = doc_item.get("nume_document")
                        
                        conf_match = None
                        for c in all_confirmari:
                            if str(c.get("matricol")) == e_matr and c.get("titlu_document") == doc_title:
                                conf_match = c
                                break
                                
                        stare_str = f"✅ Descărcat la {conf_match.get('data_ora_descarcare')}" if conf_match else "⏳ În așteptare (Nedescărcat)"
                        
                        conf_table_data.append({
                            "Nume și Prenume Elev": doc_item.get("nume_elev"),
                            "Matricol": doc_item.get("matricol"),
                            "Tip Document": doc_item.get("tip_document"),
                            "Titlu Document / Înregistrare": doc_item.get("nume_document"),
                            "Data Emiterii": doc_item.get("data_emitere"),
                            "Stare / Confirmare Primire": stare_str
                        })
                    st.dataframe(conf_table_data, use_container_width=True, hide_index=True)
                else:
                    st.info("ℹ️ Nu au fost emise încă documente oficiale.")
            except Exception as ex_conf:
                st.error(f"Eroare la generare tablou confirmări: {ex_conf}")
        else:
            st.info("ℹ️ Nu există documente oficiale emise în sistem.")
