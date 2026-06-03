# Hyperspectral Food Analysis Teaching Demo

這份教材使用公開的 SpectroFood 資料集，示範如何用 Python 與 Orange Data Mining 分析食品/農產品的 VIS-NIR hyperspectral 光譜資料。

## 內容

- `scripts/01_download_spectrofood.py`：下載公開資料集
- `scripts/02_prepare_spectrofood.py`：整理成 Python 與 Orange 可用格式，class 會是 `leek`, `apple`, `broccoli`, `mushroom`
- `scripts/03_python_teaching_demo.py`：Python 教學 demo，包含回歸、分類與視覺化
- `scripts/04_fix_orange_crop_labels.py`：修正既有 Orange 檔的 class 標記
- `scripts/05_rename_wavelength_columns.py`：把 `wl_397_66` 欄位改成實際波長 `397.66`
- `orange/Orange_Data_Mining_操作流程.md`：Orange Data Mining 操作步驟
- `docs/hyperspectral_food_teaching_demo.html`：完整教學 HTML

## 快速開始

最簡單的方式是在 PowerShell 執行：

```powershell
cd D:\course\food_analysis
.\run_demo.ps1
```

或手動逐步執行：

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

python scripts\01_download_spectrofood.py
python scripts\02_prepare_spectrofood.py
python scripts\04_fix_orange_crop_labels.py
python scripts\05_rename_wavelength_columns.py
python scripts\03_python_teaching_demo.py
```

完成後可開啟：

- `docs/hyperspectral_food_teaching_demo.html`
- `data/processed/spectrofood_regression_orange.tab`
- `data/processed/spectrofood_classification_orange.tab`

## 修正 Orange class 標記

如果 `spectrofood_classification_orange.tab` 的 class 顯示成 `l1`, `l2`, `l3` 這類樣本代碼，執行：

```powershell
.\fix_orange_crop_labels.ps1
```

修正後 `crop` class 會是 `leek`, `apple`, `broccoli`, `mushroom`。

## 修正波長欄位名稱

如果 Orange 或 Excel 裡看到 `wl_397_66` 這類欄位名稱，執行：

```powershell
.\fix_wavelength_column_names.ps1
```

修正後欄位會改成實際波長，例如 `397.66`, `400.28`, `402.9`。

## 打包成教室用壓縮檔

```powershell
.\package_demo.ps1
```

壓縮檔會產生在：

```text
dist\hyperspectral-food-analysis-demo.zip
```

## 發佈到 GitHub

先安裝 Git 與 GitHub CLI，並登入：

```powershell
gh auth login
```

接著執行：

```powershell
.\publish_to_github.ps1 -Owner Tai-ShengYeh -RepoName hyperspectral-food-analysis-demo
```

GitHub Pages workflow 已放在 `.github/workflows/pages.yml`。推上 GitHub 後，到 repo 的 `Settings > Pages`，選擇 `GitHub Actions`，即可部署教學 HTML。

## 資料來源

SpectroFood dataset: https://zenodo.org/records/8362947
