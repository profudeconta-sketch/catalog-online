"""Hartă geometrică măsurată direct din șablonul V6 aprobat.

Coordonatele sunt în puncte PDF în spațiul logic al deschiderii 500 x 350 mm,
cu originea PDF în stânga-jos. Nu conține logică de date și nu modifică surse.
"""

from __future__ import annotations

from dataclasses import dataclass

MM_TO_PT = 72.0 / 25.4
SPREAD_HEIGHT_PT = 350 * MM_TO_PT
CENTER_X_PT = 250 * MM_TO_PT

# Măsurate din vectorii șablonului V6 (toleranță de extracție sub 0,1 pt).
LEFT_OUTER_X = 22.67717
LEFT_IDENTITY_RIGHT_X = 187.08656
LEFT_AUX_RIGHT_X = 225.35431
LEFT_SUBJECT_RIGHT_X = 702.99213

RIGHT_SUBJECT_LEFT_X = 714.33069
RIGHT_SUBJECT_RIGHT_X = 1315.27563
RIGHT_TERMINAL_RIGHT_X = 1394.64612

LEFT_SUBJECT_EDGES_X = (
    225.35429, 268.77591, 312.19754, 355.61923, 399.04083, 442.46243,
    485.88403, 529.30560, 572.72736, 616.14893, 659.57056, 702.99213,
)
RIGHT_SUBJECT_EDGES_X = (
    714.33069, 757.25531, 800.17993, 843.10461, 886.02924, 928.95380,
    971.87854, 1014.80310, 1057.72766, 1100.65271, 1143.57666,
    1186.50171, 1229.42664, 1272.35071, 1315.27563,
)

# Coordonate PyMuPDF (origine sus-stânga) convertite mai jos la origine PDF.
_BLOCKS_TOP_COORDS = (
    (110.55115, 384.18896, (344.50, 357.73, 370.96)),
    (390.42517, 664.06299, (624.38, 637.61, 650.83)),
    (670.29919, 943.93701, (904.25, 917.48, 930.71)),
)


@dataclass(frozen=True)
class StudentBlockGeometry:
    top_y: float
    bottom_y: float
    mean_lines_y: tuple[float, float, float]


def _pdf_y(top_origin_y: float) -> float:
    return SPREAD_HEIGHT_PT - top_origin_y


STUDENT_BLOCKS = tuple(
    StudentBlockGeometry(
        top_y=_pdf_y(top),
        bottom_y=_pdf_y(bottom),
        mean_lines_y=tuple(_pdf_y(y) for y in mean_lines),
    )
    for top, bottom, mean_lines in _BLOCKS_TOP_COORDS
)


def half_local_x(spread_x: float, side: str) -> float:
    if side == "stanga":
        return spread_x
    if side == "dreapta":
        return spread_x - CENTER_X_PT
    raise ValueError("side trebuie să fie 'stanga' sau 'dreapta'")


def output_xy(spread_x: float, spread_y: float, side: str) -> tuple[float, float]:
    """Transformarea exactă V6 -> pagina oficială: scalare 1,4 + 5 mm vertical."""
    return (
        half_local_x(spread_x, side) * 1.4,
        spread_y * 1.4 + 5 * MM_TO_PT,
    )
