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

WEBAPP_URL = "https://script.google.com/macros/s/AKfycbxf-chEeMc6pA02EU0-pwqMTVp8htzzku6TvX5Uhea_nqqCNEcT3D6RYrmke1n0tAwD/exec"

# --- FUNCTIE DE SINCRONIZARE SI DESCARCARE AUTOMATA EXCEL DIN GITHUB ---
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


def push_file_to_github(file_path):
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            token = st.secrets.get("GITHUB_TOKEN", "")
        except Exception:
            token = ""
    if not token:
        return
    try:
        repo = "profudeconta-sketch/catalog-online"
        rel_path = os.path.relpath(file_path, ".").replace("\\", "/")
        url = f"https://api.github.com/repos/{repo}/contents/{rel_path}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "StreamlitApp"
        }
        req_get = urllib.request.Request(url, headers=headers)
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
            "message": f"Update automat documente: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}",
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
            pass
    except Exception:
        pass

def sync_json_from_github(file_path):
    rel_path = os.path.relpath(file_path, ".").replace("\\", "/")
    ts = int(datetime.datetime.now().timestamp())
    raw_url = f"https://raw.githubusercontent.com/profudeconta-sketch/catalog-online/main/{rel_path}?t={ts}"
    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        try:
            token = st.secrets.get("GITHUB_TOKEN", "")
        except Exception:
            token = ""
    headers = {"User-Agent": "StreamlitApp", "Cache-Control": "no-cache"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        req = urllib.request.Request(raw_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                content = resp.read()
                os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(content)
                return True
    except Exception:
        pass
    return False

def load_json_data(file_path, default):
    sync_json_from_github(file_path)
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json_data(file_path, data):
    try:
        os.makedirs(os.path.dirname(file_path) if os.path.dirname(file_path) else ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        push_file_to_github(file_path)
    except Exception:
        pass

def register_download_confirmation(doc_id, matricol, nume_elev, tip_doc, titlu_doc, nume_fisier):
    conf_data = load_json_data("confirmari_documente.json", {})
    now_str = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
    conf_data[doc_id] = {
        "doc_id": doc_id,
        "matricol": matricol,
        "nume_elev": nume_elev,
        "tip_doc": tip_doc,
        "titlu_doc": titlu_doc,
        "nume_fisier": nume_fisier,
        "data_descarcare": now_str,
        "stare": f"Descărcat la {now_str}"
    }
    save_json_data("confirmari_documente.json", conf_data)

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
    col_hdr1, col_hdr2 = st.columns([3, 1])
    with col_hdr1:
       st.success(
        f"✅ Autentificare securizată reușită pentru elevul:"
        f" **{student_found[1]}** (Matricol {student_found[3]})"
    )

    # --- ÎNREGISTRARE CONECTARE ÎN GOOGLE SHEETS (O SINGURĂ DATĂ PER SESIUNE) ---
    if "logged_to_sheet" not in st.session_state:
      st.session_state["logged_to_sheet"] = False

    if not st.session_state["logged_to_sheet"]:
      import requests

      try:
        nume_e = requests.utils.quote(str(student_found[1]))
        matr_e = requests.utils.quote(str(student_found[3]))
        url_call = f"{WEBAPP_URL}?elev={nume_e}&matricol={matr_e}"

        res = requests.get(url_call, timeout=8)

        if "SUCCESS_LOGGED" in res.text:
          st.session_state["logged_to_sheet"] = True
          st.toast(
              "✅ Autentificarea a fost înregistrată în Google Sheet!", icon="📊"
          )
        else:
          st.warning(
              "⚠️ Răspuns Google: "
              + (res.text[:100] if res.text else "Niciun răspuns")
          )
      except Exception as err:
        st.warning(f"⚠️ Eroare conectare Google Sheet: {err}")

    with col_hdr2:
      if st.button(
          "🔄 Actualizează Datele", use_container_width=True, type="primary"
      ):
        sync_excel_from_github()
        st.rerun()

    st.divider()

    if not os.path.exists(excel_path):
        st.error(f"Fișierul catalog '{excel_path}' nu a fost găsit.")
    else:
        try:
            wb = openpyxl.load_workbook(excel_path, data_only=True)
            ws_cg = wb["Cultură Generală"]
            ws_th = wb["Module Tehnologice"]
            
            # Recalculare statistici si clasamente pentru toti elevii din clasa
            all_mgs = []
            all_abs = []
            student_specific_data = None

            for idx_e, e_item in enumerate(ELEVI):
                r_row = 9 + idx_e
                
                c_avgs = []
                t_nem = 0
                t_mot = 0
                
                for _, c_col in DISCIPLINE_CG:
                    nts = []
                    for k in range(10):
                        nv = ws_cg.cell(row=r_row, column=c_col + (k * 2)).value
                        if nv is not None and str(nv).strip() != "":
                            try: nts.append(float(nv))
                            except Exception: pass
                    if nts: c_avgs.append(round(sum(nts)/len(nts), 2))
                    
                    for k in range(30):
                        av = ws_cg.cell(row=r_row, column=c_col + 21 + k).value
                        if av is not None and str(av).strip() != "":
                            sa = str(av).strip()
                            if sa.endswith('m') or sa.endswith('M'): t_mot += 1
                            else: t_nem += 1
                            
                h_avgs = []
                for _, c_col in MODULE_TH:
                    nts = []
                    for k in range(10):
                        nv = ws_th.cell(row=r_row, column=c_col + (k * 2)).value
                        if nv is not None and str(nv).strip() != "":
                            try: nts.append(float(nv))
                            except Exception: pass
                    if nts: h_avgs.append(round(sum(nts)/len(nts), 2))
                    
                    for k in range(30):
                        av = ws_th.cell(row=r_row, column=c_col + 21 + k).value
                        if av is not None and str(av).strip() != "":
                            sa = str(av).strip()
                            if sa.endswith('m') or sa.endswith('M'): t_mot += 1
                            else: t_nem += 1

                mcg_val = round(sum(c_avgs)/len(c_avgs), 2) if c_avgs else None
                mth_val = round(sum(h_avgs)/len(h_avgs), 2) if h_avgs else None
                
                if mcg_val is not None and mth_val is not None: mg_val = round((mcg_val + mth_val)/2.0, 2)
                elif mcg_val is not None: mg_val = mcg_val
                elif mth_val is not None: mg_val = mth_val
                else: mg_val = None
                    
                tot_abs_val = t_nem + t_mot
                all_mgs.append((idx_e, mg_val))
                all_abs.append((idx_e, tot_abs_val, t_nem))
                
                if e_item[0] == student_found[0]:
                    purtare_val = max(1, 10 - int(t_nem / 20))
                    student_specific_data = {
                        'mcg': mcg_val,
                        'mth': mth_val,
                        'mg': mg_val,
                        'purtare': purtare_val,
                        'tot_abs': tot_abs_val,
                        'abs_nem': t_nem,
                        'abs_mot': t_mot
                    }

            # Clasament medii
            valid_mgs_list = sorted([m[1] for m in all_mgs if m[1] is not None], reverse=True)
            if student_specific_data['mg'] is not None and valid_mgs_list:
                rank_mg_str = f"Locul {valid_mgs_list.index(student_specific_data['mg']) + 1} din {len(ELEVI)}"
            else:
                rank_mg_str = "Fără medie generală"

            # Clasament absente
            sorted_abs_list = sorted([a[1] for a in all_abs], reverse=True)
            rank_abs_num = sorted_abs_list.index(student_specific_data['tot_abs']) + 1
            rank_abs_str = f"Locul {rank_abs_num} din {len(ELEVI)}"

            col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)
            col_kpi1.metric("Media Cultură Gen.", safe_float_str(student_specific_data['mcg']))
            col_kpi2.metric("Media Module TH.", safe_float_str(student_specific_data['mth']))
            col_kpi3.metric("Media Generală", safe_float_str(student_specific_data['mg']), help=rank_mg_str)
            col_kpi4.metric("Nota la Purtare", str(student_specific_data['purtare']))
            col_kpi5.metric("Total Absențe", f"{student_specific_data['tot_abs']} ({student_specific_data['abs_nem']} nem. / {student_specific_data['abs_mot']} mot.)", help=rank_abs_str)

            st.info(f"🏆 **Poziție Școlară Elev în Clasă**: **{rank_mg_str}** în clasamentul mediilor generale | **{rank_abs_str}** în clasamentul numărului de absențe ({student_specific_data['tot_abs']} absențe din care {student_specific_data['abs_nem']} nemotivate).")

            st.divider()

            s_idx = student_found[0] - 1
            s_row = 9 + s_idx

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
                        "Absențe Înregistrate (Total / Nem / Mot)": abs_str_formatted,
                        "Medie Actuală": media_str
                    })
                st.dataframe(rows_data, use_container_width=True, hide_index=True)

            wb.close()
        except Exception as ex:
            st.error(f"Eroare la încărcarea fișei elevului: {ex}")


            # --- SECȚIUNEA 1: ÎNCĂRCARE DOCUMENTE PĂRINȚI ---
            st.divider()
            st.markdown("### 📤 Transmitere Documente către Diriginte / Școală")
            st.info("💡 Puteți încărca adeverințe medicale, scutiri, copii după acte de identitate sau documente pentru dosare de bursă. Dirigintele le va primi direct în catalogul școlar.")
            
            with st.expander("➕ Formular Încărcare Document Nou", expanded=False):
                col_up1, col_up2 = st.columns(2)
                with col_up1:
                    cat_doc = st.selectbox(
                        "📋 Selectați tipul documentului:",
                        [
                            "🩺 Scutire Medicală / Adeverință",
                            "🪪 Copie Carte de Identitate (Elev / Părinte)",
                            "📜 Copie Certificat de Naștere",
                            "💰 Documente Dosar Bursă (Socială / Medicală / Venit)",
                            "📁 Alt Document / Cerere Oficială"
                        ],
                        key="parent_cat_doc"
                    )
                with col_up2:
                    obs_doc = st.text_input(
                        "📝 Mențiuni / Observații (opțional):",
                        placeholder="Ex: Scutire medicală pentru perioada 01-05 Octombrie",
                        key="parent_obs_doc"
                    )

                up_file = st.file_uploader(
                    "📎 Alegeți fișierul (PDF, JPG, PNG - max 10MB):",
                    type=["pdf", "jpg", "jpeg", "png"],
                    key="parent_file_uploader"
                )

                if st.button("📤 Trimite Documentul către Diriginte", type="primary", use_container_width=True):
                    if up_file is None:
                        st.error("⚠️ Vă rugăm să selectați un fișier înainte de a apăsa butonul de trimitere.")
                    else:
                        matr_safe = str(student_found[3]).replace("/", "_").replace(" ", "_")
                        ext = os.path.splitext(up_file.name)[1].lower()
                        ts_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                        clean_cat = cat_doc.split(" ")[1] if " " in cat_doc else "Document"
                        saved_filename = f"{clean_cat}_{matr_safe}_{ts_str}{ext}"
                        
                        folder_path = os.path.join("documente_parinti", matr_safe)
                        os.makedirs(folder_path, exist_ok=True)
                        full_save_path = os.path.join(folder_path, saved_filename)
                        
                        with open(full_save_path, "wb") as f_out:
                            f_out.write(up_file.getbuffer())
                            
                        push_file_to_github(full_save_path)
                        
                        doc_records = load_json_data("documente_parinti.json", [])
                        new_entry = {
                            "id": f"DOCP_{matr_safe}_{ts_str}",
                            "matricol": str(student_found[3]),
                            "nume_elev": str(student_found[1]),
                            "tip_doc": cat_doc,
                            "observatii": obs_doc.strip(),
                            "nume_fisier_original": up_file.name,
                            nume_fisier_salvat: saved_filename,
                            "cale_fisier": full_save_path.replace("\\", "/"),
                            "data_incarcare": datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
                        }
                        doc_records.append(new_entry)
                        save_json_data("documente_parinti.json", doc_records)
                        
                        st.success("✅ Documentul a fost încărcat și transmis cu succes către diriginte!")
                        st.toast("🎉 S-a salvat în dosarul securizat al elevului!", icon="📄")

            parent_docs_all = load_json_data("documente_parinti.json", [])
            parent_docs_student = [d for d in parent_docs_all if str(d.get("matricol")) == str(student_found[3])]
            if parent_docs_student:
                st.markdown("##### 📋 Documente Transmise Anterior de la Părinte:")
                p_rows = []
                for pd in reversed(parent_docs_student):
                    p_rows.append({
                        "Data Încărcării": pd.get("data_incarcare", "-"),
                        "Tip Document": pd.get("tip_doc", "-"),
                        "Nume Fișier Original": pd.get("nume_fisier_original", "-"),
                        "Observații": pd.get("observatii", "-") or "-"
                    })
                st.dataframe(p_rows, use_container_width=True, hide_index=True)


            # --- SECȚIUNEA 2: RECEPȚIONARE DOCUMENTE OFICIALE DE LA DIRIGINTE ---
            st.divider()
            st.markdown("### 📩 Înștiințări și Documente Oficiale de la Școală")
            st.info("🔒 Aici puteți vizualiza și descărca documentele oficiale emise de diriginte (mustrări scrise, preavize, adrese, înștiințări). Descărcarea înregistrează automat confirmarea de primire.")

            official_docs_all = load_json_data("documente_oficiale.json", [])
            official_docs_student = [d for d in official_docs_all if str(d.get("matricol")) == str(student_found[3])]
            confirmations_dict = load_json_data("confirmari_documente.json", {})

            if not official_docs_student:
                st.info("ℹ️ Nu există înștiințări sau documente oficiale noi emise de școală pentru acest elev.")
            else:
                for o_doc in reversed(official_docs_student):
                    doc_id = o_doc.get("id")
                    file_path = o_doc.get("cale_fisier")
                    
                    if file_path and not os.path.exists(file_path):
                        sync_json_from_github(file_path)

                    conf_info = confirmations_dict.get(doc_id)
                    if conf_info:
                        stare_str = f"✅ **{conf_info.get('stare', 'Descărcat')}**"
                    else:
                        stare_str = "⏳ **În așteptare (Neconfirmat)**"

                    with st.container():
                        c_d1, c_d2 = st.columns([3, 2])
                        with c_d1:
                            st.markdown(f"**{o_doc.get('tip_doc', 'Document Oficial')}**: {o_doc.get('titlu_doc', '')}")
                            st.caption(f"📅 Data emiterii: {o_doc.get('data_emitere', '-')} | Stare: {stare_str}")
                            if o_doc.get('observatii'):
                                st.caption(f"📝 Detalii: {o_doc.get('observatii')}")

                        with c_d2:
                            if file_path and os.path.exists(file_path):
                                with open(file_path, "rb") as f_doc:
                                    doc_bytes = f_doc.read()
                                
                                ext_doc = os.path.splitext(file_path)[1].lower()
                                mime_t = "application/pdf" if ext_doc == ".pdf" else f"image/{ext_doc.replace('.', '')}"
                                
                                st.download_button(
                                    label=f"📥 Descarcă / Vizualizează Documentul",
                                    data=doc_bytes,
                                    file_name=o_doc.get("nume_fisier_salvat", f"Document_Oficial_{student_found[3]}.pdf"),
                                    mime=mime_t,
                                    key=f"dl_off_{doc_id}",
                                    type="primary",
                                    use_container_width=True,
                                    on_click=register_download_confirmation,
                                    args=(
                                        doc_id,
                                        str(student_found[3]),
                                        str(student_found[1]),
                                        o_doc.get("tip_doc", "Document Oficial"),
                                        o_doc.get("titlu_doc", "Document Oficial"),
                                        o_doc.get("nume_fisier_salvat", "Document.pdf")
                                    )
                                )
                            else:
                                st.warning("⚠️ Fișierul nu a putut fi încărcat de pe server.")
                        st.divider()

st.markdown("---")
st.caption("© 2026 Prof. Ec. Gherman Octavian-Theodor. Toate drepturile de autor rezervate.")
st.caption("🏫 Colegiul 'Emil Negruțiu' Turda — Sistem Școlar Securizat pentru Părinți | Date actualizate în timp real.")
