from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.cross_decomposition import PLSRegression
from sklearn.decomposition import PCA
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    mean_absolute_error,
    mean_squared_error,
    r2_score,
)
from sklearn.model_selection import GroupKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = ROOT / "data" / "processed"
OUTPUT_DIR = ROOT / "outputs"
ML_FILE = PROCESSED_DIR / "spectrofood_ml.csv"
METADATA_FILE = PROCESSED_DIR / "spectrofood_metadata.json"


def is_spectral_column(col: str) -> bool:
    text = str(col)
    if text.startswith("wl_") or text.startswith("band_"):
        return True
    try:
        value = float(text)
    except ValueError:
        return False
    return 350 <= value <= 2500


def safe_pls_components(n_samples: int, n_features: int, preferred: int = 12) -> int:
    return max(1, min(preferred, n_features, max(1, n_samples - 1)))


def safe_stratify(labels: pd.Series, test_size: float) -> pd.Series | None:
    counts = labels.value_counts()
    if labels.nunique() < 2 or counts.min() < 2:
        return None

    expected_test = int(np.ceil(len(labels) * test_size))
    expected_train = len(labels) - expected_test
    if expected_test < labels.nunique() or expected_train < labels.nunique():
        return None

    return labels


def rmse(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    return math.sqrt(mean_squared_error(y_true, y_pred))


def plot_mean_spectra(df: pd.DataFrame, features: list[str], wavelengths: list[float]) -> None:
    plt.figure(figsize=(11, 6))
    for crop, group in df.groupby("crop"):
        values = group[features].to_numpy(dtype=float)
        mean = np.nanmean(values, axis=0)
        sd = np.nanstd(values, axis=0)
        plt.plot(wavelengths, mean, label=crop)
        plt.fill_between(wavelengths, mean - sd, mean + sd, alpha=0.12)
    plt.title("Mean VIS-NIR spectra by crop")
    plt.xlabel("Wavelength (nm)")
    plt.ylabel("Reflectance / intensity")
    plt.legend(title="Crop")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "01_mean_spectra_by_crop.png", dpi=180)
    plt.close()


def plot_dry_matter_distribution(df: pd.DataFrame) -> None:
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x="crop", y="dry_matter_pct", color="#b9d7ea")
    sns.stripplot(data=df, x="crop", y="dry_matter_pct", color="#264653", alpha=0.45, size=3)
    plt.title("Dry matter distribution by crop")
    plt.xlabel("Crop")
    plt.ylabel("Dry matter (%)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "02_dry_matter_distribution.png", dpi=180)
    plt.close()


def plot_pca(df: pd.DataFrame, features: list[str]) -> None:
    matrix = SimpleImputer(strategy="median").fit_transform(df[features])
    matrix = StandardScaler().fit_transform(matrix)
    scores = PCA(n_components=2, random_state=42).fit_transform(matrix)
    plot_df = pd.DataFrame({"PC1": scores[:, 0], "PC2": scores[:, 1], "crop": df["crop"]})

    plt.figure(figsize=(8, 6))
    sns.scatterplot(data=plot_df, x="PC1", y="PC2", hue="crop", s=55, alpha=0.85)
    plt.title("PCA score plot of spectra")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "03_pca_crop_scatter.png", dpi=180)
    plt.close()


def train_regression_models(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    X = df[features]
    y = df["dry_matter_pct"].to_numpy(dtype=float)
    stratify = safe_stratify(df["crop"], test_size=0.25)

    X_train, X_test, y_train, y_test, crop_train, crop_test = train_test_split(
        X,
        y,
        df["crop"],
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )

    n_pls = safe_pls_components(len(X_train), len(features), preferred=12)
    models = {
        f"PLSRegression_{n_pls}_components": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", PLSRegression(n_components=n_pls)),
            ]
        ),
        "RandomForestRegressor": Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                (
                    "model",
                    RandomForestRegressor(
                        n_estimators=300,
                        random_state=42,
                        n_jobs=-1,
                        min_samples_leaf=2,
                    ),
                ),
            ]
        ),
    }

    rows = []
    prediction_frames = []
    for name, model in models.items():
        model.fit(X_train, y_train)
        pred = np.ravel(model.predict(X_test))
        rows.append(
            {
                "task": "dry_matter_regression",
                "model": name,
                "rmse": rmse(y_test, pred),
                "mae": mean_absolute_error(y_test, pred),
                "r2": r2_score(y_test, pred),
                "test_samples": len(y_test),
            }
        )
        prediction_frames.append(
            pd.DataFrame(
                {
                    "model": name,
                    "actual": y_test,
                    "predicted": pred,
                    "crop": crop_test.to_numpy(),
                }
            )
        )

    predictions = pd.concat(prediction_frames, ignore_index=True)
    predictions.to_csv(OUTPUT_DIR / "regression_predictions.csv", index=False)

    plt.figure(figsize=(8, 7))
    sns.scatterplot(data=predictions, x="actual", y="predicted", hue="crop", style="model", s=60)
    limit_min = min(predictions["actual"].min(), predictions["predicted"].min())
    limit_max = max(predictions["actual"].max(), predictions["predicted"].max())
    plt.plot([limit_min, limit_max], [limit_min, limit_max], color="#333333", linewidth=1)
    plt.title("Dry matter prediction: actual vs predicted")
    plt.xlabel("Actual dry matter (%)")
    plt.ylabel("Predicted dry matter (%)")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "04_regression_actual_vs_predicted.png", dpi=180)
    plt.close()

    return pd.DataFrame(rows)


def run_leave_one_crop_out(df: pd.DataFrame, features: list[str]) -> pd.DataFrame:
    X = df[features]
    y = df["dry_matter_pct"].to_numpy(dtype=float)
    groups = df["crop"].to_numpy()

    if df["crop"].nunique() < 2:
        return pd.DataFrame()

    rows = []
    splitter = GroupKFold(n_splits=df["crop"].nunique())
    for train_idx, test_idx in splitter.split(X, y, groups=groups):
        held_out = sorted(set(groups[test_idx]))[0]
        model = Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("model", PLSRegression(n_components=safe_pls_components(len(train_idx), len(features), preferred=8))),
            ]
        )
        model.fit(X.iloc[train_idx], y[train_idx])
        pred = np.ravel(model.predict(X.iloc[test_idx]))
        rows.append(
            {
                "held_out_crop": held_out,
                "model": "PLSRegression_leave_one_crop_out",
                "rmse": rmse(y[test_idx], pred),
                "mae": mean_absolute_error(y[test_idx], pred),
                "r2": r2_score(y[test_idx], pred) if len(test_idx) > 1 else np.nan,
                "test_samples": len(test_idx),
            }
        )
    result = pd.DataFrame(rows)
    result.to_csv(OUTPUT_DIR / "leave_one_crop_out_regression.csv", index=False)
    return result


def train_classifier(df: pd.DataFrame, features: list[str], wavelengths: list[float]) -> pd.DataFrame:
    class_counts = df["crop"].value_counts()
    keep_classes = class_counts[class_counts >= 2].index
    df = df[df["crop"].isin(keep_classes)].copy()

    if df["crop"].nunique() < 2:
        return pd.DataFrame()

    X = df[features]
    y = df["crop"]
    stratify = safe_stratify(y, test_size=0.25)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.25,
        random_state=42,
        stratify=stratify,
    )

    model = Pipeline(
        [
            ("imputer", SimpleImputer(strategy="median")),
            (
                "model",
                RandomForestClassifier(
                    n_estimators=300,
                    random_state=42,
                    n_jobs=-1,
                    min_samples_leaf=2,
                ),
            ),
        ]
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, pred)

    labels = sorted(y.unique())
    cm = confusion_matrix(y_test, pred, labels=labels)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=labels)
    fig, ax = plt.subplots(figsize=(7, 6))
    disp.plot(ax=ax, cmap="Blues", values_format="d", colorbar=False)
    ax.set_title("Crop classification confusion matrix")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "05_crop_confusion_matrix.png", dpi=180)
    plt.close(fig)

    report = classification_report(y_test, pred, labels=labels, zero_division=0)
    (OUTPUT_DIR / "classification_report.txt").write_text(report, encoding="utf-8")

    rf = model.named_steps["model"]
    importance = pd.DataFrame(
        {
            "feature": features,
            "wavelength": wavelengths,
            "importance": rf.feature_importances_,
        }
    ).sort_values("importance", ascending=False)
    importance.to_csv(OUTPUT_DIR / "crop_band_importance.csv", index=False)

    top = importance.head(25).sort_values("importance")
    plt.figure(figsize=(8, 7))
    plt.barh(top["feature"], top["importance"], color="#2a9d8f")
    plt.title("Top spectral bands for crop classification")
    plt.xlabel("Random Forest importance")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / "06_top_band_importance.png", dpi=180)
    plt.close()

    return pd.DataFrame(
        [
            {
                "task": "crop_classification",
                "model": "RandomForestClassifier",
                "accuracy": accuracy,
                "test_samples": len(y_test),
            }
        ]
    )


def main(argv: list[str] | None = None) -> None:
    if not ML_FILE.exists() or not METADATA_FILE.exists():
        raise SystemExit("Prepared data is missing. Run scripts/02_prepare_spectrofood.py first.")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    df = pd.read_csv(ML_FILE)
    metadata = json.loads(METADATA_FILE.read_text(encoding="utf-8"))
    metadata_features = metadata.get("feature_columns") or []
    if metadata_features and all(col in df.columns for col in metadata_features):
        features = metadata_features
    else:
        features = [col for col in df.columns if is_spectral_column(col)]

    features = [
        col
        for col in features
        if pd.to_numeric(df[col], errors="coerce").notna().mean() >= 0.5
        and pd.to_numeric(df[col], errors="coerce").nunique(dropna=True) > 1
    ]
    wavelengths = metadata.get("wavelengths") or list(range(1, len(features) + 1))
    wavelengths = [float(value) for value in wavelengths[: len(features)]]

    if not features:
        raise SystemExit("No spectral feature columns found.")

    plot_mean_spectra(df, features, wavelengths)
    plot_dry_matter_distribution(df)
    plot_pca(df, features)

    regression_scores = train_regression_models(df, features)
    leave_one_crop = run_leave_one_crop_out(df, features)
    classification_scores = train_classifier(df, features, wavelengths)

    all_scores = pd.concat(
        [table for table in [regression_scores, classification_scores] if not table.empty],
        ignore_index=True,
        sort=False,
    )
    all_scores.to_csv(OUTPUT_DIR / "model_scores.csv", index=False)

    print("Python teaching demo complete.")
    print(f"  Samples: {len(df)}")
    print(f"  Spectral features: {len(features)}")
    print(f"  Outputs: {OUTPUT_DIR}")
    print()
    print(all_scores.to_string(index=False))
    if not leave_one_crop.empty:
        print()
        print("Leave-one-crop-out regression:")
        print(leave_one_crop.to_string(index=False))


if __name__ == "__main__":
    main(sys.argv[1:])
