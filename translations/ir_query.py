#!/usr/bin/env python3
"""
ir_query.py — Exact-key lookup against the COBOL IR Redis dictionary.

Inference boundary: plain Redis GET only. No embeddings, no KNN, no FT.SEARCH.

Usage:
  py translations/ir_query.py COACTUPC 1200-EDIT-MAP-INPUTS
  py translations/ir_query.py COACTUPC:para:1200-EDIT-MAP-INPUTS
  py translations/ir_query.py --list COACTUPC
  py translations/ir_query.py --scan COACTUPC
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


def connect() -> redis.Redis:
    return redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        password=REDIS_PASSWORD,
        decode_responses=True,
        socket_connect_timeout=10,
    )


def normalize_key(query: str, program: str | None = None) -> str | None:
    """Turn user input into a Redis key if possible."""
    q = query.strip()
    if not q:
        return None
    # Already a full key (preserve :para: / :meta / :cfg / :index case)
    if q == "cobol:manifest":
        return q
    m = re.match(r"^([A-Za-z0-9_]+):(para|meta|cfg|index)(?::(.+))?$", q, re.I)
    if m:
        prog = m.group(1).upper()
        kind = m.group(2).lower()
        rest = m.group(3)
        if kind == "para" and rest:
            return f"{prog}:para:{rest}"
        if kind == "cfg" and rest:
            return f"{prog}:cfg:{rest}"
        if kind in ("meta", "index"):
            return f"{prog}:{kind}"
        if kind == "cfg" and not rest:
            return f"{prog}:cfg:summary"
    # PROG:para:NAME loose
    if ":para:" in q.lower():
        parts = re.split(r":para:", q, maxsplit=1, flags=re.I)
        if len(parts) == 2:
            return f"{parts[0].upper()}:para:{parts[1]}"
    # Two-token: PROGRAM PARAGRAPH
    tokens = q.replace("/", " ").split()
    if program and len(tokens) >= 1:
        para = tokens[0] if len(tokens) == 1 else "-".join(
            t for t in tokens if not t.upper().startswith(program.upper())
        )
        # Prefer last token patterns like 1200-EDIT-MAP-INPUTS
        for t in tokens:
            if re.match(r"^\d{4}-", t) or re.match(r"^[A-Z0-9]+-\w+", t, re.I):
                return f"{program.upper()}:para:{t.upper() if t[0].isdigit() else t}"
        return f"{program.upper()}:para:{tokens[-1]}"
    if len(tokens) >= 2:
        prog = tokens[0].upper()
        # Join remaining as paragraph name (keep original casing for hyphens)
        rest = tokens[1:]
        # Common form: 1200 EDIT MAP INPUTS → 1200-EDIT-MAP-INPUTS
        if rest and re.match(r"^\d{4}$", rest[0]):
            para = "-".join(rest)
        elif rest and re.match(r"^\d{4}-", rest[0]):
            para = rest[0] if len(rest) == 1 else "-".join(rest)
        else:
            para = "-".join(rest)
        return f"{prog}:para:{para}"
    return None


def get_para(r: redis.Redis, key: str) -> dict | None:
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
    # Fallback SCAN
    names = []
    prefix = f"{program.upper()}:para:"
    for k in r.scan_iter(match=f"{prefix}*", count=200):
        names.append(k[len(prefix) :])
    return sorted(names)


def scan_paras(r: redis.Redis, program: str) -> list[str]:
    return list_program_index(r, program)


def resolve_query(r: redis.Redis, user_query: str) -> dict:
    """
    Exact GET first; if missing, SCAN program index and return candidates.
    Never calls embeddings or FT.SEARCH.
    """
    result = {
        "query": user_query,
        "method": None,
        "key": None,
        "store": "redis-canonical-dict",
        "host": f"{REDIS_HOST}:{REDIS_PORT}",
        "hit": None,
        "candidates": [],
        "error": None,
    }

    # Direct key
    key = normalize_key(user_query)
    if key:
        hit = get_para(r, key)
        if hit:
            result["method"] = "GET"
            result["key"] = key
            result["hit"] = hit
            return result

    # Try PROGRAM + paragraph patterns from free text
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
        # default CardDemo focus program for short queries
        prog = "COACTUPC"

    # Find paragraph-like token
    para_token = None
    for t in tokens:
        if re.match(r"^\d{4}-", t):
            para_token = t
            break
        if re.match(r"^\d{4}$", t):
            # join following words
            idx = tokens.index(t)
            rest = [t] + tokens[idx + 1 :]
            para_token = "-".join(rest[:6])
            break

    if prog and para_token:
        key = f"{prog}:para:{para_token}"
        hit = get_para(r, key)
        if hit:
            result["method"] = "GET"
            result["key"] = key
            result["hit"] = hit
            return result
        # fuzzy: scan index for substring
        names = scan_paras(r, prog)
        matches = [n for n in names if para_token.upper() in n.upper() or n.upper() in para_token.upper()]
        if len(matches) == 1:
            key = f"{prog}:para:{matches[0]}"
            hit = get_para(r, key)
            result["method"] = "GET-after-scan"
            result["key"] = key
            result["hit"] = hit
            result["candidates"] = matches
            return result
        result["method"] = "SCAN"
        result["key"] = f"{prog}:para:*"
        result["candidates"] = matches or names[:50]
        result["error"] = "exact key not found; returning candidates"
        return result

    # Fallback: list program
    if prog:
        names = scan_paras(r, prog)
        result["method"] = "SCAN"
        result["key"] = f"{prog}:para:*"
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
    args = ap.parse_args()

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
    out = resolve_query(r, user_query)

    if args.raw and out.get("hit"):
        print(json.dumps(out["hit"], indent=2, ensure_ascii=False))
        return 0

    print(f"Query: {user_query}")
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
