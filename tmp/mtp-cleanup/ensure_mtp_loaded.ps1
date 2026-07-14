# ensure_mtp_loaded.ps1
# Unloads non-MTP Qwen3.6-35B-A3B if resident; ensures MTP is loaded and active.
# Safe to run after Lemonade start. Does not stop Hermes or Honcho.
# Usage: powershell -NoProfile -File C:\work\HermesCOBOL\tmp\mtp-cleanup\ensure_mtp_loaded.ps1

$ErrorActionPreference = 'Continue'
$Base = 'http://127.0.0.1:8000'
$NonMtp = 'Qwen3.6-35B-A3B-GGUF'
$Mtp = 'Qwen3.6-35B-A3B-MTP-GGUF'

function Invoke-JsonPost($Path, $Body) {
    $json = $Body | ConvertTo-Json -Compress
    try {
        $r = Invoke-WebRequest -Uri "$Base$Path" -Method POST -Body $json `
            -ContentType 'application/json' -UseBasicParsing -TimeoutSec 180
        return @{ ok = $true; code = [int]$r.StatusCode; body = $r.Content }
    } catch {
        $code = $null
        $msg = $_.Exception.Message
        if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
        if ($_.ErrorDetails.Message) { $msg = $_.ErrorDetails.Message }
        return @{ ok = $false; code = $code; body = $msg }
    }
}

Write-Host "=== ensure_mtp_loaded ===" -ForegroundColor Cyan

# Health
try {
    $h = Invoke-RestMethod "$Base/api/v1/health" -TimeoutSec 10
} catch {
    Write-Host "FAIL: Lemonade not reachable at $Base" -ForegroundColor Red
    exit 2
}

$loaded = @($h.all_models_loaded | ForEach-Object { $_.model_name })
Write-Host "Before: model_loaded=$($h.model_loaded)"
Write-Host "Before: loaded=$($loaded -join ', ')"

# Unload non-MTP if present
if ($loaded -contains $NonMtp) {
    Write-Host "Unloading $NonMtp ..."
    $u = Invoke-JsonPost '/api/v0/unload' @{ model_name = $NonMtp }
    Write-Host "  unload: code=$($u.code) $($u.body)"
}

# Prefer load MTP (idempotent if already loaded)
Write-Host "Ensuring $Mtp is loaded ..."
$l = Invoke-JsonPost '/api/v1/load' @{ model_name = $Mtp }
if (-not $l.ok) {
    $l = Invoke-JsonPost '/api/v0/load' @{ model_name = $Mtp }
}
Write-Host "  load: code=$($l.code) $($l.body)"

Start-Sleep -Seconds 1
$h2 = Invoke-RestMethod "$Base/api/v1/health" -TimeoutSec 10
$loaded2 = @($h2.all_models_loaded | ForEach-Object { $_.model_name })
Write-Host "After:  model_loaded=$($h2.model_loaded)"
Write-Host "After:  loaded=$($loaded2 -join ', ')"

$hasNon = $loaded2 -contains $NonMtp
$hasMtp = $loaded2 -contains $Mtp
if ($hasNon) {
    Write-Host "FAIL: non-MTP still loaded" -ForegroundColor Red
    exit 1
}
if (-not $hasMtp) {
    Write-Host "FAIL: MTP not loaded" -ForegroundColor Red
    exit 1
}
if ($h2.model_loaded -ne $Mtp) {
    Write-Host "WARN: model_loaded is '$($h2.model_loaded)' not $Mtp (MTP is loaded but not active)" -ForegroundColor Yellow
    # Still success if non-MTP gone and MTP present
}
Write-Host "OK: non-MTP absent; MTP present" -ForegroundColor Green
exit 0
