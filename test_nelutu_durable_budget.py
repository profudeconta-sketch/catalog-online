"""Stage 39 offline tests for a persistent Gemini quota prototype."""
import os
import multiprocessing
import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from nelutu_durable_budget import DurableBudget


def _reserve_in_process(path):
    return DurableBudget(path, limit=12).reserve()


class DurableBudgetTests(unittest.TestCase):
    def test_requires_explicit_absolute_path(self):
        for path in ("", "budget.db", "../budget.db"):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    DurableBudget(path)

    def test_survives_new_objects_and_blocks_after_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "isolated_gemini_quota.sqlite3")
            self.assertEqual(DurableBudget(path, limit=3).remaining(), 0)
            self.assertTrue(DurableBudget(path, limit=3).reserve())
            self.assertTrue(DurableBudget(path, limit=3).reserve())
            self.assertTrue(DurableBudget(path, limit=3).reserve())
            self.assertFalse(DurableBudget(path, limit=3).reserve())
            self.assertEqual(DurableBudget(path, limit=3).remaining(), 0)
            with sqlite3.connect(path) as db:
                self.assertEqual(db.execute("SELECT used FROM gemini_budget").fetchone()[0], 3)

    def test_parallel_reservations_never_exceed_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "isolated_gemini_quota.sqlite3")
            with ThreadPoolExecutor(max_workers=16) as pool:
                results = list(pool.map(
                    lambda _: DurableBudget(path, limit=12).reserve(), range(48)))
            self.assertEqual(sum(results), 12)
            self.assertFalse(DurableBudget(path).reserve())

    def test_parallel_processes_share_one_atomic_limit(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "quota.sqlite3")
            with multiprocessing.get_context("spawn").Pool(processes=4) as pool:
                results = pool.map(_reserve_in_process, [path] * 24)
            self.assertEqual(sum(results), 12)
            self.assertEqual(DurableBudget(path).remaining(), 0)

    def test_new_process_sees_previous_reservations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "quota.sqlite3")
            self.assertTrue(DurableBudget(path, limit=2).reserve())
            with multiprocessing.get_context("spawn").Pool(processes=1) as pool:
                self.assertTrue(pool.apply(_reserve_in_process, (path,)))
                self.assertFalse(pool.apply(_reserve_in_process, (path,)))
            self.assertFalse(DurableBudget(path, limit=2).reserve())

    def test_preview_opt_in_and_fail_closed_wiring(self):
        source = Path(__file__).with_name("nelutu_gemini_preview.py").read_text(encoding="utf-8")
        self.assertIn('st.secrets.get("NELUTU_DURABLE_BUDGET_ENABLED", False) is True', source)
        self.assertIn('st.secrets.get("NELUTU_DURABLE_BUDGET_PATH", "")', source)
        self.assertIn("if durable_budget is None or not shared_budget.allowed()", source)
        self.assertIn("if not durable_budget.reserve():", source)
        self.assertLess(source.index("if not durable_budget.reserve():"), source.index("if budget_gate.reserve(shared_budget):"))

    def test_missing_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "not-created" / "quota.sqlite3")
            budget = DurableBudget(path)
            self.assertFalse(budget.reserve())
            self.assertEqual(budget.remaining(), 0)


if __name__ == "__main__":
    unittest.main()
