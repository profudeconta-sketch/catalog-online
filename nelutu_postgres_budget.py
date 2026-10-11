"""Fail-closed atomic daily/minute Gemini quota for the dedicated Neon database.

Requires a one-time additive schema migration. Never logs or stores school data.
Google free-tier rate limits remain authoritative; no retry on 429.
"""
from __future__ import annotations

MAX_ATTEMPTS = 450
MAX_PER_MINUTE = 12


class PostgreSQLBudget:
    """Shared quota, Pacific-calendar daily reset, atomic per-minute throttling."""

    def __init__(self, dsn: str, limit: int = MAX_ATTEMPTS):
        if not isinstance(dsn, str) or not dsn.strip():
            raise ValueError("Dedicated PostgreSQL DSN required")
        if type(limit) is not int or not 1 <= limit <= MAX_ATTEMPTS:
            raise ValueError("Daily limit must be between 1 and 450")
        self._dsn = dsn
        self.limit = limit

    def reserve(self) -> bool:
        """One atomic reservation; missing migration/permissions fail closed."""
        try:
            import psycopg
            with psycopg.connect(self._dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        WITH clock AS (
                            SELECT
                                (now() AT TIME ZONE 'America/Los_Angeles')::date AS day,
                                date_trunc('minute', now()) AS minute
                        )
                        UPDATE public.nelutu_gemini_budget AS b
                        SET
                            used = CASE WHEN b.budget_day = clock.day
                                THEN b.used + 1 ELSE 1 END,
                            budget_day = clock.day,
                            minute_used = CASE WHEN b.minute_window = clock.minute
                                THEN b.minute_used + 1 ELSE 1 END,
                            minute_window = clock.minute
                        FROM clock
                        WHERE b.id = 1
                          AND b.used >= 0
                          AND b.minute_used >= 0
                          AND (CASE WHEN b.budget_day = clock.day
                              THEN b.used ELSE 0 END) < %s
                          AND (CASE WHEN b.minute_window = clock.minute
                              THEN b.minute_used ELSE 0 END) < %s
                        RETURNING b.used
                        """,
                        (self.limit, MAX_PER_MINUTE),
                    )
                    return cur.fetchone() is not None
        except Exception:
            return False

    def remaining(self) -> int:
        """Return today's remaining reservations, or zero on any DB error."""
        try:
            import psycopg
            with psycopg.connect(self._dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT used, budget_day,
                               (now() AT TIME ZONE 'America/Los_Angeles')::date
                        FROM public.nelutu_gemini_budget WHERE id = 1
                        """
                    )
                    row = cur.fetchone()
                    if not row or type(row[0]) is not int or row[0] < 0:
                        return 0
                    return max(0, self.limit - row[0]) if row[1] == row[2] else self.limit
        except Exception:
            return 0

    def status(self):
        """Read-only counters; None means unavailable, never guess zero."""
        try:
            import psycopg
            with psycopg.connect(self._dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT used, budget_day, minute_used, minute_window,
                               (now() AT TIME ZONE 'America/Los_Angeles')::date,
                               date_trunc('minute', now())
                        FROM public.nelutu_gemini_budget WHERE id = 1
                        """
                    )
                    row = cur.fetchone()
                    if not row or any(type(row[i]) is not int or row[i] < 0 for i in (0, 2)):
                        return None
                    used = row[0] if row[1] == row[4] else 0
                    minute_used = row[2] if row[3] == row[5] else 0
                    if used > self.limit or minute_used > MAX_PER_MINUTE:
                        return None
                    return {"used": used, "remaining": self.limit - used,
                            "daily_limit": self.limit, "minute_used": minute_used,
                            "minute_limit": MAX_PER_MINUTE, "budget_day": str(row[4])}
        except Exception:
            return None
