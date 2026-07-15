# Poll experiment health every 10 minutes until complete or max 8 hours.
$ErrorActionPreference = 'Continue'
$Root = 'C:\work\HermesCOBOL'
$results = Join-Path $Root 'experiment\results'
if (-not (Test-Path $results)) { New-Item -ItemType Directory -Path $results -Force | Out-Null }
$loopLog = Join-Path $results 'monitor_loop.log'
$monitorScript = Join-Path $Root 'scripts\monitor_experiment.ps1'
# Pin the full 30-cell suite
$env:HERMES_EXPERIMENT_RUN_ID = '20260715T170600Z'

function Write-Loop([string]$msg) {
  $line = "[$(Get-Date -Format o)] $msg"
  Add-Content -Path $loopLog -Value $line -Encoding utf8
}

Write-Loop "MONITOR LOOP START interval=10m max_ticks=48"
$maxTicks = 48
$deadTicks = 0

for ($i = 0; $i -lt $maxTicks; $i++) {
  Write-Loop "TICK $i start"
  try {
    & $monitorScript
  } catch {
    Write-Loop "monitor_script error: $_"
  }

  $done = $false
  $runs = Get-ChildItem (Join-Path $results 'run_*') -Directory -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending
  foreach ($r in $runs) {
    if (Test-Path (Join-Path $r.FullName 'summary.json')) {
      $done = $true
      Write-Loop "COMPLETE artifact=$($r.FullName)"
      break
    }
  }

  $runnerAlive = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object {
    $_.CommandLine -and ($_.CommandLine -match 'experiment_runner\.py')
  }).Count -gt 0

  if ($done) {
    Write-Loop "EXIT: experiment complete"
    break
  }

  if (-not $runnerAlive) {
    $deadTicks++
    Write-Loop "WARN: runner not alive (deadTicks=$deadTicks)"
    if ($deadTicks -ge 2) {
      Write-Loop "EXIT: runner dead for 2 consecutive ticks without summary — needs manual resume"
      break
    }
  } else {
    $deadTicks = 0
  }

  Write-Loop "sleep 600s (tick $i done)"
  Start-Sleep -Seconds 600
}

Write-Loop "MONITOR LOOP END"
