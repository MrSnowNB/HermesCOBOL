#!/usr/bin/env python3
"""
experiment_runner.py — A/B/C harness comparison runner (scaffolding).

Runs the same question set against harness profiles A, B, and C via
`hermes chat -Q -q ...`. Does NOT score answers automatically — stores
raw transcripts under experiment/results/ for human rubric scoring.

IMPORTANT: Do not run the full suite until:
  1. Phase 2 L1 coverage >= 95%
  2. Smoke tests pass (see --smoke)

Usage:
  python experiment_runner.py --list
  python experiment_runner.py --smoke --harness c
  python experiment_runner.py --harness a,b,c          # full run (gated)
  python experiment_runner.py --harness c --questions Q01,Q05
  python experiment_runner.py --force-run              # skip L1 gate (debug only)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
QUESTIONS_PATH = ROOT / "experiment" / "questions.json"
RESULTS_DIR = ROOT / "experiment" / "results"
PROFILES_DIR = ROOT / "experiment" / "profiles"

HARNESS_META = {
    "a": {
        "name": "baseline_no_redis",
        "compose": "docker-compose-harness-a.yml",
        "redis_layer": None,
        "profile": "a",
        "system_hint": (
            "HARNESS A: Do not use Redis COBOL dictionary or ir_query.py. "
            "Answer without IR. Label uncertainty."
        ),
    },
    "b": {
        "name": "l0_ir_query_time",
        "compose": "docker-compose-harness-b.yml",
        "redis_layer": "l0",
        "profile": "b",
        "system_hint": (
            "HARNESS B: Use only L0 ir_query (no --english/--rules). "
            "GET para/meta/index first, then re-interpret IR at query time."
        ),
    },
    "c": {
        "name": "l1_english_ingestion",
        "compose": "docker-compose-harness-c.yml",
        "redis_layer": "l1",
        "profile": "c",
        "system_hint": (
            "HARNESS C: Use ir_query --english / --rules only. "
            "Do not re-interpret :para: at query time. On L1 miss refuse."
        ),
    },
}

L1_COVERAGE_GATE = 0.95
DEFAULT_MODEL = os.environ.get("HERMES_EXPERIMENT_MODEL", "Qwen3.6-35B-A3B-MTP-GGUF")


def resolve_hermes_bin() -> str:
    """Locate hermes CLI on Windows/Unix (hermes.bat / hermes.exe / PATH)."""
    env = os.environ.get("HERMES_BIN")
    if env:
        return env
    candidates = [
        Path.home() / ".local" / "bin" / "hermes.bat",
        Path.home() / ".local" / "bin" / "hermes.exe",
        Path.home() / ".local" / "bin" / "hermes",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    return "hermes"


DEFAULT_HERMES = resolve_hermes_bin()


def load_questions() -> list[dict[str, Any]]:
    data = json.loads(QUESTIONS_PATH.read_text(encoding="utf-8"))
    return list(data["questions"])


def redis_client():
    try:
        import redis
    except ImportError:
        return None
    return redis.Redis(
        host=os.environ.get("REDIS_COBOL_HOST", "localhost"),
        port=int(os.environ.get("REDIS_COBOL_PORT", "6380")),
        password=os.environ.get("REDIS_COBOL_PASSWORD", "cobol123"),
        decode_responses=True,
        socket_connect_timeout=5,
    )


def measure_l1_coverage() -> dict[str, Any]:
    """Return L0 para count, L1 english count, coverage ratio."""
    r = redis_client()
    if r is None:
        return {"ok": False, "error": "redis package missing"}
    try:
        r.ping()
    except Exception as e:
        return {"ok": False, "error": str(e)}

    # Prefer index keys when present
    para_keys = 0
    eng_keys = 0
    cursor = 0
    while True:
        cursor, batch = r.scan(cursor=cursor, match="*:para:*", count=500)
        para_keys += len(batch)
        if cursor == 0:
            break
    cursor = 0
    while True:
        cursor, batch = r.scan(cursor=cursor, match="*:english:*", count=500)
        eng_keys += len(batch)
        if cursor == 0:
            break
    ratio = (eng_keys / para_keys) if para_keys else 0.0
    return {
        "ok": True,
        "para_keys": para_keys,
        "english_keys": eng_keys,
        "coverage": ratio,
        "gate": L1_COVERAGE_GATE,
        "pass": ratio >= L1_COVERAGE_GATE,
    }


def prepend_profile(harness: str, question: str) -> str:
    meta = HARNESS_META[harness]
    profile_path = PROFILES_DIR / meta["profile"] / "AGENTS.md"
    profile_text = ""
    if profile_path.is_file():
        profile_text = profile_path.read_text(encoding="utf-8")[:4000]
    return (
        f"[EXPERIMENT HARNESS {harness.upper()} — {meta['name']}]\n"
        f"{meta['system_hint']}\n\n"
        f"--- profile excerpt ---\n{profile_text}\n--- end profile ---\n\n"
        f"QUESTION:\n{question}\n"
    )


def run_hermes(query: str, model: str, timeout: int) -> dict[str, Any]:
    # Do NOT pass --ignore-user-config: local Hermes needs ~/.hermes/config.yaml
    # for Lemonade custom provider (base_url). Ignoring it yields HTTP 401.
    cmd = [
        DEFAULT_HERMES,
        "chat",
        "-Q",
        "-q",
        query,
        "-m",
        model,
    ]
    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "HERMES_COBOL_ROOT": str(ROOT)},
        )
        elapsed = time.time() - t0
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "elapsed_sec": round(elapsed, 2),
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": e.stdout or "",
            "stderr": (e.stderr or "") + f"\nTIMEOUT after {timeout}s",
            "elapsed_sec": timeout,
            "cmd": cmd,
        }
    except FileNotFoundError:
        return {
            "ok": False,
            "returncode": -2,
            "stdout": "",
            "stderr": f"hermes binary not found: {DEFAULT_HERMES}",
            "elapsed_sec": 0,
            "cmd": cmd,
        }


def smoke_test(harness: str, model: str, timeout: int) -> int:
    """Minimal connectivity check — does not run the full 10Q suite."""
    print(f"=== SMOKE harness={harness} ===")
    if harness in ("b", "c"):
        cov = measure_l1_coverage()
        print(json.dumps(cov, indent=2))
        if not cov.get("ok"):
            print("SMOKE FAIL: Redis not reachable", file=sys.stderr)
            return 2
        # L0 probe via ir_query
        probe = subprocess.run(
            [sys.executable, str(ROOT / "translations" / "ir_query.py"), "--list", "COACTUPC"],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(ROOT),
        )
        print("ir_query --list COACTUPC exit=", probe.returncode)
        print((probe.stdout or probe.stderr)[:500])
        if probe.returncode != 0:
            return 2
        if harness == "c":
            eng = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "translations" / "ir_query.py"),
                    "COACTUPC",
                    "1200-EDIT-MAP-INPUTS",
                    "--english",
                ],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(ROOT),
            )
            print("L1 english probe exit=", eng.returncode)
            print((eng.stdout or eng.stderr)[:400])
            if eng.returncode != 0 or "L1 key not found" in (eng.stdout + eng.stderr):
                print("SMOKE WARN: L1 english missing for pilot paragraph", file=sys.stderr)

    # One short hermes call (optional if hermes missing — report only)
    q = "Reply with exactly: SMOKE_OK"
    result = run_hermes(q, model=model, timeout=min(timeout, 120))
    print("hermes smoke ok=", result["ok"], "elapsed=", result["elapsed_sec"])
    if result["stdout"]:
        print(result["stdout"][:300])
    if result["stderr"]:
        print(result["stderr"][:300], file=sys.stderr)
    print("SMOKE complete (full experiment NOT run)")
    return 0 if result["ok"] or result["returncode"] == -2 else 1


def run_suite(
    harnesses: list[str],
    question_ids: list[str] | None,
    model: str,
    timeout: int,
    force: bool,
) -> int:
    questions = load_questions()
    if question_ids:
        want = set(question_ids)
        questions = [q for q in questions if q["id"] in want]
        if not questions:
            print("No matching questions", file=sys.stderr)
            return 2

    if any(h in ("b", "c") for h in harnesses) and not force:
        cov = measure_l1_coverage()
        print("L1 coverage:", json.dumps(cov))
        if not cov.get("ok"):
            print("Redis unreachable — abort. Use --force-run only for debug.", file=sys.stderr)
            return 2
        if not cov.get("pass"):
            print(
                f"L1 coverage {cov.get('coverage', 0):.1%} < {L1_COVERAGE_GATE:.0%} gate. "
                "Finish Phase 2 or pass --force-run.",
                file=sys.stderr,
            )
            return 3

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = RESULTS_DIR / f"run_{run_id}.jsonl"
    manifest = {
        "run_id": run_id,
        "model": model,
        "harnesses": harnesses,
        "questions": [q["id"] for q in questions],
        "started_at": datetime.now(timezone.utc).isoformat(),
        "force": force,
    }
    (RESULTS_DIR / f"run_{run_id}_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    print(f"Writing results → {out_path}")

    n = 0
    with out_path.open("w", encoding="utf-8") as fh:
        for h in harnesses:
            for q in questions:
                payload = prepend_profile(h, q["text"])
                print(f"--- {h.upper()} {q['id']} ---")
                result = run_hermes(payload, model=model, timeout=timeout)
                row = {
                    "run_id": run_id,
                    "harness": h,
                    "harness_name": HARNESS_META[h]["name"],
                    "question_id": q["id"],
                    "question_title": q.get("title"),
                    "question_text": q["text"],
                    "model": model,
                    "ts": datetime.now(timezone.utc).isoformat(),
                    **result,
                }
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                fh.flush()
                n += 1
                status = "OK" if result["ok"] else "FAIL"
                print(f"  {status} {result['elapsed_sec']}s rc={result['returncode']}")

    print(f"Done. {n} runs → {out_path}")
    print("Score with docs/EXPERIMENT-QUESTIONS.md rubric. Do not auto-claim PASS.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="A/B/C harness experiment runner")
    ap.add_argument("--list", action="store_true", help="List questions and harnesses")
    ap.add_argument("--smoke", action="store_true", help="Smoke test only (no full suite)")
    ap.add_argument(
        "--harness",
        default="c",
        help="Comma-separated harness ids: a,b,c (default: c)",
    )
    ap.add_argument(
        "--questions",
        default="",
        help="Comma-separated question ids e.g. Q01,Q05 (default: all)",
    )
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--timeout", type=int, default=300, help="Per-query timeout seconds")
    ap.add_argument(
        "--force-run",
        action="store_true",
        help="Skip L1 coverage gate (debug only)",
    )
    args = ap.parse_args()

    if args.list:
        print("Harnesses:")
        for k, v in HARNESS_META.items():
            print(f"  {k}: {v['name']}  compose={v['compose']}")
        print("Questions:")
        for q in load_questions():
            print(f"  {q['id']}: {q['title']}")
        cov = measure_l1_coverage()
        print("L1 coverage probe:", json.dumps(cov))
        return 0

    harnesses = [h.strip().lower() for h in args.harness.split(",") if h.strip()]
    for h in harnesses:
        if h not in HARNESS_META:
            print(f"Unknown harness: {h}", file=sys.stderr)
            return 2

    qids = [x.strip().upper() for x in args.questions.split(",") if x.strip()] or None

    if args.smoke:
        # smoke each requested harness
        rc = 0
        for h in harnesses:
            rc = max(rc, smoke_test(h, model=args.model, timeout=args.timeout))
        return rc

    print(
        "NOTE: Full experiment run requested. "
        "Ensure partner has approved after smoke tests."
    )
    return run_suite(
        harnesses=harnesses,
        question_ids=qids,
        model=args.model,
        timeout=args.timeout,
        force=args.force_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
