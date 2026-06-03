$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

$Python = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python scripts\05_rename_wavelength_columns.py
if ($LASTEXITCODE -ne 0) {
    throw "Wavelength column rename failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Done. Reopen data\processed\spectrofood_classification_orange.tab in Orange or Excel."
