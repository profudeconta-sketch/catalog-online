import datetime
import os
import openpyxl
import streamlit as st

st.set_page_config(
    page_title="Catalog Școlar Online IX TH",
    page_icon="🏫",
    layout="wide"
)

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

st.title("🏫 Colegiul 'Emil Negruțiu' Turda — Catalog Școlar Online (IX TH Turism)")
st.caption("Aplicație Web Streamlit pentru gestionare note, absențe și vizualizare catalog complet")

if not os.path.exists(excel_path):
    st.warning(f"⚠️ Fișierul catalog '{excel_path}' nu a fost găsit în directorul curent. Vă rugăm să îl încărcați pe GitHub în același folder.")

# Sidebar setup
with st.sidebar:
    st.header("⚙️ Opțiuni Catalog")
    selected_file = st.text_input("Fișier Excel:", value=excel_path)
    
    st.markdown("---")
    st.subheader("📥 Descarcă Fișierul Excel")
    if os.path.exists(selected_file):
        with open(selected_file, "rb") as f:
            bytes_data = f.read()
        st.download_button(
            label="📥 Descarcă Catalog Excel (.xlsx)",
            data=bytes_data,
            file_name="catalog_scolar_clasa_IX_TH_Turda-v14.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        st.caption("Puteți descărca oricând versiunea actualizată a fișierului Excel pe telefon sau calculator.")
    else:
        st.error("Fișierul nu este disponibil pentru descărcare.")
        
    st.markdown("---")
    st.info("💡 Modificările făcute în aplicație se salvează automat în fișierul Excel.")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "📊 Fișă Elev",
    "📋 Centralizator Clasă",
    "📈 Raport Diriginte"
])

elev_options = [f"{e[0]}. {e[1]} (Matr. {e[2]})" for e in ELEVI]

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
                    st.rerun()
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
                    st.rerun()
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
                    st.rerun()
                elif not found:
                    st.warning(f"Nu s-a găsit nicio absență nemotivată cu data '{target_d}'.")
                wb.close()
            except Exception as ex:
                st.error(f"Eroare: {ex}")

# --- TAB 4: FIȘĂ ELEV ---
with tab4:
    st.subheader("Fișă Elev & Rezumat Individual")
    elev_idx_v = st.selectbox("Alege Elevul:", range(len(ELEVI)), format_func=lambda i: elev_options[i], key="elev_v")
    
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            e_info = ELEVI[elev_idx_v]
            st.markdown(f"### 👤 {e_info[1]} (Matricol {e_info[2]} | RM/PG {e_info[3]})")
            
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
    else:
        st.info("Fișierul Excel nu a fost încărcat încă.")

# --- TAB 5: CENTRALIZATOR CLASĂ ---
with tab5:
    st.subheader("📋 Centralizator Clasă (Toți Elevii)")
    st.write("Aici puteți vedea situația generală a tuturor celor 32 de elevi direct din browser.")
    
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            
            # Preluare din Absențe & Purtare
            ws_abs = wb["Absențe & Purtare"]
            # Preluare din Centralizator Medii
            ws_cent = wb["Centralizator Medii"]
            
            table_data = []
            for idx, e in enumerate(ELEVI):
                r = 9 + idx
                
                # Centralizator Medii columns:
                # col 1: Nr, col 2: Nume, col 3: Matr, col 4: RM/PG, col 5: Media CG, col 6: Media Module, col 7: Media Gen, col 8: Purtare, col 9: Statut
                med_cg = ws_cent.cell(row=r, column=5).value
                med_mod = ws_cent.cell(row=r, column=6).value
                med_gen = ws_cent.cell(row=r, column=7).value
                not_purt = ws_cent.cell(row=r, column=8).value
                statut = ws_cent.cell(row=r, column=9).value
                
                # Absențe & Purtare columns:
                # col 5: Nemotivate, col 6: Motivate, col 7: Total Abs
                abs_nem = ws_abs.cell(row=r, column=5).value
                abs_mot = ws_abs.cell(row=r, column=6).value
                abs_tot = ws_abs.cell(row=r, column=7).value
                
                table_data.append({
                    "Nr.": e[0],
                    "Nume și Prenume": e[1],
                    "Matricol": e[2],
                    "Media CG": f"{float(med_cg):.2f}" if isinstance(med_cg, (int, float)) else (str(med_cg) if med_cg else "-"),
                    "Media Module": f"{float(med_mod):.2f}" if isinstance(med_mod, (int, float)) else (str(med_mod) if med_mod else "-"),
                    "Media Generală": f"{float(med_gen):.2f}" if isinstance(med_gen, (int, float)) else (str(med_gen) if med_gen else "-"),
                    "Abs. Nemotivate": abs_nem if abs_nem is not None else 0,
                    "Abs. Motivate": abs_mot if abs_mot is not None else 0,
                    "Total Absențe": abs_tot if abs_tot is not None else 0,
                    "Notă Purtare": not_purt if not_purt is not None else 10,
                    "Statut Școlar": statut if statut else "Înscris"
                })
            
            st.dataframe(table_data, use_container_width=True, height=600)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire centralizator: {ex}")

# --- TAB 6: RAPORT DIRIGINTE ---
with tab6:
    st.subheader("📈 Raport DirigINTE & Statistica Clasei")
    
    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            ws_rap = wb["Raport Diriginte"]
            
            tot_elevi = ws_rap.cell(row=6, column=1).value or 32
            promovabilitate = ws_rap.cell(row=6, column=2).value or "100%"
            med_clasa = ws_rap.cell(row=6, column=3).value or "-"
            med_purtare = ws_rap.cell(row=6, column=4).value or "10"
            tot_abs_clasa = ws_rap.cell(row=6, column=5).value or 0
            
            c1, c2, c3, c4, c5 = st.columns(5)
            c1.metric("Total Elevi", tot_elevi)
            c2.metric("Promovabilitate", f"{promovabilitate}")
            c3.metric("Media Clasei", f"{float(med_clasa):.2f}" if isinstance(med_clasa, (int, float)) else str(med_clasa))
            c4.metric("Media Purtare", f"{float(med_purtare):.2f}" if isinstance(med_purtare, (int, float)) else str(med_purtare))
            c5.metric("Total Absențe Clasă", tot_abs_clasa)
            
            st.markdown("---")
            st.subheader("Distribuția Mediilor & Centralizator Absențe")
            
            dist_data = []
            for r in range(11, 16):
                transa = ws_rap.cell(row=r, column=1).value
                nr_e = ws_rap.cell(row=r, column=2).value
                pondere = ws_rap.cell(row=r, column=3).value
                cat_abs = ws_rap.cell(row=r, column=4).value
                val_abs = ws_rap.cell(row=r, column=5).value
                
                if transa or cat_abs:
                    dist_data.append({
                        "Tranșă Medie Generală": transa or "-",
                        "Nr. Elevi": nr_e if nr_e is not None else 0,
                        "Pondere (%)": f"{float(pondere)*100:.1f}%" if isinstance(pondere, (int, float)) else str(pondere or "-"),
                        "Indicator Absențe / Disciplină": cat_abs or "-",
                        "Valoare Clasă": val_abs if val_abs is not None else 0
                    })
            
            st.dataframe(dist_data, use_container_width=True)
            wb.close()
        except Exception as ex:
            st.error(f"Eroare la citire raport diriginte: {ex}")
