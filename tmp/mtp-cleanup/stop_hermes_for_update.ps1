# stop_hermes_for_update.ps1
# Kill all Hermes processes so hermes.exe can be replaced during `hermes update`.
# Usage: powershell -NoProfile -File C:\work\HermesCOBOL\tmp\mtp-cleanup\stop_hermes_for_update.ps1

$ErrorActionPreference = 'Continue'
Write-Host "Stopping all Hermes-related processes..." -ForegroundColor Cyan

Get-Process -Name hermes -ErrorAction SilentlyContinue | ForEach-Object {
    Write-Host "  Stop-Process hermes PID=$($_.Id)"
    Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
}

Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object {
        ($_.ExecutablePath -and $_.ExecutablePath -like '*hermes.exe*') -or
        ($_.CommandLine -and (
            $_.CommandLine -like '*hermes-agent*' -or
            $_.CommandLine -like '*Scripts\hermes.exe*' -or
            $_.CommandLine -like '*Scripts/hermes.exe*'
        ))
    } |
    ForEach-Object {
        Write-Host "  Stop-Process PID=$($_.ProcessId) Name=$($_.Name)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }

Start-Sleep -Seconds 1
$left = @(Get-Process -Name hermes -ErrorAction SilentlyContinue)
if ($left.Count -gt 0) {
    Write-Host "FAIL: hermes still running: $($left.Id -join ', ')" -ForegroundColor Red
    exit 1
}

$exe = 'C:\work\hermes-agent\.venv\Scripts\hermes.exe'
if (Test-Path $exe) {
    try {
        $fs = [System.IO.File]::Open($exe, 'Open', 'ReadWrite', 'None')
        $fs.Close()
        Write-Host "OK: hermes.exe is not locked — safe to run: hermes update" -ForegroundColor Green
    } catch {
        Write-Host "WARN: hermes.exe still locked: $($_.Exception.Message)" -ForegroundColor Yellow
        Write-Host "  Close any remaining terminals/IDEs holding the file, then retry."
        exit 1
    }
} else {
    Write-Host "OK: hermes.exe path missing (will be recreated on install)" -ForegroundColor Green
}
exit 0
