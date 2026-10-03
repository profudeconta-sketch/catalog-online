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

def _atomic_replace_bytes(filename, content, validator):
    temp = filename + ".download.tmp"
    try:
        with open(temp, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        validator(temp)
        os.replace(temp, filename)
        return filename
    except Exception:
        try:
            if os.path.exists(temp):
                os.remove(temp)
        except Exception:
            pass
        raise

def _validate_excel(path):
    wb = openpyxl.load_workbook(path, read_only=True, data_only=False)
    try:
        required = {"Centralizator Medii", "Cultură Generală", "Module Tehnologice", "Absențe & Purtare"}
        missing = required.difference(wb.sheetnames)
        if missing:
            raise ValueError("Fișier Excel incomplet.")
    finally:
        wb.close()

def _validate_gestiune(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list) or not data:
        raise ValueError("Fișierul de gestiune este gol sau invalid.")
    for row in data:
        if not isinstance(row, dict) or not {"id", "matricol", "pin"}.issubset(row):
            raise ValueError("Structură invalidă în fișierul de gestiune.")

# --- FUNCTIE DE SINCRONIZARE SI DESCARCARE AUTOMATA EXCEL DIN GITHUB ---
def sync_excel_from_github():
    filename = "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

    token = os.environ.get("GITHUB_TOKEN") or ""

    try:
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or str(st.secrets["GITHUB_TOKEN"])
    except Exception:
        pass

    if not token:
        return False

    api_url = (
        "https://api.github.com/repos/"
        "profudeconta-sketch/catalog-online-date-private/"
        f"contents/{filename}?ref=main"
    )

    headers = {
        "User-Agent": "StreamlitApp",
        "Cache-Control": "no-cache",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    try:
        req = urllib.request.Request(api_url, headers=headers)

        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return False

            payload = json.loads(resp.read().decode("utf-8"))

        content_b64 = payload.get("content", "")

        if not content_b64:
            return False

        content = base64.b64decode(content_b64)

        return _atomic_replace_bytes(
            filename,
            content,
            _validate_excel
        )

    except Exception:
        return False

# Sincronizare la incarcarea portalului
sync_excel_from_github()

GESTIUNE_FILE = "gestiune_elevi.json"

def sync_gestiune_from_github():
    filename = GESTIUNE_FILE

    token = os.environ.get("GITHUB_TOKEN") or ""

    try:
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or str(st.secrets["GITHUB_TOKEN"])
    except Exception:
        pass

    if not token:
        return False

    api_url = (
        "https://api.github.com/repos/"
        "profudeconta-sketch/catalog-online-date-private/"
        f"contents/{filename}?ref=main"
    )

    headers = {
        "User-Agent": "StreamlitApp",
        "Cache-Control": "no-cache",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    temp_file = filename + ".download.tmp"

    try:
        req = urllib.request.Request(api_url, headers=headers)

        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return False

            payload = json.loads(resp.read().decode("utf-8"))

        content_b64 = payload.get("content", "")

        if not content_b64:
            return False

        content = base64.b64decode(content_b64)

        with open(temp_file, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        _validate_gestiune(temp_file)

        os.replace(temp_file, filename)
        return True

    except Exception:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass

        return False
        
try:
    sync_gestiune_from_github()
except Exception:
    pass

def get_current_elevi_parinti():
    if os.path.exists(GESTIUNE_FILE):
        try:
            with open(GESTIUNE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list) and len(data) > 0:
                    elevi_list = []
                    for d in data:
                        nume_full = d.get("nume_complet", f"{d.get('nume','')} {d.get('initiala','')} {d.get('prenume','')}".strip())
                        nume_full = " ".join(nume_full.split())
                        elevi_list.append((
                            d["id"],
                            nume_full,
                            d.get("rand_excel", 12 + d["id"]),
                            d["matricol"],
                            str(d.get("pin", "1234"))
                        ))
                    return elevi_list
        except Exception:
            pass
    st.error(
        "Datele elevilor nu au putut fi încărcate din sursa privată. "
        "Portalul părinților a fost oprit pentru protejarea datelor."
    )
    st.stop()


# Lista celor 32 de elevi (ID, Nume, RM/PG, Nr. Matr., PIN)


ELEVI = get_current_elevi_parinti()
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

st.markdown("---")
st.caption("© 2026 Prof. Ec. Gherman Octavian-Theodor. Toate drepturile de autor rezervate.")
st.caption("🏫 Colegiul 'Emil Negruțiu' Turda — Sistem Școlar Securizat pentru Părinți | Date actualizate în timp real.")
