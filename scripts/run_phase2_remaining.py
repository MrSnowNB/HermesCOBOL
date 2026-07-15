#!/usr/bin/env python3
"""Phase 2 batch for incomplete programs. Idempotent (worker SKIPs existing L1)."""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = ROOT / ".venv" / "Scripts" / "python.exe"
if not PY.is_file():
    PY = Path(sys.executable)

LOG = ROOT / "docs" / "phase2_full_corpus_run.log"
SUMMARY = ROOT / "docs" / "phase2_full_corpus_summary.jsonl"
WORKER = ROOT / "phase2_english_worker.py"

# Skip COACTUPC (complete) and COBSWAIT (0 paras). Order matches prior PS1.
PROGS = [
    "CBACT01C", "CBACT02C", "CBACT03C", "CBACT04C", "CBCUS01C",
    "CBEXPORT", "CBIMPORT", "CBSTM03A", "CBSTM03B", "CBTRN01C", "CBTRN02C", "CBTRN03C",
    "COACTVWC", "COADM01C", "COBIL00C", "COCRDLIC", "COCRDSLC", "COCRDUPC",
    "COMEN01C", "CORPT00C", "COSGN00C", "COTRN00C", "COTRN01C", "COTRN02C",
    "COUSR00C", "COUSR01C", "COUSR02C", "COUSR03C", "CSUTLDTC",
]


def log(msg: str) -> None:
    line = msg if msg.endswith("\n") else msg + "\n"
    print(line, end="", flush=True)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8", errors="replace") as fh:
        fh.write(line)


def main() -> int:
    log(f"=== Phase 2 remaining programs start {datetime.now().astimezone().isoformat()} ===")
    log(f"python={PY} worker={WORKER}")
    overall = 0
    for prog in PROGS:
        log(f"=== PROGRAM {prog} {datetime.now().astimezone().isoformat()} ===")
        t0 = time.time()
        proc = subprocess.run(
            [str(PY), str(WORKER), "--program", prog, "--timeout", "180", "--workers", "1"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        out = (proc.stdout or "") + (proc.stderr or "")
        for line in out.splitlines():
            log(line)
        summary_bits = [
            ln for ln in out.splitlines()
            if any(k in ln for k in ("DONE:", "Phase 2 complete", "SKIP", "FAIL", "ERROR"))
        ]
        entry = {
            "program": prog,
            "exit": proc.returncode,
            "summary": " | ".join(summary_bits[-8:]),
            "elapsed_sec": round(time.time() - t0, 1),
            "ts": datetime.now(timezone.utc).isoformat(),
        }
        with SUMMARY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
        log(f"=== END {prog} exit={proc.returncode} ===")
        if proc.returncode not in (0, None):
            overall = proc.returncode or 1
    log(f"=== Phase 2 remaining programs end {datetime.now().astimezone().isoformat()} ===")
    return overall


if __name__ == "__main__":
    raise SystemExit(main())
