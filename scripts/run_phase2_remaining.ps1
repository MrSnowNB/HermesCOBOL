# Run Phase 2 English worker for every incomplete program (no --force).
# Logs: docs/phase2_full_corpus_run.log (Append only; no dual redirect)
$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot\..
$py = if (Test-Path '.\.venv\Scripts\python.exe') { '.\.venv\Scripts\python.exe' } else { 'python' }
$log = Join-Path (Get-Location) 'docs\phase2_full_corpus_run.log'
$summary = Join-Path (Get-Location) 'docs\phase2_full_corpus_summary.jsonl'
$docs = Join-Path (Get-Location) 'docs'
if (-not (Test-Path $docs)) { New-Item -ItemType Directory -Path $docs | Out-Null }

function Write-Log([string]$msg) {
  $line = $msg
  Write-Host $line
  Add-Content -Path $log -Value $line -Encoding utf8 -ErrorAction SilentlyContinue
}

$progs = @(
  'CBACT01C','CBACT02C','CBACT03C','CBACT04C','CBCUS01C',
  'CBEXPORT','CBIMPORT','CBSTM03A','CBSTM03B','CBTRN01C','CBTRN02C','CBTRN03C',
  'COACTVWC','COADM01C','COBIL00C','COCRDLIC','COCRDSLC','COCRDUPC',
  'COMEN01C','CORPT00C','COSGN00C','COTRN00C','COTRN01C','COTRN02C',
  'COUSR00C','COUSR01C','COUSR02C','COUSR03C','CSUTLDTC'
)
# COACTUPC complete; COBSWAIT has 0 paras

Write-Log "=== Phase 2 remaining programs start $(Get-Date -Format o) ==="

foreach ($prog in $progs) {
  Write-Log "=== PROGRAM $prog $(Get-Date -Format o) ==="
  $tmpOut = Join-Path $env:TEMP "phase2_$prog.out.txt"
  $tmpErr = Join-Path $env:TEMP "phase2_$prog.err.txt"
  $p = Start-Process -FilePath $py -ArgumentList @(
    'phase2_english_worker.py','--program',$prog,'--timeout','180','--workers','1'
  ) -WorkingDirectory (Get-Location) -NoNewWindow -Wait -PassThru `
    -RedirectStandardOutput $tmpOut -RedirectStandardError $tmpErr
  $exit = $p.ExitCode
  $outText = @()
  if (Test-Path $tmpOut) { $outText += Get-Content $tmpOut -ErrorAction SilentlyContinue }
  if (Test-Path $tmpErr) { $outText += Get-Content $tmpErr -ErrorAction SilentlyContinue }
  foreach ($line in $outText) { Write-Log $line }
  $summaryLine = ($outText | Select-String -Pattern 'DONE:|Phase 2 complete|SKIP|FAIL|ERROR' | ForEach-Object { $_.Line }) -join ' | '
  $entry = @{ program = $prog; exit = $exit; summary = $summaryLine; ts = (Get-Date -Format o) }
  ($entry | ConvertTo-Json -Compress) | Add-Content $summary -Encoding utf8
  Write-Log "=== END $prog exit=$exit ==="
  Remove-Item $tmpOut,$tmpErr -ErrorAction SilentlyContinue
}

Write-Log "=== Phase 2 remaining programs end $(Get-Date -Format o) ==="
