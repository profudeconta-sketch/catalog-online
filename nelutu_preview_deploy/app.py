"""Isolated deployment entrypoint for Neluțu preview, not school apps."""
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
runpy.run_path(str(ROOT / "nelutu_gemini_preview.py"), run_name="__main__")
