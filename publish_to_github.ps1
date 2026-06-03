param(
    [string]$RepoName = "hyperspectral-food-analysis-demo",
    [string]$Owner = "",
    [switch]$Private
)

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

function Invoke-Capture {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Arguments
    )

    $Output = & $FilePath @Arguments 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $null
    }
    return ($Output -join "`n")
}

function Require-Command($Name, $InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "$Name is required. $InstallHint"
    }
}

Require-Command "git" "Install Git: https://git-scm.com/downloads"
Require-Command "gh" "Install GitHub CLI: https://cli.github.com/"

$SafeRoot = $Root -replace "\\", "/"
Invoke-Checked "git" "config" "--global" "--add" "safe.directory" $SafeRoot

Invoke-Checked "gh" "auth" "status"

if (-not (Test-Path ".git")) {
    Invoke-Checked "git" "init" "-b" "main"
}

Invoke-Checked "git" "add" `
    .github `
    .gitignore `
    CLASSROOM_QUICKSTART.md `
    README.md `
    requirements.txt `
    run_demo.ps1 `
    package_demo.ps1 `
    publish_to_github.ps1 `
    index.html `
    scripts `
    docs `
    orange `
    data/raw/README.md `
    data/processed/README.md

$HasChanges = Invoke-Capture "git" "status" "--porcelain"
if ($null -ne $HasChanges -and $HasChanges.Trim().Length -gt 0) {
    Invoke-Checked "git" "commit" "-m" "Add hyperspectral food analysis teaching demo"
} else {
    Write-Host "No local changes to commit."
}

$RepoFullName = $RepoName
if ($Owner.Trim().Length -gt 0 -and -not $RepoName.Contains("/")) {
    $RepoFullName = "$Owner/$RepoName"
}

$OriginUrl = Invoke-Capture "git" "remote" "get-url" "origin"

if ($null -eq $OriginUrl -or $OriginUrl.Trim().Length -eq 0) {
    $ExistingRepoUrl = Invoke-Capture "gh" "repo" "view" $RepoFullName "--json" "url" "--jq" ".url"

    if ($null -ne $ExistingRepoUrl -and $ExistingRepoUrl.Trim().Length -gt 0) {
        $RemoteUrl = "https://github.com/$RepoFullName.git"
        Invoke-Checked "git" "remote" "add" "origin" $RemoteUrl
        Invoke-Checked "git" "branch" "-M" "main"
        Invoke-Checked "git" "push" "-u" "origin" "main"
    } else {
        $Visibility = "--public"
        if ($Private) {
            $Visibility = "--private"
        }

        Invoke-Checked "gh" "repo" "create" $RepoFullName $Visibility "--source" $Root "--remote" "origin" "--push"
    }
} else {
    Invoke-Checked "git" "branch" "-M" "main"
    Invoke-Checked "git" "push" "-u" "origin" "main"
}

Write-Host ""
Write-Host "Published to GitHub:"
Invoke-Checked "gh" "repo" "view" "--json" "url" "--jq" ".url"
Write-Host ""
Write-Host "For GitHub Pages, open repository Settings > Pages and select GitHub Actions."
Write-Host "The workflow in .github\workflows\pages.yml will build and deploy the lesson page."
