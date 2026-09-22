#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
COLEGIUL 'EMIL NEGRUȚIU' TURDA — INTERFAȚĂ INTUITIVĂ CATALOG ȘCOLAR
Clasa a IX-a TH — Lucrător Hotelier / Turism & Servicii (An școlar 2026-2027)
===============================================================================
Aplicație de birou (GUI Desktop) pentru introducerea rapidă, cronologică și
fără erori a notelor și absențelor în catalogul automatizat Excel.
"""

import os
import sys
import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import openpyxl
from openpyxl.utils import get_column_letter

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

# Mapare structură discipline și module (start_col în v14)
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

class CatalogGUIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Colegiul 'Emil Negruțiu' Turda — Asistent Introducere Catalog IX TH")
        self.geometry("880x720")
        self.minsize(800, 650)
        
        # Stiluri TTK
        self.style = ttk.Style(self)
        self.style.theme_use('clam')
        
        # Culori reprezentative
        self.NAVY = "#1B365D"
        self.BLUE_ACCENT = "#2F5496"
        self.LIGHT_BG = "#F4F6F9"
        
        self.configure(bg=self.LIGHT_BG)
        self.style.configure('TFrame', background=self.LIGHT_BG)
        self.style.configure('TLabelFrame', background=self.LIGHT_BG, font=('Calibri', 10, 'bold'))
        self.style.configure('TLabel', background=self.LIGHT_BG, font=('Calibri', 10))
        self.style.configure('TButton', font=('Calibri', 10, 'bold'), padding=6)
        self.style.configure('Header.TLabel', background=self.NAVY, foreground='white', font=('Calibri', 13, 'bold'), padding=10)
        
        # Cale fișier implicită
        self.filepath_var = tk.StringVar(value="catalog_scolar_clasa_IX_TH_Turda-v14.xlsx")
        
        self._build_ui()
        self._on_category_changed()
        
    def _build_ui(self):
        # 1. Antet Oficial
        header_frame = tk.Frame(self, bg=self.NAVY)
        header_frame.pack(fill=tk.X, side=tk.TOP)
        
        lbl_title = tk.Label(
            header_frame, 
            text="COLEGIUL 'EMIL NEGRUȚIU' TURDA\nAsistent Introducere Note & Absențe — Clasa a IX-a TH (Lucrător Hotelier)", 
            bg=self.NAVY, foreground='white', font=('Calibri', 12, 'bold'), justify=tk.CENTER, pady=8
        )
        lbl_title.pack()
        
        main_container = ttk.Frame(self, padding="12 12 12 12")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # 2. Selectare Fișier Excel
        file_frame = ttk.LabelFrame(main_container, text=" 📂 Fișier Catalog Excel ", padding="8 8 8 8")
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        entry_file = ttk.Entry(file_frame, textvariable=self.filepath_var, font=('Calibri', 10))
        entry_file.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        
        btn_browse = ttk.Button(file_frame, text="Răsfoiește...", command=self._browse_file)
        btn_browse.pack(side=tk.RIGHT)
        
        # 3. Selectare Elev & Materie
        selection_frame = ttk.LabelFrame(main_container, text=" 👤 Selecție Elev și Disciplină ", padding="10 10 10 10")
        selection_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Elev
        ttk.Label(selection_frame, text="Selectează Elevul:").grid(row=0, column=0, sticky=tk.W, pady=4)
        self.combo_elevi = ttk.Combobox(
            selection_frame, 
            values=[f"{e[0]}. {e[1]} (Matr. {e[2]})" for e in ELEVI],
            state="readonly",
            font=('Calibri', 10),
            width=50
        )
        self.combo_elevi.grid(row=0, column=1, columnspan=2, sticky=tk.W, pady=4, padx=(10, 0))
        self.combo_elevi.current(0)
        
        # Categorie
        ttk.Label(selection_frame, text="Categorie:").grid(row=1, column=0, sticky=tk.W, pady=4)
        self.cat_var = tk.StringVar(value="CG")
        rb_cg = ttk.Radiobutton(selection_frame, text="Cultură Generală (14)", variable=self.cat_var, value="CG", command=self._on_category_changed)
        rb_mod = ttk.Radiobutton(selection_frame, text="Module Tehnologice (6)", variable=self.cat_var, value="MOD", command=self._on_category_changed)
        rb_cg.grid(row=1, column=1, sticky=tk.W, padx=(10, 10), pady=4)
        rb_mod.grid(row=1, column=2, sticky=tk.W, pady=4)
        
        # Materie / Modul
        ttk.Label(selection_frame, text="Disciplină / Modul:").grid(row=2, column=0, sticky=tk.W, pady=4)
        self.combo_materii = ttk.Combobox(
            selection_frame,
            state="readonly",
            font=('Calibri', 10),
            width=50
        )
        self.combo_materii.grid(row=2, column=1, columnspan=2, sticky=tk.W, pady=4, padx=(10, 0))
        
        # 4. Tab-uri de Operațiuni (Adăugare Notă / Absență / Motivare)
        ops_frame = ttk.LabelFrame(main_container, text=" 📝 Operațiune de Înregistrare ", padding="10 10 10 10")
        ops_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.notebook = ttk.Notebook(ops_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # --- TAB 1: NOTĂ ---
        tab_nota = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(tab_nota, text="  ➕ Adăugare Notă  ")
        
        ttk.Label(tab_nota, text="Notă (1 - 10):").grid(row=0, column=0, sticky=tk.W, pady=6)
        self.combo_nota_val = ttk.Combobox(tab_nota, values=[str(n) for n in range(10, 0, -1)], width=8, state="readonly")
        self.combo_nota_val.grid(row=0, column=1, sticky=tk.W, padx=(10, 20), pady=6)
        self.combo_nota_val.current(0) # Default 10
        
        ttk.Label(tab_nota, text="Data Notei (DD.MM):").grid(row=0, column=2, sticky=tk.W, pady=6)
        today_str = datetime.datetime.now().strftime("%d.%m")
        self.entry_nota_data = ttk.Entry(tab_nota, width=12, font=('Calibri', 10))
        self.entry_nota_data.insert(0, today_str)
        self.entry_nota_data.grid(row=0, column=3, sticky=tk.W, padx=(10, 0), pady=6)
        
        btn_add_nota = ttk.Button(tab_nota, text="💾 Salvează Nota în Catalog", command=self._save_nota)
        btn_add_nota.grid(row=1, column=0, columnspan=4, pady=(12, 4))
        
        # --- TAB 2: ABSENȚĂ ---
        tab_abs = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(tab_abs, text="  ❌ Adăugare Absență  ")
        
        ttk.Label(tab_abs, text="Data Absenței (DD.MM):").grid(row=0, column=0, sticky=tk.W, pady=6)
        self.entry_abs_data = ttk.Entry(tab_abs, width=12, font=('Calibri', 10))
        self.entry_abs_data.insert(0, today_str)
        self.entry_abs_data.grid(row=0, column=1, sticky=tk.W, padx=(10, 20), pady=6)
        
        ttk.Label(tab_abs, text="Tip Absență:").grid(row=0, column=2, sticky=tk.W, pady=6)
        self.abs_type_var = tk.StringVar(value="NEM")
        rb_nem = ttk.Radiobutton(tab_abs, text="Nemotivată", variable=self.abs_type_var, value="NEM")
        rb_mot = ttk.Radiobutton(tab_abs, text="Motivată (m)", variable=self.abs_type_var, value="MOT")
        rb_nem.grid(row=0, column=3, sticky=tk.W, padx=(5, 5))
        rb_mot.grid(row=0, column=4, sticky=tk.W)
        
        btn_add_abs = ttk.Button(tab_abs, text="💾 Salvează Absența în Catalog", command=self._save_absenta)
        btn_add_abs.grid(row=1, column=0, columnspan=5, pady=(12, 4))
        
        # --- TAB 3: MOTIVARE ---
        tab_mot = ttk.Frame(self.notebook, padding="10 10 10 10")
        self.notebook.add(tab_mot, text="  ✅ Motivare Absență Existentă  ")
        
        ttk.Label(tab_mot, text="Data de motivat (ex: 21.09):").grid(row=0, column=0, sticky=tk.W, pady=6)
        self.entry_mot_data = ttk.Entry(tab_mot, width=12, font=('Calibri', 10))
        self.entry_mot_data.grid(row=0, column=1, sticky=tk.W, padx=(10, 20), pady=6)
        
        btn_mot = ttk.Button(tab_mot, text="✅ Marchează ca Motivată (Adaugă 'm')", command=self._motivate_absenta)
        btn_mot.grid(row=0, column=2, padx=(10, 0), pady=6)
        
        # 5. Jurnal Istoric / Log
        log_frame = ttk.LabelFrame(main_container, text=" 📜 Jurnal Confirmări și Salvări ", padding="8 8 8 8")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, font=('Consolas', 9), bg="#1E1E1E", fg="#D4D4D4")
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        self._log("Sistem inițializat. Gata pentru introducerea datelor în catalog.")

    def _log(self, msg):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{now}] {msg}\n")
        self.log_text.see(tk.END)

    def _browse_file(self):
        f = filedialog.askopenfilename(
            title="Selectează Fișierul Catalog",
            filetypes=[("Fișiere Excel", "*.xlsx"), ("Toate fișierele", "*.*")]
        )
        if f:
            self.filepath_var.set(f)
            self._log(f"Selectat fișier nou: {f}")

    def _on_category_changed(self):
        cat = self.cat_var.get()
        if cat == "CG":
            names = [s[0] for s in DISCIPLINE_CG]
        else:
            names = [s[0] for s in MODULE_TH]
        
        self.combo_materii['values'] = names
        if names:
            self.combo_materii.current(0)

    def _get_target_file(self):
        path = self.filepath_var.get().strip()
        if not os.path.exists(path):
            # Încercăm în artifacts
            alt_path = os.path.join("/workspace/artifacts", path)
            if os.path.exists(alt_path):
                return alt_path
            messagebox.showerror("Eroare Fișier", f"Fișierul nu a fost găsit:\n{path}")
            return None
        return path

    def _save_nota(self):
        filepath = self._get_target_file()
        if not filepath:
            return
            
        elev_idx = self.combo_elevi.current() # 0..31
        elev_info = ELEVI[elev_idx]
        student_row = 9 + elev_idx
        
        cat = self.cat_var.get()
        subject_idx = self.combo_materii.current()
        
        if cat == "CG":
            sheet_name = "Cultură Generală"
            subj_name, start_col = DISCIPLINE_CG[subject_idx]
        else:
            sheet_name = "Module Tehnologice"
            subj_name, start_col = MODULE_TH[subject_idx]
            
        nota_val = int(self.combo_nota_val.get())
        data_val = self.entry_nota_data.get().strip()
        
        if not data_val:
            messagebox.showwarning("Atenție", "Vă rugăm să introduceți data notei!")
            return
            
        try:
            wb = openpyxl.load_workbook(filepath)
            ws = wb[sheet_name]
            
            # Căutăm primul slot liber de notă (N1..N5 -> start_col + 0, +2, +4, +6, +8)
            slot_found = False
            for k in range(5):
                n_col = start_col + (k * 2)
                d_col = n_col + 1
                
                cell_n = ws.cell(row=student_row, column=n_col)
                cell_d = ws.cell(row=student_row, column=d_col)
                
                if cell_n.value is None or str(cell_n.value).strip() == "":
                    cell_n.value = nota_val
                    cell_d.value = str(data_val)
                    cell_d.number_format = '@'
                    slot_found = True
                    slot_num = k + 1
                    break
                    
            if not slot_found:
                messagebox.showerror("Sloturi Pline", f"Elevul {elev_info[1]} are deja 5 note trecute la {subj_name}!")
                wb.close()
                return
                
            wb.save(filepath)
            wb.close()
            
            msg = f"S-a salvat NOTA {nota_val} (Data: {data_val}) -> {elev_info[1]} la '{subj_name}' (Slot N{slot_num})."
            self._log(f"✅ {msg}")
            messagebox.showinfo("Succes", msg)
            
        except Exception as ex:
            messagebox.showerror("Eroare Salvare", f"Nu s-a putut salva în Excel:\n{ex}")
            self._log(f"❌ Eroare la salvare: {ex}")

    def _save_absenta(self):
        filepath = self._get_target_file()
        if not filepath:
            return
            
        elev_idx = self.combo_elevi.current()
        elev_info = ELEVI[elev_idx]
        student_row = 9 + elev_idx
        
        cat = self.cat_var.get()
        subject_idx = self.combo_materii.current()
        
        if cat == "CG":
            sheet_name = "Cultură Generală"
            subj_name, start_col = DISCIPLINE_CG[subject_idx]
        else:
            sheet_name = "Module Tehnologice"
            subj_name, start_col = MODULE_TH[subject_idx]
            
        data_val = self.entry_abs_data.get().strip()
        is_mot = (self.abs_type_var.get() == "MOT")
        
        if not data_val:
            messagebox.showwarning("Atenție", "Vă rugăm să introduceți data absenței!")
            return
            
        abs_str = f"{data_val}m" if is_mot else data_val
        
        try:
            wb = openpyxl.load_workbook(filepath)
            ws = wb[sheet_name]
            
            # Căutăm primul slot liber de absență (A1..A8 -> start_col + 11 .. start_col + 18)
            slot_found = False
            for k in range(8):
                a_col = start_col + 11 + k
                cell_a = ws.cell(row=student_row, column=a_col)
                
                if cell_a.value is None or str(cell_a.value).strip() == "":
                    cell_a.value = abs_str
                    cell_a.number_format = '@'
                    slot_found = True
                    slot_num = k + 1
                    break
                    
            if not slot_found:
                messagebox.showerror("Sloturi Pline", f"Elevul {elev_info[1]} are deja 8 absențe trecute la {subj_name}!")
                wb.close()
                return
                
            wb.save(filepath)
            wb.close()
            
            status_txt = "MOTIVATĂ" if is_mot else "NEMOTIVATĂ"
            msg = f"S-a salvat ABSENȚA {status_txt} '{abs_str}' -> {elev_info[1]} la '{subj_name}' (Slot A{slot_num})."
            self._log(f"✅ {msg}")
            messagebox.showinfo("Succes", msg)
            
        except Exception as ex:
            messagebox.showerror("Eroare Salvare", f"Nu s-a putut salva în Excel:\n{ex}")
            self._log(f"❌ Eroare la salvare: {ex}")

    def _motivate_absenta(self):
        filepath = self._get_target_file()
        if not filepath:
            return
            
        elev_idx = self.combo_elevi.current()
        elev_info = ELEVI[elev_idx]
        student_row = 9 + elev_idx
        
        cat = self.cat_var.get()
        subject_idx = self.combo_materii.current()
        
        if cat == "CG":
            sheet_name = "Cultură Generală"
            subj_name, start_col = DISCIPLINE_CG[subject_idx]
        else:
            sheet_name = "Module Tehnologice"
            subj_name, start_col = MODULE_TH[subject_idx]
            
        target_date = self.entry_mot_data.get().strip()
        if not target_date:
            messagebox.showwarning("Atenție", "Introduceți data absenței pe care doriți să o motivați (ex: 21.09)!")
            return
            
        try:
            wb = openpyxl.load_workbook(filepath)
            ws = wb[sheet_name]
            
            found = False
            for k in range(8):
                a_col = start_col + 11 + k
                cell_a = ws.cell(row=student_row, column=a_col)
                val = str(cell_a.value).strip() if cell_a.value else ""
                
                if val == target_date:
                    cell_a.value = f"{target_date}m"
                    cell_a.number_format = '@'
                    found = True
                    break
                elif val == f"{target_date}m":
                    messagebox.showinfo("Informație", f"Absența din {target_date} este deja motivată!")
                    wb.close()
                    return
                    
            if not found:
                messagebox.showwarning("Negăsit", f"Nu s-a găsit nicio absență nemotivată cu data '{target_date}' la {subj_name} pentru {elev_info[1]}.")
                wb.close()
                return
                
            wb.save(filepath)
            wb.close()
            
            msg = f"Absența din data '{target_date}' a fost MOTIVATĂ ('{target_date}m') pentru {elev_info[1]} la '{subj_name}'."
            self._log(f"✅ {msg}")
            messagebox.showinfo("Succes", msg)
            
        except Exception as ex:
            messagebox.showerror("Eroare Salvare", f"Nu s-a putut salva în Excel:\n{ex}")
            self._log(f"❌ Eroare la salvare: {ex}")

if __name__ == "__main__":
    app = CatalogGUIApp()
    app.mainloop()
