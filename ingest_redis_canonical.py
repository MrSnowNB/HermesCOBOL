#!/usr/bin/env python3
"""
ingest_redis_canonical.py — Load CardDemo canonical IR into a plain Redis dictionary.

This is the inference boundary materializer:
  data/canonical/*.canonical.json  →  Redis SET {PROG}:para:{NAME} = full JSON
No embeddings, no chunking, no RediSearch / HNSW.

Rules:
  - Does NOT modify data/canonical/ (read-only)
  - Does NOT touch Honcho
  - Optional read-only enrichment from docs/*_Honcho_Load_Manifest_v2.json
    (statement-level IR when present, e.g. COACTUPC)

Usage:
  python ingest_redis_canonical.py
  python ingest_redis_canonical.py --host localhost --port 6380 --password cobol123
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import redis
except ImportError:
    print("ERROR: redis package required. pip install redis", file=sys.stderr)
    sys.exit(2)

REPO = Path(__file__).resolve().parent
CANONICAL_DIR = REPO / "data" / "canonical"
DOCS_DIR = REPO / "docs"

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6380
DEFAULT_PASSWORD = "cobol123"


def load_statement_enrichment(program: str) -> dict[str, dict]:
    """
    Optional: map paragraph_name -> statement IR unit from Honcho load manifests.
    Does not modify source files; used only to enrich Redis values when available.
    """
    out: dict[str, dict] = {}
    for name in (
        f"{program}_Honcho_Load_Manifest_v2.json",
        f"{program}_Honcho_Load_Manifest.json",
    ):
        path = DOCS_DIR / name
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for unit in data.get("units") or []:
            val = unit.get("value", unit)
            pname = val.get("paragraph") or val.get("name")
            if not pname:
                key = unit.get("key") or ""
                if "/" in key:
                    pname = key.split("/")[-1]
            if not pname:
                continue
            # Prefer v2 (has statements); only overwrite if new has statements or missing
            if pname not in out or val.get("statements"):
                out[pname] = val
        if out:
            break
    return out


def program_name_from_file(path: Path, data: dict) -> str:
    name = data.get("program") or data.get("name") or path.stem
    name = str(name).replace(".canonical", "").upper()
    return name


def build_meta(program: str, data: dict, para_names: list[str]) -> dict:
    return {
        "program": program,
        "schema_version": data.get("schema_version"),
        "source_file": data.get("source_file"),
        "preprocess_available": data.get("preprocess_available"),
        "cics_present": data.get("cics_present"),
        "sql_present": data.get("sql_present"),
        "paragraph_count": len(para_names),
        "data_files": data.get("data_files"),
        "external_calls": data.get("external_calls"),
        "copybooks_referenced": data.get("copybooks_referenced"),
        "source_hash": data.get("source_hash") or data.get("source_sha") or data.get("sha256"),
    }


def build_para_record(program: str, para: dict, enrichment: dict | None) -> dict:
    """Full paragraph IR for Redis — structured, not chunked text."""
    name = para.get("name") or para.get("paragraph") or "UNKNOWN"
    record = {
        "program": program,
        "paragraph": name,
        "name": name,
        "terminator": para.get("terminator"),
        "falls_through_to": para.get("falls_through_to"),
        "last_verb": para.get("last_verb"),
        "last_raw": para.get("last_raw"),
        "cfg_branch_context": para.get("cfg_branch_context"),
        "is_cics_branch": para.get("is_cics_branch"),
        "performs": para.get("performs") or [],
        "goto_targets": para.get("goto_targets") or [],
        "reachable": para.get("reachable"),
        # Structured IR markers for consumers / smoke tests
        "verbs": [para["last_verb"]] if para.get("last_verb") else [],
    }
    # Preserve any extra keys from canonical without dropping them
    for k, v in para.items():
        if k not in record:
            record[k] = v

    if enrichment:
        # Merge statement-level fields when available (COACTUPC etc.)
        for field in (
            "statements",
            "reads",
            "mutates",
            "source_lines",
            "source_artifact",
            "next_paragraph",
        ):
            if field in enrichment and enrichment[field] is not None:
                record[field] = enrichment[field]
        # Expand verbs from statements if present
        stmts = enrichment.get("statements") or []
        if stmts:
            verbs = []
            for s in stmts:
                v = s.get("verb")
                if v:
                    verbs.append(v)
            if verbs:
                record["verbs"] = verbs
                record["statement_count"] = len(stmts)
    return record


def build_cfg_record(program: str, para: dict) -> dict:
    name = para.get("name") or para.get("paragraph") or "UNKNOWN"
    return {
        "program": program,
        "paragraph": name,
        "predecessors": None,  # not always in canonical; consumers use edges
        "successors": None,
        "falls_through_to": para.get("falls_through_to"),
        "performs": para.get("performs") or [],
        "goto_targets": para.get("goto_targets") or [],
        "terminator": para.get("terminator"),
        "reachable": para.get("reachable"),
        "cfg_branch_context": para.get("cfg_branch_context"),
        "is_cics_branch": para.get("is_cics_branch"),
    }


def load_program(r: redis.Redis, path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    program = program_name_from_file(path, data)
    paras = data.get("paragraphs") or data.get("sections") or []
    if not isinstance(paras, list):
        paras = []

    enrich_map = load_statement_enrichment(program)
    para_names: list[str] = []
    pipe = r.pipeline(transaction=False)

    for para in paras:
        if not isinstance(para, dict):
            continue
        name = para.get("name") or para.get("paragraph")
        if not name:
            continue
        para_names.append(name)
        enr = enrich_map.get(name)
        record = build_para_record(program, para, enr)
        cfg = build_cfg_record(program, para)
        pipe.set(f"{program}:para:{name}", json.dumps(record, ensure_ascii=False))
        pipe.set(f"{program}:cfg:{name}", json.dumps(cfg, ensure_ascii=False))

    meta = build_meta(program, data, para_names)
    # Attach program-level CFG summary when present
    if data.get("cfg_edges_resolved") is not None or data.get("cfg_paragraphs"):
        meta["cfg_paragraphs_count"] = len(data.get("cfg_paragraphs") or [])
        pipe.set(
            f"{program}:cfg:summary",
            json.dumps(
                {
                    "program": program,
                    "cfg_paragraphs": data.get("cfg_paragraphs"),
                    "cfg_edges_resolved": data.get("cfg_edges_resolved"),
                    "cics_commands": data.get("cics_commands"),
                    "cics_branches": data.get("cics_branches"),
                },
                ensure_ascii=False,
            ),
        )

    pipe.set(f"{program}:meta", json.dumps(meta, ensure_ascii=False))
    pipe.set(f"{program}:index", json.dumps(para_names, ensure_ascii=False))
    pipe.execute()

    return {
        "program": program,
        "paragraphs": len(para_names),
        "enriched_statements": sum(
            1 for n in para_names if (enrich_map.get(n) or {}).get("statements")
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Load canonical IR into Redis dictionary")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--password", default=DEFAULT_PASSWORD)
    ap.add_argument("--canonical-dir", type=Path, default=CANONICAL_DIR)
    ap.add_argument("--flush", action="store_true", help="FLUSHDB before load")
    args = ap.parse_args()

    if not args.canonical_dir.is_dir():
        print(f"ERROR: canonical dir not found: {args.canonical_dir}", file=sys.stderr)
        return 2

    files = sorted(
        p
        for p in args.canonical_dir.glob("*.canonical.json")
        if not p.name.startswith("_")
    )
    if not files:
        print(f"ERROR: no *.canonical.json in {args.canonical_dir}", file=sys.stderr)
        return 2

    r = redis.Redis(
        host=args.host,
        port=args.port,
        password=args.password,
        decode_responses=True,
        socket_connect_timeout=10,
    )
    try:
        r.ping()
    except redis.RedisError as e:
        print(f"ERROR: cannot connect to Redis {args.host}:{args.port}: {e}", file=sys.stderr)
        return 2

    if args.flush:
        r.flushdb()
        print("FLUSHDB complete")

    results = []
    total_paras = 0
    for path in files:
        info = load_program(r, path)
        results.append(info)
        total_paras += info["paragraphs"]
        enr = info["enriched_statements"]
        extra = f" (statement-enriched: {enr})" if enr else ""
        print(f"Program: {info['program']} — {info['paragraphs']} paragraphs loaded{extra}")

    loaded_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "loaded_at": loaded_at,
        "program_count": len(results),
        "paragraph_count": total_paras,
        "schema_version": "1.4",
        "store": "canonical-ir-dictionary",
        "redis_key_schema": {
            "meta": "{PROG}:meta",
            "para": "{PROG}:para:{NAME}",
            "cfg": "{PROG}:cfg:{NAME}",
            "cfg_summary": "{PROG}:cfg:summary",
            "index": "{PROG}:index",
            "manifest": "cobol:manifest",
        },
        "programs": [
            {"program": x["program"], "paragraphs": x["paragraphs"]} for x in results
        ],
    }
    r.set("cobol:manifest", json.dumps(manifest, ensure_ascii=False))

    print()
    print(f"TOTAL: {total_paras} paragraphs across {len(results)} programs")
    print(f"Manifest written: cobol:manifest")
    print(f"DBSIZE: {r.dbsize()}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
