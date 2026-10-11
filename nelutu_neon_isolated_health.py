"""Read-only, opt-in health probe for an isolated Neon laboratory.

No DDL, writes, provider calls or school data. Never use an admin DSN.
A missing/invalid setting or any DB error returns False (fail closed).
"""
from __future__ import annotations

TEST_ROLE = "nelutu_test_runner"
TEST_SCHEMA = "nelutu_test_concurenta"


def isolated_neon_ready(dsn: str | None, *, enabled: bool = False) -> bool:
    """Check only dedicated test role and schema access, without mutations."""
    if enabled is not True or not isinstance(dsn, str):
        return False
    if not dsn.startswith(("postgresql://", "postgres://")):
        return False
    try:
        import psycopg
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT current_user, "
                    "has_schema_privilege(current_user, %s, 'USAGE'), "
                    "has_table_privilege(current_user, "
                    "'public.nelutu_gemini_budget', "
                    "'SELECT, INSERT, UPDATE, DELETE, TRUNCATE')",
                    (TEST_SCHEMA,),
                )
                row = cur.fetchone()
                return (
                    isinstance(row, (tuple, list))
                    and len(row) == 3
                    and row[0] == TEST_ROLE
                    and row[1] is True
                    and row[2] is False
                )
    except Exception:
        return False
