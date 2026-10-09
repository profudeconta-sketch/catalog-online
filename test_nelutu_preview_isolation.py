"""Verifică izolarea laboratorului fără să pornească server sau să citească date."""
import os
import subprocess
import sys
import unittest

class PreviewIsolationTests(unittest.TestCase):
    def test_preview_disabled_before_streamlit_import(self):
        env = dict(os.environ)
        env.pop("NELUTU_LOCAL_DIALOGUE_EXPERIMENTAL", None)
        code = (
            "import runpy,sys;"
            "runpy.run_path('nelutu_dialogue_preview.py', run_name='__main__')"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            env=env, capture_output=True, text=True, timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dezactivat implicit", result.stderr + result.stdout)
        self.assertNotIn("ModuleNotFoundError", result.stderr)

    def test_preview_has_no_direct_school_storage_imports(self):
        from pathlib import Path
        source = Path("nelutu_dialogue_preview.py").read_text(encoding="utf-8")
        for forbidden in ("document_storage", "notification_storage",
                          "openpyxl", "github", "gestiune_elevi",
                          "catalog_scolar", "st.secrets"):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

if __name__ == "__main__":
    unittest.main()
