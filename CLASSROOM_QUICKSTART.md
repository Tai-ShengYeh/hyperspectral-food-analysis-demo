# Classroom Quickstart

這份壓縮包設計成可以帶到教室電腦使用。

## 最快展示方式

直接打開：

```text
docs\hyperspectral_food_teaching_demo.html
```

若壓縮包是在已建置狀態下產生，HTML 會顯示 Python demo 產生的圖表。

## 重新跑 Python demo

教室電腦需要：

- Python 3.10 或更新版本
- 可連網下載 Python 套件

執行：

```powershell
.\run_demo.ps1
```

這會：

1. 建立 `.venv` 虛擬環境
2. 安裝 Python 套件
3. 下載 SpectroFood dataset
4. 產生 Orange Data Mining 可讀的 `.tab` 檔
5. 產生 Python 圖表與模型評估

## Orange Data Mining demo

請先安裝 Orange Data Mining：

https://orangedatamining.com/download/

建議再安裝 Spectroscopy add-on：

```text
Options > Add-ons > Spectroscopy
```

可載入：

- `data\processed\spectrofood_regression_orange.tab`
- `data\processed\spectrofood_classification_orange.tab`

完整操作流程在：

```text
orange\Orange_Data_Mining_操作流程.md
```

## 重新打包

若你在教室電腦修改內容後想重新打包：

```powershell
.\package_demo.ps1
```

壓縮檔會產生在：

```text
dist\hyperspectral-food-analysis-demo.zip
```

