# HermesCOBOL Validation Runbook

Deterministic, LLM-free round-trip verification of the COBOL evidence pipeline.

---

## Purpose

`scripts/validate_roundtrip.py` proves that:
1. Every raw `.cbl` file can be successfully preprocessed by GnuCOBOL (`cobc -E`).
2. Every structural element extracted by `extract_facts.py` is actually present
   in the raw source — no hallucination, no missing coverage.

This script is **read-only** against `data/raw/` and `data/facts/`.
It **never modifies** source files or facts JSON.
It writes only to `validation/` which is gitignored.

---

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.10+ | `python --version` |
| GnuCOBOL | 3.2+ | `cobc --version` |

No additional pip packages required — stdlib only (`hashlib`, `re`, `json`, `subprocess`).

`data/raw/cbl/` must contain your `.cbl` files before running.
`data/facts/` is optional — Mode B will report `facts_missing` if not present
but Mode A (preprocess) will still run.

---

## How to Run

From the repo root:

```bash
# All programs in data/raw/cbl/:
python scripts/validate_roundtrip.py

# Single program:
python scripts/validate_roundtrip.py CBACT01C
```

Exit code:
- `0` — all programs PASS
- `1` — one or more programs FAIL
- `2` — fatal input error (missing directory or file)

---

## Output locations

```
validation/                          <- gitignored root
  reconstructed/
    cbl/
      CBACT01C.pre.cbl               <- cobc -E output per program
      CBACT02C.pre.cbl
      ...
  reports/
    CBACT01C.validation.json         <- per-program report
    CBACT02C.validation.json
    ...
    summary.json                     <- aggregate report
```

---

## Per-program report: `<PROG>.validation.json`

```json
{
  "program": "CBACT01C",
  "generated_at": "2026-05-07T...",
  "gnucobol_version": "cobc (GnuCOBOL) 3.2.0",
  "raw_sha256": "abc123...",
  "pre_sha256": "def456...",
  "preprocess_ok": true,
  "preprocess_error": null,
  "raw_structure_counts": {
    "paragraphs": 40,
    "data_items": 12,
    "calls": 2,
    "perform_targets": 35,
    "selects": 3
  },
  "cics_present": false,
  "sql_present": false,
  "facts_present": true,
  "facts_error": null,
  "missing_paragraphs": [],
  "missing_data_items": [],
  "missing_calls": [],
  "missing_selects": [],
  "cics_mismatch": false,
  "sql_mismatch": false,
  "gate_fail_reasons": [],
  "gate_status": "PASS"
}
```

### Field guide

| Field | Meaning |
|---|---|
| `raw_sha256` | SHA-256 of raw `.cbl` (LF-normalized) |
| `pre_sha256` | SHA-256 of `cobc -E` output (LF-normalized) |
| `preprocess_ok` | `true` if `cobc -E` exited 0 |
| `preprocess_error` | Error string if `preprocess_ok` is `false`, else `null` |
| `raw_structure_counts` | Counts of elements found in raw source |
| `facts_present` | `true` if `data/facts/<PROG>.json` exists and loaded |
| `missing_paragraphs` | Paragraph names in raw source but absent from facts |
| `missing_data_items` | 01-level names in raw source but absent from facts |
| `missing_calls` | CALL targets in raw source but absent from facts |
| `missing_selects` | SELECT files in raw source but absent from facts |
| `cics_mismatch` | Raw CICS presence disagrees with facts |
| `sql_mismatch` | Raw SQL presence disagrees with facts |
| `gate_fail_reasons` | List of failure reasons — empty if PASS |
| `gate_status` | `PASS` or `FAIL` |

---

## Summary report: `summary.json`

```json
{
  "generated_at": "...",
  "gnucobol_version": "cobc (GnuCOBOL) 3.2.0",
  "programs_total": 32,
  "programs_pass": 30,
  "programs_fail": 2,
  "first_failures": ["CBACT01C", "COUSR02C"],
  "counts": {
    "preprocess_failures": 0,
    "missing_paragraphs": 4,
    "missing_data_items": 0,
    "missing_calls": 0,
    "missing_selects": 0,
    "cics_mismatches": 2,
    "sql_mismatches": 0
  }
}
```

---

## How to interpret `gate_status`

**PASS** — program satisfies all of:
- `cobc -E` succeeded
- `data/facts/<PROG>.json` exists
- No paragraphs, data items, calls, or selects are missing from facts
- CICS/SQL presence flags agree

**FAIL** — one or more checks failed. See `gate_fail_reasons` for the list.

### Common failure patterns and fixes

| Reason | Likely cause | Fix |
|---|---|---|
| `facts_missing` | Stage 3 not yet run | Run `python scripts/extract_facts.py` |
| `preprocess_failed` | `cobc` not on PATH or syntax error | Check `cobc --version`; fix PATH |
| `missing_paragraphs` | Regex mismatch in extractor | Check `PARA_RE` against actual indentation |
| `missing_data_items` | Facts capped at `MAX_01_ITEMS` | Raise `MAX_01_ITEMS` in `scripts/config.py` |
| `missing_calls` | CALL uses variable name, not literal | Expected — dynamic CALLs are not captured |
| `cics_mismatch` | Facts missing `cics_verbs` field or wrong flag | Re-run `extract_facts.py`; check REKT data |

---

## Safety guarantees

- **`data/raw/` is never modified.** The script opens raw files read-only.
- **`data/facts/` is never modified.** Facts are loaded read-only for comparison.
- **All writes go to `validation/`**, which is gitignored.
- **No network calls.** No LLM calls. Stdlib only.
- **Idempotent.** Re-running overwrites previous reports with fresh results.
