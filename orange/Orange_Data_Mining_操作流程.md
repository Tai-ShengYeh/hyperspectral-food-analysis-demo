# Orange Data Mining 操作流程

本教材用兩個 Orange 可匯入的 `.tab` 檔：

- `data/processed/spectrofood_regression_orange.tab`：目標是 `dry_matter_pct`，用於乾物率回歸
- `data/processed/spectrofood_classification_orange.tab`：目標是 `crop`，用於作物分類

若還沒有這兩個檔案，請先執行：

```powershell
python scripts\01_download_spectrofood.py
python scripts\02_prepare_spectrofood.py
python scripts\04_fix_orange_crop_labels.py
python scripts\05_rename_wavelength_columns.py
```

## 安裝 Orange 與光譜 add-on

1. 安裝 Orange Data Mining：https://orangedatamining.com/download/
2. 開啟 Orange。
3. 到 `Options > Add-ons`。
4. 安裝 `Spectroscopy` add-on。
5. 重新啟動 Orange。

如果使用 Quasar 版 Orange，通常已經內建 Orange-Spectroscopy。

## Demo A：乾物率回歸

目的：用 VIS-NIR spectral bands 預測食品/農產品的乾物率。

建議 workflow：

```text
File
  -> Data Table
  -> Select Columns
  -> Preprocess
  -> PLS / Random Forest / SVR
  -> Test and Score
  -> Predictions
```

操作：

1. 放入 `File` widget。
2. 載入 `data/processed/spectrofood_regression_orange.tab`。
3. 用 `Data Table` 檢查資料欄位。
4. 用 `Select Columns` 確認：
   - Features：實際波長欄位，例如 `397.66`, `400.28`, `402.9`
   - Target：`dry_matter_pct`
   - Meta：`sample_id`, `crop`
5. 加入 `Preprocess`，建議做 Normalize / Standardize。
6. 加入模型：
   - `PLS`：適合光譜回歸，是光譜化學計量常用方法。
   - `Random Forest`：非線性 baseline，對教學很直覺。
   - `SVR`：可作為進階比較。
7. 用 `Test and Score`，選 `Cross validation`，例如 5-fold。
8. 觀察 RMSE、MAE、R2。
9. 用 `Predictions` 看每筆樣本的實際值與預測值。

## Demo B：作物分類

目的：用 spectra 判斷樣本屬於 apple、broccoli、leek 或 mushroom。

建議 workflow：

```text
File
  -> Data Table
  -> PCA
  -> Scatter Plot

File
  -> Random Forest / SVM / kNN
  -> Test and Score
  -> Confusion Matrix
```

操作：

1. 放入 `File` widget。
2. 載入 `data/processed/spectrofood_classification_orange.tab`。
3. 用 `Select Columns` 確認：
   - Features：實際波長欄位，例如 `397.66`, `400.28`, `402.9`
   - Target：`crop`
   - Meta：`sample_id`, `dry_matter_pct`
4. 接 `PCA`，再接 `Scatter Plot`。
5. 在 `Scatter Plot` 中用 `crop` 上色，觀察類別是否分群。
6. 加入 `Random Forest`、`SVM` 或 `kNN`。
7. 用 `Test and Score` 做 cross validation。
8. 接 `Confusion Matrix`，檢查哪些類別容易混淆。

## 常見修正

如果 class 顯示成 `l1`, `l2`, `l3` 這類樣本代碼，執行：

```powershell
.\fix_orange_crop_labels.ps1
```

如果欄位名稱顯示成 `wl_397_66`，執行：

```powershell
.\fix_wavelength_column_names.ps1
```

## Demo C：接到 Orange-Spectroscopy

若安裝了 Spectroscopy add-on，可以補充這些 widget：

- `Spectra`：看單筆或多筆光譜曲線。
- `Preprocess Spectra`：做 Savitzky-Golay smoothing、baseline correction、normalization 等光譜前處理。
- `PLS`：常用於光譜回歸。

對學生可強調：Orange 的優點是把「資料、前處理、模型、評估」視覺化；Python 的優點是可重現、可自動化、可做更嚴謹的 validation design。
