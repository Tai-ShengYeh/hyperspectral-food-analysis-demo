param(
    [string]$PackageName = "hyperspectral-food-analysis-demo",
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$Dist = Join-Path $Root "dist"
$Stage = Join-Path $Dist $PackageName
$ZipPath = Join-Path $Dist "$PackageName.zip"

Set-Location $Root

if (-not $SkipBuild) {
    Write-Host "Building demo outputs before packaging..."
    & (Join-Path $Root "run_demo.ps1")
    if ($LASTEXITCODE -ne 0) {
        throw "run_demo.ps1 failed with exit code $LASTEXITCODE"
    }
}

if (Test-Path $Stage) {
    Remove-Item -LiteralPath $Stage -Recurse -Force
}

if (Test-Path $ZipPath) {
    Remove-Item -LiteralPath $ZipPath -Force
}

New-Item -ItemType Directory -Path $Stage -Force | Out-Null

$Items = @(
    ".github",
    "data",
    "docs",
    "orange",
    "scripts",
    "outputs",
    ".gitignore",
    "CLASSROOM_QUICKSTART.md",
    "README.md",
    "requirements.txt",
    "run_demo.ps1",
    "fix_orange_crop_labels.ps1",
    "fix_wavelength_column_names.ps1",
    "package_demo.ps1",
    "publish_to_github.ps1",
    "index.html"
)

foreach ($Item in $Items) {
    $Source = Join-Path $Root $Item
    if (Test-Path $Source) {
        Copy-Item -LiteralPath $Source -Destination $Stage -Recurse -Force
    }
}

$ReadmePath = Join-Path $Stage "START_HERE.txt"
@"
Hyperspectral Food Analysis Teaching Demo

1. Open docs\hyperspectral_food_teaching_demo.html to view the lesson.
2. If Python is available, run .\run_demo.ps1 to rebuild all outputs.
3. If class labels show l1/l2/l3, run .\fix_orange_crop_labels.ps1.
4. If wavelength columns show wl_397_66, run .\fix_wavelength_column_names.ps1.
5. Orange files are in data\processed:
   - spectrofood_regression_orange.tab
   - spectrofood_classification_orange.tab

If the processed data is missing, run .\run_demo.ps1 with internet access.
"@ | Set-Content -Path $ReadmePath -Encoding UTF8

Compress-Archive -Path (Join-Path $Stage "*") -DestinationPath $ZipPath -Force

Write-Host ""
Write-Host "Package created:"
Write-Host $ZipPath
