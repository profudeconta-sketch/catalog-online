"""Experimental PostgreSQL quota adapter. Not wired to Streamlit or Gemini.

Requires optional psycopg 3 and a dedicated PostgreSQL database. Never pass school
records, prompts, API keys or student identifiers to this module.
"""
from __future__ import annotations

import os

MAX_ATTEMPTS = 12


class PostgreSQLBudget:
    """Atomic, fail-closed quota; no automatic refunds or resets.\n\n    Provision the table and singleton row separately; runtime needs only\n    SELECT and UPDATE permissions on the budget table."""

    def __init__(self, dsn: str, limit: int = MAX_ATTEMPTS):
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("Dedicated PostgreSQL DSN required")
        if type(limit) is not int or limit < 1:
            raise ValueError("Positive integer limit required")
        self._dsn = dsn
        self.limit = limit

    def reserve(self) -> bool:
        """Reserve before any outbound request; any DB failure denies access."""
        try:
            import psycopg
            with psycopg.connect(self._dsn, connect_timeout=5) as conn:
                with conn.transaction():
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE public.nelutu_gemini_budget SET used = used + 1 "
                            "WHERE id = 1 AND used < %s RETURNING used",
                            (self.limit,),
                        )
                        return cur.fetchone() is not None
        except Exception:
            return False

    def remaining(self) -> int:
        try:
            import psycopg
            with psycopg.connect(self._dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT used FROM public.nelutu_gemini_budget WHERE id = 1")
                    row = cur.fetchone()
                    return max(0, self.limit - row[0]) if row else 0
        except Exception:
            return 0
