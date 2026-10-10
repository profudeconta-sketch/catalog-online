"""Opt-in live Neon concurrency test, isolated from the real Gemini budget.

Run ONLY after reviewing the zero-cost free-tier and using a dedicated TEST
database role/connection via NELUTU_TEST_DATABASE_URL environment variable.
Never paste the DSN in chat, logs, or GitHub. No Gemini calls are made.

The test uses a uniquely named table inside nelutu_test_concurenta and
attempts to drop it in finally. This role needs CREATE only in that schema. It never reads,
writes, resets, or drops nelutu_gemini_budget.
"""
from __future__ import annotations

import os
import secrets
from concurrent.futures import ThreadPoolExecutor

DSN_ENV = "NELUTU_TEST_DATABASE_URL"
WORKERS = 8
LIMIT = 3


def run() -> bool:
    dsn = os.environ.get(DSN_ENV)
    if not dsn or not dsn.startswith(("postgresql://", "postgres://")):
        print("SKIP: dedicated test connection not configured")
        return False
    try:
        import psycopg
        from psycopg import sql
    except ImportError:
        print("SKIP: psycopg not installed")
        return False

    name = "nelutu_concurrency_test_" + secrets.token_hex(8)
    identifier = sql.Identifier("nelutu_test_concurenta", name)
    try:
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT current_user")
                role = cur.fetchone()[0]
                if role != "nelutu_test_runner":
                    print("DENIED: dedicated test role required")
                    return False
                cur.execute(
                    "SELECT has_table_privilege(current_user, "
                    "'public.nelutu_gemini_budget', 'SELECT, INSERT, UPDATE, DELETE, TRUNCATE')"
                )
                if cur.fetchone()[0]:
                    print("DENIED: test role can access live budget")
                    return False
                cur.execute(sql.SQL("CREATE TABLE {} (id integer PRIMARY KEY, used integer NOT NULL CHECK (used >= 0))").format(identifier))
                cur.execute(sql.SQL("INSERT INTO {} (id, used) VALUES (1, 0)").format(identifier))
        def reserve(_):
            try:
                with psycopg.connect(dsn, connect_timeout=5) as conn:
                    with conn.cursor() as cur:
                        cur.execute(sql.SQL(
                            "UPDATE {} SET used = used + 1 WHERE id = 1 AND used < %s RETURNING used"
                        ).format(identifier), (LIMIT,))
                        return cur.fetchone() is not None
            except Exception:
                raise RuntimeError("Reservation failed; test is inconclusive") from None
        with ThreadPoolExecutor(max_workers=WORKERS) as pool:
            results = list(pool.map(reserve, range(WORKERS)))
        with psycopg.connect(dsn, connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute(sql.SQL("SELECT used FROM {} WHERE id = 1").format(identifier))
                used = cur.fetchone()[0]
        passed = used == LIMIT and sum(results) == LIMIT
        print("PASS" if passed else "FAIL", "successful reservations:", sum(results), "stored:", used)
    finally:
        cleanup_ok = False
        try:
            with psycopg.connect(dsn, connect_timeout=5) as conn:
                with conn.cursor() as cur:
                    cur.execute(sql.SQL("DROP TABLE IF EXISTS {}").format(identifier))
            cleanup_ok = True
        except Exception:
            print("WARNING: cleanup failed; remove isolated test table manually")
        if not cleanup_ok:
            raise RuntimeError("Isolated test table cleanup could not be verified") from None
    return passed


if __name__ == "__main__":
    raise SystemExit(0 if run() else 1)
