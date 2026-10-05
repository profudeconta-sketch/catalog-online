"""Sursa oficiala statica pentru paginile tipizatului de catalog liceal.

Modulul nu modifica datele aplicatiei. Descarca exclusiv tipizatul publicat de
Ministerul Educatiei, verifica SHA-256-ul exact validat si lucreaza numai in
memorie. Orice abatere de continut, numar de pagini sau dimensiune blocheaza
generarea (fail-closed).
"""

from __future__ import annotations

import hashlib
import io
from functools import lru_cache
from urllib.request import Request, urlopen

from pypdf import PdfReader, PdfWriter

OFFICIAL_SOURCE_URL = (
    "https://www.edu.ro/sites/default/files/_fi%C8%99iere/Minister/2022/"
    "inv.%20preuniversitar/tipizate/cataloage_modele_noi_2022/"
    "4_1_catalog_invatamant_liceal.pdf"
)
OFFICIAL_SOURCE_SHA256 = "0066c8c6dba476f326a096f7ec89fa1bcfecf47f0370bffd08dacdfe2a6f5ec5"
EXPECTED_PAGES = 8
EXPECTED_WIDTH = 992.52
EXPECTED_HEIGHT = 1417.56
DIMENSION_TOLERANCE = 0.20


class OfficialCatalogSourceError(RuntimeError):
    pass


def _validate_source(data: bytes) -> bytes:
    digest = hashlib.sha256(data).hexdigest()
    if digest != OFFICIAL_SOURCE_SHA256:
        raise OfficialCatalogSourceError(
            "Tipizatul oficial descarcat nu corespunde versiunii validate (SHA-256 diferit)."
        )
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:
        raise OfficialCatalogSourceError("Tipizatul oficial nu poate fi citit ca PDF.") from exc
    if len(reader.pages) != EXPECTED_PAGES:
        raise OfficialCatalogSourceError(
            f"Tipizatul oficial are {len(reader.pages)} pagini, nu {EXPECTED_PAGES}."
        )
    for index, page in enumerate(reader.pages, start=1):
        width = float(page.mediabox.width)
        height = float(page.mediabox.height)
        if (
            abs(width - EXPECTED_WIDTH) > DIMENSION_TOLERANCE
            or abs(height - EXPECTED_HEIGHT) > DIMENSION_TOLERANCE
        ):
            raise OfficialCatalogSourceError(
                f"Pagina {index} a tipizatului are dimensiuni neasteptate: {width:.2f} x {height:.2f} pt."
            )
    return data


@lru_cache(maxsize=1)
def load_official_catalog_source() -> bytes:
    request = Request(
        OFFICIAL_SOURCE_URL,
        headers={"User-Agent": "catalog-online/official-catalog-generator"},
    )
    try:
        with urlopen(request, timeout=20) as response:
            data = response.read()
    except Exception as exc:
        raise OfficialCatalogSourceError(
            "Tipizatul oficial nu a putut fi obtinut de la sursa Ministerului Educatiei."
        ) from exc
    return _validate_source(data)


def official_source_page(page_index: int) -> bytes:
    data = load_official_catalog_source()
    reader = PdfReader(io.BytesIO(data))
    if not 0 <= page_index < len(reader.pages):
        raise OfficialCatalogSourceError(f"Pagina-sursa {page_index + 1} nu exista.")
    writer = PdfWriter()
    writer.add_page(reader.pages[page_index])
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def merge_official_page_with_overlay(page_index: int, overlay_bytes: bytes | None = None) -> bytes:
    base_reader = PdfReader(io.BytesIO(official_source_page(page_index)))
    base = base_reader.pages[0]
    if overlay_bytes:
        overlay_reader = PdfReader(io.BytesIO(overlay_bytes))
        if len(overlay_reader.pages) != 1:
            raise OfficialCatalogSourceError("Overlay-ul trebuie sa contina exact o pagina.")
        base.merge_page(overlay_reader.pages[0])
    writer = PdfWriter()
    writer.add_page(base)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()
