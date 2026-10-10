import datetime
import hashlib
import re
from zoneinfo import ZoneInfo
import os
import openpyxl
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import streamlit as st
import urllib.request
import urllib.parse
import json
import base64
import fontpkg
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import shutil
import time
import copy
from document_storage import DocumentStorageError, build_document_record, get_parent_excuse_for_document, list_student_documents, normalize_student_key, parent_excuse_usage, read_registered_document, read_registered_document_by_student_key, store_new_document
from conduct_storage import ConductStorageError, conduct_grades_for_student, load_conduct_registry, save_conduct_grade
from annual_closure_engine import AnnualClosureError, CLJ_2026_2027_COURSE_INTERVALS, IX_TH_2026_2027_CLASS_CDEOS_HOURS, build_annual_closure_snapshot, build_student_subject_inputs, preview_annual_closure
from annual_closure_storage import AnnualClosureStorageError, load_private_annual_closure_snapshots, persist_private_annual_closure_batch_once
from official_catalog_pdf import (
    OfficialCatalogError,
    generate_official_catalog_current,
    generate_official_catalog_final,
    official_catalog_state_from_records,
)
from final_status_storage import FinalStatusStorageError, load_private_final_status_registry, persist_private_final_status_batch_once
from leave_pass_storage import (
    STATUS_APPROVED as LEAVE_STATUS_APPROVED,
    STATUS_EXPIRED as LEAVE_STATUS_EXPIRED,
    STATUS_PENDING as LEAVE_STATUS_PENDING,
    STATUS_REFUSED as LEAVE_STATUS_REFUSED,
    approve_leave_request,
    get_leave_request_for_day,
    load_leave_pass_registry,
    read_approved_leave_pass,
    refuse_leave_request,
)
from notification_storage import RECIPIENT_PARENT, RECIPIENT_TEACHER, ensure_notification, list_notifications, mark_notification_read, reconcile_teacher_inbox
from whatsapp_delivery import normalize_ro_phone, whatsapp_link
from nelutu_mascot import render_nelutu_corner, render_nelutu_corner_nudge
from openpyxl.formula.translate import Translator
from catalog_photo_import import (
    PhotoImportError, ImportProposal, safe_zip_images, pair_catalog_images,
    analyze_pair_with_vision, compare_with_workbook, apply_confirmed_import,
)


GESTIUNE_FILE = "gestiune_elevi.json"



def _validate_gestiune_data(data):
    if not isinstance(data, list) or not data:
        raise ValueError("Fișierul de gestiune este gol sau invalid.")

    for row in data:
        if not isinstance(row, dict) or not {"id", "rand_excel", "matricol", "pin"}.issubset(row):
            raise ValueError("Structură invalidă în fișierul de gestiune.")


def sync_gestiune_from_private_repo():
    token = os.environ.get("GITHUB_TOKEN") or ""

    try:
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or str(st.secrets["GITHUB_TOKEN"])
    except Exception:
        pass

    if not token:
        return False

    url = (
        "https://api.github.com/repos/"
        "profudeconta-sketch/catalog-online-date-private/"
        f"contents/{GESTIUNE_FILE}?ref=main"
    )

    headers = {
        "User-Agent": "StreamlitApp",
        "Cache-Control": "no-cache",
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github.v3+json",
    }

    temp_file = GESTIUNE_FILE + ".download.tmp"

    try:
        req = urllib.request.Request(url, headers=headers)

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

        with open(temp_file, "r", encoding="utf-8") as f:
            downloaded_data = json.load(f)

        _validate_gestiune_data(downloaded_data)

        if os.path.exists(GESTIUNE_FILE):
            shutil.copy2(
                GESTIUNE_FILE,
                GESTIUNE_FILE + ".bak"
            )

        os.replace(temp_file, GESTIUNE_FILE)
        return True

    except Exception:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass

        return False


def sync_conduct_registry_from_private_repo():
    filename = "registru_purtare_2026_2027.json"
    token = os.environ.get("GITHUB_TOKEN") or ""
    try:
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or str(st.secrets["GITHUB_TOKEN"])
    except Exception:
        pass
    if not token:
        return False
    url = (
        "https://api.github.com/repos/profudeconta-sketch/"
        f"catalog-online-date-private/contents/{filename}?ref=main"
    )
    try:
        req = urllib.request.Request(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github.v3+json",
                "User-Agent": "StreamlitApp",
                "Cache-Control": "no-cache",
            },
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        content = base64.b64decode(payload.get("content", ""))
        if not content:
            return False
        temp = filename + ".download.tmp"
        with open(temp, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        with open(temp, "r", encoding="utf-8") as handle:
            candidate = json.load(handle)
        if (
            candidate.get("schema_version") != 1
            or candidate.get("school_year") != "2026-2027"
            or not isinstance(candidate.get("grades"), list)
        ):
            raise ValueError("Registru purtare invalid.")
        if os.path.exists(filename):
            shutil.copy2(filename, filename + ".bak")
        os.replace(temp, filename)
        return True
    except Exception:
        try:
            if os.path.exists(filename + ".download.tmp"):
                os.remove(filename + ".download.tmp")
        except Exception:
            pass
        return False


def load_gestiune_data():
    if not sync_gestiune_from_private_repo():
        st.error(
            "Datele elevilor nu au putut fi sincronizate și validate din sursa privată. "
            "Aplicația a fost oprită pentru protejarea integrității datelor."
        )
        st.stop()

    if os.path.exists(GESTIUNE_FILE):
        try:
            with open(
                GESTIUNE_FILE,
                "r",
                encoding="utf-8"
            ) as f:
                data = json.load(f)

            _validate_gestiune_data(data)
            return data

        except Exception:
            pass

    st.error(
        "Datele elevilor nu au putut fi încărcate din sursa privată. "
        "Aplicația a fost oprită pentru protejarea integrității datelor."
    )
    st.stop()

def save_gestiune_data(data):    
    temp_file = GESTIUNE_FILE + ".tmp"
    backup_file = GESTIUNE_FILE + ".bak"
    try:
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
        with open(temp_file, "r", encoding="utf-8") as f:
            if json.load(f) != data:
                raise ValueError("Verificarea fișierului temporar a eșuat.")
        if os.path.exists(GESTIUNE_FILE):
            shutil.copy2(GESTIUNE_FILE, backup_file)
        os.replace(temp_file, GESTIUNE_FILE)
        if not push_to_github(GESTIUNE_FILE):
            st.warning("Datele au fost salvate local, dar sincronizarea GitHub nu a fost confirmată.")
            return False
        return True
    except Exception as ex:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass
        st.error(f"Eroare la salvarea datelor elevilor: {ex}")
        return False

def _parent_phones_for_rm(student_rm_pg):
    target=str(student_rm_pg or "").strip().casefold()
    phones=[]
    for row in load_gestiune_data():
        if str(row.get("matricol","")).strip().casefold()!=target:
            continue
        for field in ("telefon_mama","telefon_tata"):
            value=str(row.get(field,"")).strip()
            if value:
                try: phones.append(normalize_ro_phone(value))
                except ValueError: pass
        break
    return list(dict.fromkeys(phones))

def _parent_whatsapp_links(student_rm_pg, message):
    """Construiește linkuri WhatsApp gratuite; nu trimite automat și nu confirmă livrarea."""
    links=[]
    for phone in _parent_phones_for_rm(student_rm_pg):
        try:
            links.append(whatsapp_link(phone,message))
        except ValueError:
            pass
    return list(dict.fromkeys(links))

def _register_parent_alert(student_rm_pg, **kwargs):
    """Înregistrează notificarea internă; WhatsApp rămâne doar opțiune manuală gratuită."""
    try:
        event,created=ensure_notification(recipient=RECIPIENT_PARENT,**kwargs)
        links=_parent_whatsapp_links(student_rm_pg,event.get("message") or "Catalog Online: aveți o actualizare nouă în Portalul Părinților.")
        return event,created,links
    except (DocumentStorageError,ValueError):
        return None,False,[]

def get_current_elevi_and_pins():
    g_data = load_gestiune_data()
    elevi_list = []
    pins_list = []
    for d in g_data:
        nume_full = d.get("nume_complet", f"{d.get('nume','')} {d.get('initiala','')} {d.get('prenume','')}".strip())
        nume_full = " ".join(nume_full.split())
        pin_str = str(d.get("pin", "1234"))
        elevi_list.append((
            d["id"],
            nume_full,
            d["rand_excel"],
            d["matricol"],
            pin_str
        ))
        pins_list.append(pin_str)
    return elevi_list, pins_list

def resolve_student_row(wb, elev_info):
    """Identifică sigur rândul elevului în catalogul v15 și validează identitatea între foi."""
    required_sheets = ("Cultură Generală", "Module Tehnologice", "Absențe & Purtare", "Centralizator Medii")
    for sheet_name in required_sheets:
        if sheet_name not in wb.sheetnames:
            raise RuntimeError(f"Lipsește foaia obligatorie: {sheet_name}")

    expected_key = str(elev_info[3]).strip()
    if not expected_key:
        raise RuntimeError("Elevul selectat nu are identificator de catalog valid.")

    resolved_rows = []
    for sheet_name in required_sheets:
        ws = wb[sheet_name]
        matches = []
        for row in range(9, ws.max_row + 1):
            actual_key = str(ws.cell(row=row, column=4).value or "").strip()
            if actual_key == expected_key:
                matches.append(row)
        if len(matches) != 1:
            raise RuntimeError(
                f"Identitatea elevului nu poate fi stabilită univoc în foaia {sheet_name}. "
                "Operația a fost oprită fără salvare."
            )
        resolved_rows.append(matches[0])

    if len(set(resolved_rows)) != 1:
        raise RuntimeError(
            "Identitatea elevului nu corespunde pe același rând în toate foile catalogului. "
            "Operația a fost oprită fără salvare."
        )
    return resolved_rows[0]

def validate_student_identity_consistency(wb, gest_data):
    """Validează corespondența Nume / NR. MATR. / RM/PG între JSON și catalogul v15."""
    sheets = ("Cultură Generală", "Module Tehnologice", "Absențe & Purtare", "Centralizator Medii")
    for sheet_name in sheets:
        if sheet_name not in wb.sheetnames:
            raise RuntimeError(f"Lipsește foaia obligatorie: {sheet_name}")

    seen_nr = set()
    seen_rm = set()
    for d in gest_data:
        expected_name = " ".join(str(d.get("nume_complet", "")).split())
        expected_nr = str(d.get("rand_excel", "")).strip()
        expected_rm = str(d.get("matricol", "")).strip()
        if not expected_name or not expected_nr or not expected_rm:
            raise RuntimeError("Există un elev cu identitate structurală incompletă.")
        if expected_nr in seen_nr or expected_rm.lower() in seen_rm:
            raise RuntimeError("NR. MATR. sau RM/PG nu este unic în datele elevilor.")
        seen_nr.add(expected_nr)
        seen_rm.add(expected_rm.lower())

        resolved_rows = []
        for sheet_name in sheets:
            ws = wb[sheet_name]
            matches = [
                row for row in range(9, ws.max_row + 1)
                if str(ws.cell(row=row, column=4).value or "").strip().lower() == expected_rm.lower()
            ]
            if len(matches) != 1:
                raise RuntimeError(f"RM/PG {expected_rm} nu este unic în {sheet_name}.")
            row = matches[0]
            actual_name = " ".join(str(ws.cell(row=row, column=2).value or "").split())
            actual_nr = str(ws.cell(row=row, column=3).value or "").strip()
            if actual_name != expected_name or actual_nr != expected_nr:
                raise RuntimeError(f"Identitatea cu RM/PG {expected_rm} diferă în {sheet_name}.")
            resolved_rows.append(row)
        if len(set(resolved_rows)) != 1:
            raise RuntimeError(f"RM/PG {expected_rm} nu este pe același rând în toate foile.")
    return True


def prepare_student_identity_edit(file_path, old_elev_info, new_name, new_nr_matr, new_rm_pg):
    """Pregătește local editarea identității elevului și păstrează backup-ul Excel."""
    backup_file = file_path + ".identity.bak"
    wb = None
    try:
        shutil.copy2(file_path, backup_file)
        wb = openpyxl.load_workbook(file_path)
        student_row = resolve_student_row(wb, old_elev_info)
        sheets = ("Cultură Generală", "Module Tehnologice", "Absențe & Purtare", "Centralizator Medii")

        new_name = " ".join(str(new_name).split())
        new_nr_matr = str(new_nr_matr).strip()
        new_rm_pg = str(new_rm_pg).strip()
        if not new_name or not new_nr_matr or not new_rm_pg:
            raise RuntimeError("Numele, NR. MATR. și RM/PG sunt obligatorii.")

        for sheet_name in sheets:
            ws = wb[sheet_name]
            for row in range(9, ws.max_row + 1):
                if row == student_row:
                    continue
                nr_value = str(ws.cell(row=row, column=3).value or "").strip()
                rm_value = str(ws.cell(row=row, column=4).value or "").strip()
                if nr_value == new_nr_matr:
                    raise RuntimeError("NR. MATR. este deja atribuit altui elev.")
                if rm_value.lower() == new_rm_pg.lower():
                    raise RuntimeError("RM/PG este deja atribuit altui elev.")

        for sheet_name in sheets:
            ws = wb[sheet_name]
            ws.cell(row=student_row, column=2).value = new_name
            ws.cell(row=student_row, column=3).value = new_nr_matr
            ws.cell(row=student_row, column=4).value = new_rm_pg

        wb.save(file_path)
        wb.close()
        wb = None
        _validate_excel_catalog(file_path)
        return backup_file
    except Exception:
        try:
            if wb is not None:
                wb.close()
        except Exception:
            pass
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, file_path)
        raise



def prepare_student_addition(file_path, gest_data, new_name, new_nr_matr, new_rm_pg):
    """Pregătește local un rând nou de elev în catalogul v15, cu backup și validare fail-closed."""
    backup_file = file_path + ".student-add.bak"
    wb = None
    try:
        shutil.copy2(file_path, backup_file)
        wb = openpyxl.load_workbook(file_path)
        validate_student_identity_consistency(wb, gest_data)

        sheets = ("Cultură Generală", "Module Tehnologice", "Absențe & Purtare", "Centralizator Medii")
        new_name = " ".join(str(new_name).split())
        new_nr_matr = str(new_nr_matr).strip()
        new_rm_pg = str(new_rm_pg).strip()
        if not new_name or not new_nr_matr or not new_rm_pg:
            raise RuntimeError("Numele, NR. MATR. și RM/PG sunt obligatorii.")

        existing_rows = []
        for d in gest_data:
            elev_info = (
                d.get("id"),
                d.get("nume_complet", ""),
                d.get("rand_excel", ""),
                d.get("matricol", ""),
                str(d.get("pin", "")),
            )
            existing_rows.append(resolve_student_row(wb, elev_info))

        if not existing_rows:
            raise RuntimeError("Catalogul nu conține elevi existenți care să poată servi drept model.")
        if sorted(existing_rows) != list(range(9, 9 + len(existing_rows))):
            raise RuntimeError("Rândurile elevilor existenți nu sunt continue; adăugarea a fost blocată.")

        source_row = max(existing_rows)
        new_row = source_row + 1

        for sheet_name in sheets:
            ws = wb[sheet_name]
            for row in range(9, ws.max_row + 1):
                nr_value = str(ws.cell(row=row, column=3).value or "").strip()
                rm_value = str(ws.cell(row=row, column=4).value or "").strip()
                if nr_value == new_nr_matr:
                    raise RuntimeError(f"NR. MATR. este deja folosit în {sheet_name}.")
                if rm_value.lower() == new_rm_pg.lower():
                    raise RuntimeError(f"RM/PG este deja folosit în {sheet_name}.")

        # Foile de note și centralizatorul folosesc rândul imediat următor,
        # fără inserare globală și fără deplasarea elevilor existenți.
        for sheet_name in ("Cultură Generală", "Module Tehnologice", "Centralizator Medii"):
            ws = wb[sheet_name]
            if any(str(ws.cell(new_row, c).value or "").strip() for c in (2, 3, 4)):
                raise RuntimeError(f"Rândul {new_row} nu este liber în {sheet_name}.")

            ws.row_dimensions[new_row].height = ws.row_dimensions[source_row].height
            for col in range(1, ws.max_column + 1):
                src = ws.cell(source_row, col)
                dst = ws.cell(new_row, col)
                dst._style = copy.copy(src._style)
                if src.has_style:
                    dst.font = copy.copy(src.font)
                    dst.fill = copy.copy(src.fill)
                    dst.border = copy.copy(src.border)
                    dst.alignment = copy.copy(src.alignment)
                    dst.protection = copy.copy(src.protection)
                if isinstance(src.value, str) and src.value.startswith("="):
                    dst.value = Translator(src.value, origin=src.coordinate).translate_formula(dst.coordinate)
                else:
                    dst.value = None

            ws.cell(new_row, 1).value = len(existing_rows) + 1
            ws.cell(new_row, 2).value = new_name
            ws.cell(new_row, 3).value = new_nr_matr
            ws.cell(new_row, 4).value = new_rm_pg

        # În foaia de absențe, rândul următor este TOTAL ABSENȚE CLASĂ.
        ws = wb["Absențe & Purtare"]
        total_label = str(ws.cell(new_row, 1).value or "").strip().upper()
        if total_label != "TOTAL ABSENȚE CLASĂ":
            raise RuntimeError(
                f"Structura foii Absențe & Purtare este neașteptată la rândul {new_row}; "
                "adăugarea a fost blocată."
            )

        total_row = new_row + 1
        total_values = [ws.cell(new_row, c).value for c in range(1, ws.max_column + 1)]
        total_styles = [copy.copy(ws.cell(new_row, c)._style) for c in range(1, ws.max_column + 1)]
        total_height = ws.row_dimensions[new_row].height

        merge_to_move = None
        for merged in list(ws.merged_cells.ranges):
            if merged.min_row == new_row and merged.max_row == new_row and merged.min_col == 1 and merged.max_col == 4:
                merge_to_move = str(merged)
                break
        if merge_to_move:
            ws.unmerge_cells(merge_to_move)

        for c in range(1, ws.max_column + 1):
            dst = ws.cell(total_row, c)
            dst._style = total_styles[c - 1]
            dst.value = total_values[c - 1]
        ws.row_dimensions[total_row].height = total_height
        ws.merge_cells(start_row=total_row, start_column=1, end_row=total_row, end_column=4)
        ws.cell(total_row, 1).value = "TOTAL ABSENȚE CLASĂ"
        for c in (5, 6, 7):
            letter = get_column_letter(c)
            ws.cell(total_row, c).value = f"=SUM({letter}9:{letter}{new_row})"

        ws.row_dimensions[new_row].height = ws.row_dimensions[source_row].height
        for col in range(1, ws.max_column + 1):
            src = ws.cell(source_row, col)
            dst = ws.cell(new_row, col)
            dst._style = copy.copy(src._style)
            if isinstance(src.value, str) and src.value.startswith("="):
                dst.value = Translator(src.value, origin=src.coordinate).translate_formula(dst.coordinate)
            else:
                dst.value = None

        ws.cell(new_row, 1).value = len(existing_rows) + 1
        ws.cell(new_row, 2).value = new_name
        ws.cell(new_row, 3).value = new_nr_matr
        ws.cell(new_row, 4).value = new_rm_pg

        wb.save(file_path)
        wb.close()
        wb = None
        _validate_excel_catalog(file_path)
        return backup_file, new_row
    except Exception:
        try:
            if wb is not None:
                wb.close()
        except Exception:
            pass
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, file_path)
        raise



def prepare_last_student_cancellation(file_path, gest_data, student_index):
    """Anulează local numai ultimul elev adăugat, dacă nu are activitate școlară."""
    backup_file = file_path + ".student-cancel.bak"
    wb = None
    try:
        if not gest_data or student_index != len(gest_data) - 1:
            raise RuntimeError("Poate fi anulată numai ultima înregistrare de elev.")
        student = gest_data[student_index]
        if str(student.get("status_scolar", "ACTIV")).upper() != "ACTIV":
            raise RuntimeError("Un elev transferat/retras nu poate fi șters; istoricul lui trebuie păstrat.")

        shutil.copy2(file_path, backup_file)
        wb = openpyxl.load_workbook(file_path, data_only=False)
        validate_student_identity_consistency(wb, gest_data)
        elev_info = (
            student.get("id"), student.get("nume_complet", ""), student.get("rand_excel", ""),
            student.get("matricol", ""), str(student.get("pin", ""))
        )
        row = resolve_student_row(wb, elev_info)
        if row != 8 + len(gest_data):
            raise RuntimeError("Elevul selectat nu este pe ultimul rând structural al catalogului.")

        # Note/absențe: formulele sunt structurale; orice valoare neidentitară introdusă manual blochează anularea.
        for sheet_name in ("Cultură Generală", "Module Tehnologice"):
            ws = wb[sheet_name]
            for col in range(5, ws.max_column + 1):
                value = ws.cell(row, col).value
                if value not in (None, "") and not (isinstance(value, str) and value.startswith("=")):
                    raise RuntimeError(f"Elevul are deja date școlare în {sheet_name}; anularea este interzisă.")

        ws_abs = wb["Absențe & Purtare"]
        for col in range(5, ws_abs.max_column + 1):
            value = ws_abs.cell(row, col).value
            if value not in (None, "") and not (isinstance(value, str) and value.startswith("=")):
                raise RuntimeError("Elevul are deja date în Absențe & Purtare; anularea este interzisă.")

        total_row = row + 1
        if str(ws_abs.cell(total_row, 1).value or "").strip().upper() != "TOTAL ABSENȚE CLASĂ":
            raise RuntimeError("Rândul TOTAL ABSENȚE CLASĂ nu este în poziția așteptată.")

        # Curăță ultimul rând din foile fără TOTAL; nu deplasează elevii existenți.
        for sheet_name in ("Cultură Generală", "Module Tehnologice", "Centralizator Medii"):
            ws = wb[sheet_name]
            for col in range(1, ws.max_column + 1):
                ws.cell(row, col).value = None

        # În Absențe, mută TOTAL înapoi pe rândul eliberat și curăță vechiul total.
        merge_total = None
        for merged in list(ws_abs.merged_cells.ranges):
            if merged.min_row == total_row and merged.max_row == total_row and merged.min_col == 1 and merged.max_col == 4:
                merge_total = str(merged)
                break
        if merge_total:
            ws_abs.unmerge_cells(merge_total)

        total_values = [ws_abs.cell(total_row, c).value for c in range(1, ws_abs.max_column + 1)]
        total_styles = [copy.copy(ws_abs.cell(total_row, c)._style) for c in range(1, ws_abs.max_column + 1)]
        for c in range(1, ws_abs.max_column + 1):
            ws_abs.cell(row, c)._style = total_styles[c - 1]
            ws_abs.cell(row, c).value = total_values[c - 1]
            ws_abs.cell(total_row, c).value = None
        ws_abs.merge_cells(start_row=row, start_column=1, end_row=row, end_column=4)
        ws_abs.cell(row, 1).value = "TOTAL ABSENȚE CLASĂ"
        previous_student_row = row - 1
        for c in (5, 6, 7):
            letter = get_column_letter(c)
            ws_abs.cell(row, c).value = f"=SUM({letter}9:{letter}{previous_student_row})"

        wb.save(file_path)
        wb.close()
        wb = None
        _validate_excel_catalog(file_path)
        return backup_file
    except Exception:
        try:
            if wb is not None:
                wb.close()
        except Exception:
            pass
        if os.path.exists(backup_file):
            shutil.copy2(backup_file, file_path)
        raise


def parse_cnp(cnp_str):
    cnp = str(cnp_str).strip()
    if len(cnp) == 13 and cnp.isdigit():
        s = int(cnp[0])
        yy = int(cnp[1:3])
        mm = int(cnp[3:5])
        dd = int(cnp[5:7])
        
        sex = "Băiat" if s in [1, 3, 5, 7] else "Fată" if s in [2, 4, 6, 8] else "N/A"
        
        year_prefix = 1900
        if s in [3, 4]: year_prefix = 1800
        elif s in [5, 6]: year_prefix = 2000
        
        birth_year = year_prefix + yy
        curr_year = datetime.datetime.now().year
        age = curr_year - birth_year
        
        return {
            "sex": sex,
            "age": age,
            "birth_date": f"{dd:02d}.{mm:02d}.{birth_year}"
        }
    return None

def get_student_sex(st_dict):
    info = parse_cnp(st_dict.get("cnp", ""))
    if info and info["sex"] != "N/A":
        return info["sex"]
    p = st_dict.get("prenume", "").upper()
    if p:
        p_first = p.split()[0]
        if p_first.endswith("A") and p_first not in ["LUCA", "HOREA", "HOMA", "MIRCEA", "COSTICA", "NICOLAE", "TOMA"]:
            return "Fată"
        return "Băiat"
    return "Băiat"

def get_student_age(st_dict):
    info = parse_cnp(st_dict.get("cnp", ""))
    if info:
        return info["age"]
    return 15

def generate_excel_bytes(rows_data, sheet_name="Raport"):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    if not rows_data:
        buffer = io.BytesIO()
        wb.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()
        
    headers = list(rows_data[0].keys())
    ws.append(headers)
    
    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    
    for row_idx, r_dict in enumerate(rows_data, start=2):
        row_vals = [r_dict.get(h, "") for h in headers]
        ws.append(row_vals)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = thin_border
            if isinstance(cell.value, (int, float)):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")
                
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len:
                max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def parse_absence_month(abs_str):
    s = str(abs_str).strip()
    if not s:
        return None, False
    is_mot = False
    if s.endswith('m') or s.endswith('M'):
        is_mot = True
        s = s[:-1].strip()
        
    parts = s.replace('-', '.').replace('/', '.').split('.')
    if len(parts) >= 2:
        try:
            day = int(parts[0])
            m_val = int(parts[1])
            if 1 <= m_val <= 12:
                return m_val, is_mot
        except Exception:
            pass
    return None, is_mot

MONTH_DEFS = [
    (9, "Septembrie 2026"),
    (10, "Octombrie 2026"),
    (11, "Noiembrie 2026"),
    (12, "Decembrie 2026"),
    (1, "Ianuarie 2027"),
    (2, "Februarie 2027"),
    (3, "Martie 2027"),
    (4, "Aprilie 2027"),
    (5, "Mai 2027"),
    (6, "Iunie 2027")
]

def calculate_lunar_student_absences(file_path):
    student_rows = []
    if not os.path.exists(file_path):
        return student_rows
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        
        for idx, e in enumerate(ELEVI):
            s_row = resolve_student_row(wb, e)
            lunar_counts = {m_code: {'nem': 0, 'mot': 0, 'tot': 0} for m_code, _ in MONTH_DEFS}
            
            for _, col in DISCIPLINE_CG:
                for k in range(30):
                    av = ws_cg.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != "":
                        m_code, is_m = parse_absence_month(av)
                        if m_code in lunar_counts:
                            if is_m: lunar_counts[m_code]['mot'] += 1
                            else: lunar_counts[m_code]['nem'] += 1
                            lunar_counts[m_code]['tot'] += 1
                            
            for _, col in MODULE_TH:
                for k in range(30):
                    av = ws_th.cell(row=s_row, column=col + 21 + k).value
                    if av is not None and str(av).strip() != "":
                        m_code, is_m = parse_absence_month(av)
                        if m_code in lunar_counts:
                            if is_m: lunar_counts[m_code]['mot'] += 1
                            else: lunar_counts[m_code]['nem'] += 1
                            lunar_counts[m_code]['tot'] += 1
                            
            row_dict = {
                "Nr.": idx + 1,
                "Nume și Prenume Elev": e[1],
                "Matricol": e[3]
            }
            tot_year_nem = 0
            tot_year_mot = 0
            for m_code, m_name in MONTH_DEFS:
                c = lunar_counts[m_code]
                row_dict[f"{m_name} - Nemotivate"] = c['nem']
                row_dict[f"{m_name} - Motivate"] = c['mot']
                row_dict[f"{m_name} - Total"] = c['tot']
                tot_year_nem += c['nem']
                tot_year_mot += c['mot']
                
            row_dict["TOTAL ANUAL - Nemotivate"] = tot_year_nem
            row_dict["TOTAL ANUAL - Motivate"] = tot_year_mot
            row_dict["TOTAL ANUAL GENERAL"] = tot_year_nem + tot_year_mot
            student_rows.append(row_dict)
            
        class_tot = {"Nr.": "", "Nume și Prenume Elev": "TOTAL GENERAL CLASĂ", "Matricol": "CLASĂ"}
        for k in student_rows[0].keys():
            if k not in ["Nr.", "Nume și Prenume Elev", "Matricol"]:
                class_tot[k] = sum(r[k] for r in student_rows)
        student_rows.append(class_tot)
        wb.close()
    except Exception:
        pass
    return student_rows

def calculate_lunar_subject_absences(file_path):
    sub_rows = []
    if not os.path.exists(file_path):
        return sub_rows
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        ws_cg = wb["Cultură Generală"]
        ws_th = wb["Module Tehnologice"]
        
        for cat_name, ws, sub_list in [("Cultură Generală", ws_cg, DISCIPLINE_CG), ("Module Tehnologice", ws_th, MODULE_TH)]:
            for s_name, col in sub_list:
                lunar_counts = {m_code: {'nem': 0, 'mot': 0, 'tot': 0} for m_code, _ in MONTH_DEFS}
                for idx, e in enumerate(ELEVI):
                    s_row = resolve_student_row(wb, e)
                    for k in range(30):
                        av = ws.cell(row=s_row, column=col + 21 + k).value
                        if av is not None and str(av).strip() != "":
                            m_code, is_m = parse_absence_month(av)
                            if m_code in lunar_counts:
                                if is_m: lunar_counts[m_code]['mot'] += 1
                                else: lunar_counts[m_code]['nem'] += 1
                                lunar_counts[m_code]['tot'] += 1
                                
                row_dict = {
                    "Categorie": cat_name,
                    "Disciplină / Modul": s_name
                }
                tot_year_nem = 0
                tot_year_mot = 0
                for m_code, m_name in MONTH_DEFS:
                    c = lunar_counts[m_code]
                    row_dict[f"{m_name} - Nemotivate Clasă"] = c['nem']
                    row_dict[f"{m_name} - Motivate Clasă"] = c['mot']
                    row_dict[f"{m_name} - Total Clasă"] = c['tot']
                    tot_year_nem += c['nem']
                    tot_year_mot += c['mot']
                    
                row_dict["TOTAL ANUAL - Nemotivate Clasă"] = tot_year_nem
                row_dict["TOTAL ANUAL - Motivate Clasă"] = tot_year_mot
                row_dict["TOTAL ANUAL GENERAL CLASĂ"] = tot_year_nem + tot_year_mot
                sub_rows.append(row_dict)
                
        # Subtotal informativ pentru modulele M1-M6, fara dublare in totalul clasei.
        module_rows = [row for row in sub_rows if row["Categorie"] == "Module Tehnologice"]
        if len(module_rows) == len(MODULE_TH):
            tech_tot = {
                "Categorie": "Module Tehnologice",
                "Disciplină / Modul": "TOTAL ABSENȚE DISCIPLINE TEHNOLOGICE",
            }
            for key in module_rows[0]:
                if key not in ("Categorie", "Disciplină / Modul"):
                    tech_tot[key] = sum(row[key] for row in module_rows)
            sub_rows.append(tech_tot)

        class_tot = {"Categorie": "TOTAL CLASĂ", "Disciplină / Modul": "TOTAL GENERAL CLASĂ"}
        for k in sub_rows[0].keys():
            if k not in ["Categorie", "Disciplină / Modul"]:
                class_tot[k] = sum(r[k] for r in sub_rows if r["Disciplină / Modul"] != "TOTAL ABSENȚE DISCIPLINE TEHNOLOGICE")
        sub_rows.append(class_tot)
        wb.close()
    except Exception:
        pass
    return sub_rows

def generate_excel_registru_elevi(gest_data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Registru Date Elevi"
    
    headers = [
        "Nr.", "Nume Completi Elev", "Nume", "Inițiala Tatălui", "Prenume", "Matricol", "CNP",
        "Telefon Elev", "Localitate", "Județ", "Stradă", "Nr. Stradă", "Bloc", "Apt.",
        "Nume Mamă", "Telefon Mamă", "Mamă Plecată", "Țară Mamă",
        "Nume Tată", "Telefon Tată", "Tată Plecat", "Țară Tată",
        "Naționalitate", "Etnie", "CES", "Orfan", "Plasament", "Bursă Medicală", "Bursă Venit"
    ]
    ws.append(headers)
    
    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    
    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        
    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    
    for idx, d in enumerate(gest_data, start=1):
        nume_full = d.get("nume_complet", f"{d.get('nume','')} {d.get('initiala','')} {d.get('prenume','')}".strip())
        row_vals = [
            idx,
            nume_full,
            d.get("nume", ""),
            d.get("initiala", ""),
            d.get("prenume", ""),
            d.get("matricol", ""),
            f"'{d.get('cnp','')}" if d.get('cnp') else "",
            d.get("telefon", ""),
            d.get("localitate", ""),
            d.get("judet", ""),
            d.get("strada", ""),
            d.get("numar_strada", ""),
            d.get("bloc", ""),
            d.get("apartament", ""),
            d.get("nume_mama", ""),
            d.get("telefon_mama", ""),
            "DA" if d.get("mama_plecata") else "NU",
            d.get("tara_mama", ""),
            d.get("nume_tata", ""),
            d.get("telefon_tata", ""),
            "DA" if d.get("tata_plecat") else "NU",
            d.get("tara_tata", ""),
            d.get("nationalitate", ""),
            d.get("etnie", ""),
            "DA" if d.get("ces") else "NU",
            "DA" if d.get("orfan") else "NU",
            "DA" if d.get("plasament") else "NU",
            "DA" if d.get("bursa_medicala") else "NU",
            "DA" if d.get("bursa_venit") else "NU"
        ]
        ws.append(row_vals)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=idx + 1, column=col_idx)
            cell.border = thin_border
            cell.alignment = Alignment(horizontal="left", vertical="center")
            
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len: max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 10)
        
    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()

def generate_excel_statistica_clasa(gest_data):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Statistica Clasa IX TH"
    
    header_fill = PatternFill(start_color="1A365D", end_color="1A365D", fill_type="solid")
    header_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    section_fill = PatternFill(start_color="2B6CB0", end_color="2B6CB0", fill_type="solid")
    section_font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    thin_border = Border(
        left=Side(style='thin', color='CBD5E0'),
        right=Side(style='thin', color='CBD5E0'),
        top=Side(style='thin', color='CBD5E0'),
        bottom=Side(style='thin', color='CBD5E0')
    )
    
    tot_el = len(gest_data)
    boys = sum(1 for d in gest_data if get_student_sex(d) == "Băiat")
    girls = sum(1 for d in gest_data if get_student_sex(d) == "Fată")
    
    def write_section_header(title, cols_count):
        ws.append([title])
        r = ws.max_row
        ws.merge_cells(start_row=r, start_column=1, end_row=r, end_column=cols_count)
        cell = ws.cell(row=r, column=1)
        cell.fill = section_fill
        cell.font = section_font
        cell.alignment = Alignment(horizontal="left", vertical="center")
        
    def write_table_header(headers):
        ws.append(headers)
        r = ws.max_row
        for c_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=r, column=c_idx)
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal="center", vertical="center")
            
    def style_data_row(row_vals):
        ws.append(row_vals)
        r = ws.max_row
        for c_idx in range(1, len(row_vals) + 1):
            cell = ws.cell(row=r, column=c_idx)
            cell.border = thin_border
            if isinstance(cell.value, (int, float)):
                cell.alignment = Alignment(horizontal="right", vertical="center")
            else:
                cell.alignment = Alignment(horizontal="left", vertical="center")

    write_section_header("1. REPARTIZAREA ELEVILOR PE SEX", 4)
    write_table_header(["Indicator", "Băieți", "Fete", "Total Clasă"])
    style_data_row(["Număr Elevi", boys, girls, tot_el])
    style_data_row(["Pondere (%)", f"{(boys/tot_el*100):.1f}%" if tot_el else "0%", f"{(girls/tot_el*100):.1f}%" if tot_el else "0%", "100%"])
    ws.append([])

    write_section_header("2. GRUPAREA ELEVILOR PE VÂRSTĂ ȘI SEX", 4)
    write_table_header(["Categorie Vârstă", "Băieți", "Fete", "Total Elevi"])
    
    age_groups = {"14 ani": [0,0], "15 ani": [0,0], "16 ani": [0,0], "17+ ani": [0,0]}
    for d in gest_data:
        a = get_student_age(d)
        sex = get_student_sex(d)
        key = "14 ani" if a <= 14 else "15 ani" if a == 15 else "16 ani" if a == 16 else "17+ ani"
        if sex == "Băiat": age_groups[key][0] += 1
        else: age_groups[key][1] += 1
        
    for a_label, (b_cnt, g_tot) in age_groups.items():
        style_data_row([a_label, b_cnt, g_tot, b_cnt + g_tot])
    ws.append([])

    write_section_header("3. ELEVI DE ALTA ETNIE / NAȚIONALITATE", 4)
    write_table_header(["Etnie / Naționalitate", "Băieți", "Fete", "Total Elevi"])
    etn_groups = {}
    for d in gest_data:
        etn = d.get("etnie", "Română").strip() or "Română"
        sex = get_student_sex(d)
        if etn not in etn_groups: etn_groups[etn] = [0, 0]
        if sex == "Băiat": etn_groups[etn][0] += 1
        else: etn_groups[etn][1] += 1
        
    for etn_label, (b_cnt, g_tot) in etn_groups.items():
        style_data_row([etn_label, b_cnt, g_tot, b_cnt + g_tot])
    ws.append([])

    write_section_header("4. BURSE SOCIALE ȘI CERINȚE EDUCAȚIONALE SPECIALE (CES)", 4)
    write_table_header(["Tip Bursă / Situație Școlară", "Băieți", "Fete", "Total Elevi"])
    
    b_med = [sum(1 for d in gest_data if d.get("bursa_medicala") and get_student_sex(d) == "Băiat"), sum(1 for d in gest_data if d.get("bursa_medicala") and get_student_sex(d) == "Fată")]
    b_ven = [sum(1 for d in gest_data if d.get("bursa_venit") and get_student_sex(d) == "Băiat"), sum(1 for d in gest_data if d.get("bursa_venit") and get_student_sex(d) == "Fată")]
    b_ces = [sum(1 for d in gest_data if d.get("ces") and get_student_sex(d) == "Băiat"), sum(1 for d in gest_data if d.get("ces") and get_student_sex(d) == "Fată")]
    
    style_data_row(["Bursă Socială Medicală", b_med[0], b_med[1], sum(b_med)])
    style_data_row(["Bursă Socială pe bază de Venit", b_ven[0], b_ven[1], sum(b_ven)])
    style_data_row(["Elevi cu CES", b_ces[0], b_ces[1], sum(b_ces)])
    ws.append([])

    write_section_header("5. ELEVI ORFANI ȘI ELEVI AFLAȚI ÎN PLASAMENT", 4)
    write_table_header(["Categorie Socială", "Băieți", "Fete", "Total Elevi"])
    orf = [sum(1 for d in gest_data if d.get("orfan") and get_student_sex(d) == "Băiat"), sum(1 for d in gest_data if d.get("orfan") and get_student_sex(d) == "Fată")]
    plas = [sum(1 for d in gest_data if d.get("plasament") and get_student_sex(d) == "Băiat"), sum(1 for d in gest_data if d.get("plasament") and get_student_sex(d) == "Fată")]
    style_data_row(["Elevi Orfani", orf[0], orf[1], sum(orf)])
    style_data_row(["Elevi în Plasament", plas[0], plas[1], sum(plas)])
    ws.append([])

    write_section_header("6. ELEVI CU PĂRINȚI PLECAȚI ÎN STRĂINĂTATE (PE ȚĂRI)", 4)
    write_table_header(["Țară Destinație / Părinte Plecat", "Băieți", "Fete", "Total Elevi"])
    
    tari = {}
    for d in gest_data:
        sex = get_student_sex(d)
        if d.get("mama_plecata") and d.get("tara_mama"):
            tm = d.get("tara_mama").strip()
            key = f"{tm} (Mamă)"
            if key not in tari: tari[key] = [0, 0]
            if sex == "Băiat": tari[key][0] += 1
            else: tari[key][1] += 1
            
        if d.get("tata_plecat") and d.get("tara_tata"):
            tt = d.get("tara_tata").strip()
            key = f"{tt} (Tată)"
            if key not in tari: tari[key] = [0, 0]
            if sex == "Băiat": tari[key][0] += 1
            else: tari[key][1] += 1
            
    if tari:
        for t_label, (b_cnt, g_tot) in tari.items():
            style_data_row([t_label, b_cnt, g_tot, b_cnt + g_tot])
    else:
        style_data_row(["Niciun părinte înregistrat ca plecat", 0, 0, 0])

    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        for cell in col:
            val_str = str(cell.value or "")
            if len(val_str) > max_len: max_len = len(val_str)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    buffer = io.BytesIO()
    wb.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


st.set_page_config(
    page_title="Catalog Școlar Online IX TH",
    page_icon="🏫",
    layout="wide"
)

# --- SINCRONIZARE AUTOMATĂ PE GITHUB VIA API ---
def push_to_github(file_path):
    token = os.environ.get("GITHUB_TOKEN") or ""
    try:
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or st.secrets["GITHUB_TOKEN"]
    except Exception:
        pass
    if not token:
        return False
    try:
        filename = os.path.basename(file_path)
        repo = (
             "profudeconta-sketch/catalog-online-date-private"
              if filename in {
                 GESTIUNE_FILE,
                 "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx",
                 "registru_purtare_2026_2027.json"
              }
              else "profudeconta-sketch/catalog-online"
        )
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
                return True
    except Exception as ex:
        st.warning(f"Sincronizarea GitHub nu a fost confirmată: {ex}")
    return False

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
def get_required_secret(name):
    value = os.environ.get(name, "")
    try:
        if hasattr(st, "secrets") and name in st.secrets:
            value = value or str(st.secrets[name])
    except Exception:
        pass
    if not value:
        st.error(f"Configurare lipsă: secretul {name} nu este definit în Streamlit Secrets.")
        st.stop()
    return value

PAROLA_PROFESORI = get_required_secret("PAROLA_PROFESORI")

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

# Mascota globală: doar vizuală, fără acces la date sau acțiuni.
st.markdown(render_nelutu_corner("idle"), unsafe_allow_html=True)
st.markdown(render_nelutu_corner_nudge(), unsafe_allow_html=True)

# Lista celor 32 de elevi (ID, Nume, RM/PG, Nr. Matr., PIN)


ELEVI, PINS = get_current_elevi_and_pins()

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
            s_row = resolve_student_row(wb, e)
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
        return True
    except Exception as ex:
        try:
            wb.close()
        except Exception:
            pass
        st.error(f"Eroare la recalcularea valorilor din catalog: {ex}")
        return False

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
            s_row = resolve_student_row(wb, e)
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
def _validate_excel_catalog(path):
    required_sheets = {
        "Centralizator Medii",
        "Cultură Generală",
        "Module Tehnologice",
        "Absențe & Purtare",
    }

    wb = openpyxl.load_workbook(
        path,
        read_only=True,
        data_only=False
    )

    try:
        missing = required_sheets.difference(wb.sheetnames)

        if missing:
            raise ValueError(
                "Lipsesc foi obligatorii din catalog: "
                + ", ".join(sorted(missing))
            )
    finally:
        wb.close()


def sync_excel_from_private_repo():
    filename = "catalog_scolar_clasa_IX_TH_Turda-v15.xlsx"

    token = os.environ.get("GITHUB_TOKEN") or ""

    try:
        if hasattr(st, "secrets") and "GITHUB_TOKEN" in st.secrets:
            token = token or str(st.secrets["GITHUB_TOKEN"])
    except Exception:
        pass

    if not token:
        st.error(
            "GITHUB_TOKEN nu este disponibil pentru "
            "sincronizarea catalogului Excel."
        )
        return False

    url = (
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

    temp_file = filename + ".download.xlsx"

    try:
        req = urllib.request.Request(url, headers=headers)

        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                raise RuntimeError(
                    f"GitHub a răspuns cu status {resp.status}."
                )

            payload = json.loads(
                resp.read().decode("utf-8")
            )

        content_b64 = payload.get("content", "")

        if not content_b64:
            raise ValueError(
                "Repository-ul privat nu a returnat "
                "conținutul catalogului Excel."
            )

        content = base64.b64decode(content_b64)

        with open(temp_file, "wb") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())

        _validate_excel_catalog(temp_file)

        if os.path.exists(filename):
            shutil.copy2(
                filename,
                filename + ".bak"
            )

        os.replace(temp_file, filename)

        return True

    except Exception as ex:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass

        st.error(
            "Eroare la sincronizarea catalogului Excel "
            f"din repository-ul privat: {type(ex).__name__}: {ex}"
        )

        return False


if not sync_excel_from_private_repo():
    st.error(
        "Catalogul Excel nu a putut fi sincronizat și validat din sursa privată. "
        "Aplicația a fost oprită pentru protejarea integrității datelor."
    )
    st.stop()

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
selected_file = excel_path

st.title("🏫 Colegiul 'Emil Negruțiu' Turda — Catalog Școlar Online (IX TH Turism)")
st.caption("Sistem Informatizat de Gestionare Note, Absențe și Generare Documente Oficiale")

with st.sidebar:
    st.header("⚙️ Opțiuni Catalog")
    st.caption(f"📄 Fișier Excel Sursă: {os.path.basename(selected_file)}")
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

# Inbox global diriginte: derivat din registrele primare, independent de elevul selectat.
try:
    reconcile_teacher_inbox()
    _student_name_by_key={normalize_student_key(e[3]): e[1] for e in ELEVI}
    _teacher_notifications=list_notifications(recipient=RECIPIENT_TEACHER)
    _teacher_unread=list_notifications(recipient=RECIPIENT_TEACHER,unread_only=True)
    with st.expander(f"🔔 Inbox diriginte — {len(_teacher_unread)} necitite", expanded=bool(_teacher_unread)):
        if not _teacher_notifications:
            st.info("Nu există documente sau solicitări noi de la părinți.")
        for _n in _teacher_notifications[:100]:
            _name=_student_name_by_key.get(_n.get("student_key"),"Elev")
            if _n.get("superseded_at_utc"):
                _status=f"↪ înlocuită de revizia {_n.get('superseded_by_revision','curentă')}"
            else:
                _status="🆕 NECITIT" if not _n.get("read_at_utc") else "✓ văzut"
            st.markdown(f"**{_status} — {_n.get('title','Notificare')}**  \nElev: **{_name}**  \n{_n.get('message','')}")
            if _n.get("superseded_at_utc"):
                st.caption("Această formă rămâne în istoric pentru trasabilitate. Consultați revizia curentă a solicitării.")
                st.divider()
                continue
            _source_type=_n.get("source_type")
            _source_id=_n.get("source_id")
            _student_key=_n.get("student_key")
            if _source_type=="DOCUMENT":
                try:
                    _doc_record,_doc_content=read_registered_document_by_student_key(_student_key,_source_id)
                    _mime=_doc_record.get("mime_type") or "application/octet-stream"
                    _filename=_doc_record.get("original_filename") or f"document_{_source_id}"
                    if st.download_button(
                        "📄 Deschide / descarcă documentul",
                        data=_doc_content,file_name=_filename,mime=_mime,
                        key=f"inbox_open_doc_{_n['id']}",
                    ):
                        mark_notification_read(_n["id"],RECIPIENT_TEACHER)
                        st.rerun()
                except DocumentStorageError as _source_error:
                    st.error(f"Documentul sursă nu poate fi deschis în siguranță: {_source_error}")
            elif _source_type=="INVOIRE":
                try:
                    _leave_registry,_=load_leave_pass_registry()
                    _leave_matches=[
                        item for item in _leave_registry.get("requests",[])
                        if str(item.get("id"))==str(_source_id)
                        and item.get("student_key")==str(_student_key)
                        and str(item.get("revision",1))==str(_n.get("source_revision") or 1)
                    ]
                    if len(_leave_matches)!=1:
                        raise DocumentStorageError("Solicitarea sursă nu există în revizia notificată.")
                    _leave=dict(_leave_matches[0])
                    with st.expander("📋 Deschide solicitarea de învoire"):
                        st.write(f"Data: {_leave.get('request_date','-')}")
                        st.write(f"Ora plecării: {_leave.get('departure_time','-')}")
                        st.write(f"Motiv: {_leave.get('reason_label','-')}")
                        st.write(f"Stare: {_leave.get('status','-')}")
                        if not _n.get("read_at_utc") and st.button(
                            "Confirmă vizualizarea solicitării",
                            key=f"inbox_open_leave_{_n['id']}",
                        ):
                            mark_notification_read(_n["id"],RECIPIENT_TEACHER)
                            st.rerun()
                except DocumentStorageError as _source_error:
                    st.error(f"Solicitarea sursă nu poate fi deschisă în siguranță: {_source_error}")
            else:
                st.warning("Tipul sursei notificării nu este recunoscut; notificarea rămâne necitită.")
            st.divider()
except DocumentStorageError as _inbox_error:
    st.warning(f"Inbox-ul nu a putut fi sincronizat în siguranță: {_inbox_error}")

tab1, tab2, tab3, tab_del, tab4, tab5, tab6, tab7, tab8, tab9, tab_photo = st.tabs([
    "➕ Adăugare Notă", 
    "❌ Adăugare Absență", 
    "✅ Motivare Absență", 
    "🗑️ Ștergere Notă / Absență",
    "📊 Fișă Elev",
    "📈 Centralizator Clasă",
    "📋 Raport Diriginte",
    "👥 Gestiune Elevi",
    "📁 Documente Elevi",
    "🧭 Purtare pe intervale",
    "📷 Import catalog fizic"
])

elev_options = [f"{e[0]}. {e[1]} (Matr. {e[3]})" for e in ELEVI]

# --- IMPORT FOTO CATALOG FIZIC ---
with tab_photo:
    st.subheader("📷 Import note și absențe din catalogul fizic")
    st.caption(
        "Flux protejat: fotografii → analiză → comparație → confirmare → backup → scriere. "
        "Nicio valoare nu este salvată înainte de confirmarea explicită."
    )
    c1, c2 = st.columns(2)
    with c1:
        import_start = st.date_input(
            "Prima zi inclusă", value=datetime.date(2026, 9, 30),
            min_value=datetime.date(2026, 9, 1), max_value=datetime.date(2027, 8, 31),
            key="photo_import_start"
        )
    with c2:
        import_end = st.date_input(
            "Ultima zi inclusă", value=datetime.date(2026, 10, 2),
            min_value=datetime.date(2026, 9, 1), max_value=datetime.date(2027, 8, 31),
            key="photo_import_end"
        )
    if import_start > import_end:
        st.error("Perioada este invalidă: prima zi este după ultima zi.")
    elif (import_end - import_start).days > 6:
        st.warning("Intervalul depășește 7 zile. Pentru verificare mai sigură recomand maximum 7 zile.")

    photo_zip = st.file_uploader(
        "Încarcă arhiva ZIP cu fotografiile în ordine: copertă (opțional), apoi stânga/dreapta pentru fiecare 3 elevi",
        type=["zip"], key="photo_catalog_zip"
    )

    if photo_zip is not None and import_start <= import_end:
        try:
            images = safe_zip_images(photo_zip.getvalue())
            pairs = pair_catalog_images(images, skip_cover=True)
            expected_pairs = (len(ELEVI) + 2) // 3
            if len(pairs) != expected_pairs:
                st.warning(
                    f"Au fost găsite {len(pairs)} perechi pentru {len(ELEVI)} elevi; "
                    f"structura curentă a clasei așteaptă {expected_pairs} perechi."
                )
            else:
                st.success(f"Structură validată: {len(images)} fotografii, {len(pairs)} perechi stânga/dreapta.")

            zoom = st.slider("Zoom pentru verificarea scrisului olograf", 100, 250, 150, 25, key="photo_zoom")
            pair_no = st.selectbox(
                "Pereche pentru verificare vizuală", range(len(pairs)),
                format_func=lambda i: f"Perechea {i+1}: elevii {i*3+1}–{min(i*3+3, len(ELEVI))}",
                key="photo_pair_preview"
            )
            left, right = pairs[pair_no]
            pc1, pc2 = st.columns(2)
            with pc1:
                st.caption(f"Stânga — {left[0]}")
                st.image(left[1], width=int(420 * zoom / 100))
            with pc2:
                st.caption(f"Dreapta — {right[0]}")
                st.image(right[1], width=int(420 * zoom / 100))

            if st.button("🔎 Analizează fotografiile pentru perioada selectată", type="primary", key="photo_analyze"):
                allowed = [name for name, _ in DISCIPLINE_CG] + [name for name, _ in MODULE_TH]
                all_proposals = []
                progress = st.progress(0.0, text="Analizez perechile fără a modifica Excelul...")
                for pair_idx, (left_img, right_img) in enumerate(pairs):
                    start_idx = pair_idx * 3
                    if start_idx >= len(ELEVI):
                        break
                    names = [ELEVI[i][1] for i in range(start_idx, min(start_idx + 3, len(ELEVI)))]
                    local = analyze_pair_with_vision(
                        left_img, right_img, names, import_start, import_end, allowed
                    )
                    for p in local:
                        all_proposals.append(ImportProposal(
                            student_index=start_idx + p.student_index,
                            category=p.category, subject=p.subject, kind=p.kind,
                            value=p.value, date=p.date, motivated=p.motivated,
                            confidence=p.confidence, source_image=p.source_image,
                        ))
                    progress.progress((pair_idx + 1) / len(pairs))
                comparison = compare_with_workbook(
                    selected_file, ELEVI, DISCIPLINE_CG, MODULE_TH,
                    resolve_student_row, all_proposals
                )
                st.session_state["photo_import_comparison"] = comparison
                st.session_state["photo_import_period"] = (str(import_start), str(import_end))
                st.success("Analiza s-a încheiat. Verifică fiecare propunere înainte de salvare.")

            comparison = st.session_state.get("photo_import_comparison")
            if comparison:
                st.markdown("#### Verificare înainte de scriere")
                approved = []
                for i, item in enumerate(comparison):
                    p, status, msg = item
                    elev_name = ELEVI[p.student_index][1]
                    value_text = f"nota {p.value}" if p.kind == "grade" else ("absență motivată" if p.motivated else "absență")
                    label = (
                        f"{status} — {elev_name} — {p.subject} — {value_text} — "
                        f"{p.date} — încredere {p.confidence:.0%}"
                    )
                    if status == "NOU":
                        if st.checkbox(label, value=False, key=f"photo_approve_{i}"):
                            approved.append(item)
                    elif status == "DEJA_EXISTENT":
                        st.info(label + " — nu se dublează.")
                    else:
                        st.warning(label + " — " + msg)

                st.warning(
                    "Butonul de mai jos este singurul pas care poate modifica Excelul. "
                    "Se creează backup înainte de scriere și se reverifică datele."
                )
                if st.button("✅ Confirmă și actualizează catalogul", disabled=not approved, key="photo_apply"):
                    changed, backup = apply_confirmed_import(
                        selected_file, ELEVI, DISCIPLINE_CG, MODULE_TH,
                        resolve_student_row, approved
                    )
                    if changed:
                        if not update_excel_computed_values(selected_file):
                            if backup and os.path.exists(backup):
                                shutil.copy2(backup, selected_file)
                            raise PhotoImportError("Recalcularea post-import a eșuat; backup-ul a fost restaurat.")
                        # Reverificare fail-closed: după scriere, aceleași propuneri trebuie să fie deja existente.
                        post = compare_with_workbook(
                            selected_file, ELEVI, DISCIPLINE_CG, MODULE_TH,
                            resolve_student_row, [x[0] for x in approved]
                        )
                        if any(status != "DEJA_EXISTENT" for _, status, _ in post):
                            if backup and os.path.exists(backup):
                                shutil.copy2(backup, selected_file)
                            raise PhotoImportError("Verificarea post-scriere a eșuat; backup-ul a fost restaurat.")
                        if not push_to_github(selected_file):
                            if backup and os.path.exists(backup):
                                shutil.copy2(backup, selected_file)
                            raise PhotoImportError("Sincronizarea privată nu a fost confirmată; backup-ul local a fost restaurat.")
                        st.session_state.pop("photo_import_comparison", None)
                        st.success(f"Import confirmat: {changed} înregistrări noi. Suprapunerile nu au fost duplicate.")
                        st.rerun()
                    else:
                        st.info("Nu a fost necesară nicio modificare.")
        except PhotoImportError as ex:
            st.error(str(ex))
        except Exception as ex:
            st.error(f"Importul a fost oprit fără scriere: {type(ex).__name__}: {ex}")


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
        s_row = resolve_student_row(wb, ELEVI[student_idx])
        
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
            Paragraph(clean_pdf_text(f"<b>{e[4] if len(e)>4 else '1234'}</b>"), cell_bold)
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

def _normalize_manual_ddmm(value):
    value = str(value or "").strip()
    m = re.fullmatch(r"(\d{1,2})[./-](\d{1,2})", value)
    if not m:
        raise ValueError("Data trebuie introdusă în format DD.MM, de exemplu 02.10.")
    day, month = map(int, m.groups())
    datetime.date(2026, month, day)
    return f"{day:02d}.{month:02d}"

def _restore_manual_backup(path, backup):
    if backup and os.path.exists(backup):
        shutil.copy2(backup, path)

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
            backup = None
            wb = None
            try:
                data_nota = _normalize_manual_ddmm(data_nota)
                backup = selected_file + ".manual.bak"
                shutil.copy2(selected_file, backup)
                wb = openpyxl.load_workbook(selected_file)
                sheet_name = "Cultură Generală" if cat_n == "Cultură Generală" else "Module Tehnologice"
                ws = wb[sheet_name]
                student_row = resolve_student_row(wb, ELEVI[elev_idx_n])
                start_col = DISCIPLINE_CG[mat_idx_n][1] if cat_n == "Cultură Generală" else MODULE_TH[mat_idx_n][1]
                
                slot_found = False
                for k in range(10):
                    n_col = start_col + (k * 2)
                    d_col = n_col + 1
                    cell_n = ws.cell(row=student_row, column=n_col)
                    cell_d = ws.cell(row=student_row, column=d_col)
                    existing_date = str(cell_d.value or "").strip()
                    if existing_date == data_nota:
                        if str(cell_n.value).strip() == str(int(nota_val)):
                            raise ValueError(f"Nota {nota_val} din {data_nota} există deja; nu a fost duplicată.")
                        raise ValueError(f"Există deja nota {cell_n.value} în data {data_nota}; salvarea este blocată.")
                    if cell_n.value is None or str(cell_n.value).strip() == "":
                        cell_n.value = int(nota_val)
                        cell_d.value = str(data_nota)
                        cell_d.number_format = '@'
                        slot_found = True
                        slot_num = k + 1
                        break
                if slot_found:
                    wb.save(selected_file)
                    if not update_excel_computed_values(selected_file):
                        _restore_manual_backup(selected_file, backup)
                        raise RuntimeError("Recalcularea a eșuat; modificarea a fost anulată.")
                    if push_to_github(selected_file):
                        st.success(f"✅ Notă salvată și sincronizată: {nota_val} pe {data_nota} la {materii[mat_idx_n]} (Slot N{slot_num}) pentru {ELEVI[elev_idx_n][1]}")
                        st.rerun()
                    else:
                        _restore_manual_backup(selected_file, backup)
                        raise RuntimeError("Sincronizarea privată a eșuat; modificarea locală a fost anulată.")
                else:
                    st.error("❌ Toate cele 10 sloturi de note sunt pline pentru această disciplină!")
                wb.close()
            except Exception as ex:
                if wb is not None:
                    try: wb.close()
                    except Exception: pass
                _restore_manual_backup(selected_file, backup)
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
            backup = None
            wb = None
            try:
                data_abs = _normalize_manual_ddmm(data_abs)
                backup = selected_file + ".manual.bak"
                shutil.copy2(selected_file, backup)
                wb = openpyxl.load_workbook(selected_file)
                sheet_name = "Cultură Generală" if cat_a == "Cultură Generală" else "Module Tehnologice"
                ws = wb[sheet_name]
                student_row = resolve_student_row(wb, ELEVI[elev_idx_a])
                start_col = DISCIPLINE_CG[mat_idx_a][1] if cat_a == "Cultură Generală" else MODULE_TH[mat_idx_a][1]
                
                abs_val = f"{data_abs.strip()}m" if is_mot else data_abs.strip()
                
                slot_found = False
                for k in range(30):
                    a_col = start_col + 21 + k
                    cell_a = ws.cell(row=student_row, column=a_col)
                    existing_abs = str(cell_a.value or "").strip()
                    if existing_abs.lower().rstrip("m") == data_abs:
                        requested = f"{data_abs}m" if is_mot else data_abs
                        if existing_abs.lower() == requested.lower():
                            raise ValueError(f"Absența din {data_abs} există deja; nu a fost duplicată.")
                        raise ValueError(f"Absența din {data_abs} există deja cu altă stare de motivare; salvarea este blocată.")
                    if cell_a.value is None or str(cell_a.value).strip() == "":
                        cell_a.value = abs_val
                        cell_a.number_format = '@'
                        slot_found = True
                        slot_num = k + 1
                        break
                if slot_found:
                    wb.save(selected_file)
                    if not update_excel_computed_values(selected_file):
                        _restore_manual_backup(selected_file, backup)
                        raise RuntimeError("Recalcularea a eșuat; modificarea a fost anulată.")
                    if push_to_github(selected_file):
                        st.success(f"✅ Absență salvată și sincronizată: '{abs_val}' la {materii_a[mat_idx_a]} (Slot A{slot_num}) pentru {ELEVI[elev_idx_a][1]}")
                        st.rerun()
                    else:
                        _restore_manual_backup(selected_file, backup)
                        raise RuntimeError("Sincronizarea privată a eșuat; modificarea locală a fost anulată.")
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
                student_row = resolve_student_row(wb, ELEVI[elev_idx_m])
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
                    if not update_excel_computed_values(selected_file):
                        st.warning("⚠️ Modificarea a fost salvată, dar recalcularea valorilor derivate nu a fost confirmată.")
                    if push_to_github(selected_file):
                        st.success(f"✅ Absență motivată și sincronizată ('{target_d}m') pentru {ELEVI[elev_idx_m][1]} la {materii_m[mat_idx_m]}")
                        st.rerun()
                    else:
                        st.warning("⚠️ Motivarea a fost salvată local, dar sincronizarea cu repository-ul privat nu a fost confirmată.")
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
                student_row = resolve_student_row(wb, ELEVI[elev_idx_del])
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
                    student_row = resolve_student_row(wb, ELEVI[elev_idx_del])
                    
                    c1, c2 = item_coords[item_selected_idx]
                    ws.cell(row=student_row, column=c1).value = None
                    if c2 is not None:
                        ws.cell(row=student_row, column=c2).value = None
                        
                    wb.save(selected_file)
                    if not update_excel_computed_values(selected_file):
                        st.warning("⚠️ Modificarea a fost salvată, dar recalcularea valorilor derivate nu a fost confirmată.")
                    if push_to_github(selected_file):
                        st.success(f"✅ {existing_items[item_selected_idx]} a fost ștearsă și sincronizată cu succes din catalog!")
                        wb.close()
                        st.rerun()
                    else:
                        st.warning("⚠️ Ștergerea a fost aplicată local, dar sincronizarea cu repository-ul privat nu a fost confirmată.")
                        wb.close()
                except Exception as ex:
                    st.error(f"Eroare la ștergere: {ex}")
        else:
            st.info(f"ℹ️ Nu există nicio {tip_del.lower()} înregistrată pentru elevul selectat la {materii_del[mat_idx_del]}.")

def generate_parent_access_pdf(elev_idx, file_path):
    """Generează în memorie fișa individuală de acces pentru părintele/reprezentantul legal."""
    elev_info = ELEVI[elev_idx]
    wb = openpyxl.load_workbook(file_path, data_only=True)
    try:
        resolve_student_row(wb, elev_info)
    finally:
        wb.close()

    student_name = str(elev_info[1]).strip()
    nr_matr = str(elev_info[2]).strip()
    rm_pg = str(elev_info[3]).strip()
    pin = str(elev_info[4]).strip() if len(elev_info) > 4 else ""
    if not student_name or not nr_matr or not rm_pg or not pin:
        raise RuntimeError("Datele de acces ale elevului sunt incomplete. PDF-ul nu a fost generat.")

    portal_url = "https://catalog-online-5482kppsbvvl6nffpe332g.streamlit.app/"
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=32,
        bottomMargin=32,
        invariant=1,
    )
    try:
        font_path = str(fontpkg.path("Noto Sans"))
        if "ParentAccessNoto" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("ParentAccessNoto", font_path))
        if "ParentAccessNotoBold" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("ParentAccessNotoBold", font_path))
        pdfmetrics.registerFontFamily(
            "ParentAccessNoto",
            normal="ParentAccessNoto",
            bold="ParentAccessNotoBold",
            italic="ParentAccessNoto",
            boldItalic="ParentAccessNotoBold",
        )
    except Exception as ex:
        raise RuntimeError("Fontul Unicode necesar pentru fișa de acces nu este disponibil.") from ex

    styles = getSampleStyleSheet()
    body = ParagraphStyle(
        "AccessBody",
        parent=styles["BodyText"],
        fontName="ParentAccessNoto",
        fontSize=10,
        leading=14,
        spaceAfter=8,
    )
    title = ParagraphStyle(
        "AccessTitle",
        parent=styles["Heading2"],
        fontName="ParentAccessNotoBold",
        fontSize=14,
        leading=18,
        alignment=1,
        spaceAfter=14,
    )
    centered = ParagraphStyle(
        "AccessCentered",
        parent=body,
        alignment=1,
    )

    story = [
        Paragraph("COLEGIUL „EMIL NEGRUȚIU” TURDA", centered),
        Paragraph("AN ȘCOLAR 2026–2027 | CLASA a IX-a TH (TURISM ȘI ALIMENTAȚIE)", centered),
        Paragraph("Prof. Diriginte: Prof. Ec. Gherman Octavian-Theodor", centered),
        Spacer(1, 10),
        Paragraph("BILET INDIVIDUAL DE ACCES — PORTAL PĂRINȚI", title),
        Paragraph(f"<b>ELEV / ELEVĂ:</b> {student_name}", body),
        Paragraph(f"<b>NUMĂR MATRICOL (UTILIZATOR):</b> {rm_pg} (sau numărul simplu: {nr_matr})", body),
        Paragraph(f"<b>COD PIN CONFIDENȚIAL (PAROLĂ):</b> {pin}", body),
        Paragraph(f"<b>ADRESĂ WEB PORTAL:</b> {portal_url}", body),
        Spacer(1, 8),
        Paragraph("<b>INSTRUCȚIUNI DE CONECTARE ȘI ADĂUGARE PE ECRANUL TELEFONULUI:</b>", body),
        Paragraph(f"1. <b>Autentificare:</b> Accesați adresa {portal_url} și introduceți Numărul Matricol și Codul PIN de mai sus.", body),
        Paragraph("2. <b>Telefoane Android (Samsung, Xiaomi, Motorola etc.):</b> Deschideți în Google Chrome → apăsați pe cele 3 puncte (dreapta sus) → selectați opțiunea „Adaugă pe ecranul de pornire” (sau „Instalează aplicația”).", body),
        Paragraph("3. <b>Telefoane iPhone (Apple iOS):</b> Deschideți în Safari → apăsați pe butonul Partajare → selectați opțiunea „Adaugă pe ecranul principal”.", body),
        Spacer(1, 18),
        Paragraph("© Software Creat și Deținut de Prof. Ec. Gherman Octavian-Theodor | Protejat de Legea nr. 8/1996 privind drepturile de autor.", centered),
        Paragraph("Comercializarea este interzisă! Produs utilizat gratuit exclusiv de persoanele autorizate de autor.", centered),
    ]
    doc.build(story)
    return buffer.getvalue()


# --- TAB 5: FIȘĂ ELEV ---
with tab4:
    st.subheader("Fișă Elev & Rezumat")
    col_v1, col_v2, col_v3 = st.columns([3, 1, 1])
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
    with col_v3:
        st.write("")
        st.write("")
        try:
            access_pdf_bytes = generate_parent_access_pdf(elev_idx_v, selected_file)
            st.download_button(
                "🔐 Descarcă Fișa de acces pentru părinte",
                data=access_pdf_bytes,
                file_name=f"Fisa_Acces_Parinte_{ELEVI[elev_idx_v][1].replace(' ', '_')}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as ex:
            st.error(f"Eroare fișă acces: {ex}")

    if os.path.exists(selected_file):
        try:
            wb = openpyxl.load_workbook(selected_file, data_only=True)
            e_info = ELEVI[elev_idx_v]
            st.markdown(f"### 👤 {e_info[1]} (Matricol {e_info[3]}) | Cod PIN Părinți: `{e_info[4] if len(e_info)>4 else '1234'}`")
            
            _academic_payload=[]
            for cat_title, sheet_n, sub_list in [("Cultură Generală", "Cultură Generală", DISCIPLINE_CG), ("Module Tehnologice", "Module Tehnologice", MODULE_TH)]:
                st.markdown(f"#### {cat_title}")
                ws = wb[sheet_n]
                s_row = resolve_student_row(wb, ELEVI[elev_idx_v])
                
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
                _academic_payload.extend(rows_data)
            _academic_fingerprint=hashlib.sha256(
                json.dumps(_academic_payload,ensure_ascii=False,sort_keys=True).encode("utf-8")
            ).hexdigest()
            if st.button(
                "📱 Informează părintele despre actualizarea situației școlare",
                type="primary",use_container_width=True,
                key=f"notify_parent_school_state_{e_info[0]}",
            ):
                _event,_created=ensure_notification(
                    recipient=RECIPIENT_PARENT,
                    event_type="SITUATIE_SCOLARA_ACTUALIZATA",
                    source_type="CATALOG",
                    source_id=normalize_student_key(e_info[3]),
                    source_revision=_academic_fingerprint,
                    student_key=normalize_student_key(e_info[3]),
                    title="Situația școlară a fost actualizată",
                    message="Situația școlară din Catalog Online a fost verificată și actualizată. Accesați Portalul Părinților pentru detalii.",
                )
                if _created:
                    _wa_links=_parent_whatsapp_links(e_info[3],_event.get("message") or "")
                    st.success("✅ Informarea a fost înregistrată în Portalul Părinților.")
                    for _idx,_wa in enumerate(_wa_links):
                        st.link_button(f"📲 Deschide WhatsApp pentru părinte {(_idx+1)}",_wa,use_container_width=True)
                else:
                    st.info("ℹ️ Părintele a fost deja informat pentru această versiune a situației școlare.")
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
            col_lun1, col_lun2 = st.columns(2)
            with col_lun1:
                try:
                    lunar_st_rows = calculate_lunar_student_absences(selected_file)
                    if lunar_st_rows:
                        excel_lun_st_bytes = generate_excel_bytes(lunar_st_rows, sheet_name="Absente Lunare Elevi")
                        st.download_button("📊 Descarcă Absențe Lunare pe Elevi (.xlsx)", data=excel_lun_st_bytes, file_name="Absente_Lunare_Elevi_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except Exception as ex:
                    st.error(f"Eroare Excel Absențe Lunare Elevi: {ex}")

            with col_lun2:
                try:
                    lunar_sub_rows = calculate_lunar_subject_absences(selected_file)
                    if lunar_sub_rows:
                        excel_lun_sub_bytes = generate_excel_bytes(lunar_sub_rows, sheet_name="Absente Lunare Discipline")
                        st.download_button("📊 Descarcă Absențe Lunare pe Discipline (.xlsx)", data=excel_lun_sub_bytes, file_name="Absente_Lunare_Discipline_IX_TH.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
                except Exception as ex:
                    st.error(f"Eroare Excel Absențe Lunare Discipline: {ex}")

            # Raport separat pentru o singura luna a anului scolar configurat.
            st.markdown("#### 📅 Raport absențe pentru o lună selectată")
            month_options = {name.split(" ")[0]: (code, int(name.split(" ")[1])) for code, name in MONTH_DEFS}
            col_month, col_year = st.columns(2)
            with col_month:
                selected_month_name = st.selectbox("Selectează luna", list(month_options), key="abs_disc_month")
            with col_year:
                selected_report_year = st.selectbox(
                    "Selectează anul",
                    sorted({year for _, year in month_options.values()}),
                    key="abs_disc_year",
                )
            selected_code, expected_year = month_options[selected_month_name]
            valid_month_year = selected_report_year == expected_year
            if not valid_month_year:
                st.info("Luna și anul selectate nu aparțin anului școlar configurat. Selectează o combinație validă.")
            if st.button("📊 Generează raport absențe lunar", key="generate_abs_disc_single_month", disabled=not valid_month_year):
                if valid_month_year:
                    try:
                        monthly_rows = calculate_lunar_subject_absences(selected_file)
                        month_label = f"{selected_month_name} {selected_report_year}"
                        monthly_columns = [
                            "Categorie", "Disciplină / Modul",
                            f"{month_label} - Nemotivate Clasă",
                            f"{month_label} - Motivate Clasă",
                            f"{month_label} - Total Clasă",
                        ]
                        if monthly_rows:
                            report_rows = [{key: row[key] for key in monthly_columns} for row in monthly_rows]
                            st.session_state["abs_disc_monthly_download"] = (
                                generate_excel_bytes(report_rows, sheet_name="Absente Discipline Lunar"),
                                f"Absente_Discipline_{selected_month_name}_{selected_report_year}_IX_TH.xlsx",
                            )
                        else:
                            st.error("Raportul nu a putut fi calculat. Nu a fost generat niciun fișier.")
                    except Exception as ex:
                        st.error(f"Eroare la generarea raportului lunar: {ex}")
            if "abs_disc_monthly_download" in st.session_state:
                monthly_bytes, monthly_filename = st.session_state["abs_disc_monthly_download"]
                st.download_button(
                    "⬇️ Descarcă raportul lunar (.xlsx)",
                    data=monthly_bytes,
                    file_name=monthly_filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

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
                    "COD PIN ACCES PĂRINTE": e[4] if len(e)>4 else "1234"
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
            st.markdown(f"#### 🏆 Clasament Complet Elevi în Funcție de Absențe ({len(ELEVI)} Elevi)")
            
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
with tab7:
    st.subheader("👥 GESTIUNE ELEVI — Date Personale, Părinți & Situații Speciale")
    st.caption("Meniu administrativ pentru introducerea, modificarea și exportul datelor generale ale elevilor din clasă.")
    
    gest_data = load_gestiune_data()
    try:
        wb_identity_check = openpyxl.load_workbook(selected_file, data_only=False)
        validate_student_identity_consistency(wb_identity_check, gest_data)
        wb_identity_check.close()
    except Exception as ex:
        try:
            wb_identity_check.close()
        except Exception:
            pass
        st.error(
            "Gestiunea elevilor a fost blocată deoarece JSON și catalogul Excel "
            f"nu sunt perfect aliniate: {ex}"
        )
        st.stop()
    
    op_gest = st.radio(
        "Alegeți operațiunea dorită:",
        ["✏️ Modificare Date Elev Existent", "➕ Adăugare Elev Nou în Clasă", "🔄 Transfer/Retragere Elev", "↩️ Anulare adăugare greșită"],
        horizontal=True,
        key="radio_op_gest"
    )
    
    st.divider()
    
    if op_gest == "✏️ Modificare Date Elev Existent":
        if gest_data:
            sel_st_idx = st.selectbox(
                "Selectează Elevul de Modificat:",
                range(len(gest_data)),
                format_func=lambda i: f"{i+1}. {gest_data[i].get('nume_complet', '')} [{gest_data[i].get('status_scolar', 'ACTIV')}] (RM/PG {gest_data[i].get('matricol', '')})",
                key="sel_st_mod"
            )
            st_curr = gest_data[sel_st_idx]
            
            with st.form("form_edit_elev"):
                st.markdown("#### 1. 🆔 Identificare & Școlar")
                c1, c2, c3 = st.columns(3)
                with c1:
                    e_nume = st.text_input("Nume de Familie:", value=st_curr.get("nume", ""))
                    e_initiala = st.text_input("Inițiala Tatălui:", value=st_curr.get("initiala", ""))
                    e_prenume = st.text_input("Prenume:", value=st_curr.get("prenume", ""))
                with c2:
                    e_nr_matr = st.text_input("NR. MATR.:", value=str(st_curr.get("rand_excel", "")))
                    e_rm_pg = st.text_input("RM/PG:", value=st_curr.get("matricol", ""))
                    e_cnp = st.text_input("Cod Numeric Personal (CNP):", value=st_curr.get("cnp", ""))
                    e_tel = st.text_input("Telefon Elev:", value=st_curr.get("telefon", ""))
                with c3:
                    e_nat = st.text_input("Naționalitate:", value=st_curr.get("nationalitate", "Română"))
                    e_etn = st.text_input("Etnie:", value=st_curr.get("etnie", "Română"))
                    e_pin = st.text_input("PIN Acces Părinte:", value=st_curr.get("pin", "1234"))

                st.markdown("#### 2. 🏠 Adresă Domiciliu")
                a1, a2, a3 = st.columns(3)
                with a1:
                    e_loc = st.text_input("Localitate:", value=st_curr.get("localitate", "Turda"))
                    e_jud = st.text_input("Județ:", value=st_curr.get("judet", "Cluj"))
                with a2:
                    e_str = st.text_input("Stradă:", value=st_curr.get("strada", ""))
                    e_nr = st.text_input("Număr Stradă:", value=st_curr.get("numar_strada", ""))
                with a3:
                    e_bl = st.text_input("Bloc:", value=st_curr.get("bloc", ""))
                    e_apt = st.text_input("Apartament:", value=st_curr.get("apartament", ""))

                st.markdown("#### 3. 👨‍👩‍👧 Informații Părinți & Plecări Străinătate")
                m1, m2 = st.columns(2)
                with m1:
                    e_nume_m = st.text_input("Nume și Prenume Mamă:", value=st_curr.get("nume_mama", ""))
                    e_tel_m = st.text_input("Telefon Mamă:", value=st_curr.get("telefon_mama", ""))
                    e_m_plec = st.checkbox("Mamă plecată în străinătate", value=st_curr.get("mama_plecata", False))
                    e_tara_m = st.text_input("Țara unde este plecată mama:", value=st_curr.get("tara_mama", ""))
                with m2:
                    e_nume_t = st.text_input("Nume și Prenume Tată:", value=st_curr.get("nume_tata", ""))
                    e_tel_t = st.text_input("Telefon Tată:", value=st_curr.get("telefon_tata", ""))
                    e_t_plec = st.checkbox("Tată plecat în străinătate", value=st_curr.get("tata_plecat", False))
                    e_tara_t = st.text_input("Țara unde este plecat tatăl:", value=st_curr.get("tara_tata", ""))

                st.markdown("#### 4. 🩺 Situații Speciale, Burse & CES (Bife)")
                b1, b2, b3 = st.columns(3)
                with b1:
                    e_ces = st.checkbox("Elev cu Cerințe Educaționale Speciale (CES)", value=st_curr.get("ces", False))
                    e_orfan = st.checkbox("Elev Orfan", value=st_curr.get("orfan", False))
                with b2:
                    e_plas = st.checkbox("Elev aflat în Plasament", value=st_curr.get("plasament", False))
                    e_bmed = st.checkbox("Bursă Socială Medicală", value=st_curr.get("bursa_medicala", False))
                with b3:
                    e_bven = st.checkbox("Bursă Socială pe bază de Venit", value=st_curr.get("bursa_venit", False))

                btn_save_edit = st.form_submit_button("💾 Salvează Date Elev", type="primary", use_container_width=True)
                if btn_save_edit:
                    n_full = f"{e_nume.strip()} {e_initiala.strip()} {e_prenume.strip()}".replace("  ", " ").strip()
                    original_student = dict(st_curr)
                    old_elev_info = (
                        st_curr.get("id"),
                        st_curr.get("nume_complet", ""),
                        st_curr.get("rand_excel", ""),
                        st_curr.get("matricol", ""),
                        str(st_curr.get("pin", ""))
                    )
                    try:
                        excel_backup = prepare_student_identity_edit(
                            selected_file, old_elev_info, n_full, e_nr_matr, e_rm_pg
                        )
                    except Exception as ex:
                        st.error(f"Modificarea a fost oprită înainte de salvare: {ex}")
                        st.stop()
                    st_curr.update({
                        "nume": e_nume.strip(),
                        "initiala": e_initiala.strip(),
                        "prenume": e_prenume.strip(),
                        "nume_complet": n_full,
                        "rand_excel": e_nr_matr.strip(),
                        "matricol": e_rm_pg.strip(),
                        "cnp": e_cnp.strip(),
                        "telefon": e_tel.strip(),
                        "nationalitate": e_nat.strip(),
                        "etnie": e_etn.strip(),
                        "pin": e_pin.strip(),
                        "localitate": e_loc.strip(),
                        "judet": e_jud.strip(),
                        "strada": e_str.strip(),
                        "numar_strada": e_nr.strip(),
                        "bloc": e_bl.strip(),
                        "apartament": e_apt.strip(),
                        "nume_mama": e_nume_m.strip(),
                        "telefon_mama": e_tel_m.strip(),
                        "mama_plecata": e_m_plec,
                        "tara_mama": e_tara_m.strip(),
                        "nume_tata": e_nume_t.strip(),
                        "telefon_tata": e_tel_t.strip(),
                        "tata_plecat": e_t_plec,
                        "tara_tata": e_tara_t.strip(),
                        "ces": e_ces,
                        "orfan": e_orfan,
                        "plasament": e_plas,
                        "bursa_medicala": e_bmed,
                        "bursa_venit": e_bven
                    })
                    if not push_to_github(selected_file):
                        shutil.copy2(excel_backup, selected_file)
                        st_curr.clear()
                        st_curr.update(original_student)
                        st.warning("⚠️ Excel nu a fost sincronizat. Copia originală a fost restaurată, iar JSON nu a fost modificat.")
                    elif save_gestiune_data(gest_data):
                        try:
                            os.remove(excel_backup)
                        except Exception:
                            pass
                        st.success(f"✅ Datele elevului {n_full} au fost salvate și sincronizate cu succes!")
                        st.rerun()
                    else:
                        st.error("⚠️ Excel a fost sincronizat, dar JSON nu a fost confirmat. Gestiunea elevilor va fi blocată la următoarea verificare de consistență.")

    elif op_gest == "➕ Adăugare Elev Nou în Clasă":
        with st.form("form_add_elev"):
            st.markdown("#### Introduceți Datele Noului Elev")
            a1, a2, a3 = st.columns(3)
            with a1:
                add_nume = st.text_input("Nume de Familie:")
                add_init = st.text_input("Inițiala Tatălui:")
                add_prenume = st.text_input("Prenume:")
            with a2:
                next_id = max([d.get("id", 0) for d in gest_data] or [0]) + 1
                add_nr_matr = st.text_input("NR. MATR. (atribuit de școală):")
                add_rm_pg = st.text_input("RM/PG (atribuit de școală):")
                add_cnp = st.text_input("CNP (13 cifre):")
                add_tel = st.text_input("Telefon Elev:")
            with a3:
                add_pin = st.text_input("Cod PIN Acces Părinte:", value=str(1000 + next_id))
                add_nat = st.text_input("Naționalitate:", value="Română")
                add_etn = st.text_input("Etnie:", value="Română")
                
            btn_add = st.form_submit_button("➕ Adaugă Elev în Clasă", type="primary", use_container_width=True)
            if btn_add:
                if not add_nume.strip() or not add_prenume.strip() or not add_nr_matr.strip() or not add_rm_pg.strip():
                    st.error("Numele, prenumele, NR. MATR. și RM/PG sunt obligatorii!")
                else:
                    n_full = f"{add_nume.strip()} {add_init.strip()} {add_prenume.strip()}".replace("  ", " ").strip()
                    new_item = {
                        "id": next_id,
                        "rand_excel": add_nr_matr.strip(),
                        "matricol": add_rm_pg.strip(),
                        "pin": add_pin.strip(),
                        "nume": add_nume.strip(),
                        "initiala": add_init.strip(),
                        "prenume": add_prenume.strip(),
                        "nume_complet": n_full,
                        "cnp": add_cnp.strip(),
                        "telefon": add_tel.strip(),
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
                        "nationalitate": add_nat.strip(),
                        "etnie": add_etn.strip(),
                        "ces": False,
                        "orfan": False,
                        "plasament": False,
                        "bursa_medicala": False,
                        "bursa_venit": False,
                        "status_scolar": "ACTIV",
                        "istoric_miscare": [{
                            "tip": "ADAUGAT",
                            "data": datetime.datetime.now(
                                ZoneInfo("Europe/Bucharest")
                            ).strftime("%Y-%m-%d"),
                        }]
                    }
                    excel_backup = None
                    try:
                        excel_backup, _new_row = prepare_student_addition(
                            selected_file,
                            gest_data,
                            n_full,
                            add_nr_matr,
                            add_rm_pg,
                        )
                    except Exception as ex:
                        st.error(f"Adăugarea a fost oprită înainte de salvare: {ex}")
                    else:
                        if not push_to_github(selected_file):
                            shutil.copy2(excel_backup, selected_file)
                            st.warning(
                                "⚠️ Excel nu a fost sincronizat. Copia originală a fost restaurată, "
                                "iar JSON nu a fost modificat."
                            )
                        else:
                            gest_data.append(new_item)
                            if save_gestiune_data(gest_data):
                                try:
                                    os.remove(excel_backup)
                                except Exception:
                                    pass
                                st.success(
                                    f"✅ Elevul {n_full} a fost adăugat în catalog și în gestiune "
                                    "și sincronizarea a fost confirmată."
                                )
                                st.rerun()
                            else:
                                gest_data.pop()
                                st.error(
                                    "⚠️ Excel a fost sincronizat, dar JSON nu a fost confirmat. "
                                    "Gestiunea elevilor va fi blocată la următoarea verificare de consistență."
                                )

    elif op_gest == "🔄 Transfer/Retragere Elev":
        if gest_data:
            sel_status_idx = st.selectbox(
                "Selectează elevul:",
                range(len(gest_data)),
                format_func=lambda i: (
                    f"{i+1}. {gest_data[i].get('nume_complet', '')} "
                    f"[{gest_data[i].get('status_scolar', 'ACTIV')}] "
                    f"(RM/PG {gest_data[i].get('matricol', '')})"
                ),
                key="sel_st_status"
            )
            status_item = gest_data[sel_status_idx]
            status_curent = str(status_item.get("status_scolar", "ACTIV")).upper()
            status_options = ["ACTIV", "TRANSFERAT", "RETRAS"]
            status_index = status_options.index(status_curent) if status_curent in status_options else 0
            status_nou = st.selectbox(
                "Stare școlară:",
                status_options,
                index=status_index,
                key="status_scolar_nou"
            )
            st.info(
                "Schimbarea stării nu șterge elevul și nu modifică notele, mediile, "
                "absențele, NR. MATR. sau RM/PG."
            )
            if st.button("💾 Salvează starea școlară", type="primary", use_container_width=True):
                status_vechi = status_item.get("status_scolar")
                istoric_vechi = list(status_item.get("istoric_miscare", []))
                status_item["status_scolar"] = status_nou
                if status_nou != status_curent:
                    istoric = list(status_item.get("istoric_miscare", []))
                    istoric.append({
                        "tip": status_nou,
                        "data": datetime.datetime.now(
                            ZoneInfo("Europe/Bucharest")
                        ).strftime("%Y-%m-%d"),
                    })
                    status_item["istoric_miscare"] = istoric
                if save_gestiune_data(gest_data):
                    st.success(
                        f"✅ Starea elevului {status_item.get('nume_complet')} a fost actualizată la {status_nou}. "
                        "Istoricul școlar a rămas neschimbat."
                    )
                    st.rerun()
                else:
                    if status_vechi is None:
                        status_item.pop("status_scolar", None)
                    else:
                        status_item["status_scolar"] = status_vechi
                    if istoric_vechi:
                        status_item["istoric_miscare"] = istoric_vechi
                    else:
                        status_item.pop("istoric_miscare", None)
                    st.warning(
                        "⚠️ Modificarea stării nu a fost confirmată în repository-ul privat. "
                        "Datele încărcate în sesiunea curentă au fost restaurate."
                    )

    elif op_gest == "↩️ Anulare adăugare greșită":
        if gest_data:
            last_index = len(gest_data) - 1
            last_item = gest_data[last_index]
            st.warning(
                "Această operație este destinată exclusiv anulării ultimei înregistrări introduse din greșeală. "
                "Este refuzată dacă elevul are deja note, absențe sau alte date școlare."
            )
            st.write(
                f"Ultima înregistrare: **{last_item.get('nume_complet', '')}** "
                f"(NR. MATR. {last_item.get('rand_excel', '')}, RM/PG {last_item.get('matricol', '')})"
            )
            confirm_cancel = st.checkbox(
                "Confirm că această înregistrare a fost introdusă din greșeală și trebuie anulată.",
                key="confirm_cancel_last_student"
            )
            if st.button(
                "↩️ Anulează ultima adăugare",
                type="primary",
                use_container_width=True,
                disabled=not confirm_cancel
            ):
                try:
                    excel_backup = prepare_last_student_cancellation(selected_file, gest_data, last_index)
                except Exception as ex:
                    st.error(f"Anularea a fost oprită fără modificări: {ex}")
                else:
                    if not push_to_github(selected_file):
                        shutil.copy2(excel_backup, selected_file)
                        st.warning(
                            "⚠️ Excel nu a fost sincronizat. Copia originală a fost restaurată, "
                            "iar JSON nu a fost modificat."
                        )
                    else:
                        removed = gest_data.pop()
                        if save_gestiune_data(gest_data):
                            try:
                                os.remove(excel_backup)
                            except Exception:
                                pass
                            st.success(
                                f"✅ Adăugarea greșită pentru {removed.get('nume_complet', '')} a fost anulată "
                                "în catalog și în gestiune."
                            )
                            st.rerun()
                        else:
                            gest_data.append(removed)
                            st.error(
                                "⚠️ Excel a fost sincronizat, dar JSON nu a fost confirmat. "
                                "Gestiunea elevilor va fi blocată la următoarea verificare de consistență."
                            )

    st.divider()
    st.markdown("#### 📊 Export Registru & Statistică Clasă (Excel)")
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        try:
            excel_reg_bytes = generate_excel_registru_elevi(gest_data)
            st.download_button(
                "📊 Descarcă Registru Date Elevi (.xlsx)",
                data=excel_reg_bytes,
                file_name="Registru_Gestiune_Elevi_IX_TH.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as ex:
            st.error(f"Eroare la generare Registru Excel: {ex}")

    with col_g2:
        try:
            excel_stat_bytes = generate_excel_statistica_clasa(gest_data)
            st.download_button(
                "📊 Descarcă Statistica Clasa (.xlsx)",
                data=excel_stat_bytes,
                file_name="Statistica_Clasa_IX_TH.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as ex:
            st.error(f"Eroare la generare Statistică Excel: {ex}")


# --- TAB 9: DOCUMENTE ELEVI ---
with tab8:
    st.subheader("📁 DOCUMENTE ELEVI — Centru documente")
    doc_student_idx = st.selectbox(
        "Selectează elevul:",
        range(len(ELEVI)),
        format_func=lambda i: elev_options[i],
        key="doc_student_preview",
    )
    doc_student = ELEVI[doc_student_idx]

    st.info(
        f"Elev selectat: **{doc_student[1]}** — RM/PG: **{doc_student[3]}**."
    )

    st.markdown("#### 🚪 Bilet de voie — solicitarea părintelui")
    try:
        leave_request = get_leave_request_for_day(doc_student[3])
        if not leave_request:
            st.info("Nu există o solicitare de învoire pentru elevul selectat în ziua curentă.")
        else:
            leave_status = leave_request.get("status")
            leave_status_labels = {
                LEAVE_STATUS_PENDING: "⏳ ÎN AȘTEPTARE",
                LEAVE_STATUS_REFUSED: "❌ REFUZATĂ",
                LEAVE_STATUS_EXPIRED: "❌ EXPIRATĂ — CONSIDERATĂ REFUZATĂ",
                LEAVE_STATUS_APPROVED: "✅ APROBATĂ",
            }
            st.markdown(f"**Stare:** {leave_status_labels.get(leave_status, leave_status)}")
            st.markdown(
                f"**Părinte/Reprezentant legal:** {leave_request.get('parent_name')}  \n"
                f"**Data:** {leave_request.get('request_date')}  \n"
                f"**Ora solicitată pentru plecare:** {leave_request.get('departure_time')}  \n"
                f"**Motiv:** {leave_request.get('reason_label')}  \n"
                f"**Revizia solicitării:** {leave_request.get('revision')}"
            )
            transmitted_raw = str(leave_request.get("transmitted_at_utc") or "")
            if transmitted_raw:
                try:
                    transmitted_dt = datetime.datetime.fromisoformat(transmitted_raw.replace("Z", "+00:00"))
                    if transmitted_dt.tzinfo is None:
                        transmitted_dt = transmitted_dt.replace(tzinfo=datetime.timezone.utc)
                    transmitted_display = transmitted_dt.astimezone(
                        ZoneInfo("Europe/Bucharest")
                    ).strftime("%d.%m.%Y, ora %H:%M")
                except (ValueError, TypeError):
                    transmitted_display = transmitted_raw
                st.caption(f"Ultima formulare transmisă: {transmitted_display}")

            st.info(
                "Biletul de voie permite exclusiv părăsirea unității la data și ora aprobate. "
                "Nu reprezintă motivare/scutire și nu modifică automat absențele."
            )

            if leave_status == LEAVE_STATUS_PENDING:
                col_leave_approve, col_leave_refuse = st.columns(2)
                if col_leave_approve.button(
                    "✅ Aprobă învoirea",
                    type="primary",
                    use_container_width=True,
                    key=f"approve_leave_{leave_request['id']}_{leave_request['revision']}",
                ):
                    try:
                        result = approve_leave_request(
                            student_rm_pg=doc_student[3],
                            request_id=leave_request["id"],
                            expected_revision=leave_request["revision"],
                        )
                        if result.get("status") == LEAVE_STATUS_APPROVED:
                            st.success("Învoirea a fost aprobată și biletul de voie a fost generat.")
                        elif result.get("status") == LEAVE_STATUS_EXPIRED:
                            st.error(
                                "Ora solicitată a fost atinsă sau depășită. Solicitarea este "
                                "considerată refuzată și nu a fost generat niciun bilet de voie."
                            )
                        st.rerun()
                    except (DocumentStorageError, ValueError) as ex:
                        st.error(f"Învoirea nu a putut fi aprobată: {ex}")

                if col_leave_refuse.button(
                    "❌ Refuză învoirea",
                    use_container_width=True,
                    key=f"refuse_leave_{leave_request['id']}_{leave_request['revision']}",
                ):
                    try:
                        result = refuse_leave_request(
                            student_rm_pg=doc_student[3],
                            request_id=leave_request["id"],
                            expected_revision=leave_request["revision"],
                        )
                        if result.get("status") == LEAVE_STATUS_EXPIRED:
                            st.error(
                                "Ora solicitată a fost atinsă sau depășită; solicitarea este "
                                "considerată refuzată prin expirare."
                            )
                        else:
                            st.success("Solicitarea de învoire a fost refuzată.")
                        st.rerun()
                    except (DocumentStorageError, ValueError) as ex:
                        st.error(f"Refuzul nu a putut fi înregistrat: {ex}")

            elif leave_status == LEAVE_STATUS_REFUSED:
                st.warning(
                    "Solicitarea a fost refuzată. Părintele o poate reformula în aceeași zi "
                    "pentru o oră viitoare."
                )
            elif leave_status == LEAVE_STATUS_EXPIRED:
                st.warning(
                    "Solicitarea nu a fost aprobată înainte de ora solicitată și este considerată "
                    "refuzată. Nu poate fi aprobată retroactiv."
                )
            elif leave_status == LEAVE_STATUS_APPROVED:
                approved_raw = str(leave_request.get("approved_at_utc") or "")
                if approved_raw:
                    try:
                        approved_dt = datetime.datetime.fromisoformat(approved_raw.replace("Z", "+00:00"))
                        if approved_dt.tzinfo is None:
                            approved_dt = approved_dt.replace(tzinfo=datetime.timezone.utc)
                        approved_display = approved_dt.astimezone(
                            ZoneInfo("Europe/Bucharest")
                        ).strftime("%d.%m.%Y, ora %H:%M")
                    except (ValueError, TypeError):
                        approved_display = approved_raw
                    st.success(f"✅ Învoire aprobată — {approved_display}")
                try:
                    _, leave_pdf = read_approved_leave_pass(
                        doc_student[3], leave_request["id"]
                    )
                    st.download_button(
                        "📥 Descarcă biletul de voie aprobat",
                        data=leave_pdf,
                        file_name=f"Bilet_de_voie_{leave_request['request_date']}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        key=f"teacher_leave_download_{leave_request['id']}",
                    )
                except DocumentStorageError as ex:
                    st.error(f"Biletul de voie nu poate fi deschis în siguranță: {ex}")
    except (DocumentStorageError, ValueError) as ex:
        st.error(f"Solicitarea de învoire nu poate fi încărcată în siguranță: {ex}")

    st.divider()

    st.markdown("#### 📤 Trimite document către părinte/reprezentant legal")
    st.caption(
        "Documentul va fi transmis în contul autentificat aferent elevului selectat. "
        "După prima accesare de către părinte/reprezentant legal, sistemul va putea "
        "înregistra confirmarea de primire și luare la cunoștință."
    )
    teacher_document_type_label = st.selectbox(
        "Tip document transmis:",
        ["Înștiințare", "Document transmis de școală"],
        key="teacher_school_document_type",
    )
    teacher_document_type = (
        "INSTIINTARE"
        if teacher_document_type_label == "Înștiințare"
        else "DOCUMENT_SCOALA"
    )
    teacher_upload = st.file_uploader(
        "Încarcă documentul (PDF, JPG/JPEG sau PNG, maximum 15 MB):",
        type=["pdf", "jpg", "jpeg", "png"],
        key=f"teacher_school_document_upload_{doc_student[0]}",
    )

    if teacher_upload is not None:
        st.info(
            f"Destinatar: **{doc_student[1]}** — RM/PG: **{doc_student[3]}**  \n"
            f"Fișier: **{teacher_upload.name}**"
        )
        if st.button(
            "📤 Trimite către părinte",
            type="primary",
            use_container_width=True,
            key=f"teacher_send_school_document_{doc_student[0]}",
        ):
            try:
                upload_content = teacher_upload.getvalue()
                record, validated_content = build_document_record(
                    student_rm_pg=doc_student[3],
                    direction="SCOALA_PARINTE",
                    category="SCOALA_CATRE_PARINTE",
                    document_type=teacher_document_type,
                    original_filename=teacher_upload.name,
                    mime_type=teacher_upload.type,
                    content=upload_content,
                    school_year="2026-2027",
                    sender_role="SCOALA",
                    recipient_role="PARINTE",
                )
                store_new_document(record, validated_content)
                _event,_created,_wa_links=_register_parent_alert(
                    doc_student[3],event_type="DOCUMENT_SCOALA",source_type="DOCUMENT",
                    source_id=record["id"],student_key=record["student_key"],
                    title="Comunicare nouă din partea dirigintelui",
                    message="Catalog Online: aveți o nouă comunicare din partea dirigintelui. Accesați Portalul Părinților pentru detalii.",
                    created_at_utc=record.get("created_at_utc"),
                )
                for _idx,_wa in enumerate(_wa_links):
                    st.link_button(f"📲 Deschide WhatsApp pentru părinte {(_idx+1)}",_wa,use_container_width=True)
                st.success(
                    "Documentul a fost transmis și înregistrat în siguranță pentru "
                    "părintele/reprezentantul legal al elevului selectat."
                )
                st.rerun()
            except (DocumentStorageError, ValueError) as ex:
                st.error(f"Documentul nu a fost transmis: {ex}")

    st.divider()

    try:
        sent_documents = list_student_documents(
            doc_student[3],
            direction="SCOALA_PARINTE",
        )
        st.markdown("#### 📬 Documente trimise către părinte/reprezentant legal")
        if not sent_documents:
            st.info("Nu există documente transmise de școală pentru elevul selectat.")
        else:
            sent_labels = {
                "INSTIINTARE": "Înștiințare",
                "DOCUMENT_SCOALA": "Document transmis de școală",
            }
            selected_sent_id = st.selectbox(
                "Document trimis:",
                [item["id"] for item in sent_documents],
                format_func=lambda doc_id: next(
                    (
                        f"{sent_labels.get(item.get('document_type'), item.get('document_type'))} — "
                        f"{item.get('original_filename')} — "
                        f"{item.get('created_at_utc', '')[:10]}"
                    )
                    for item in sent_documents
                    if item["id"] == doc_id
                ),
                key="teacher_sent_document",
            )
            selected_sent = next(
                item for item in sent_documents if item["id"] == selected_sent_id
            )
            first_accessed = str(selected_sent.get("first_accessed_at_utc") or "")
            if first_accessed:
                try:
                    accessed_dt = datetime.datetime.fromisoformat(first_accessed.replace("Z", "+00:00"))
                    if accessed_dt.tzinfo is None:
                        accessed_dt = accessed_dt.replace(tzinfo=datetime.timezone.utc)
                    accessed_display = accessed_dt.astimezone(
                        ZoneInfo("Europe/Bucharest")
                    ).strftime("%d.%m.%Y, ora %H:%M")
                except (ValueError, TypeError):
                    accessed_display = first_accessed
                st.success(f"✅ Accesat de părinte — {accessed_display}")
            else:
                st.warning("🔔 Neaccesat de părinte")

            st.caption(
                f"Tip: {sent_labels.get(selected_sent.get('document_type'), selected_sent.get('document_type'))} | "
                f"An școlar: {selected_sent.get('school_year')} | "
                f"Dimensiune: {selected_sent.get('size_bytes', 0)} bytes"
            )
            try:
                sent_meta, sent_content = read_registered_document(
                    doc_student[3],
                    selected_sent_id,
                )
                st.download_button(
                    "📥 Descarcă documentul trimis",
                    data=sent_content,
                    file_name=sent_meta.get("original_filename", "document"),
                    mime=sent_meta.get("mime_type", "application/octet-stream"),
                    use_container_width=True,
                    key="teacher_download_sent_document",
                )
                _sent_wa_links = _parent_whatsapp_links(
                    doc_student[3],
                    "Catalog Online: aveți un document transmis de școală disponibil în Portalul Părinților.",
                )
                for _idx, _wa in enumerate(_sent_wa_links):
                    st.link_button(
                        f"📲 Deschide WhatsApp pentru părinte {(_idx + 1)}",
                        _wa,
                        use_container_width=True,
                        key=f"teacher_sent_document_wa_{selected_sent_id}_{_idx}",
                    )
            except DocumentStorageError as ex:
                st.error(f"Documentul trimis nu poate fi deschis în siguranță: {ex}")

            confirmation_id = selected_sent.get("confirmation_document_id")
            if confirmation_id:
                try:
                    confirmation_meta, confirmation_content = read_registered_document(
                        doc_student[3],
                        confirmation_id,
                    )
                    st.download_button(
                        "📄 Descarcă confirmarea de primire",
                        data=confirmation_content,
                        file_name=confirmation_meta.get("original_filename", "confirmare_primire.pdf"),
                        mime="application/pdf",
                        use_container_width=True,
                        key="teacher_download_receipt",
                    )
                except DocumentStorageError as ex:
                    st.error(f"Confirmarea de primire nu poate fi deschisă în siguranță: {ex}")
    except DocumentStorageError as ex:
        st.error(f"Documentele trimise nu pot fi încărcate în siguranță: {ex}")

    st.divider()

    try:
        received_documents = list_student_documents(
            doc_student[3],
            direction="PARINTE_SCOALA",
        )
        col_doc1, col_doc2 = st.columns(2)
        col_doc1.metric("Documente de la părinte", len(received_documents))
        col_doc2.metric(
            "Documente primite în anul curent",
            sum(1 for item in received_documents if item.get("school_year") == "2026-2027"),
        )

        try:
            excuse_usage = parent_excuse_usage(doc_student[3], "2026-2027")
            st.markdown("#### 📝 Scutiri / Motivări întocmite de părinte — anul școlar 2026–2027")
            col_exc1, col_exc2, col_exc3 = st.columns(3)
            col_exc1.metric("Ore utilizate", excuse_usage["used_hours"])
            col_exc2.metric("Ore rămase", excuse_usage["remaining_hours"])
            col_exc3.metric("Limită anuală", excuse_usage["annual_limit"])
        except DocumentStorageError as ex:
            st.error(f"Contorul anual al motivărilor nu poate fi încărcat în siguranță: {ex}")

        if not received_documents:
            st.info("Nu există documente transmise de părinte pentru elevul selectat.")
        else:
            labels = {
                "DOSAR_PERSONAL": "Dosar personal",
                "SCUTIRE_MEDICALA": "Scutire / document medical",
                "DOSAR_BURSA": "Dosar bursă",
                "MOTIVARE_PARINTE": "Scutire / Motivare absențe — Părinte",
            }
            selected_doc_id = st.selectbox(
                "Document primit:",
                [item["id"] for item in received_documents],
                format_func=lambda doc_id: next(
                    (
                        f"{labels.get(item.get('category'), item.get('category'))} — "
                        f"{item.get('original_filename')} — "
                        f"{item.get('created_at_utc', '')[:10]}"
                    )
                    for item in received_documents
                    if item["id"] == doc_id
                ),
                key="teacher_received_document",
            )
            selected_meta = next(
                item for item in received_documents if item["id"] == selected_doc_id
            )
            st.caption(
                f"Tip: {selected_meta.get('document_type')} | "
                f"An școlar: {selected_meta.get('school_year')} | "
                f"Dimensiune: {selected_meta.get('size_bytes', 0)} bytes"
            )

            if selected_meta.get("category") == "MOTIVARE_PARINTE":
                try:
                    excuse_meta = get_parent_excuse_for_document(
                        doc_student[3],
                        selected_doc_id,
                    )
                    if excuse_meta is None:
                        st.warning(
                            "Documentul există în registrul general, dar înregistrarea administrativă "
                            "a motivării nu a fost găsită. Situația trebuie verificată înainte de prelucrare."
                        )
                    else:
                        absence_date = str(excuse_meta.get("absence_date", ""))
                        try:
                            absence_date_display = datetime.date.fromisoformat(absence_date).strftime("%d.%m.%Y")
                        except ValueError:
                            absence_date_display = absence_date or "—"
                        transmitted_at = str(excuse_meta.get("transmitted_at_utc", ""))
                        try:
                            transmitted_display = datetime.datetime.fromisoformat(transmitted_at).strftime("%d.%m.%Y %H:%M")
                        except ValueError:
                            transmitted_display = transmitted_at or "—"
                        st.markdown(
                            f"**Data absenței:** {absence_date_display}  \n"
                            f"**Număr ore:** {excuse_meta.get('hours', '—')}  \n"
                            f"**Transmis de:** {excuse_meta.get('parent_name') or '—'}  \n"
                            f"**Stare:** {excuse_meta.get('status') or '—'}  \n"
                            f"**Înregistrat la:** {transmitted_display} UTC"
                        )
                        st.info(
                            "Cererea a fost transmisă prin contul autentificat al părintelui/reprezentantului "
                            "legal și este considerată depusă. Dacă sunt necesare clarificări sau documente "
                            "suplimentare, părintele va fi contactat."
                        )
                except DocumentStorageError as ex:
                    st.error(f"Datele administrative ale motivării nu pot fi încărcate în siguranță: {ex}")

            try:
                verified_meta, verified_content = read_registered_document(
                    doc_student[3],
                    selected_doc_id,
                )
                st.download_button(
                    "📥 Descarcă documentul selectat",
                    data=verified_content,
                    file_name=verified_meta.get("original_filename", "document"),
                    mime=verified_meta.get("mime_type", "application/octet-stream"),
                    use_container_width=True,
                    key="teacher_download_received_document",
                )
            except DocumentStorageError as ex:
                st.error(f"Documentul nu poate fi deschis în siguranță: {ex}")
    except DocumentStorageError as ex:
        st.error(f"Registrul documentelor nu poate fi încărcat în siguranță: {ex}")


render_copyright_footer()


# --- TAB 9: PURTARE PE INTERVALE ---
with tab9:
    st.subheader("Purtare pe intervalele de cursuri")
    if not sync_conduct_registry_from_private_repo():
        st.error(
            "Registrul notelor la purtare nu a putut fi sincronizat din sursa privată. "
            "Acordarea notelor este blocată pentru protejarea datelor."
        )
        st.stop()
    st.caption(
        "Nota este acordată de diriginte după consultarea consiliului clasei. "
        "Absențele nu generează automat nota pe interval; diminuarea pentru "
        "nefrecventare se aplică mediei anuale la închiderea anului."
    )
    elev_idx_p = st.selectbox(
        "Selectează elevul:",
        range(len(ELEVI)),
        format_func=lambda i: elev_options[i],
        key="elev_purtare_interval",
    )
    today_ro = datetime.datetime.now(ZoneInfo("Europe/Bucharest")).date()
    registry = load_conduct_registry()
    student_key = str(ELEVI[elev_idx_p][3]).strip()
    existing = {
        int(item["interval_number"]): item
        for item in registry.get("grades", [])
        if str(item.get("student_key", "")).strip() == student_key
    }

    for interval in CLJ_2026_2027_COURSE_INTERVALS:
        current = existing.get(interval.number)
        label = (
            f"Intervalul {interval.number}: "
            f"{interval.start_date.strftime('%d.%m.%Y')}–{interval.end_date.strftime('%d.%m.%Y')}"
        )
        if current:
            st.success(
                f"{label} — nota {current['grade']}, acordată la {current['awarded_on']}."
            )
            continue
        if today_ro < interval.end_date:
            st.info(f"{label} — nota poate fi acordată după încheierea intervalului.")
            continue

        with st.expander(f"{label} — acordă nota"):
            nota_p = st.number_input(
                "Nota la purtare",
                min_value=1,
                max_value=10,
                value=10,
                step=1,
                key=f"nota_purtare_{interval.number}_{student_key}",
            )
            if st.button(
                f"💾 Salvează nota pentru intervalul {interval.number}",
                key=f"save_purtare_{interval.number}_{student_key}",
                use_container_width=True,
            ):
                try:
                    wb_check = openpyxl.load_workbook(selected_file, read_only=True, data_only=False)
                    try:
                        resolve_student_row(wb_check, ELEVI[elev_idx_p])
                    finally:
                        wb_check.close()
                    save_conduct_grade(
                        student_key=student_key,
                        interval_number=interval.number,
                        grade=int(nota_p),
                        awarded_on=today_ro.isoformat(),
                    )
                    if not push_to_github("registru_purtare_2026_2027.json"):
                        st.warning(
                            "Nota a fost salvată local, dar sincronizarea în sursa privată "
                            "nu a fost confirmată."
                        )
                    else:
                        st.success("Nota la purtare a fost salvată și sincronizată.")
                        st.rerun()
                except (ConductStorageError, Exception) as ex:
                    st.error(f"Nota la purtare nu a fost salvată: {ex}")


def build_class_annual_closure_previews(file_path):
    """Construiește read-only situația anuală pentru întreaga clasă.

    Nu scrie în Excel, gestiune sau registrul de purtare. Identitatea elevilor
    este indexată o singură dată, secvențial, pentru a evita accesul aleatoriu
    repetat foarte lent al openpyxl în modul read_only.
    """
    results = []
    wb = openpyxl.load_workbook(file_path, read_only=False, data_only=True)
    try:
        required_sheets = ("Cultură Generală", "Module Tehnologice", "Absențe & Purtare", "Centralizator Medii")
        for sheet_name in required_sheets:
            if sheet_name not in wb.sheetnames:
                raise RuntimeError(f"Lipsește foaia obligatorie: {sheet_name}")

        row_maps = {}
        for sheet_name in required_sheets:
            ws = wb[sheet_name]
            key_rows = {}
            for row_number, values in enumerate(
                ws.iter_rows(min_row=9, min_col=4, max_col=4, values_only=True),
                start=9,
            ):
                key = str(values[0] or "").strip()
                if not key:
                    continue
                if key in key_rows:
                    raise RuntimeError(
                        f"Identificatorul {key!r} apare de mai multe ori în foaia {sheet_name}."
                    )
                key_rows[key] = row_number
            row_maps[sheet_name] = key_rows

        def indexed_row_resolver(_wb, elev_info):
            key = str(elev_info[3]).strip()
            if not key:
                raise RuntimeError("Elevul nu are identificator de catalog valid.")
            rows = []
            for sheet_name in required_sheets:
                row = row_maps[sheet_name].get(key)
                if row is None:
                    raise RuntimeError(
                        f"Identitatea elevului nu există în foaia {sheet_name}. "
                        "Operația a fost oprită fără salvare."
                    )
                rows.append(row)
            if len(set(rows)) != 1:
                raise RuntimeError(
                    "Identitatea elevului nu corespunde pe același rând în toate foile catalogului. "
                    "Operația a fost oprită fără salvare."
                )
            return rows[0]

        for elev_info in ELEVI:
            student_key = str(elev_info[3]).strip()
            try:
                subjects = build_student_subject_inputs(
                    wb,
                    elev_info,
                    indexed_row_resolver,
                    IX_TH_2026_2027_CLASS_CDEOS_HOURS,
                )
                conduct_values = conduct_grades_for_student(student_key)
                preview = preview_annual_closure(
                    subjects,
                    sum(item.motivated_absences for item in subjects),
                    conduct_values,
                )
                results.append({
                    "student_key": student_key,
                    "name": str(elev_info[1]).strip(),
                    "preview": preview,
                    "conduct_values": tuple(conduct_values),
                    "error": None,
                })
            except (ConductStorageError, AnnualClosureError, RuntimeError, ValueError) as ex:
                results.append({
                    "student_key": student_key,
                    "name": str(elev_info[1]).strip(),
                    "preview": None,
                    "conduct_values": None,
                    "error": str(ex),
                })
    finally:
        wb.close()
    return tuple(results)


# Catalogul la zi este complet separat de închiderea anuală și nu persistă nimic.
with tab9:
    st.divider()
    st.subheader("Catalog oficial la zi")
    st.caption(
        "Generează situația existentă în acest moment: note și absențe curente. "
        "Rubricile anuale/finale care nu există încă rămân necompletate. "
        "Operația este strict read-only și nu modifică Excelul, gestiunea elevilor "
        "sau registrele private."
    )
    if st.button(
        "📘 Generează catalogul la zi",
        key="generate_current_official_catalog_pdf",
        use_container_width=True,
    ):
        try:
            with st.spinner("Generez catalogul oficial la zi, fără nicio scriere..."):
                current_catalog_pdf = generate_official_catalog_current(
                    selected_file,
                    load_gestiune_data(),
                )
            st.session_state["current_official_catalog_pdf"] = current_catalog_pdf
            st.success(
                "Catalogul la zi a fost generat read-only. "
                "Nu s-a modificat nicio dată din catalog."
            )
        except (OfficialCatalogError, RuntimeError, OSError, ValueError) as ex:
            st.session_state.pop("current_official_catalog_pdf", None)
            st.error(f"Catalogul la zi nu a putut fi generat în siguranță: {ex}")

    current_pdf = st.session_state.get("current_official_catalog_pdf")
    if current_pdf:
        st.download_button(
            "⬇️ Descarcă catalogul oficial la zi",
            data=current_pdf,
            file_name="catalog_oficial_la_zi.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_current_official_catalog_pdf",
        )


# Validarea clasei este numai informativă/read-only. Nu închide și nu persistă situații.
with tab9:
    st.divider()
    st.subheader("Validare clasă înainte de închiderea situației școlare")
    st.caption(
        "Verificarea citește situația tuturor elevilor și indică blocajele. "
        "Nu modifică Excelul, registrul de purtare sau gestiunea elevilor."
    )
    if st.button(
        "🔎 Verifică întreaga clasă pentru închidere",
        key="annual_class_validation_readonly",
        use_container_width=True,
    ):
        try:
            validation_status = st.status(
                "Diagnostic validare: pornesc citirea catalogului...",
                expanded=True,
            )
            validation_started = time.perf_counter()
            validation_status.write("Etapa 1/2 — deschid și citesc catalogul Excel.")
            class_results = build_class_annual_closure_previews(selected_file)
            validation_status.write(
                f"Etapa 1/2 finalizată în {time.perf_counter() - validation_started:.2f} s."
            )
            validation_status.write("Etapa 2/2 — sintetizez rezultatele clasei.")
            ready_count = 0
            blocked_count = 0
            error_count = 0
            for item in class_results:
                preview = item["preview"]
                if item["error"] is not None:
                    error_count += 1
                elif preview.ready_for_final_closure:
                    ready_count += 1
                else:
                    blocked_count += 1

            validation_elapsed = time.perf_counter() - validation_started
            validation_status.update(
                label=f"Diagnostic finalizat în {validation_elapsed:.2f} s.",
                state="complete",
                expanded=True,
            )
            st.session_state["annual_class_validation_summary"] = {
                "ready_count": ready_count,
                "blocked_count": blocked_count,
                "error_count": error_count,
                "elapsed": validation_elapsed,
            }

            col_ready, col_blocked, col_error = st.columns(3)
            col_ready.metric("Pregătiți", ready_count)
            col_blocked.metric("Cu blocaje", blocked_count)
            col_error.metric("Date incomplete/incoerente", error_count)

            if blocked_count == 0 and error_count == 0:
                st.success(
                    "Toți elevii au trecut validarea read-only. "
                    "Această verificare NU a închis încă situația școlară."
                )
            else:
                st.warning(
                    "Clasa nu este încă pregătită integral pentru închidere. "
                    "Problemele de mai jos trebuie analizate înainte de orice persistență."
                )

            for item in class_results:
                preview = item["preview"]
                if item["error"] is not None:
                    with st.expander(f"❌ {item['name']} — calcul indisponibil"):
                        st.error(item["error"])
                    continue
                if preview.ready_for_final_closure:
                    st.success(
                        f"✅ {item['name']} — {preview.final_status}; "
                        f"purtare {preview.conduct_annual_average}; "
                        f"absențe {preview.total_absences}."
                    )
                    continue
                with st.expander(f"⚠️ {item['name']} — necesită verificare"):
                    st.write(
                        f"Situație calculată: **{preview.final_status}** | "
                        f"Purtare: **{preview.conduct_annual_average}** | "
                        f"Absențe: **{preview.total_absences}**"
                    )
                    for blocker in preview.readiness_blockers:
                        st.warning(blocker)
        except (AnnualClosureError, ConductStorageError, RuntimeError, OSError) as ex:
            st.session_state["annual_class_validation_summary"] = {
                "error": str(ex),
            }
            st.error(f"Validarea clasei nu a putut fi finalizată: {ex}")

    persisted_validation = st.session_state.get("annual_class_validation_summary")
    if persisted_validation:
        st.caption("Ultimul rezultat al verificării read-only (păstrat în această sesiune):")
        if persisted_validation.get("error"):
            st.error(
                "Ultima verificare nu a putut fi finalizată: "
                + persisted_validation["error"]
            )
        else:
            p_ready, p_blocked, p_error = st.columns(3)
            p_ready.metric("Pregătiți", persisted_validation["ready_count"])
            p_blocked.metric("Cu blocaje", persisted_validation["blocked_count"])
            p_error.metric(
                "Date incomplete/incoerente",
                persisted_validation["error_count"],
            )
            st.caption(
                f"Timpul ultimei verificări: {persisted_validation['elapsed']:.2f} s. "
                "Rezultatul este numai informativ; nu s-a efectuat nicio scriere."
            )


# Închiderea situației școlare persistă numai snapshoturi validate în registrul privat separat.
with tab9:
    st.divider()
    st.subheader("Închiderea situației școlare")
    st.warning(
        "Operația fixează snapshotul de la încheierea cursurilor. Nu modifică Excelul. "
        "Snapshoturile existente nu sunt suprascrise; orice conflict blochează operația."
    )
    closure_confirmed = st.checkbox(
        "Confirm că am verificat situația clasei și doresc închiderea situației școlare.",
        key="confirm_annual_class_closure",
    )
    if st.button(
        "🔒 Închiderea situației școlare",
        key="persist_annual_class_closure",
        type="primary",
        use_container_width=True,
        disabled=not closure_confirmed,
    ):
        try:
            class_results = build_class_annual_closure_previews(selected_file)
            invalid = [item for item in class_results if item["error"] is not None]
            blocked = [
                item for item in class_results
                if item["error"] is None
                and not item["preview"].ready_for_final_closure
                and item["preview"].final_status != "AMANAT"
            ]
            if invalid or blocked:
                st.error(
                    "Închiderea a fost blocată înainte de orice scriere: "
                    "cel puțin un elev are date incomplete/incoerente sau blocaje nerezolvate."
                )
                for item in invalid:
                    st.error(f"{item['name']}: {item['error']}")
                for item in blocked:
                    for reason in item["preview"].readiness_blockers:
                        st.warning(f"{item['name']}: {reason}")
            else:
                snapshots = []
                for item in class_results:
                    snapshots.append(
                        build_annual_closure_snapshot(
                            student_key=item["student_key"],
                            preview=item["preview"],
                            interval_conduct_grades=item["conduct_values"],
                        )
                    )

                # Revalidăm toate snapshoturile înainte de prima publicare.
                if len(snapshots) != len(class_results):
                    raise AnnualClosureError("Numărul snapshoturilor nu corespunde clasei validate.")

                persist_private_annual_closure_batch_once(tuple(snapshots))
                persisted = len(snapshots)
                st.success(
                    f"Închiderea situației școlare a fost înregistrată pentru {persisted} elevi. "
                    "Datele primare din Excel nu au fost modificate."
                )
        except (AnnualClosureError, AnnualClosureStorageError, ConductStorageError, RuntimeError, OSError) as ex:
            st.error(
                "Închiderea situației școlare nu a fost finalizată în siguranță. "
                f"Motiv: {ex}"
            )


# Situația definitivă este o etapă separată de snapshotul de la încheierea cursurilor.
# Nu rescrie snapshoturile și nu modifică datele primare.
with tab9:
    st.divider()
    st.subheader("Situație definitivă")
    st.caption(
        "Această etapă poate fi înregistrată numai după închiderea situației școlare pentru "
        "întreaga clasă. PROMOVAT și REPETENT pot deveni definitive direct; CORIGENT și "
        "AMÂNAT necesită mai întâi rezultatul/actul ulterior auditabil."
    )
    try:
        definitive_closed_snapshots = load_private_annual_closure_snapshots()
        definitive_expected_keys = {str(elev[3]).strip() for elev in ELEVI}
        definitive_missing = definitive_expected_keys - set(definitive_closed_snapshots)
        definitive_extra = set(definitive_closed_snapshots) - definitive_expected_keys
        definitive_pending = {
            key: snapshot.final_status
            for key, snapshot in definitive_closed_snapshots.items()
            if str(snapshot.final_status).strip().upper() in {"CORIGENT", "AMANAT", "AMÂNAT"}
        }
        definitive_unknown = {
            key: snapshot.final_status
            for key, snapshot in definitive_closed_snapshots.items()
            if str(snapshot.final_status).strip().upper()
            not in {"PROMOVAT", "REPETENT", "CORIGENT", "AMANAT", "AMÂNAT"}
        }

        final_registry, _final_registry_sha = load_private_final_status_registry()
        final_existing = set(final_registry["students"])
        already_final = final_existing == definitive_expected_keys

        if definitive_missing or definitive_extra:
            st.warning(
                "Situația definitivă este blocată: registrul de închidere nu corespunde exact clasei."
            )
        elif definitive_pending:
            st.warning(
                f"Situația definitivă nu poate fi încă înregistrată pentru clasă: "
                f"{len(definitive_pending)} elev(i) au CORIGENT/AMÂNAT și necesită act ulterior auditabil."
            )
        elif definitive_unknown:
            st.error("Situația definitivă este blocată de statute anuale necunoscute.")
        elif already_final:
            st.success("Situația școlară definitivă a întregii clase este deja înregistrată.")
        else:
            definitive_confirmed = st.checkbox(
                "Confirm că am verificat situația definitivă a întregii clase.",
                key="confirm_definitive_class_status",
            )
            if st.button(
                "🔐 Situație definitivă",
                key="persist_definitive_class_status",
                type="primary",
                use_container_width=True,
                disabled=not definitive_confirmed,
            ):
                persist_private_final_status_batch_once(
                    definitive_closed_snapshots,
                    definitive_expected_keys,
                )
                st.success(
                    "Situația școlară definitivă a clasei a fost înregistrată în registrul privat. "
                    "Excelul, gestiunea elevilor și snapshoturile de la încheierea cursurilor "
                    "nu au fost modificate."
                )
                st.rerun()
    except (AnnualClosureStorageError, FinalStatusStorageError, RuntimeError, OSError, ValueError) as ex:
        st.error(f"Situația definitivă nu poate fi înregistrată în siguranță: {ex}")


# PDF-ul de după închidere folosește exclusiv snapshoturile private validate pentru situația anuală.
with tab9:
    st.divider()
    st.subheader("Catalog PDF după închiderea situației școlare")
    try:
        closed_snapshots = load_private_annual_closure_snapshots()
        expected_keys = {str(elev[3]).strip() for elev in ELEVI}
        if set(closed_snapshots) == expected_keys:
            annual_states = {
                key: official_catalog_state_from_records(snapshot)
                for key, snapshot in closed_snapshots.items()
            }
            closed_catalog_pdf = generate_official_catalog_final(
                selected_file,
                load_gestiune_data(),
                annual_states,
            )
            st.download_button(
                "📘 Descarcă catalogul PDF din situația închisă",
                data=closed_catalog_pdf,
                file_name="catalog_situatie_inchisa.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_closed_official_catalog_pdf",
            )
            st.caption(
                "Mediile anuale, purtarea și statutul școlar provin din snapshoturile "
                "private verificate SHA-256; notele și absențele curente sunt citite "
                "read-only pentru rubricile de evidență ale catalogului."
            )
        elif closed_snapshots:
            st.info(
                "Registrul privat conține numai o parte din elevii clasei. "
                "Catalogul din situația închisă nu este generat până când setul nu este complet."
            )
        else:
            st.info(
                "Catalogul din situația închisă va deveni disponibil după înregistrarea "
                "snapshoturilor pentru întreaga clasă."
            )
    except (AnnualClosureStorageError, OfficialCatalogError, RuntimeError, OSError, ValueError) as ex:
        st.error(f"Catalogul PDF din situația închisă nu poate fi generat: {ex}")


# Preview-ul anual rămâne read-only; este disponibil doar când registrul are toate cele 5 note.
with tab9:
    st.divider()
    st.subheader("Simulare închidere anuală")
    if st.button("🧮 Simulează situația anuală", key="annual_preview_readonly", use_container_width=True):
        try:
            conduct_values = conduct_grades_for_student(student_key)
            wb_preview = openpyxl.load_workbook(selected_file, read_only=True, data_only=True)
            try:
                subjects = build_student_subject_inputs(
                    wb_preview, ELEVI[elev_idx_p], resolve_student_row, IX_TH_2026_2027_CLASS_CDEOS_HOURS
                )
            finally:
                wb_preview.close()
            preview = preview_annual_closure(
                subjects,
                sum(item.motivated_absences for item in subjects),
                conduct_values,
            )
            st.success(
                f"Situație preliminară: {preview.final_status}; "
                f"purtare anuală: {preview.conduct_annual_average}; "
                f"absențe totale: {preview.total_absences}."
            )
            if preview.general_average is not None:
                st.info(f"Media generală anuală preliminară: {preview.general_average}")
            if preview.ready_for_final_closure:
                st.success(
                    "Validarea preliminară nu a identificat blocaje pentru închiderea situației școlare. "
                    "Nu s-a efectuat nicio scriere."
                )
            else:
                st.warning(
                    "Situația poate fi simulată, dar NU este pregătită pentru închiderea situației școlare."
                )
                for blocker in preview.readiness_blockers:
                    st.warning(blocker)
        except (ConductStorageError, AnnualClosureError, RuntimeError) as ex:
            st.warning(f"Simularea anuală nu poate fi finalizată încă: {ex}")
