#!/usr/bin/env python3
"""
experiment_runner.py — A/B/C harness comparison runner.

Runs the same question set against harness profiles A, B, and C via
`hermes chat -Q -q ...`. Does NOT score answers automatically — stores
raw transcripts under experiment/results/ for human rubric scoring.

Auditable artifact layout (per run):
  experiment/results/run_<id>/
    MANIFEST.json          — run config, host, coverage gate, model
    RUN.log                — verbose master log (timestamps, every step)
    INDEX.md               — human index of all cells + status
    results.jsonl          — one JSON object per cell (full text)
    summary.json           — counts, timings, paths
    cells/<H>/<QID>/
      meta.json            — timing, rc, cmd, sizes
      prompt.txt           — exact payload sent to Hermes
      stdout.txt           — Hermes stdout
      stderr.txt           — Hermes stderr
      combined.md          — auditable markdown view of the cell

Usage:
  python experiment_runner.py --list
  python experiment_runner.py --smoke --harness c
  python experiment_runner.py --harness a,b,c --verbose
  python experiment_runner.py --harness c --questions Q01,Q05
  python experiment_runner.py --force-run              # skip L1 gate (debug only)
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TextIO

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


class AuditLog:
    """Tee-style verbose logger to console + RUN.log."""

    def __init__(self, path: Path, verbose: bool = True) -> None:
        self.path = path
        self.verbose = verbose
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fh: TextIO = path.open("w", encoding="utf-8", newline="\n")
        self.line("AUDIT LOG OPEN", path=str(path))

    def close(self) -> None:
        try:
            self.line("AUDIT LOG CLOSE")
            self._fh.close()
        except Exception:
            pass

    def line(self, msg: str, **fields: Any) -> None:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        extra = ""
        if fields:
            extra = " " + " ".join(f"{k}={v!r}" for k, v in fields.items())
        text = f"[{ts}] {msg}{extra}"
        self._fh.write(text + "\n")
        self._fh.flush()
        if self.verbose:
            print(text, flush=True)

    def section(self, title: str) -> None:
        bar = "=" * 72
        self.line(bar)
        self.line(title)
        self.line(bar)


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

    para_keys = 0
    eng_keys = 0
    rules_keys = 0
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
    cursor = 0
    while True:
        cursor, batch = r.scan(cursor=cursor, match="*:rules:*", count=500)
        rules_keys += len(batch)
        if cursor == 0:
            break
    ratio = (eng_keys / para_keys) if para_keys else 0.0
    return {
        "ok": True,
        "para_keys": para_keys,
        "english_keys": eng_keys,
        "rules_keys": rules_keys,
        "dbsize": r.dbsize(),
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


def run_hermes(
    query: str,
    model: str,
    timeout: int,
    verbose_hermes: bool,
    log: AuditLog | None = None,
) -> dict[str, Any]:
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
    if verbose_hermes:
        cmd.append("-v")

    if log:
        log.line("HERMES_START", cmd=cmd[:6] + ["…"], model=model, timeout=timeout)

    t0 = time.time()
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            env={**os.environ, "HERMES_COBOL_ROOT": str(ROOT)},
        )
        elapsed = time.time() - t0
        result = {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout or "",
            "stderr": proc.stderr or "",
            "elapsed_sec": round(elapsed, 2),
            "cmd": cmd,
        }
    except subprocess.TimeoutExpired as e:
        result = {
            "ok": False,
            "returncode": -1,
            "stdout": (e.stdout or "") if isinstance(e.stdout, str) else "",
            "stderr": ((e.stderr or "") if isinstance(e.stderr, str) else "")
            + f"\nTIMEOUT after {timeout}s",
            "elapsed_sec": timeout,
            "cmd": cmd,
        }
    except FileNotFoundError:
        result = {
            "ok": False,
            "returncode": -2,
            "stdout": "",
            "stderr": f"hermes binary not found: {DEFAULT_HERMES}",
            "elapsed_sec": 0,
            "cmd": cmd,
        }
    except Exception as e:
        result = {
            "ok": False,
            "returncode": -3,
            "stdout": "",
            "stderr": f"{type(e).__name__}: {e}\n{traceback.format_exc()}",
            "elapsed_sec": round(time.time() - t0, 2),
            "cmd": cmd,
        }

    if log:
        log.line(
            "HERMES_END",
            ok=result["ok"],
            rc=result["returncode"],
            elapsed=result["elapsed_sec"],
            stdout_bytes=len(result["stdout"]),
            stderr_bytes=len(result["stderr"]),
        )
    return result


def write_cell_artifacts(
    cell_dir: Path,
    *,
    harness: str,
    question: dict[str, Any],
    prompt: str,
    result: dict[str, Any],
    run_id: str,
    model: str,
    seq: int,
    total: int,
) -> dict[str, Any]:
    cell_dir.mkdir(parents=True, exist_ok=True)
    (cell_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
    (cell_dir / "stdout.txt").write_text(result.get("stdout") or "", encoding="utf-8")
    (cell_dir / "stderr.txt").write_text(result.get("stderr") or "", encoding="utf-8")

    meta = {
        "run_id": run_id,
        "seq": seq,
        "total": total,
        "harness": harness,
        "harness_name": HARNESS_META[harness]["name"],
        "question_id": question["id"],
        "question_title": question.get("title"),
        "question_text": question["text"],
        "model": model,
        "ok": result.get("ok"),
        "returncode": result.get("returncode"),
        "elapsed_sec": result.get("elapsed_sec"),
        "cmd": result.get("cmd"),
        "stdout_chars": len(result.get("stdout") or ""),
        "stderr_chars": len(result.get("stderr") or ""),
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "artifact_dir": str(cell_dir.relative_to(ROOT)).replace("\\", "/"),
    }
    (cell_dir / "meta.json").write_text(
        json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    status = "OK" if result.get("ok") else "FAIL"
    combined = (
        f"# Cell {seq}/{total}: Harness {harness.upper()} · {question['id']}\n\n"
        f"- **Status:** {status}\n"
        f"- **Harness:** {harness} ({HARNESS_META[harness]['name']})\n"
        f"- **Question:** {question['id']} — {question.get('title')}\n"
        f"- **Model:** {model}\n"
        f"- **Elapsed:** {result.get('elapsed_sec')}s\n"
        f"- **Return code:** {result.get('returncode')}\n"
        f"- **UTC:** {meta['ts_utc']}\n"
        f"- **Run:** {run_id}\n\n"
        f"## Question text\n\n```\n{question['text']}\n```\n\n"
        f"## Prompt payload (sent to Hermes)\n\n```\n{prompt}\n```\n\n"
        f"## Hermes stdout\n\n```\n{result.get('stdout') or ''}\n```\n\n"
        f"## Hermes stderr\n\n```\n{result.get('stderr') or ''}\n```\n"
    )
    (cell_dir / "combined.md").write_text(combined, encoding="utf-8")
    return meta


def smoke_test(harness: str, model: str, timeout: int, verbose: bool) -> int:
    """Minimal connectivity check — does not run the full 10Q suite."""
    print(f"=== SMOKE harness={harness} ===")
    if harness in ("b", "c"):
        cov = measure_l1_coverage()
        print(json.dumps(cov, indent=2))
        if not cov.get("ok"):
            print("SMOKE FAIL: Redis not reachable", file=sys.stderr)
            return 2
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

    q = "Reply with exactly: SMOKE_OK"
    result = run_hermes(q, model=model, timeout=min(timeout, 120), verbose_hermes=verbose)
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
    verbose: bool,
    verbose_hermes: bool,
) -> int:
    questions = load_questions()
    if question_ids:
        want = set(question_ids)
        questions = [q for q in questions if q["id"] in want]
        if not questions:
            print("No matching questions", file=sys.stderr)
            return 2

    cov = measure_l1_coverage()
    if any(h in ("b", "c") for h in harnesses) and not force:
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
    run_dir = RESULTS_DIR / f"run_{run_id}"
    cells_dir = run_dir / "cells"
    run_dir.mkdir(parents=True, exist_ok=True)
    cells_dir.mkdir(parents=True, exist_ok=True)

    log = AuditLog(run_dir / "RUN.log", verbose=verbose)
    try:
        log.section(f"EXPERIMENT RUN {run_id}")
        log.line("ROOT", path=str(ROOT))
        log.line("HERMES_BIN", path=DEFAULT_HERMES)
        log.line("MODEL", model=model)
        log.line("TIMEOUT_SEC", value=timeout)
        log.line("HARNESSES", value=harnesses)
        log.line("QUESTIONS", value=[q["id"] for q in questions])
        log.line("PLATFORM", value=platform.platform())
        log.line("PYTHON", value=sys.version.replace("\n", " "))
        log.line("L1_COVERAGE", **{k: cov.get(k) for k in cov})
        log.line("FORCE", value=force)
        log.line("VERBOSE_HERMES", value=verbose_hermes)

        total = len(harnesses) * len(questions)
        manifest = {
            "run_id": run_id,
            "artifact_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
            "model": model,
            "hermes_bin": DEFAULT_HERMES,
            "harnesses": harnesses,
            "harness_meta": {h: HARNESS_META[h] for h in harnesses},
            "questions": [
                {"id": q["id"], "title": q.get("title"), "text": q["text"]} for q in questions
            ],
            "total_cells": total,
            "timeout_sec": timeout,
            "started_at": datetime.now(timezone.utc).isoformat(),
            "force": force,
            "verbose": verbose,
            "verbose_hermes": verbose_hermes,
            "l1_coverage": cov,
            "platform": platform.platform(),
            "python": sys.version,
            "cwd": str(ROOT),
            "rubric_doc": "docs/EXPERIMENT-QUESTIONS.md",
            "scoring": "manual — runner does not auto-PASS",
        }
        (run_dir / "MANIFEST.json").write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        log.line("MANIFEST_WRITTEN", path=str(run_dir / "MANIFEST.json"))

        jsonl_path = run_dir / "results.jsonl"
        index_rows: list[dict[str, Any]] = []
        ok_n = fail_n = 0
        seq = 0
        t_suite = time.time()

        with jsonl_path.open("w", encoding="utf-8") as fh:
            for h in harnesses:
                log.section(f"HARNESS {h.upper()} — {HARNESS_META[h]['name']}")
                for q in questions:
                    seq += 1
                    log.line(
                        "CELL_START",
                        seq=f"{seq}/{total}",
                        harness=h,
                        question=q["id"],
                        title=q.get("title"),
                    )
                    prompt = prepend_profile(h, q["text"])
                    result = run_hermes(
                        prompt,
                        model=model,
                        timeout=timeout,
                        verbose_hermes=verbose_hermes,
                        log=log,
                    )
                    cell_dir = cells_dir / h / q["id"]
                    meta = write_cell_artifacts(
                        cell_dir,
                        harness=h,
                        question=q,
                        prompt=prompt,
                        result=result,
                        run_id=run_id,
                        model=model,
                        seq=seq,
                        total=total,
                    )
                    row = {
                        **meta,
                        "stdout": result.get("stdout") or "",
                        "stderr": result.get("stderr") or "",
                    }
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
                    fh.flush()
                    index_rows.append(meta)
                    if result.get("ok"):
                        ok_n += 1
                        log.line("CELL_OK", seq=seq, harness=h, q=q["id"], s=result["elapsed_sec"])
                    else:
                        fail_n += 1
                        log.line(
                            "CELL_FAIL",
                            seq=seq,
                            harness=h,
                            q=q["id"],
                            rc=result.get("returncode"),
                            stderr_preview=(result.get("stderr") or "")[:200],
                        )
                    # console progress line
                    status = "OK" if result.get("ok") else "FAIL"
                    print(
                        f"  [{seq}/{total}] {h.upper()} {q['id']} → {status} "
                        f"{result.get('elapsed_sec')}s  → {cell_dir.relative_to(ROOT)}",
                        flush=True,
                    )

        ended = datetime.now(timezone.utc).isoformat()
        suite_elapsed = round(time.time() - t_suite, 1)
        summary = {
            "run_id": run_id,
            "artifact_dir": str(run_dir.relative_to(ROOT)).replace("\\", "/"),
            "started_at": manifest["started_at"],
            "ended_at": ended,
            "elapsed_sec": suite_elapsed,
            "total_cells": total,
            "ok": ok_n,
            "fail": fail_n,
            "model": model,
            "harnesses": harnesses,
            "questions": [q["id"] for q in questions],
            "results_jsonl": str(jsonl_path.relative_to(ROOT)).replace("\\", "/"),
            "run_log": str((run_dir / "RUN.log").relative_to(ROOT)).replace("\\", "/"),
            "cells": [
                {
                    "harness": m["harness"],
                    "question_id": m["question_id"],
                    "ok": m["ok"],
                    "elapsed_sec": m["elapsed_sec"],
                    "artifact_dir": m["artifact_dir"],
                }
                for m in index_rows
            ],
        }
        (run_dir / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
        )

        # INDEX.md for human navigation
        lines = [
            f"# Experiment run `{run_id}`",
            "",
            f"- **Started:** {manifest['started_at']}",
            f"- **Ended:** {ended}",
            f"- **Elapsed:** {suite_elapsed}s",
            f"- **Model:** `{model}`",
            f"- **Cells:** {ok_n} OK / {fail_n} FAIL / {total} total",
            f"- **L1 coverage:** {cov.get('coverage')} ({cov.get('english_keys')}/{cov.get('para_keys')})",
            f"- **Master log:** [`RUN.log`](RUN.log)",
            f"- **Manifest:** [`MANIFEST.json`](MANIFEST.json)",
            f"- **JSONL:** [`results.jsonl`](results.jsonl)",
            f"- **Summary:** [`summary.json`](summary.json)",
            f"- **Rubric:** `docs/EXPERIMENT-QUESTIONS.md` (manual scoring)",
            "",
            "## Cells",
            "",
            "| # | Harness | Q | Status | Sec | Artifacts |",
            "|---|---------|---|--------|-----|-----------|",
        ]
        for m in index_rows:
            st = "OK" if m["ok"] else "FAIL"
            rel = m["artifact_dir"].replace("experiment/results/" + f"run_{run_id}/", "")
            # relative from run_dir
            cell_rel = f"cells/{m['harness']}/{m['question_id']}"
            lines.append(
                f"| {m['seq']} | {m['harness'].upper()} | {m['question_id']} | {st} | "
                f"{m['elapsed_sec']} | [`{cell_rel}`]({cell_rel}/combined.md) |"
            )
        lines.extend(
            [
                "",
                "## Scoring note",
                "",
                "Runner records execution only. Apply the rubric in "
                "`docs/EXPERIMENT-QUESTIONS.md` before claiming PASS/FAIL on answer quality.",
                "",
            ]
        )
        (run_dir / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")

        # also write a pointer at results/LATEST
        latest = RESULTS_DIR / "LATEST"
        try:
            if latest.is_symlink() or latest.exists():
                latest.unlink()
            latest.write_text(run_id + "\n", encoding="utf-8")
        except OSError:
            (RESULTS_DIR / "LATEST.txt").write_text(run_id + "\n", encoding="utf-8")

        log.section("RUN COMPLETE")
        log.line("SUMMARY", ok=ok_n, fail=fail_n, total=total, elapsed=suite_elapsed)
        log.line("ARTIFACT_DIR", path=str(run_dir))
        print(f"\nDone. Artifacts → {run_dir}")
        print(f"  INDEX:  {run_dir / 'INDEX.md'}")
        print(f"  LOG:    {run_dir / 'RUN.log'}")
        print(f"  JSONL:  {jsonl_path}")
        print("Score with docs/EXPERIMENT-QUESTIONS.md rubric. Do not auto-claim PASS.")
        return 0 if fail_n == 0 else 1
    finally:
        log.close()


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
    ap.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="Per-query timeout seconds (default: 600)",
    )
    ap.add_argument(
        "--force-run",
        action="store_true",
        help="Skip L1 coverage gate (debug only)",
    )
    ap.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=True,
        help="Verbose audit log to console (default: on)",
    )
    ap.add_argument(
        "--quiet",
        action="store_true",
        help="Less console noise (still writes full RUN.log)",
    )
    ap.add_argument(
        "--verbose-hermes",
        action="store_true",
        default=True,
        help="Pass -v to hermes chat (default: on)",
    )
    ap.add_argument(
        "--no-verbose-hermes",
        action="store_true",
        help="Do not pass -v to hermes",
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
    verbose = not args.quiet
    verbose_hermes = args.verbose_hermes and not args.no_verbose_hermes

    if args.smoke:
        rc = 0
        for h in harnesses:
            rc = max(rc, smoke_test(h, model=args.model, timeout=args.timeout, verbose=verbose_hermes))
        return rc

    print(
        "NOTE: Full experiment run requested. "
        "Artifacts under experiment/results/run_<id>/."
    )
    return run_suite(
        harnesses=harnesses,
        question_ids=qids,
        model=args.model,
        timeout=args.timeout,
        force=args.force_run,
        verbose=verbose,
        verbose_hermes=verbose_hermes,
    )


if __name__ == "__main__":
    raise SystemExit(main())
