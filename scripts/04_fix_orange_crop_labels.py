from __future__ import annotations

import csv
import re
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"

CROP_NAMES = ["apple", "broccoli", "leek", "mushroom"]
LABEL_PREFIX_TO_CROP = {
    "a": "apple",
    "ap": "apple",
    "b": "broccoli",
    "br": "broccoli",
    "broc": "broccoli",
    "l": "leek",
    "le": "leek",
    "m": "mushroom",
    "mu": "mushroom",
}


def normalize_name(value: object) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^0-9a-z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text


def infer_crop(value: object) -> str | None:
    text = str(value).strip().lower()
    if not text or text == "nan":
        return None

    for crop in CROP_NAMES:
        if crop in text:
            return crop

    normalized = normalize_name(text)
    match = re.match(r"^([a-z]+)_?\d+$", normalized)
    if match:
        prefix = match.group(1)
        if prefix in LABEL_PREFIX_TO_CROP:
            return LABEL_PREFIX_TO_CROP[prefix]
        first_letter = prefix[:1]
        if first_letter in LABEL_PREFIX_TO_CROP:
            return LABEL_PREFIX_TO_CROP[first_letter]

    return None


def fix_csv(path: Path) -> int:
    if not path.exists():
        return 0

    df = pd.read_csv(path)
    if "crop" not in df.columns:
        return 0

    original = df["crop"].copy()
    df["crop"] = df["crop"].map(lambda value: infer_crop(value) or value)
    changed = int((original != df["crop"]).sum())
    if changed:
        df.to_csv(path, index=False)
    return changed


def fix_orange_tab(path: Path) -> int:
    if not path.exists():
        return 0

    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.reader(handle, delimiter="\t"))

    if len(rows) < 4:
        return 0

    names, types, flags = rows[0], rows[1], rows[2]
    target_indexes = []
    if "crop" in names:
        target_indexes.append(names.index("crop"))
    target_indexes.extend(index for index, flag in enumerate(flags) if flag == "class")
    target_indexes = sorted(set(target_indexes))

    changed = 0
    for row in rows[3:]:
        for index in target_indexes:
            if index >= len(row):
                continue
            crop = infer_crop(row[index])
            if crop is not None and row[index] != crop:
                row[index] = crop
                changed += 1

    for index in target_indexes:
        if index < len(types) and index < len(names) and names[index] == "crop":
            types[index] = "d"

    if changed:
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.writer(handle, delimiter="\t", lineterminator="\n")
            writer.writerows(rows)

    return changed


def main() -> None:
    targets = {
        "spectrofood_ml.csv": fix_csv(PROCESSED_DIR / "spectrofood_ml.csv"),
        "spectrofood_regression_orange.tab": fix_orange_tab(PROCESSED_DIR / "spectrofood_regression_orange.tab"),
        "spectrofood_classification_orange.tab": fix_orange_tab(PROCESSED_DIR / "spectrofood_classification_orange.tab"),
    }

    print("Crop label repair complete.")
    for name, changed in targets.items():
        print(f"  {name}: {changed} value(s) changed")


if __name__ == "__main__":
    main()
