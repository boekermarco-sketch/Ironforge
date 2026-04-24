param(
    [string]$RepoOwner = "boekermarco-sketch",
    [string]$RepoName = "Ironforge",
    [string]$Branch = "main",
    [string]$TargetUrl = "https://boekermarco-sketch.github.io/Ironforge/training-preview.html",
    [string]$ExpectedBuildStamp = "",
    [int]$WaitMinutes = 10
)

$ErrorActionPreference = "Stop"

function Get-BuildStampFromHtml {
    param([string]$HtmlContent)
    $match = [regex]::Match($HtmlContent, "BUILD_STAMP\s*=\s*'([^']+)'")
    if (-not $match.Success) { return $null }
    return $match.Groups[1].Value
}

function Get-Json {
    param([string]$Url)
    return Invoke-RestMethod -Uri $Url -Headers @{ "User-Agent" = "Ironforge-Deploy-Check" } -Method Get
}

function Get-RunAnnotations {
    param([string]$Owner, [string]$Name, [long]$RunId)
    $jobs = Get-Json "https://api.github.com/repos/$Owner/$Name/actions/runs/$RunId/jobs"
    $out = @()
    foreach ($job in ($jobs.jobs | Where-Object { $_.name -eq "deploy" })) {
        $checkRunId = [string]$job.id
        try {
            $annotations = Get-Json "https://api.github.com/repos/$Owner/$Name/check-runs/$checkRunId/annotations"
            $out += $annotations
        }
        catch {
            # Annotation endpoint may be missing for some runs; continue.
        }
    }
    return $out
}

Write-Host "Pages Deploy Health Check gestartet..."
$remoteSha = (git rev-parse "origin/$Branch").Trim()
Write-Host "Ziel-SHA auf origin/${Branch}: $remoteSha"

$deadline = (Get-Date).AddMinutes($WaitMinutes)
$matchingRun = $null

while ((Get-Date) -lt $deadline) {
    $runs = Get-Json "https://api.github.com/repos/$RepoOwner/$RepoName/actions/runs?per_page=30"
    $matchingRun = $runs.workflow_runs |
        Where-Object { $_.name -eq "pages build and deployment" -and $_.head_branch -eq $Branch -and $_.head_sha -eq $remoteSha } |
        Select-Object -First 1

    if (-not $matchingRun) {
        Write-Host "Noch kein Pages-Run fuer SHA $remoteSha gefunden..."
        Start-Sleep -Seconds 8
        continue
    }

    Write-Host "Run gefunden: #$($matchingRun.run_number) | status=$($matchingRun.status) | conclusion=$($matchingRun.conclusion)"

    if ($matchingRun.status -ne "completed") {
        Start-Sleep -Seconds 8
        continue
    }

    if ($matchingRun.conclusion -ne "success") {
        $annotations = Get-RunAnnotations -Owner $RepoOwner -Name $RepoName -RunId $matchingRun.id
        $lockMsg = $annotations | Where-Object { $_.message -match "in progress deployment" } | Select-Object -First 1
        if ($lockMsg) {
            throw "Pages-Deploy fehlgeschlagen: Deployment-Lock erkannt. Hinweis: $($lockMsg.message)"
        }
        throw "Pages-Deploy fehlgeschlagen: conclusion=$($matchingRun.conclusion). Details: $($matchingRun.html_url)"
    }

    break
}

if (-not $matchingRun) {
    throw "Kein passender Pages-Run fuer SHA $remoteSha innerhalb $WaitMinutes Minuten gefunden."
}
if ($matchingRun.status -ne "completed" -or $matchingRun.conclusion -ne "success") {
    throw "Pages-Run fuer $remoteSha wurde nicht erfolgreich abgeschlossen."
}

Write-Host "Pages-Run erfolgreich. Pruefe Live-Seite..."
$liveMatched = $false
while ((Get-Date) -lt $deadline) {
    try {
        $res = Invoke-WebRequest -Uri $TargetUrl -UseBasicParsing
        $liveStamp = Get-BuildStampFromHtml -HtmlContent $res.Content
        Write-Host "Live BUILD_STAMP: $liveStamp"
        if ([string]::IsNullOrWhiteSpace($ExpectedBuildStamp)) {
            $liveMatched = $true
            break
        }
        if ($liveStamp -eq $ExpectedBuildStamp) {
            $liveMatched = $true
            break
        }
    }
    catch {
        Write-Host "Live-Check Fehler: $($_.Exception.Message)"
    }
    Start-Sleep -Seconds 10
}

if (-not $liveMatched) {
    if ([string]::IsNullOrWhiteSpace($ExpectedBuildStamp)) {
        throw "Live-Seite nicht stabil erreichbar bzw. ohne BUILD_STAMP innerhalb $WaitMinutes Minuten."
    }
    throw "Live BUILD_STAMP nicht synchron. Erwartet: '$ExpectedBuildStamp'."
}

Write-Host "OK: Deploy + Live-Check erfolgreich."
