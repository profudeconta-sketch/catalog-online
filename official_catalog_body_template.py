"""Transformare vectorială read-only a șablonului V6 al corpului catalogului."""

from __future__ import annotations

import io
from pathlib import Path

from pypdf import PdfReader, PdfWriter, Transformation
from pypdf.generic import RectangleObject


MM_TO_PT = 72.0 / 25.4
SPREAD_W = 500 * MM_TO_PT
SPREAD_H = 350 * MM_TO_PT
HALF_W = 250 * MM_TO_PT
PAGE_W = 350 * MM_TO_PT
PAGE_H = 500 * MM_TO_PT
SCALE = 1.4
Y_OFFSET = 5 * MM_TO_PT

TEMPLATE_FILENAME = "catalog_P3_P4_model_oficial_50x35_v6_denumiri_sistem (1).pdf"
TOLERANCE_PT = 1.0


class CatalogBodyTemplateError(RuntimeError):
    pass


def template_path() -> Path:
    return Path(__file__).resolve().with_name(TEMPLATE_FILENAME)


def _validated_source_page():
    path = template_path()
    if not path.is_file():
        raise CatalogBodyTemplateError(f"Lipsește șablonul V6: {TEMPLATE_FILENAME}")
    reader = PdfReader(str(path))
    if len(reader.pages) != 1:
        raise CatalogBodyTemplateError("Șablonul V6 trebuie să conțină exact o pagină.")
    page = reader.pages[0]
    width = float(page.mediabox.width)
    height = float(page.mediabox.height)
    if abs(width - SPREAD_W) > TOLERANCE_PT or abs(height - SPREAD_H) > TOLERANCE_PT:
        raise CatalogBodyTemplateError(
            "Șablonul V6 nu are dimensiunea fizică așteptată de 500 × 350 mm."
        )
    return page


def build_body_template_half(side: str) -> bytes:
    """Returnează jumătatea V6 ca pagină vectorială 350 × 500 mm.

    Decupare: 250 × 350 mm. Scalare uniformă: 1,4.
    Rezultat: 350 × 490 mm, centrat vertical cu 5 mm sus/jos.
    """
    if side not in {"stanga", "dreapta"}:
        raise CatalogBodyTemplateError("Partea șablonului trebuie să fie 'stanga' sau 'dreapta'.")

    source = _validated_source_page()
    x0 = 0.0 if side == "stanga" else HALF_W
    source.mediabox = RectangleObject((x0, 0.0, x0 + HALF_W, SPREAD_H))
    source.cropbox = RectangleObject((x0, 0.0, x0 + HALF_W, SPREAD_H))

    # După decupare, jumătatea dreaptă trebuie readusă cu originea la x=0.
    source.add_transformation(
        Transformation().translate(tx=-x0, ty=0).scale(sx=SCALE, sy=SCALE)
    )

    target = PdfWriter()
    blank = target.add_blank_page(width=PAGE_W, height=PAGE_H)
    source.mediabox = RectangleObject((0.0, 0.0, PAGE_W, SPREAD_H * SCALE))
    source.cropbox = RectangleObject((0.0, 0.0, PAGE_W, SPREAD_H * SCALE))
    source.add_transformation(Transformation().translate(tx=0, ty=Y_OFFSET))
    blank.merge_page(source)

    out = io.BytesIO()
    target.write(out)
    return out.getvalue()


def build_body_template_pair() -> tuple[bytes, bytes]:
    return build_body_template_half("stanga"), build_body_template_half("dreapta")
