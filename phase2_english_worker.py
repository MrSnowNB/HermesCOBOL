#!/usr/bin/env python3
"""
phase2_english_worker.py — Phase 2 English ingestion worker (ingestion-time only).

Reads L0 Redis keys  {PROG}:para:{NAME}
Writes L1 Redis keys {PROG}:english:{NAME} and {PROG}:rules:{NAME}

WRITE PROTECTION: may only SET keys containing ':english:' or ':rules:'.
Never overwrites :para:, :meta:, :cfg:, or :index:.

Usage:
  python phase2_english_worker.py --dry-run --program COACTUPC
  python phase2_english_worker.py --program COACTUPC --paragraph 1200-EDIT-MAP-INPUTS --force
  python phase2_english_worker.py --program COACTUPC
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any

try:
    import redis
except ImportError:
    print("ERROR: redis package required (pip install redis)", file=sys.stderr)
    sys.exit(2)

try:
    import httpx
except ImportError:
    try:
        import urllib.request

        httpx = None  # type: ignore
    except ImportError:
        print("ERROR: httpx or urllib required for LLM calls", file=sys.stderr)
        sys.exit(2)

GENERATOR_ID = "phase2_english_worker/v1"
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6380
DEFAULT_PASSWORD = "cobol123"
DEFAULT_MODEL = "Qwen3.6-35B-A3B-MTP-GGUF"
DEFAULT_BASE_URL = "http://127.0.0.1:8000/api/v1"

SYSTEM_MSG = (
    "You are a COBOL business analyst producing auditable documentation. "
    "Every business rule must cite [seq N] from the IR. "
    "No code. No COBOL syntax in prose."
)

SECTION_HEADERS = [
    "PARAGRAPH:",
    "PROGRAM:",
    "SOURCE LINES:",
    "PURPOSE",
    "PRECONDITIONS:",
    "BUSINESS LOGIC",
    "BUSINESS RULES",
    "DATA FLOW:",
    "EDGE CASES AND RISKS:",
]

# ---------------------------------------------------------------------------
# Redis write protection
# ---------------------------------------------------------------------------


def assert_writable_key(key: str) -> None:
    """Raise if key is not an L1 english/rules key."""
    if ":english:" not in key and ":rules:" not in key:
        raise RuntimeError(
            f"WRITE PROTECTION: refused to write non-L1 key '{key}'. "
            "Only :english: and :rules: keys are allowed."
        )
    # Extra guard: must not look like L0
    for banned in (":para:", ":meta", ":cfg:", ":index"):
        # allow :english: and :rules: only — ban substrings of L0
        if banned in key and ":english:" not in key and ":rules:" not in key:
            raise RuntimeError(f"WRITE PROTECTION: banned pattern in key '{key}'")


def safe_set(r: redis.Redis, key: str, value: str) -> None:
    assert_writable_key(key)
    r.set(key, value)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------


def connect_redis(host: str, port: int, password: str) -> redis.Redis:
    r = redis.Redis(
        host=host,
        port=port,
        password=password,
        decode_responses=True,
        socket_connect_timeout=10,
    )
    r.ping()
    return r


def list_programs(r: redis.Redis) -> list[str]:
    raw = r.get("cobol:manifest")
    if raw:
        try:
            m = json.loads(raw)
            progs = [p["program"] for p in m.get("programs", []) if p.get("program")]
            if progs:
                return sorted(progs)
        except json.JSONDecodeError:
            pass
    # Fallback: scan :index keys
    names = set()
    for k in r.scan_iter(match="*:index", count=200):
        if k.count(":") == 1:
            names.add(k.split(":")[0])
    return sorted(names)


def list_paragraphs(r: redis.Redis, program: str) -> list[str]:
    prog = program.upper()
    raw = r.get(f"{prog}:index")
    if raw:
        try:
            names = json.loads(raw)
            if isinstance(names, list):
                return names
        except json.JSONDecodeError:
            pass
    prefix = f"{prog}:para:"
    return sorted(k[len(prefix) :] for k in r.scan_iter(match=prefix + "*", count=500))


def get_para_ir(r: redis.Redis, program: str, paragraph: str) -> dict | None:
    raw = r.get(f"{program.upper()}:para:{paragraph}")
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def get_schema_version(r: redis.Redis, program: str, ir: dict) -> str:
    if ir.get("schema_version"):
        return str(ir["schema_version"])
    meta = r.get(f"{program.upper()}:meta")
    if meta:
        try:
            m = json.loads(meta)
            if m.get("schema_version"):
                return str(m["schema_version"])
        except json.JSONDecodeError:
            pass
    man = r.get("cobol:manifest")
    if man:
        try:
            return str(json.loads(man).get("schema_version") or "1.4")
        except json.JSONDecodeError:
            pass
    return "1.4"


# ---------------------------------------------------------------------------
# Prompt construction
# ---------------------------------------------------------------------------


def build_user_prompt(program: str, paragraph: str, ir: dict) -> str:
    source_lines = ir.get("source_lines")
    if source_lines is None:
        source_lines = "unknown"
    ir_json = json.dumps(ir, indent=2, ensure_ascii=False)
    # Cap enormous IR to keep context sane (keep structure)
    if len(ir_json) > 48000:
        ir_trim = {
            "program": ir.get("program", program),
            "paragraph": ir.get("paragraph") or ir.get("name") or paragraph,
            "source_lines": source_lines,
            "reads": ir.get("reads"),
            "mutates": ir.get("mutates"),
            "performs": ir.get("performs"),
            "goto_targets": ir.get("goto_targets"),
            "terminator": ir.get("terminator"),
            "last_verb": ir.get("last_verb"),
            "statements": (ir.get("statements") or [])[:80],
            "_note": "statements truncated for context; cite only seq present below",
        }
        ir_json = json.dumps(ir_trim, indent=2, ensure_ascii=False)

    return f"""You are a COBOL business analyst, not a code translator.

The following is the structured IR for Redis key {program.upper()}:para:{paragraph}.
Produce a structured English business logic document with THESE EXACT section headers:

PARAGRAPH: [name]
PROGRAM: {program.upper()}
SOURCE LINES: [from IR source_lines field]

PURPOSE (2-3 sentences):
  What business function does this paragraph perform?
  Not what the code does — what the BUSINESS does.

PRECONDITIONS:
  What must be true before this paragraph runs?
  (from cfg predecessors and reads fields)

BUSINESS LOGIC (numbered steps):
  For each logical group of statements, one plain-English sentence.
  Do NOT translate line by line — group by intent.
  Cite the seq range for each step: [seq 209-211]

BUSINESS RULES (bullet list):
  Explicit rules embedded in the logic — conditions, validations,
  constraints. These are the sentences that belong in a requirements doc.
  Format each as: - BR-N: The system SHALL ... [seq N]

DATA FLOW:
  READS: [field names from IR reads array]
  WRITES: [field names from IR mutates array]
  CALLS: [paragraphs from IR performs array]

EDGE CASES AND RISKS:
  What would a developer miss if they didn't read this carefully?
  Any short-circuit logic, implicit defaults, blank-vs-null distinctions?

Keep the total output under 400 words. Do not show code.
Every fact must trace to the Redis IR — cite [seq N] for each rule.
If the IR has no statements/seq fields, cite [seq unknown] only when unavoidable and prefer field names from reads/mutates/performs.

=== IR JSON ===
{ir_json}
"""


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------


def chat_completions(
    base_url: str,
    model: str,
    system: str,
    user: str,
    timeout: float,
) -> str:
    url = base_url.rstrip("/") + "/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.2,
        "max_tokens": 1600,
    }
    # Discourage long CoT if the server honors it
    payload["chat_template_kwargs"] = {"enable_thinking": False}
    if httpx is not None:
        with httpx.Client(timeout=timeout) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
    else:
        import urllib.error
        import urllib.request

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {e.code}: {body[:500]}") from e

    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    content = msg.get("content") or ""
    # Some local models put text only in reasoning_content
    if not content.strip():
        content = msg.get("reasoning_content") or ""
    if not content.strip():
        raise RuntimeError("LLM returned empty content")
    return content.strip()


# ---------------------------------------------------------------------------
# Parse model output → rules + seq cites
# ---------------------------------------------------------------------------

SEQ_RE = re.compile(r"\[seq\s+([0-9]+(?:\s*-\s*[0-9]+)?|unknown)\]", re.I)
BR_RE = re.compile(
    r"(?:^|\n)\s*(?:[-*•]|\d+\.)?\s*(?:BR[- ]?(\d+)\s*:)?\s*"
    r"(The system SHALL\s+.+?)(?=\n\s*(?:[-*•]|\d+\.|BR[- ]?\d+\s*:|DATA FLOW|EDGE CASES|BUSINESS LOGIC|PRECONDITIONS|PURPOSE|READS:|WRITES:|CALLS:|$))",
    re.I | re.S,
)
BR_LINE_RE = re.compile(
    r"^\s*(?:[-*•]|\d+\.)?\s*(?:BR[- ]?(\d+)\s*:)?\s*(The system SHALL\s+.+)$",
    re.I,
)


def extract_seq_cites(text: str) -> list[Any]:
    cites: list[Any] = []
    for m in SEQ_RE.finditer(text):
        raw = m.group(1).replace(" ", "")
        if raw.lower() == "unknown":
            continue
        if "-" in raw:
            a, b = raw.split("-", 1)
            try:
                cites.append({"from": int(a), "to": int(b)})
            except ValueError:
                continue
        else:
            try:
                cites.append(int(raw))
            except ValueError:
                continue
    # unique preserve order
    seen = set()
    out = []
    for c in cites:
        key = json.dumps(c, sort_keys=True) if isinstance(c, dict) else c
        if key not in seen:
            seen.add(key)
            out.append(c)
    return out


def extract_rules(text: str) -> list[dict]:
    rules: list[dict] = []
    # Prefer BUSINESS RULES section
    section = text
    m = re.search(
        r"BUSINESS RULES.*?\n(.*?)(?=\nDATA FLOW:|\nEDGE CASES|\Z)",
        text,
        re.I | re.S,
    )
    if m:
        section = m.group(1)

    n = 0
    for line in section.splitlines():
        line = line.strip()
        if not line:
            continue
        bm = BR_LINE_RE.match(line)
        if not bm:
            # also accept lines that contain SHALL without prefix
            if "The system SHALL" in line or "the system SHALL" in line:
                idx = line.lower().find("the system shall")
                text_rule = line[idx:]
                # strip trailing seq for storage in text but keep in field
            else:
                continue
            text_rule = line if "The system SHALL" not in line else line[line.find("The system SHALL") :]
        else:
            text_rule = bm.group(2).strip()

        # ensure starts with The system SHALL
        if not text_rule.lower().startswith("the system shall"):
            continue
        # normalize capital T
        text_rule = "The system SHALL" + text_rule[len("The system SHALL") :]

        seq_m = SEQ_RE.search(text_rule)
        seq_val: Any = None
        if seq_m:
            raw = seq_m.group(1).replace(" ", "")
            if raw.lower() != "unknown":
                if "-" in raw:
                    a, b = raw.split("-", 1)
                    try:
                        seq_val = {"from": int(a), "to": int(b)}
                    except ValueError:
                        seq_val = None
                else:
                    try:
                        seq_val = int(raw)
                    except ValueError:
                        seq_val = None
            # strip cite from text for cleanliness optional — keep cite in text for audit
        n += 1
        rid = f"BR-{bm.group(1)}" if bm and bm.group(1) else f"BR-{n}"
        rules.append({"id": rid, "text": text_rule, "seq": seq_val})

    # Fallback: any The system SHALL in full doc
    if not rules:
        for line in text.splitlines():
            if "The system SHALL" in line or "the system shall" in line.lower():
                idx = line.lower().find("the system shall")
                text_rule = "The system SHALL" + line[idx + len("the system shall") :]
                seq_m = SEQ_RE.search(text_rule)
                seq_val = None
                if seq_m:
                    raw = seq_m.group(1).replace(" ", "")
                    if raw.isdigit():
                        seq_val = int(raw)
                n += 1
                rules.append({"id": f"BR-{n}", "text": text_rule.strip(), "seq": seq_val})
    return rules


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", text))


def clean_document(text: str) -> str:
    """
    Strip chain-of-thought preambles common in local models.
    Prefer content starting at the first PARAGRAPH: section header.
    """
    t = text.strip()
    # Drop leading thinking blocks
    for marker in (
        "Here's a thinking process:",
        "Here is a thinking process:",
        "**Thinking:**",
        "<think>",
    ):
        if t.lower().startswith(marker.lower()):
            # find first required section after preamble
            m = re.search(r"(?im)^PARAGRAPH\s*:", t)
            if m:
                t = t[m.start() :].strip()
            break
    # If PARAGRAPH: appears later, take from there
    m = re.search(r"(?im)^PARAGRAPH\s*:", t)
    if m and m.start() > 0:
        # only cut if substantial preamble
        if m.start() > 80:
            t = t[m.start() :].strip()
    # Close unclosed think tags
    t = re.sub(r"</?think>", "", t, flags=re.I)
    return t.strip()


def check_section_headers(document: str) -> list[str]:
    missing = []
    for h in SECTION_HEADERS:
        # PURPOSE / BUSINESS LOGIC may appear without trailing colon in model output
        if h.rstrip(":").upper() not in document.upper() and h.upper() not in document.upper():
            missing.append(h)
    return missing


# ---------------------------------------------------------------------------
# Process one paragraph
# ---------------------------------------------------------------------------


def process_one(
    r: redis.Redis,
    program: str,
    paragraph: str,
    *,
    model: str,
    base_url: str,
    force: bool,
    dry_run: bool,
    timeout: float,
) -> dict:
    prog = program.upper()
    source_key = f"{prog}:para:{paragraph}"
    eng_key = f"{prog}:english:{paragraph}"
    rules_key = f"{prog}:rules:{paragraph}"

    result = {
        "status": "PENDING",
        "program": prog,
        "paragraph": paragraph,
        "source_key": source_key,
        "seconds": 0.0,
        "word_count": 0,
        "br_count": 0,
        "error": None,
    }

    if not force and r.exists(eng_key) and r.exists(rules_key):
        result["status"] = "SKIP"
        return result

    ir = get_para_ir(r, prog, paragraph)
    if ir is None:
        result["status"] = "ERROR"
        result["error"] = f"missing L0 key {source_key}"
        return result

    if dry_run:
        result["status"] = "WOULD"
        return result

    t0 = time.perf_counter()
    try:
        user_prompt = build_user_prompt(prog, paragraph, ir)
        document = chat_completions(
            base_url=base_url,
            model=model,
            system=SYSTEM_MSG,
            user=user_prompt,
            timeout=timeout,
        )
    except Exception as e:
        result["seconds"] = round(time.perf_counter() - t0, 2)
        err = str(e).lower()
        if "timeout" in err or "timed out" in err:
            result["status"] = "FAIL"
            result["error"] = f"timeout after {timeout}s: {e}"
        else:
            result["status"] = "ERROR"
            result["error"] = f"LLM error: {e}"
        return result

    elapsed = round(time.perf_counter() - t0, 2)
    result["seconds"] = elapsed
    document = clean_document(document)
    cites = extract_seq_cites(document)
    rules = extract_rules(document)
    wc = word_count(document)
    schema_ver = get_schema_version(r, prog, ir)
    generated_at = datetime.now(timezone.utc).isoformat()

    english_obj = {
        "paragraph": paragraph,
        "program": prog,
        "document": document,
        "source_key": source_key,
        "ir_schema_version": schema_ver,
        "generator_id": GENERATOR_ID,
        "generated_at": generated_at,
        "model_id": model,
        "seq_cites": cites,
        "word_count": wc,
    }
    rules_obj = {
        "paragraph": paragraph,
        "program": prog,
        "rules": rules,
        "source_key": source_key,
        "ir_schema_version": schema_ver,
        "generator_id": GENERATOR_ID,
        "generated_at": generated_at,
        "model_id": model,
    }

    try:
        safe_set(r, eng_key, json.dumps(english_obj, ensure_ascii=False))
        safe_set(r, rules_key, json.dumps(rules_obj, ensure_ascii=False))
    except Exception as e:
        result["status"] = "ERROR"
        result["error"] = f"Redis write error: {e}"
        return result

    result["status"] = "DONE"
    result["word_count"] = wc
    result["br_count"] = len(rules)
    result["missing_headers"] = check_section_headers(document)
    return result


def format_line(res: dict) -> str:
    sk = res["source_key"]
    st = res["status"]
    if st == "DONE":
        return (
            f"[DONE]  {sk} → :english: + :rules: "
            f"({res['word_count']}w, {res['br_count']} BRs, {res['seconds']}s)"
        )
    if st == "SKIP":
        return f"[SKIP]  {sk} → already exists (use --force to regenerate)"
    if st == "WOULD":
        return f"[WOULD] {sk} → would generate :english: + :rules:"
    if st == "FAIL":
        return f"[FAIL]  {sk} → {res.get('error')}"
    return f"[ERROR] {sk} → {res.get('error')}"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="Phase 2 English ingestion worker")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--password", default=DEFAULT_PASSWORD)
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--base-url", default=DEFAULT_BASE_URL)
    ap.add_argument("--program", default=None, help="Single program (e.g. COACTUPC)")
    ap.add_argument("--paragraph", default=None, help="Single paragraph name")
    ap.add_argument("--force", action="store_true", help="Overwrite existing L1 keys")
    ap.add_argument("--dry-run", action="store_true", help="No LLM calls, no writes")
    ap.add_argument("--workers", type=int, default=1, help="Parallel workers (1-4)")
    ap.add_argument("--timeout", type=float, default=120.0, help="Per-paragraph LLM timeout")
    args = ap.parse_args()

    workers = max(1, min(4, args.workers))

    try:
        r = connect_redis(args.host, args.port, args.password)
    except redis.RedisError as e:
        print(f"ERROR: Redis connect failed: {e}", file=sys.stderr)
        return 2

    # Build work list
    if args.program and args.paragraph:
        jobs = [(args.program.upper(), args.paragraph)]
    elif args.program:
        paras = list_paragraphs(r, args.program)
        jobs = [(args.program.upper(), p) for p in paras]
    elif args.paragraph:
        print("ERROR: --paragraph requires --program", file=sys.stderr)
        return 2
    else:
        jobs = []
        for prog in list_programs(r):
            for p in list_paragraphs(r, prog):
                jobs.append((prog, p))

    if not jobs:
        print("No paragraphs to process.")
        return 1

    print(
        f"Phase 2 English worker | model={args.model} | base_url={args.base_url} | "
        f"jobs={len(jobs)} | dry_run={args.dry_run} | force={args.force} | workers={workers}"
    )
    t_start = time.perf_counter()
    counts = {"DONE": 0, "SKIP": 0, "FAIL": 0, "ERROR": 0, "WOULD": 0}
    results: list[dict] = []

    def _run(job: tuple[str, str]) -> dict:
        # each worker gets its own redis client
        rr = connect_redis(args.host, args.port, args.password)
        return process_one(
            rr,
            job[0],
            job[1],
            model=args.model,
            base_url=args.base_url,
            force=args.force,
            dry_run=args.dry_run,
            timeout=args.timeout,
        )

    if workers == 1 or args.dry_run:
        for job in jobs:
            res = _run(job)
            results.append(res)
            counts[res["status"]] = counts.get(res["status"], 0) + 1
            print(format_line(res), flush=True)
    else:
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = {ex.submit(_run, j): j for j in jobs}
            for fut in as_completed(futs):
                res = fut.result()
                results.append(res)
                counts[res["status"]] = counts.get(res["status"], 0) + 1
                print(format_line(res), flush=True)

    elapsed = time.perf_counter() - t_start
    done = counts.get("DONE", 0)
    would = counts.get("WOULD", 0)
    l1_written = done * 2  # english + rules

    print()
    print(f"Phase 2 complete: {len(jobs)} paragraphs attempted")
    print(
        f"DONE: {counts.get('DONE', 0)}  SKIP: {counts.get('SKIP', 0)}  "
        f"FAIL: {counts.get('FAIL', 0)}  ERROR: {counts.get('ERROR', 0)}"
        + (f"  WOULD: {would}" if would else "")
    )
    print(f"L1 keys written: {l1_written} ({done} english + {done} rules)")
    mins, secs = divmod(int(elapsed), 60)
    print(f"Elapsed: {mins}m {secs}s")

    # Non-zero exit if any FAIL/ERROR on real runs
    if not args.dry_run and (counts.get("FAIL", 0) or counts.get("ERROR", 0)):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
