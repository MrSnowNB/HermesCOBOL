# HermesCOBOL Validation Runbook

Deterministic, LLM-free round-trip verification of the COBOL extraction pipeline.

---

## Purpose

`scripts/validate_roundtrip.py` runs two independent validation modes:

**Mode A — Preprocess hash roundtrip (non-CICS programs only)**
- Runs `cobc -E -I cpy -I cpy-bms` on each non-CICS `.cbl` file.
- SHA-256 hashes both the raw source and the preprocessed output (LF-normalized).
- Pins the GnuCOBOL version used.
- **Requires GnuCOBOL.** If `cobc` is not on PATH, Mode A exits with
  `cobc not found on PATH` and Mode B still runs normally.
- **CICS programs (17 of 31) are permanently skipped** with reason
  `cics_no_translator`. GnuCOBOL cannot preprocess raw `EXEC CICS` blocks
  without the IBM CICS translator. This is by design, not a failure.

**Mode B — Structural coverage check (all 31 programs)**
- Pure Python — no GnuCOBOL dependency.
- Independently scans each `.cbl` for: paragraphs, 01-level data items,
  CALL/PERFORM targets, SELECT/ASSIGN file definitions, EXEC CICS/SQL presence.
- Compares against `data/facts/<PROG>.json` (canonical schema v1.0).
- Runs for **all 31 programs**, including CICS programs.

**Gate 10 — Walker baseline regression (all 31 programs)**
- On every `validate_roundtrip.py` run, `audit_cobol_walker.py` is invoked
  automatically.
- First run: creates `validation/walker-baseline.json`.
- Subsequent runs: verifies current walk output matches the saved baseline.
  Any deviation causes an immediate `FAIL`.
- Baseline sums: **live=205, full=518** across 31 programs.

This script is **read-only** against `data/raw/` and `data/facts/`.
It **never modifies** source files or facts JSON.
It writes only to `validation/` which is gitignored.

---

## Prerequisites

| Tool | Version | Required? | Check |
|---|---|---|---|
| Python | 3.10+ | **Required** | `python --version` |
| GnuCOBOL | 3.2+ | **Optional** (Mode A only) | `cobc --version` |

No additional pip packages required — stdlib only (`hashlib`, `re`, `json`, `subprocess`).

`data/raw/cbl/` must contain your `.cbl` files before running.
`data/facts/` is optional — Mode B will report `facts_missing` if absent,
but Mode A will still run (for non-CICS programs, if GnuCOBOL is available).
`data/canonical/` must be present for Gate 10 (walker baseline) to run.

---

## How to Run

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
validation/
  reconstructed/
    cbl/
      CBACT01C.pre.cbl               <- cobc -E output (Mode A, non-CICS only)
      ...
  reports/
    CBACT01C.validation.json         <- per-program report
    ...
    summary.json                     <- aggregate report
  walker-baseline.json               <- Gate 10 baseline (created on first run)
```

---

## Per-program report: `<PROG>.validation.json`

### Non-CICS program (Mode A + Mode B both ran)
```json
{
  "program": "CBACT01C",
  "generated_at": "2026-05-07T...",
  "gnucobol_version": "cobc (GnuCOBOL) 3.2.0",
  "raw_sha256": "abc123...",
  "pre_sha256": "def456...",
  "preprocess_ok": true,
  "preprocess_skipped": false,
  "preprocess_skipped_reason": null,
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
  "gate_note": null,
  "gate_status": "PASS"
}
```

### CICS program (Mode A skipped, Mode B ran)
```json
{
  "program": "COACTUPC",
  "preprocess_ok": false,
  "preprocess_skipped": true,
  "preprocess_skipped_reason": "cics_no_translator",
  "cics_present": true,
  "gate_fail_reasons": [],
  "gate_note": "cics_structural_only",
  "gate_status": "PASS"
}
```

### Field guide

| Field | Meaning |
|---|---|
| `raw_sha256` | SHA-256 of raw `.cbl` (LF-normalized) |
| `pre_sha256` | SHA-256 of `cobc -E` output (LF-normalized, null if skipped) |
| `preprocess_ok` | `true` if `cobc -E` exited 0 |
| `preprocess_skipped` | `true` for CICS programs (Mode A intentionally not run) |
| `preprocess_skipped_reason` | `"cics_no_translator"` for CICS programs, else null |
| `preprocess_error` | Error string if Mode A failed (not skipped), else null |
| `raw_structure_counts` | Counts of elements found in raw source by Mode B |
| `facts_present` | `true` if `data/facts/<PROG>.json` exists and loaded |
| `missing_paragraphs` | Paragraph names in raw source but absent from facts |
| `missing_data_items` | 01-level names in raw source but absent from facts |
| `missing_calls` | CALL targets in raw source but absent from facts |
| `missing_selects` | SELECT files in raw source but absent from facts |
| `cics_mismatch` | Raw CICS presence disagrees with facts |
| `sql_mismatch` | Raw SQL presence disagrees with facts |
| `gate_fail_reasons` | List of failure reasons — empty if PASS |
| `gate_note` | `"cics_structural_only"` for CICS PASS programs, else null |
| `gate_status` | `PASS` or `FAIL` |

---

## Summary report: `summary.json`

```json
{
  "generated_at": "...",
  "gnucobol_version": "cobc (GnuCOBOL) 3.2.0",
  "programs_total": 31,
  "programs_pass": 31,
  "programs_fail": 0,
  "programs_skipped_preprocess": 17,
  "skipped_reasons": {"cics_no_translator": 17},
  "first_failures": [],
  "counts": {
    "preprocess_failures": 0,
    "preprocess_skipped": 17,
    "missing_paragraphs": 0,
    "missing_data_items": 0,
    "missing_calls": 0,
    "missing_selects": 0,
    "cics_mismatches": 0,
    "sql_mismatches": 0
  }
}
```

---

## How to interpret `gate_status`

**PASS** — program satisfies all of:
- Mode A: `cobc -E` succeeded OR program is CICS (intentionally skipped)
- Mode B: `data/facts/<PROG>.json` exists
- Mode B: No paragraphs, data items, calls, or selects are missing from facts
- Mode B: CICS/SQL presence flags agree

**FAIL** — one or more checks failed. See `gate_fail_reasons` for the list.

### Common failure patterns and fixes

| Reason | Likely cause | Fix |
|---|---|---|
| `facts_missing` | Stage 1 not yet run | Run `python scripts/extract_facts.py` |
| `preprocess_failed` | `cobc` not on PATH or syntax error in non-CICS program | Check `cobc --version`; fix PATH |
| `missing_paragraphs` | Regex mismatch in extractor | Check `PARA_RE` against actual indentation |
| `missing_data_items` | Facts capped at `MAX_01_ITEMS` | Raise `MAX_01_ITEMS` in `scripts/config.py` |
| `missing_calls` | CALL uses variable name, not literal | Expected — dynamic CALLs are not captured |
| `cics_mismatch` | Facts missing `cics_present` field or wrong flag | Re-run `extract_facts.py` |
| walker baseline diverged | Paragraph edges changed since last baseline | Run `python scripts/audit_cobol_walker.py` to refresh |

---

## Safety guarantees

- **`data/raw/` is never modified.** The script opens raw files read-only.
- **`data/facts/` is never modified.** Facts are loaded read-only for comparison.
- **All writes go to `validation/`**, which is gitignored.
- **No network calls. No LLM calls.** Stdlib only.
- **Idempotent.** Re-running overwrites previous reports with fresh results.
