from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    ROOT / "scripts" / "01_download_spectrofood.py",
    ROOT / "scripts" / "02_prepare_spectrofood.py",
    ROOT / "scripts" / "04_fix_orange_crop_labels.py",
    ROOT / "scripts" / "05_rename_wavelength_columns.py",
    ROOT / "scripts" / "03_python_teaching_demo.py",
]


def main() -> None:
    for script in SCRIPTS:
        print(f"\n=== Running {script.name} ===")
        subprocess.check_call([sys.executable, str(script)], cwd=ROOT)


if __name__ == "__main__":
    main()
