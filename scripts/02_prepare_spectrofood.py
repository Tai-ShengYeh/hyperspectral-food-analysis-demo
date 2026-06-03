from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
RAW_FILE = ROOT / "data" / "raw" / "SpectroFood_dataset.csv"
PROCESSED_DIR = ROOT / "data" / "processed"


CROP_NAMES = ["apple", "broccoli", "leek", "mushroom"]


def normalize_name(value: object) -> str:
    text = str(value).strip()
    text = text.replace("%", "pct")
    text = re.sub(r"[^0-9A-Za-z]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text.lower() or "unnamed"


def coerce_numeric_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")

    text = series.astype(str).str.strip()
    text = text.str.replace("\u2212", "-", regex=False)

    comma_decimal = text.str.contains(",", regex=False).mean() > 0.2
    dot_decimal = text.str.contains(".", regex=False).mean() > 0.2
    if comma_decimal and not dot_decimal:
        text = text.str.replace(",", ".", regex=False)

    return pd.to_numeric(text, errors="coerce")


def detect_target_column(df: pd.DataFrame) -> str:
    candidates = []
    for col in df.columns:
        low = str(col).lower()
        score = 0
        if "dry" in low:
            score += 3
        if "matter" in low:
            score += 3
        if low in {"dm", "dmc"}:
            score += 2
        if "%" in low or "pct" in low:
            score += 1
        if score:
            candidates.append((score, col))

    if candidates:
        candidates.sort(reverse=True, key=lambda item: item[0])
        return str(candidates[0][1])

    numeric_cols = []
    for col in df.columns:
        numeric = coerce_numeric_series(df[col])
        if numeric.notna().mean() > 0.8:
            numeric_cols.append(str(col))

    if not numeric_cols:
        raise ValueError("Could not detect a numeric target column.")

    return numeric_cols[0]


def detect_crop_column(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        values = df[col].astype(str).str.lower()
        hits = sum(values.str.contains(name, regex=False).any() for name in CROP_NAMES)
        if hits >= 2:
            return str(col)
    return None


def extract_crop(row: pd.Series, crop_col: str | None) -> str:
    if crop_col is not None:
        text = str(row[crop_col]).lower()
        for crop in CROP_NAMES:
            if crop in text:
                return crop
        cleaned = normalize_name(row[crop_col])
        return cleaned or "unknown"

    combined = " ".join(str(value).lower() for value in row.values)
    for crop in CROP_NAMES:
        if crop in combined:
            return crop
    return "unknown"


def parse_wavelength_from_column(col: str) -> float | None:
    text = str(col).strip().lower()
    text = text.replace(",", ".")
    match = re.search(r"(\d{3,4}(?:\.\d+)?)", text)
    if not match:
        return None
    value = float(match.group(1))
    if 350 <= value <= 2500:
        return value
    return None


def detect_spectral_columns(df: pd.DataFrame, target_col: str, crop_col: str | None) -> list[str]:
    spectral = []
    excluded = {target_col}
    if crop_col:
        excluded.add(crop_col)

    for col in df.columns:
        if str(col) in excluded:
            continue

        wavelength = parse_wavelength_from_column(str(col))
        numeric = coerce_numeric_series(df[col])
        numeric_ratio = numeric.notna().mean()

        if wavelength is not None and numeric_ratio > 0.5:
            spectral.append(str(col))

    if len(spectral) >= 10:
        spectral.sort(key=lambda name: parse_wavelength_from_column(name) or 0)
        return spectral

    numeric_features = []
    for col in df.columns:
        if str(col) in excluded:
            continue
        numeric = coerce_numeric_series(df[col])
        if numeric.notna().mean() > 0.8:
            numeric_features.append(str(col))

    if len(numeric_features) < 10:
        raise ValueError(
            "Could not detect enough spectral columns. "
            "Check the CSV format or inspect data/raw/SpectroFood_dataset.csv."
        )

    return numeric_features


def orange_type_for_discrete(values: pd.Series) -> str:
    return "d"


def write_orange_tab(
    df: pd.DataFrame,
    output: Path,
    target: str,
    target_type: str,
    meta_columns: set[str] | None = None,
) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    meta_columns = meta_columns or set()

    names = list(df.columns)
    types = []
    flags = []
    for col in names:
        if col in meta_columns:
            if col == "sample_id":
                types.append("s")
            elif col == "crop":
                types.append(orange_type_for_discrete(df[col]))
            else:
                types.append("c")
            flags.append("meta")
        elif col == "crop":
            if target == "crop":
                types.append(orange_type_for_discrete(df[col]))
                flags.append("class")
            else:
                types.append(orange_type_for_discrete(df[col]))
                flags.append("meta")
        elif col == target:
            types.append(target_type)
            flags.append("class")
        else:
            types.append("c")
            flags.append("")

    with output.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\t".join(names) + "\n")
        handle.write("\t".join(types) + "\n")
        handle.write("\t".join(flags) + "\n")
        df.to_csv(handle, sep="\t", index=False, header=False)


def main(argv: list[str] | None = None) -> None:
    if not RAW_FILE.exists():
        raise SystemExit(
            f"Missing {RAW_FILE}. Run scripts/01_download_spectrofood.py first."
        )

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(RAW_FILE, sep=None, engine="python")
    raw.columns = [str(col).strip() for col in raw.columns]

    target_col = detect_target_column(raw)
    crop_col = detect_crop_column(raw)
    spectral_cols = detect_spectral_columns(raw, target_col, crop_col)

    ml = pd.DataFrame()
    ml["sample_id"] = [f"S{i + 1:04d}" for i in range(len(raw))]
    ml["crop"] = raw.apply(lambda row: extract_crop(row, crop_col), axis=1)
    ml["dry_matter_pct"] = coerce_numeric_series(raw[target_col])

    wavelength_names = []
    wavelengths = []
    for index, col in enumerate(spectral_cols, start=1):
        wavelength = parse_wavelength_from_column(col)
        wavelengths.append(wavelength if wavelength is not None else float(index))
        if wavelength is not None:
            feature_name = f"wl_{wavelength:g}".replace(".", "_")
        else:
            feature_name = f"wl_{index:03d}"
        while feature_name in ml.columns or feature_name in wavelength_names:
            feature_name = f"{feature_name}_{index}"
        wavelength_names.append(feature_name)
        ml[feature_name] = coerce_numeric_series(raw[col])

    ml = ml.dropna(subset=["dry_matter_pct"]).reset_index(drop=True)
    all_wavelength_names = list(wavelength_names)
    all_wavelengths = list(wavelengths)
    usable_wavelength_names = [
        name for name in wavelength_names if ml[name].notna().mean() >= 0.5 and ml[name].nunique(dropna=True) > 1
    ]
    if len(usable_wavelength_names) < 5:
        raise ValueError("Too few usable spectral columns after numeric conversion.")
    wavelength_names = usable_wavelength_names
    wavelengths = [
        all_wavelengths[all_wavelength_names.index(name)]
        for name in wavelength_names
    ]
    spectral_medians = ml[wavelength_names].median(numeric_only=True)
    ml[wavelength_names] = ml[wavelength_names].fillna(spectral_medians)

    ml_csv = PROCESSED_DIR / "spectrofood_ml.csv"
    ml.to_csv(ml_csv, index=False)

    regression_cols = ["sample_id", "crop"] + wavelength_names + ["dry_matter_pct"]
    classification_cols = ["sample_id", "dry_matter_pct"] + wavelength_names + ["crop"]

    write_orange_tab(
        ml[regression_cols],
        PROCESSED_DIR / "spectrofood_regression_orange.tab",
        target="dry_matter_pct",
        target_type="c",
        meta_columns={"sample_id", "crop"},
    )
    write_orange_tab(
        ml[classification_cols],
        PROCESSED_DIR / "spectrofood_classification_orange.tab",
        target="crop",
        target_type=orange_type_for_discrete(ml["crop"]),
        meta_columns={"sample_id", "dry_matter_pct"},
    )

    summary = (
        ml.groupby("crop")
        .agg(samples=("sample_id", "count"), dry_matter_mean=("dry_matter_pct", "mean"), dry_matter_sd=("dry_matter_pct", "std"))
        .reset_index()
    )
    summary.to_csv(PROCESSED_DIR / "spectrofood_summary_by_crop.csv", index=False)

    metadata = {
        "source_file": str(RAW_FILE),
        "rows": int(len(ml)),
        "target_column_detected": target_col,
        "crop_column_detected": crop_col,
        "spectral_columns_detected": len(spectral_cols),
        "feature_columns": wavelength_names,
        "wavelengths": wavelengths,
        "crops": sorted(ml["crop"].unique().tolist()),
        "outputs": {
            "python_ml_csv": str(ml_csv),
            "orange_regression": str(PROCESSED_DIR / "spectrofood_regression_orange.tab"),
            "orange_classification": str(PROCESSED_DIR / "spectrofood_classification_orange.tab"),
        },
    }
    (PROCESSED_DIR / "spectrofood_metadata.json").write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Prepared SpectroFood teaching data")
    print(f"  Samples: {len(ml)}")
    print(f"  Spectral features: {len(wavelength_names)}")
    print(f"  Crops: {', '.join(metadata['crops'])}")
    print(f"  Python CSV: {ml_csv}")
    print(f"  Orange regression: {PROCESSED_DIR / 'spectrofood_regression_orange.tab'}")
    print(f"  Orange classification: {PROCESSED_DIR / 'spectrofood_classification_orange.tab'}")


if __name__ == "__main__":
    main(sys.argv[1:])
