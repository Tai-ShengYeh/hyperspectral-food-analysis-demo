$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python scripts\04_fix_orange_crop_labels.py
if ($LASTEXITCODE -ne 0) {
    throw "Crop label repair failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Done. Reopen data\processed\spectrofood_classification_orange.tab in Orange or Excel."
