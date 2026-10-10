"""Stage 63: quota storage path safety and fail-closed corruption behavior."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from nelutu_durable_budget import DurableBudget


class DurableStorageSafetyTests(unittest.TestCase):
    def test_reject_symlink_to_unrelated_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "unrelated.txt"
            target.write_text("DO NOT TOUCH", encoding="utf-8")
            link = root / "quota.sqlite3"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                DurableBudget(str(link))
            self.assertEqual(target.read_text(encoding="utf-8"), "DO NOT TOUCH")

    def test_reject_symlinked_parent(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            real = root / "real"
            real.mkdir()
            link = root / "link"
            link.symlink_to(real, target_is_directory=True)
            with self.assertRaises(ValueError):
                DurableBudget(str(link / "quota.sqlite3"))

    def test_corrupt_file_blocks_without_overwriting(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "quota.sqlite3"
            path.write_bytes(b"corrupt quota database")
            quota = DurableBudget(str(path))
            self.assertFalse(quota.reserve())
            self.assertEqual(quota.remaining(), 0)
            self.assertEqual(path.read_bytes(), b"corrupt quota database")

    def test_existing_unrelated_table_fails_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "quota.sqlite3"
            with sqlite3.connect(path) as db:
                db.execute("CREATE TABLE gemini_budget (wrong_column INTEGER)")
            self.assertFalse(DurableBudget(str(path)).reserve())


if __name__ == "__main__":
    unittest.main()
