"""Read-only diagnostic of isolated Neon access; no credentials or SQL errors exposed."""
from __future__ import annotations

from importlib.util import find_spec

from nelutu_neon_isolated_health import TEST_ROLE, TEST_SCHEMA


def diagnose_isolated_neon(dsn: str | None) -> str:
    """Return a coarse safe status, never an exception or connection string."""
    if not isinstance(dsn, str) or not dsn:
        return "missing_secret"
    if not dsn.startswith(("postgresql://", "postgres://")):
        return "invalid_scheme"
    if find_spec("psycopg") is None:
        return "missing_driver"
    try:
        import psycopg
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_user")
                row = cur.fetchone()
                if not row or row[0] != TEST_ROLE:
                    return "wrong_role"
                cur.execute(
                    "SELECT has_schema_privilege(current_user, %s, 'USAGE'), "
                    "has_table_privilege(current_user, "
                    "'public.nelutu_gemini_budget', 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE')",
                    (TEST_SCHEMA,),
                )
                permissions = cur.fetchone()
                if not permissions or permissions[0] is not True or permissions[1] is not False:
                    return "permissions_failed"
                return "ready"
    except Exception:
        return "connection_or_query_failed"
