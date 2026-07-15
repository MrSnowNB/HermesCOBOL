# Health monitor for experiment_runner full A/B/C suite.
# Appends a timestamped snapshot every invocation. Exit 0 always (observability).
$ErrorActionPreference = 'Continue'
$Root = Split-Path (Split-Path $PSScriptRoot -Parent) -ErrorAction SilentlyContinue
if (-not $Root) { $Root = 'C:\work\HermesCOBOL' }
if (-not (Test-Path (Join-Path $Root 'experiment_runner.py'))) { $Root = 'C:\work\HermesCOBOL' }
Set-Location $Root

$results = Join-Path $Root 'experiment\results'
$monitorLog = Join-Path $results 'monitor.log'
# Prefer the largest incomplete (or largest) full suite run — not a 2-cell smoke.
# Override: $env:HERMES_EXPERIMENT_RUN_ID = '20260715T170600Z'
$runs = @(Get-ChildItem (Join-Path $results 'run_*') -Directory -ErrorAction SilentlyContinue)
function Get-RunScore($dir) {
  $cells = @(Get-ChildItem (Join-Path $dir.FullName 'cells') -Recurse -Filter meta.json -ErrorAction SilentlyContinue).Count
  $hasSummary = Test-Path (Join-Path $dir.FullName 'summary.json')
  $log = Get-Item (Join-Path $dir.FullName 'RUN.log') -ErrorAction SilentlyContinue
  $age = if ($log) { ((Get-Date) - $log.LastWriteTime).TotalMinutes } else { 9999 }
  # Higher cells first; prefer no summary if still active; fresher log wins
  return [pscustomobject]@{
    Dir = $dir
    Cells = $cells
    HasSummary = $hasSummary
    AgeMin = $age
    Score = ($cells * 1000) + ($(if ($hasSummary) { 0 } else { 100 })) - [int]$age
  }
}
$ranked = $runs | ForEach-Object { Get-RunScore $_ } | Sort-Object Score -Descending
$runId = $env:HERMES_EXPERIMENT_RUN_ID
if ($runId) {
  $runDir = Join-Path $results ("run_" + $runId)
} elseif ($ranked) {
  $runDir = $ranked[0].Dir.FullName
  $runId = $ranked[0].Dir.Name -replace '^run_',''
} else {
  $runDir = $null
  $runId = 'NONE'
}

function Write-Mon([string]$msg) {
  $line = "[$(Get-Date -Format o)] $msg"
  Write-Host $line
  Add-Content -Path $monitorLog -Value $line -Encoding utf8
}

Write-Mon "=== MONITOR TICK run=$runId ==="

$runner = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
  $_.CommandLine -and ($_.CommandLine -match 'experiment_runner\.py')
})
$hermes = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
  $_.CommandLine -and (
    $_.CommandLine -match 'hermes\.bat.*chat' -or
    $_.CommandLine -match 'hermes\.exe.*chat' -or
    ($_.CommandLine -match 'hermes-agent' -and $_.CommandLine -match ' chat ')
  )
})

Write-Mon "runner_pids=$($runner.ProcessId -join ',') hermes_count=$($hermes.Count)"

if (-not $runDir -or -not (Test-Path $runDir)) {
  Write-Mon "STATUS=NO_RUN_DIR"
  Write-Mon "=== MONITOR END ==="
  exit 0
}

$summaryPath = Join-Path $runDir 'summary.json'
$runLog = Join-Path $runDir 'RUN.log'
$complete = $false
if (Test-Path $summaryPath) {
  try {
    $s = Get-Content $summaryPath -Raw | ConvertFrom-Json
    # Full suite is 30 cells; ignore tiny smoke runs
    if ([int]$s.total_cells -ge 30) { $complete = $true }
    else { Write-Mon "NOTE: summary exists but total_cells=$($s.total_cells) (not full suite)" }
  } catch {
    $complete = $true
  }
}

if ($complete) {
  Write-Mon "STATUS=COMPLETE summary=$summaryPath"
  try {
    $s = Get-Content $summaryPath -Raw | ConvertFrom-Json
    Write-Mon "ok=$($s.ok) fail=$($s.fail) total=$($s.total_cells) elapsed=$($s.elapsed_sec)"
  } catch {}
  Write-Mon "=== MONITOR END (done) ==="
  exit 0
}

$cells = @(Get-ChildItem (Join-Path $runDir 'cells') -Recurse -Filter meta.json -ErrorAction SilentlyContinue)
$ok = 0; $fail = 0; $last = $null
foreach ($m in $cells) {
  try {
    $j = Get-Content $m.FullName -Raw | ConvertFrom-Json
    if ($j.ok) { $ok++ } else { $fail++ }
    if (-not $last -or $j.seq -gt $last.seq) { $last = $j }
  } catch {}
}
Write-Mon "cells_done=$($cells.Count)/30 ok=$ok fail=$fail"

if ($last) {
  Write-Mon "last_cell seq=$($last.seq) $($last.harness)/$($last.question_id) ok=$($last.ok) sec=$($last.elapsed_sec)"
}

$logAgeMin = $null
if (Test-Path $runLog) {
  $li = Get-Item $runLog
  $logAgeMin = [math]::Round(((Get-Date) - $li.LastWriteTime).TotalMinutes, 1)
  Write-Mon "RUN.log age_min=$logAgeMin size=$($li.Length)"
  Get-Content $runLog -Tail 5 | ForEach-Object { Write-Mon "LOG| $_" }
}

$stuck = $false
$reason = @()
if ($runner.Count -eq 0 -and $cells.Count -lt 30) {
  $stuck = $true
  $reason += 'runner_dead'
}
# Cell timeout is 600s; allow 11 min before declaring log stall while runner alive
if ($runner.Count -gt 0 -and $logAgeMin -ne $null -and $logAgeMin -gt 12) {
  $stuck = $true
  $reason += "log_stale_${logAgeMin}m"
}
# Hermes hung past timeout without runner advancing: hermes alive, log stale >11m
if ($hermes.Count -gt 0 -and $logAgeMin -ne $null -and $logAgeMin -gt 11) {
  $stuck = $true
  $reason += 'hermes_past_timeout_window'
}

if ($stuck) {
  Write-Mon "STUCK_SUSPECT reason=$($reason -join ',')"
  # Soft recovery: kill orphan hermes chat children if log stalled past timeout window
  if ($logAgeMin -gt 12 -and $hermes.Count -gt 0) {
    foreach ($h in $hermes) {
      Write-Mon "RECOVERY kill hermes pid=$($h.ProcessId)"
      Stop-Process -Id $h.ProcessId -Force -ErrorAction SilentlyContinue
    }
  }
  if ($runner.Count -eq 0) {
    Write-Mon "RECOVERY needed: restart experiment_runner (not auto-restarted by this script)"
  }
} else {
  Write-Mon "STATUS=HEALTHY_OR_IN_PROGRESS"
}

Write-Mon "=== MONITOR END ==="
exit 0
