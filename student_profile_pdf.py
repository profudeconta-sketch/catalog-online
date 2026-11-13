"""Fișa completă a elevului: prezentare read-only din registrul Gestiune Elevi.

Nu importă aplicația Streamlit, nu folosește conexiuni și nu modifică date.
PIN-ul de autentificare rămâne exclusiv în fișa de acces pentru părinți.
"""
import json
import re
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.platypus import LongTable, Paragraph, Spacer, TableStyle


_SECTIONS = (
    ("DATE DE IDENTIFICARE", (
        ("ID intern înregistrare", "id"),
        ("Nume de familie", "nume"),
        ("Inițiala tatălui", "initiala"),
        ("Prenume", "prenume"),
        ("Nume și prenume complet", "nume_complet"),
        ("Nr. matricol", "rand_excel"),
        ("RM/PG", "matricol"),
        ("Cod numeric personal (CNP)", "cnp"),
        ("Telefon elev", "telefon"),
        ("Naționalitate", "nationalitate"),
        ("Cetățenie", "cetatenie"),
        ("Etnie", "etnie"),
    )),
    ("DOMICILIUL ELEVULUI", (
        ("Localitate", "localitate"),
        ("Județ", "judet"),
        ("Stradă", "strada"),
        ("Număr stradă", "numar_strada"),
        ("Bloc", "bloc"),
        ("Apartament", "apartament"),
    )),
    ("PĂRINȚI ȘI SITUAȚIA FAMILIALĂ", (
        ("Nume și prenume mamă", "nume_mama"),
        ("Telefon mamă", "telefon_mama"),
        ("Mamă plecată în străinătate", "mama_plecata"),
        ("Țara unde este plecată mama", "tara_mama"),
        ("Nume și prenume tată", "nume_tata"),
        ("Telefon tată", "telefon_tata"),
        ("Tată plecat în străinătate", "tata_plecat"),
        ("Țara unde este plecat tatăl", "tara_tata"),
        ("Părinte unic susținător plecat", "parinte_unic_sustinator_plecat"),
        ("Părinte unic susținător plecat — cine", "parinte_unic_sustinator_plecat_tip"),
        ("Starea civilă a părinților", "stare_civila_parinti"),
        ("Copilul locuiește cu", "locuieste_cu"),
        ("Revenit în țară după ședere în străinătate peste un an",
         "revenit_strainatate_peste_un_an"),
    )),
    ("PERSOANA CARE ÎNGRIJEȘTE COPILUL", (
        ("Nume și prenume îngrijitor", "ingrijitor_nume"),
        ("Telefon de contact îngrijitor", "ingrijitor_telefon"),
    )),
    ("SITUAȚII SPECIALE, BURSE ȘI CES", (
        ("Cerințe educaționale speciale (CES)", "ces"),
        ("Elev orfan", "orfan"),
        ("Elev în plasament", "plasament"),
        ("Bursă socială medicală", "bursa_medicala"),
        ("Bursă socială pe bază de venit", "bursa_venit"),
    )),
    ("SITUAȚIE ȘCOLARĂ ADMINISTRATIVĂ ȘI ISTORIC", (
        ("Stare școlară", "status_scolar"),
        ("Istoric mișcări școlare", "istoric_miscare"),
    )),
)

_BOOLEAN_KEYS = {
    "mama_plecata", "tata_plecat", "parinte_unic_sustinator_plecat",
    "revenit_strainatate_peste_un_an", "ces", "orfan", "plasament",
    "bursa_medicala", "bursa_venit",
}
# Cheile tehnice de autentificare nu apar nici ca rubrici suplimentare.
_SECRET_PATTERN = re.compile(r"(?:pin|parol|password|secret|token|credential|api.?key)", re.I)


def _identity_text(value):
    return " ".join(str(value or "").split()).casefold()


def find_student_profile(gest_data, elev_info):
    """Selectează exclusiv elevul curent și refuză orice ambiguitate JSON/Excel."""
    if not isinstance(gest_data, list) or len(elev_info) < 4:
        raise ValueError("Identitatea elevului nu poate fi verificată.")
    rm_pg = _identity_text(elev_info[3])
    matches = [
        row for row in gest_data
        if isinstance(row, dict) and _identity_text(row.get("matricol")) == rm_pg
    ]
    if not rm_pg or len(matches) != 1:
        raise ValueError("Elevul nu are o înregistrare unică în Gestiune Elevi.")
    row = matches[0]
    for key, expected in (
        ("id", elev_info[0]),
        ("nume_complet", elev_info[1]),
        ("rand_excel", elev_info[2]),
        ("matricol", elev_info[3]),
    ):
        if _identity_text(row.get(key)) != _identity_text(expected):
            raise ValueError("Identitatea elevului diferă între Gestiune Elevi și catalog.")
    return dict(row)


def _text(value):
    if value is None or value == "":
        return "—"
    if isinstance(value, bool):
        return "Da" if value else "Nu"
    if isinstance(value, (dict, list, tuple)):
        if not value:
            return "—"
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value)


def _history(value):
    if not isinstance(value, list) or not value:
        return _text(value)
    parts = []
    for number, item in enumerate(value, 1):
        if not isinstance(item, dict):
            parts.append(str(number) + ". " + _text(item))
            continue
        summary = [str(item.get("tip") or "Eveniment fără tip")]
        if item.get("data"):
            summary.append(str(item["data"]))
        extras = [
            str(key) + ": " + _text(val)
            for key, val in item.items() if key not in ("tip", "data")
            and not _SECRET_PATTERN.search(str(key))
        ]
        parts.append(str(number) + ". " + " — ".join(summary + extras))
    return "; ".join(parts)


def profile_sections(record):
    """Include toate rubricile de gestiune și orice extensii neconfidențiale."""
    if not isinstance(record, dict):
        raise ValueError("Profilul elevului este invalid.")
    known_keys = set()
    sections = []
    for heading, fields in _SECTIONS:
        entries = []
        for label, key in fields:
            known_keys.add(key)
            if key == "istoric_miscare":
                value = _history(record.get(key))
            elif key in _BOOLEAN_KEYS and key in record:
                value = "Da" if bool(record[key]) else "Nu"
            else:
                value = _text(record.get(key))
            entries.append((label, value))
        sections.append((heading, entries))
    extras = [
        (str(key).replace("_", " ").capitalize(), _text(val))
        for key, val in sorted(record.items())
        if key not in known_keys and not _SECRET_PATTERN.search(str(key))
        and not str(key).startswith("_")
    ]
    if extras:
        sections.append(("ALTE DATE ÎNREGISTRATE ÎN GESTIUNE ELEVI", extras))
    return sections


def append_student_profile_pdf(story, record, *, heading_style, cell_style,
                               cell_bold, pdf_clean):
    """Adaugă secțiunile înainte de situația la învățătură și absențe.

    Nu citește registre/Excel și nu emite mesaje în loguri; numai randare PDF.
    """
    for heading, entries in profile_sections(record):
        story.append(Paragraph(pdf_clean(escape(heading)), heading_style))
        cells = [
            [
                Paragraph(pdf_clean(escape(label)), cell_bold),
                Paragraph(pdf_clean(escape(value)), cell_style),
            ]
            for label, value in entries
        ]
        table = LongTable(cells, colWidths=[178, 342], hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EDF2F7")),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CBD5E0")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ]))
        story.append(table)
        story.append(Spacer(1, 6))
