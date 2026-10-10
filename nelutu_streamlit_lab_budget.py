"""Isolated persistent counter for laboratory-only tests.

This module is NOT connected to Gemini, school apps or the live quota table.
Provision the dedicated test table manually with a restricted role.
Runtime never creates, deletes, resets or alters database objects.
"""
from __future__ import annotations

from nelutu_neon_isolated_health import isolated_neon_ready

SCHEMA = "nelutu_test_concurenta"
TABLE = "nelutu_streamlit_lab_budget"
LIMIT = 3


class IsolatedLabBudget:
    def __init__(self, dsn: str, *, enabled: bool = False):
        if enabled is not True or not isinstance(dsn, str) or not dsn.startswith(
            ("postgresql://", "postgres://")
        ):
            raise ValueError("Isolated lab budget disabled or invalid")
        self._dsn = dsn

    def _ready(self) -> bool:
        return isolated_neon_ready(self._dsn, enabled=True)

    def remaining(self) -> int:
        if not self._ready():
            return 0
        try:
            import psycopg
            with psycopg.connect(self._dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT used FROM nelutu_test_concurenta.nelutu_streamlit_lab_budget "
                        "WHERE id = 1"
                    )
                    row = cur.fetchone()
                    if not row or type(row[0]) is not int or not 0 <= row[0] <= LIMIT:
                        return 0
                    return LIMIT - row[0]
        except Exception:
            return 0

    def reserve(self) -> bool:
        """Atomically reserve one fictitious test token, fail closed."""
        if not self._ready():
            return False
        try:
            import psycopg
            with psycopg.connect(self._dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE nelutu_test_concurenta.nelutu_streamlit_lab_budget "
                        "SET used = used + 1 WHERE id = 1 AND used >= 0 AND used < %s "
                        "RETURNING used",
                        (LIMIT,),
                    )
                    return cur.fetchone() is not None
        except Exception:
            return False
