"""Read-only diagnostic of isolated Neon access; no credentials or SQL errors exposed."""
from __future__ import annotations

from importlib.util import find_spec
from urllib.parse import urlsplit, unquote

from nelutu_neon_isolated_health import TEST_ROLE, TEST_SCHEMA


def diagnose_isolated_neon(dsn: str | None) -> str:
    """Return a coarse safe status, never an exception or connection string."""
    if not isinstance(dsn, str) or not dsn:
        return "missing_secret"
    if not dsn.startswith(("postgresql://", "postgres://")):
        return "invalid_scheme"
    if find_spec("psycopg") is None:
        return "missing_driver"
    # Check only the structure of the private DSN; never expose its contents.
    try:
        parsed = urlsplit(dsn)
        if not parsed.hostname:
            return "dsn_missing_host"
        if not parsed.username:
            return "dsn_missing_user"
        if not parsed.path.strip("/"):
            return "dsn_missing_database"
        if not parsed.password or parsed.password == "****":
            return "dsn_missing_password"
        if unquote(parsed.username) != TEST_ROLE:
            return "dsn_wrong_role"
    except (ValueError, AttributeError):
        return "incomplete_dsn"
    try:
        import psycopg
        conn = psycopg.connect(dsn, connect_timeout=5)
    except Exception as exc:
        # Classify using driver exception classes only, not exception text:
        # error messages may contain private hostnames, usernames or DSN fragments.
        if isinstance(exc, psycopg.OperationalError):
            return "connection_operational_failure"
        return "connection_other_failure"
    try:
        with conn:
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
                cur.execute(
                    "SELECT has_schema_privilege(current_user, %s, 'CREATE')",
                    (TEST_SCHEMA,),
                )
                create_permission = cur.fetchone()
                if not create_permission or create_permission[0] is not True:
                    return "schema_create_missing"
                return "ready"
    except Exception:
        return "query_failed"
