$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $FilePath $($Arguments -join ' ')"
    }
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Invoke-Checked "python" "-m" "venv" ".venv"
}

Invoke-Checked ".\.venv\Scripts\python.exe" "-m" "pip" "install" "--upgrade" "pip"
Invoke-Checked ".\.venv\Scripts\python.exe" "-m" "pip" "install" "-r" "requirements.txt"

Invoke-Checked ".\.venv\Scripts\python.exe" "scripts\run_all.py"

Write-Host ""
Write-Host "Demo finished."
Write-Host "Open docs\hyperspectral_food_teaching_demo.html"
