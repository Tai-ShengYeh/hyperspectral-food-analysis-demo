from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"


def rename_wavelength_column(name: object) -> str:
    text = str(name)
    match = re.fullmatch(r"wl_(\d+)_([0-9]+)(?:_\d+)?", text)
    if match:
        return f"{match.group(1)}.{match.group(2)}"

    match = re.fullmatch(r"wl_(\d+)(?:_\d+)?", text)
    if match:
        return match.group(1)

    return text


def rename_csv(path: Path) -> int:
    if not path.exists():
        return 0

    df = pd.read_csv(path)
    rename_map = {
        col: rename_wavelength_column(col)
        for col in df.columns
        if rename_wavelength_column(col) != col
    }
    if not rename_map:
        return 0

    df = df.rename(columns=rename_map)
    df.to_csv(path, index=False)
    return len(rename_map)


def rename_orange_tab(path: Path) -> int:
    if not path.exists():
        return 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))

    if not rows:
        return 0

    changed = 0
    names = rows[0]
    for index, name in enumerate(names):
        new_name = rename_wavelength_column(name)
        if new_name != name:
            names[index] = new_name
            changed += 1

    if changed:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerows(rows)

    return changed


def rename_metadata(path: Path) -> int:
    if not path.exists():
        return 0

    metadata = json.loads(path.read_text(encoding="utf-8"))
    features = metadata.get("feature_columns")
    if not isinstance(features, list):
        return 0

    renamed = [rename_wavelength_column(feature) for feature in features]
    changed = sum(1 for old, new in zip(features, renamed) if old != new)
    if changed:
        metadata["feature_columns"] = renamed
        path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")

    return changed


def main() -> None:
    results = {
        "spectrofood_ml.csv": rename_csv(PROCESSED_DIR / "spectrofood_ml.csv"),
        "spectrofood_summary_by_crop.csv": rename_csv(PROCESSED_DIR / "spectrofood_summary_by_crop.csv"),
        "spectrofood_regression_orange.tab": rename_orange_tab(PROCESSED_DIR / "spectrofood_regression_orange.tab"),
        "spectrofood_classification_orange.tab": rename_orange_tab(PROCESSED_DIR / "spectrofood_classification_orange.tab"),
        "spectrofood_metadata.json": rename_metadata(PROCESSED_DIR / "spectrofood_metadata.json"),
    }

    print("Wavelength column rename complete.")
    for name, changed in results.items():
        print(f"  {name}: {changed} column(s) renamed")


if __name__ == "__main__":
    main()
