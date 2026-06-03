# Orange Data Mining 操作流程

本教材用兩個 Orange 可匯入的 `.tab` 檔：

- `data/processed/spectrofood_regression_orange.tab`：目標是 `dry_matter_pct`，用於乾物率回歸
- `data/processed/spectrofood_classification_orange.tab`：目標是 `crop`，用於作物分類

若還沒有這兩個檔案，請先執行：

```powershell
python scripts\01_download_spectrofood.py
python scripts\02_prepare_spectrofood.py
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
   - Features：`wl_*`
   - Target：`dry_matter_pct`
   - Meta：`sample_id`, `crop`
5. 加入 `Preprocess`：
   - Continuize 不一定需要，因為光譜欄位已是連續變數。
   - 建議加 Normalize / Standardize。
6. 加入模型：
   - `PLS`：適合光譜回歸，是光譜化學計量常用方法。
   - `Random Forest`：非線性 baseline，對教學很直覺。
   - `SVR`：可作為進階比較。
7. 用 `Test and Score`，選 `Cross validation`，例如 5-fold。
8. 觀察 RMSE、MAE、R2。
9. 用 `Predictions` 看每筆樣本的實際值與預測值。

課堂討論重點：

- 光譜資料通常是高維度且 band 之間高度相關。
- PLS 可以同時降維與回歸，因此很適合 spectroscopy。
- 隨機分割的分數不等於跨作物泛化能力；Python demo 另外示範 leave-one-crop-out。

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
   - Features：`wl_*`
   - Target：`crop`
   - Meta：`sample_id`, `dry_matter_pct`
4. 接 `PCA`，再接 `Scatter Plot`。
5. 在 `Scatter Plot` 中用 `crop` 上色，觀察類別是否分群。
6. 加入 `Random Forest`、`SVM` 或 `kNN`。
7. 用 `Test and Score` 做 cross validation。
8. 接 `Confusion Matrix`，檢查哪些類別容易混淆。

課堂討論重點：

- PCA 不是分類器，但能幫助檢查光譜資料是否自然分群。
- Confusion Matrix 比 accuracy 更能看出模型錯在哪些類別。
- 若樣本數小，交叉驗證比較穩，但仍要小心資料洩漏與樣本來源偏差。

## Demo C：接到 Orange-Spectroscopy

若安裝了 Spectroscopy add-on，可以補充這些 widget：

- `Spectra`：看單筆或多筆光譜曲線。
- `Preprocess Spectra`：做 Savitzky-Golay smoothing、baseline correction、normalization 等光譜前處理。
- `PLS`：常用於光譜回歸。

對學生可強調：Orange 的優點是把「資料、前處理、模型、評估」視覺化；Python 的優點是可重現、可自動化、可做更嚴謹的 validation design。

