#!/usr/bin/env python3
"""
ir_query.py — Exact-key lookup against the COBOL IR Redis dictionary.

Inference boundary: plain Redis GET only. No embeddings, no KNN, no FT.SEARCH.

Layers:
  L0 (default): {PROG}:para:{NAME}
  L1:           {PROG}:english:{NAME}   --english
                {PROG}:rules:{NAME}     --rules

Usage:
  py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS
  py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --english
  py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS --rules --raw
  py translations/ir_query.py --list COACTUPC
"""

from __future__ import annotations

import argparse
import json
import re
import sys

import redis

REDIS_HOST = "localhost"
REDIS_PORT = 6380
REDIS_PASSWORD = "cobol123"

L1_MISSING_MSG = "L1 key not found — run phase2_english_worker.py"


def connect() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=10,
    )


def layer_kind(english: bool, rules: bool) -> str:
    if english and rules:
        raise ValueError("use only one of --english or --rules")
    if english:
        return "english"
    if rules:
        return "rules"
    return "para"


def to_layer_key(key: str | None, layer: str) -> str | None:
    """Rewrite a resolved para/meta/cfg key to the requested layer when applicable."""
    if not key:
        return key
    if layer == "para":
        return key
    # Only rewrite paragraph IR keys to L1
    m = re.match(r"^([A-Z0-9_]+):para:(.+)$", key, re.I)
    if m:
        return f"{m.group(1).upper()}:{layer}:{m.group(2)}"
    # Already an L1 key
    m2 = re.match(r"^([A-Z0-9_]+):(english|rules):(.+)$", key, re.I)
    if m2:
        return f"{m2.group(1).upper()}:{layer}:{m2.group(3)}"
    # meta/index/cfg/manifest: leave as-is for L0-only semantics
    return key


def normalize_key(query: str, program: str | None = None) -> str | None:
    """Turn user input into a Redis L0-style key when possible."""
    q = query.strip()
    if not q:
        return None
    if q == "cobol:manifest":
        return q
    m = re.match(
        r"^([A-Za-z0-9_]+):(para|meta|cfg|index|english|rules)(?::(.+))?$",
        q,
        re.I,
    )
    if m:
        prog = m.group(1).upper()
        kind = m.group(2).lower()
        rest = m.group(3)
        if kind in ("para", "english", "rules") and rest:
            return f"{prog}:{kind}:{rest}"
        if kind == "cfg" and rest:
            return f"{prog}:cfg:{rest}"
        if kind in ("meta", "index"):
            return f"{prog}:{kind}"
        if kind == "cfg" and not rest:
            return f"{prog}:cfg:summary"
    if ":para:" in q.lower():
        parts = re.split(r":para:", q, maxsplit=1, flags=re.I)
        if len(parts) == 2:
            return f"{parts[0].upper()}:para:{parts[1]}"
    for mid in (":english:", ":rules:"):
        if mid in q.lower():
            parts = re.split(re.escape(mid), q, maxsplit=1, flags=re.I)
            if len(parts) == 2:
                kind = "english" if "english" in mid else "rules"
                return f"{parts[0].upper()}:{kind}:{parts[1]}"

    tokens = q.replace("/", " ").split()
    if program and len(tokens) >= 1:
        for t in tokens:
            if re.match(r"^\d{4}-", t) or re.match(r"^[A-Z0-9]+-\w+", t, re.I):
                return f"{program.upper()}:para:{t}"
        return f"{program.upper()}:para:{tokens[-1]}"
    if len(tokens) >= 2:
        prog = tokens[0].upper()
        rest = tokens[1:]
        if rest and re.match(r"^\d{4}$", rest[0]):
            para = "-".join(rest)
        elif rest and re.match(r"^\d{4}-", rest[0]):
            para = rest[0] if len(rest) == 1 else "-".join(rest)
        else:
            para = "-".join(rest)
        return f"{prog}:para:{para}"
    return None


def get_json(r: redis.Redis, key: str) -> dict | None:
    raw = r.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"_raw": raw}


def list_program_index(r: redis.Redis, program: str) -> list[str]:
    raw = r.get(f"{program.upper()}:index")
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            pass
    names = []
    prefix = f"{program.upper()}:para:"
    for k in r.scan_iter(match=f"{prefix}*", count=200):
        names.append(k[len(prefix) :])
    return sorted(names)


def resolve_query(r: redis.Redis, user_query: str, layer: str = "para") -> dict:
    """
    Exact GET first; if missing L0, SCAN candidates.
    For L1 (english/rules): never fall back to :para: content.
    """
    result = {
        "query": user_query,
        "method": None,
        "key": None,
        "layer": layer,
        "store": "redis-canonical-dict",
        "host": f"{REDIS_HOST}:{REDIS_PORT}",
        "hit": None,
        "candidates": [],
        "error": None,
        "l1_missing": False,
    }

    # Direct key (may already be L1)
    key = normalize_key(user_query)
    if key:
        # If user passed :para: but wants L1, rewrite
        if layer != "para" and ":para:" in key:
            key = to_layer_key(key, layer)
        elif layer != "para" and re.search(r":(english|rules):", key, re.I):
            key = to_layer_key(key, layer)
        hit = get_json(r, key)
        if hit:
            result["method"] = "GET"
            result["key"] = key
            result["hit"] = hit
            return result
        # Direct L1 miss
        if layer != "para" and re.search(rf":{layer}:", key or "", re.I):
            result["method"] = "GET"
            result["key"] = key
            result["l1_missing"] = True
            result["error"] = L1_MISSING_MSG
            return result

    tokens = user_query.replace("/", " ").split()
    prog = None
    for t in tokens:
        if re.match(r"^C[OB][A-Z0-9]{4,7}$", t.upper()) or t.upper() in (
            "COACTUPC",
            "COACTVWC",
            "COBIL00C",
        ):
            prog = t.upper()
            break
    if not prog and tokens:
        prog = "COACTUPC"

    para_token = None
    for t in tokens:
        if re.match(r"^\d{4}-", t):
            para_token = t
            break
        if re.match(r"^\d{4}$", t):
            idx = tokens.index(t)
            rest = [t] + tokens[idx + 1 :]
            para_token = "-".join(rest[:6])
            break
        # non-numeric paragraph names (COMMON-RETURN, etc.)
        if re.match(r"^[A-Z][A-Z0-9-]+$", t, re.I) and t.upper() != prog:
            if "-" in t or len(t) > 4:
                para_token = t

    if prog and para_token:
        # Resolve paragraph name via L0 index if needed
        names = list_program_index(r, prog)
        matches = [
            n
            for n in names
            if para_token.upper() in n.upper() or n.upper() in para_token.upper()
        ]
        resolved_name = para_token
        if para_token not in names and len(matches) == 1:
            resolved_name = matches[0]

        l0_key = f"{prog}:para:{resolved_name}"
        key = to_layer_key(l0_key, layer)
        hit = get_json(r, key)
        if hit:
            result["method"] = "GET"
            result["key"] = key
            result["hit"] = hit
            if matches:
                result["candidates"] = matches
            return result

        if layer != "para":
            # L1 miss: do NOT return :para: content
            result["method"] = "GET"
            result["key"] = key
            result["l1_missing"] = True
            result["error"] = L1_MISSING_MSG
            if matches:
                result["candidates"] = matches
            return result

        # L0 miss → SCAN candidates
        result["method"] = "SCAN"
        result["key"] = f"{prog}:para:*"
        result["candidates"] = matches or names[:50]
        result["error"] = "exact key not found; returning candidates"
        return result

    if prog:
        names = list_program_index(r, prog)
        result["method"] = "SCAN"
        result["key"] = f"{prog}:{layer}:*" if layer != "para" else f"{prog}:para:*"
        result["candidates"] = names
        result["error"] = "no paragraph resolved; listing index"
        return result

    result["error"] = "could not parse program/paragraph from query"
    result["method"] = "NONE"
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="Exact Redis GET for COBOL IR dictionary")
    ap.add_argument("query", nargs="*", help="PROGRAM PARAGRAPH or full key")
    ap.add_argument("--list", dest="list_prog", metavar="PROG", help="List paragraph index")
    ap.add_argument("--scan", dest="scan_prog", metavar="PROG", help="SCAN all para keys")
    ap.add_argument("--raw", action="store_true", help="Print only JSON hit")
    ap.add_argument(
        "--english",
        action="store_true",
        help="GET L1 {PROG}:english:{NAME} (no :para: fallback)",
    )
    ap.add_argument(
        "--rules",
        action="store_true",
        help="GET L1 {PROG}:rules:{NAME} (no :para: fallback)",
    )
    args = ap.parse_args()

    if args.english and args.rules:
        print("ERROR: use only one of --english or --rules", file=sys.stderr)
        return 2

    try:
        layer = layer_kind(args.english, args.rules)
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2

    try:
        r = connect()
        r.ping()
    except redis.RedisError as e:
        print(f"Redis connection error: {e}", file=sys.stderr)
        return 2

    if args.list_prog or args.scan_prog:
        prog = (args.list_prog or args.scan_prog).upper()
        names = list_program_index(r, prog)
        print(json.dumps({"program": prog, "count": len(names), "paragraphs": names}, indent=2))
        return 0

    user_query = " ".join(args.query) if args.query else "COACTUPC 1200-EDIT-MAP-INPUTS"
    out = resolve_query(r, user_query, layer=layer)

    # L1 missing — explicit message, exit 1, never dump :para:
    if out.get("l1_missing"):
        if args.raw:
            print(L1_MISSING_MSG)
        else:
            print(f"Query: {user_query}")
            print(f"Layer: {layer}")
            print(f"Key: {out.get('key')}")
            print(L1_MISSING_MSG)
        return 1

    if args.raw and out.get("hit"):
        print(json.dumps(out["hit"], indent=2, ensure_ascii=False))
        return 0

    print(f"Query: {user_query}")
    print(f"Layer: {layer}")
    print(f"Method: {out['method']}  (no embeddings / no KNN / no FT.SEARCH)")
    print(f"Key: {out.get('key')}")
    print(f"Store: {out['store']} @ {out['host']}")
    if out.get("error"):
        print(f"Note: {out['error']}")
    if out.get("candidates") and not out.get("hit"):
        print(f"Candidates ({len(out['candidates'])}):")
        for c in out["candidates"][:40]:
            print(f"  - {c}")
        return 1
    if out.get("hit"):
        hit = out["hit"]
        if layer == "english":
            print(f"Hit paragraph: {hit.get('paragraph')}")
            print(f"word_count: {hit.get('word_count')}")
            print(f"source_key: {hit.get('source_key')}")
            doc = hit.get("document") or ""
            print("--- document (truncated) ---")
            print(doc[:3000] + ("\n... [truncated] ..." if len(doc) > 3000 else ""))
        elif layer == "rules":
            print(f"Hit paragraph: {hit.get('paragraph')}")
            print(f"rules: {len(hit.get('rules') or [])}")
            print(f"source_key: {hit.get('source_key')}")
            print("--- JSON (truncated) ---")
            text = json.dumps(hit, indent=2, ensure_ascii=False)
            print(text[:4000] + ("\n... [truncated] ..." if len(text) > 4000 else ""))
        else:
            print(f"Hit paragraph: {hit.get('paragraph') or hit.get('name')}")
            print(f"last_verb: {hit.get('last_verb')}")
            print(f"statements: {len(hit.get('statements') or [])}")
            print(f"verbs: {len(hit.get('verbs') or [])}")
            print("--- JSON (truncated) ---")
            text = json.dumps(hit, indent=2, ensure_ascii=False)
            print(text[:4000] + ("\n... [truncated] ..." if len(text) > 4000 else ""))
        return 0
    print("No hit.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
