param(
    [Parameter(Mandatory = $true)]
    [string]$CommitMessage,
    [int]$WaitMinutes = 8,
    [string]$TargetUrl = "https://boekermarco-sketch.github.io/Ironforge/training-preview.html"
)

$ErrorActionPreference = "Stop"

function Get-BuildStampFromHtml {
    param([string]$HtmlContent)
    $match = [regex]::Match($HtmlContent, "BUILD_STAMP\s*=\s*'([^']+)'")
    if (-not $match.Success) {
        return $null
    }
    return $match.Groups[1].Value
}

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$previewPath = Join-Path $repoRoot "training-preview.html"
if (-not (Test-Path $previewPath)) {
    throw "training-preview.html nicht gefunden: $previewPath"
}

$localHtml = Get-Content -Path $previewPath -Raw -Encoding UTF8
$localStamp = Get-BuildStampFromHtml -HtmlContent $localHtml
if ([string]::IsNullOrWhiteSpace($localStamp)) {
    throw "BUILD_STAMP in training-preview.html nicht gefunden."
}

Write-Host "Lokaler BUILD_STAMP: $localStamp"
Write-Host "Commit + Push wird ausgefuehrt..."

git add "training-preview.html"
git commit --trailer "Made-with: Cursor" -m "$CommitMessage`n`nPublish training-preview build $localStamp."
git pull --rebase origin main
git push origin main

$checkScript = Join-Path $PSScriptRoot "check_pages_deploy.ps1"
if (-not (Test-Path $checkScript)) {
    throw "Deploy-Check Script fehlt: $checkScript"
}

& $checkScript -ExpectedBuildStamp $localStamp -TargetUrl $TargetUrl -WaitMinutes $WaitMinutes
Write-Host "OK: Live-Version ist synchron ($localStamp)."
