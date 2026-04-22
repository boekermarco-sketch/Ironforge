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

Write-Host "Warte auf GitHub Pages und pruefe Live-BUILD_STAMP..."

$deadline = (Get-Date).AddMinutes($WaitMinutes)
$matched = $false

while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest -Uri $TargetUrl -UseBasicParsing
        $remoteStamp = Get-BuildStampFromHtml -HtmlContent $response.Content
        Write-Host "Live BUILD_STAMP: $remoteStamp"
        if ($remoteStamp -eq $localStamp) {
            $matched = $true
            break
        }
    }
    catch {
        Write-Host "Live-Check fehlgeschlagen: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds 20
}

if (-not $matched) {
    throw "Live-Version ist noch nicht synchron. Erwartet: '$localStamp'."
}

Write-Host "OK: Live-Version ist synchron ($localStamp)."
