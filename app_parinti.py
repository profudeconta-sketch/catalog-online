import datetime
import os
import openpyxl
import streamlit as st
import urllib.request
import urllib.parse
import json
import base64

st.set_page_config(
    page_title="Portal Părinți - Catalog IX TH",
    page_icon="👨‍👩‍👧‍👦",
    layout="wide"
)

# --- FUNCTIE DE SINCRONIZARE SI DESCARCARE AUTOMATA EXCEL DIN GITHUB ---
WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxf-chEeMc6pA02EU0-pwqMTVp8htzzku6TvX5Uhea_nqqCNEcT3D6RYrmke1n0tAwD/exec"

def sync_excel_from_github():
    filename = "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"
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
                if len(content) > 2000:
                    with open(filename, "wb") as f:
                        f.write(content)
                    return filename
    except Exception:
        pass

    try:
        api_url = f"https://api.github.com/repos/profudeconta-sketch/catalog-online/contents/{filename}?t={ts}"
        req_api = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req_api, timeout=5) as resp:
            if resp.status == 200:
                res_json = json.loads(resp.read().decode('utf-8'))
                content_b64 = res_json.get('content', '')
                if content_b64:
                    binary_data = base64.b64decode(content_b64)
                    with open(filename, "wb") as f:
                        f.write(binary_data)
                    return filename
    except Exception:
        pass

    return filename

# Sincronizare la incarcarea portalului
sync_excel_from_github()

# Lista celor 32 de elevi (ID, Nume, Nr. Matr. Simplu, Nr. Matr. Registru/Complet, PIN Confidențial)
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

def log_parent_access(elev_nume, matricol):
    if "logged_students" not in st.session_state:
        st.session_state["logged_students"] = set()
    
    key = f"{elev_nume}_{matricol}"
    if key not in st.session_state["logged_students"]:
        st.session_state["logged_students"].add(key)
        try:
            params = urllib.parse.urlencode({"elev": elev_nume, "matricol": matricol})
            full_url = f"{WEBAPP_URL}?{params}"
            req = urllib.request.Request(full_url, headers={'User-Agent': 'Mozilla/5.0'})
            urllib.request.urlopen(req, timeout=3)
        except Exception:
            pass

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

st.title("🏫 Colegiul 'Emil Negruțiu' Turda")
st.subheader("👨‍👩‍👧‍👦 Portal Părinți — Vizualizare Fișă Școlară Elev (IX TH)")
st.info("🔒 Acces securizat pentru părinți. Vă rugăm să vă autentificați mai jos cu Numărul Matricol și Codul PIN confidențial primit de la diriginte.")

col_auth1, col_auth2 = st.columns(2)

with col_auth1:
    nr_matricol_input = st.text_input(
        "🔑 Introduceți Numărul Matricol (ex: 126/76 sau 13):",
        value="",
        placeholder="Exemplu: 126/76",
        help="Numărul matricol se găsește pe carnetul de elev sau adeverința de înscriere."
    ).strip()

with col_auth2:
    pin_input = st.text_input(
        "🔒 Introduceți Codul PIN Confidențial (4 cifre):",
        value="",
        type="password",
        placeholder="Exemplu: 2951",
        help="Codul PIN confidențial individual eliberat de către diriginte."
    ).strip()

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

student_found = None
pin_correct = False

if nr_matricol_input:
    for e in ELEVI:
        if nr_matricol_input == str(e[2]) or nr_matricol_input == str(e[3]) or nr_matricol_input.lower() == str(e[3]).lower():
            student_found = e
            if pin_input and pin_input == str(e[4]):
                pin_correct = True
            break

if not nr_matricol_input or not pin_input:
    st.warning("👈 Vă rugăm să completați atât Numărul Matricol, cât și Codul PIN confidențial de mai sus.")
elif not student_found:
    st.error("❌ Nu s-a găsit niciun elev cu acest Număr Matricol. Verificați carnetul elevului și încercați din nou.")
elif not pin_correct:
    st.error("❌ Cod PIN incorect pentru acest elev! Vă rugăm să verificați biletul confidențial primit de la diriginte.")
else:
    log_parent_access(student_found[1], student_found[3])
    
    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
        st.success(f"✅ Autentificare securizată reușită pentru elevul: **{student_found[1]}** (Matricol {student_found[3]})")
    with col_hdr2:
        if st.button("🔄 Actualizează Datele", use_container_width=True, type="primary"):
            sync_excel_from_github()
            st.rerun()

    st.divider()

    if not os.path.exists(excel_path):
        st.error(f"Fișierul catalog '{excel_path}' nu a fost găsit.")
    else:
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            s_idx = student_found[0] - 1
            s_row = 9 + s_idx

            ws_cg = wb["Cultură Generală"]
            ws_th = wb["Module Tehnologice"]
            
            # 1. Calculare date clasa întreagă pentru clasamente
            class_stats = []
            for idx_c, e_c in enumerate(ELEVI):
                r_c = 9 + idx_c
                
                cg_a = []
                abs_n_c = 0
                abs_m_c = 0
                for _, col_c in DISCIPLINE_CG:
                    nts = []
                    for k in range(10):
                        v_c = ws_cg.cell(row=r_c, column=col_c + (k * 2)).value
                        if v_c is not None and str(v_c).strip() != "":
                            try:
                                nts.append(float(v_c))
                            except Exception:
                                pass
                    if nts:
                        cg_a.append(round(sum(nts)/len(nts), 2))
                    for k in range(30):
                        av_c = ws_cg.cell(row=r_c, column=col_c + 21 + k).value
                        if av_c is not None and str(av_c).strip() != "":
                            s_av = str(av_c).strip()
                            if s_av.endswith('m'):
                                abs_m_c += 1
                            else:
                                abs_n_c += 1
                                
                th_a = []
                for _, col_c in MODULE_TH:
                    nts = []
                    for k in range(10):
                        v_c = ws_th.cell(row=r_c, column=col_c + (k * 2)).value
                        if v_c is not None and str(v_c).strip() != "":
                            try:
                                nts.append(float(v_c))
                            except Exception:
                                pass
                    if nts:
                        th_a.append(round(sum(nts)/len(nts), 2))
                    for k in range(30):
                        av_c = ws_th.cell(row=r_c, column=col_c + 21 + k).value
                        if av_c is not None and str(av_c).strip() != "":
                            s_av = str(av_c).strip()
                            if s_av.endswith('m'):
                                abs_m_c += 1
                            else:
                                abs_n_c += 1
                                
                mcg_c = round(sum(cg_a)/len(cg_a), 2) if cg_a else None
                mth_c = round(sum(th_a)/len(th_a), 2) if th_a else None
                
                if mcg_c is not None and mth_c is not None:
                    mg_c = round((mcg_c + mth_c)/2.0, 2)
                elif mcg_c is not None:
                    mg_c = mcg_c
                elif mth_c is not None:
                    mg_c = mth_c
                else:
                    mg_c = None
                    
                tot_a_c = abs_n_c + abs_m_c
                class_stats.append({
                    'idx': idx_c,
                    'mg': mg_c,
                    'tot_abs': tot_a_c,
                    'abs_nem': abs_n_c,
                    'abs_mot': abs_m_c
                })

            # Clasamente la nivel de clasă
            valid_mgs = sorted([c['mg'] for c in class_stats if c['mg'] is not None], reverse=True)
            sorted_abs = sorted([c['tot_abs'] for c in class_stats])

            curr_stat = class_stats[s_idx]
            
            if curr_stat['mg'] is not None:
                rank_mg_str = f"Locul {valid_mgs.index(curr_stat['mg']) + 1} din {len(ELEVI)} elevi"
            else:
                rank_mg_str = "Fără medie generală"
                
            rank_abs_str = f"Locul {sorted_abs.index(curr_stat['tot_abs']) + 1} din {len(ELEVI)} elevi"

            # Calcul specific pentru elevul autentificat
            cg_avgs = []
            for _, col_c in DISCIPLINE_CG:
                nts = []
                for k in range(10):
                    v_c = ws_cg.cell(row=s_row, column=col_c + (k * 2)).value
                    if v_c is not None and str(v_c).strip() != "":
                        try:
                            nts.append(float(v_c))
                        except Exception:
                            pass
                if nts:
                    cg_avgs.append(round(sum(nts)/len(nts), 2))
                    
            th_avgs = []
            for _, col_c in MODULE_TH:
                nts = []
                for k in range(10):
                    v_c = ws_th.cell(row=s_row, column=col_c + (k * 2)).value
                    if v_c is not None and str(v_c).strip() != "":
                        try:
                            nts.append(float(v_c))
                        except Exception:
                            pass
                if nts:
                    th_avgs.append(round(sum(nts)/len(nts), 2))

            med_cg = round(sum(cg_avgs)/len(cg_avgs), 2) if cg_avgs else None
            med_th = round(sum(th_avgs)/len(th_avgs), 2) if th_avgs else None
            
            if med_cg is not None and med_th is not None:
                med_gen = round((med_cg + med_th)/2.0, 2)
            elif med_cg is not None:
                med_gen = med_cg
            elif med_th is not None:
                med_gen = med_th
            else:
                med_gen = None

            abs_nem = curr_stat['abs_nem']
            abs_mot = curr_stat['abs_mot']
            purtare = max(1, 10 - int(abs_nem / 20))
            abs_tot = abs_nem + abs_mot

            # Indicatori principali (Medii, Purtare, Absențe)
            m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
            m_col1.metric("Media Cultură Gen.", safe_float_str(med_cg))
            m_col2.metric("Media Module TH.", safe_float_str(med_th))
            m_col3.metric("Media Generală", safe_float_str(med_gen))
            m_col4.metric("Nota la Purtare", str(purtare))
            m_col5.metric("Total Absențe", f"{abs_tot} ({abs_nem} nem. / {abs_mot} mot.)")

            # Card informativ dedicat: Pozitie & Clasament Elev
            st.markdown(
                f"""
                <div style="background-color: #EDF2F7; border-left: 5px solid #2B6CB0; padding: 14px 18px; border-radius: 8px; margin-top: 15px; margin-bottom: 15px;">
                    <div style="font-size: 1.05rem; font-weight: bold; color: #1A365D; margin-bottom: 8px;">
                        📊 Poziție și Clasament Elev în Clasă
                    </div>
                    <div style="display: flex; gap: 30px; flex-wrap: wrap; font-size: 0.95rem; color: #2D3748;">
                        <div>🏆 <b>Clasament Medii Generale:</b> <span style="color: #2B6CB0; font-weight: bold;">{rank_mg_str}</span></div>
                        <div>📌 <b>Clasament Frecvență (Absențe):</b> <span style="color: #2B6CB0; font-weight: bold;">{rank_abs_str}</span> <span style="font-size: 0.8rem; color: #718096;">(Locul 1 = cele mai puține absențe)</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.divider()

            # Tabel detaliat pe discipline
            for cat_title, ws, sub_list in [("📚 DISCIPLINE CULTURĂ GENERALĂ", ws_cg, DISCIPLINE_CG), ("⚙️ MODULE TEHNOLOGICE", ws_th, MODULE_TH)]:
                st.markdown(f"#### {cat_title}")

                rows_data = []
                for s_name, start_col in sub_list:
                    notes = []
                    for k in range(10):
                        n_val = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        d_val = ws.cell(row=s_row, column=start_col + (k * 2) + 1).value
                        if n_val is not None and str(n_val).strip() != "":
                            d_str = f" ({d_val})" if d_val else ""
                            notes.append(f"{n_val}{d_str}")
                            
                    abs_dates = []
                    abs_nem_sub = 0
                    abs_mot_sub = 0
                    for k in range(30):
                        a_val = ws.cell(row=s_row, column=start_col + 21 + k).value
                        if a_val is not None and str(a_val).strip() != "":
                            s_a = str(a_val).strip()
                            abs_dates.append(s_a)
                            if s_a.endswith('m'):
                                abs_mot_sub += 1
                            else:
                                abs_nem_sub += 1
                                
                    tot_sub = abs_nem_sub + abs_mot_sub
                    if tot_sub > 0:
                        abs_display = f"{tot_sub} total ({abs_nem_sub} nem. / {abs_mot_sub} mot.) — Date: {', '.join(abs_dates)}"
                    else:
                        abs_display = "Fără absențe"
                            
                    sub_notes_float = []
                    for k in range(10):
                        nv = ws.cell(row=s_row, column=start_col + (k * 2)).value
                        if nv is not None and str(nv).strip() != "":
                            try:
                                sub_notes_float.append(float(nv))
                            except Exception:
                                pass
                    media_str = f"{(sum(sub_notes_float)/len(sub_notes_float)):.2f}" if sub_notes_float else "-"

                    rows_data.append({
                        "Disciplină / Modul": s_name,
                        "Note Obtinute": ", ".join(notes) if notes else "Fără note înregistrate",
                        "Absențe Înregistrate": abs_display,
                        "Medie Actuală": media_str
                    })
                st.dataframe(rows_data, use_container_width=True, hide_index=True)

            wb.close()
        except Exception as ex:
            st.error(f"Eroare la încărcarea fișei elevului: {ex}")

st.markdown("---")
st.caption("© 2026 Prof. Ec. Gherman Octavian-Theodor. Toate drepturile de autor rezervate.")
st.caption("🏫 Colegiul 'Emil Negruțiu' Turda — Sistem Școlar Securizat pentru Părinți | Date actualizate în timp real.")
