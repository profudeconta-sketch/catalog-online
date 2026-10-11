"""Read-only final runtime privilege check for the isolated Streamlit–Neon lab.

This is distinct from the setup diagnostic (which checks CREATE).
No DDL, quota reservations, provider calls or school data.
"""
from __future__ import annotations

from nelutu_neon_isolated_health import TEST_ROLE, TEST_SCHEMA

TEST_TABLE = "nelutu_test_concurenta.nelutu_streamlit_lab_budget"


def runtime_permissions_ready(dsn: str | None, *, enabled: bool = False) -> bool:
    """Require only isolated table read/update privileges and deny schema CREATE."""
    if enabled is not True or not isinstance(dsn, str) or not dsn.startswith(
        ("postgresql://", "postgres://")
    ):
        return False
    try:
        import psycopg
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_user, "
                    "has_schema_privilege(current_user, %s, 'USAGE'), "
                    "has_schema_privilege(current_user, %s, 'CREATE'), "
                    "has_table_privilege(current_user, %s, 'SELECT'), "
                    "has_table_privilege(current_user, %s, 'UPDATE'), "
                    "has_table_privilege(current_user, "
                    "'public.nelutu_gemini_budget', "
                    "'SELECT, INSERT, UPDATE, DELETE, TRUNCATE')",
                    (TEST_SCHEMA, TEST_SCHEMA, TEST_TABLE, TEST_TABLE),
                )
                row = cur.fetchone()
                return (
                    isinstance(row, (tuple, list))
                    and len(row) == 6
                    and row[0] == TEST_ROLE
                    and row[1] is True
                    and row[2] is False
                    and row[3] is True
                    and row[4] is True
                    and row[5] is False
                )
    except Exception:
        return False
