# AI First Scratchpad

> **Purpose:** Context management for AI First protocol agents working on this repo.# HermesCOBOL — Agent Scratchpad

> **MANDATORY PROTOCOL**
> READ this file before any action.
> WRITE this file after every action.
> If CURRENT STATE does not match what you see on disk — correct it before proceeding.

---

## PROBLEM FRAME
> Rewrite this section completely at the start of every new task.
> If you cannot fill every field with a concrete artifact — you are not ready to act.

**Status:** ACTIVE — fixing test fixture returncode assertion

**Irreducible unit:** Fix the `regenerate_facts` fixture in `tests/test_extract_facts_alignment.py`
**Root cause being addressed:** Fixture asserts `returncode == 0`, but `extract_facts.py` returns 1 when any program has a WARN gate (COBSWAIT has no paragraphs — expected). This makes the setup fixture fail, cascading to 31 errors across all parametrized tests.
**Inputs required:** None — root cause was identified from pytest output alone.
**Invariants — must not change:**
- data_flow.py frozen contracts: _normalise_source, _join_source_lines,
  extract_paragraphs, _is_area_a_paragraph, _mask_literals, _dispatch_inline, _parse_call
- audit\3_4_warning_baseline.json — DO NOT OVERWRITE until Section 3.4 gate closes
- SCHEMA_VERSION 1.2 — does not bump until Section 3.4 gate closes

**Proof of correct:** `python -m pytest tests/ -v` returns `113 passed in 0.84s`, zero errors.
**Proof of wrong:** Before fix — `31 errors` in setup, all caused by `assert result.returncode == 0` failing because COBSWAIT's WARN gate caused extract_facts.py to exit with code 1.
**Explicitly out of scope:** Section 3.4 gate closure (data_flow.py changes, schema version bump, Batch 2 promotion). This fix is a prerequisite for the gate.
**First-principles assumption that could be false:** That returncode 1 from extract_facts.py always means "completed with warnings" rather than "actual failure." Verified: returncode 2 is used for actual failures (missing dirs). Returncode 1 is used for WARN gates.

---

## CURRENT STATE
> Overwrite this section after every single action.

**Status:** IN PROGRESS — test fixture fixed, awaiting commit
**Branch:** audit/3.4-local-second-opinion
**Last confirmed good state:** 113 passed, 0 errors on `tests/`
**Last action taken:** Fixed `regenerate_facts` fixture to accept returncode in (0, 1)
**Last action result:** PASS — full test suite green
**Next action:** Commit fix and push to remote
**Blocker:** (none)
**Revised assumption:** (none)

---

## FROZEN GROUND TRUTH
> APPEND ONLY. Never delete. Never edit existing entries.
> This section survives compaction. It is institutional memory.

### [2026-05-12] Frozen contracts — data_flow.py
**Gate:** Sections 2, 3.1, 3.2, 3.3 (all closed)
**Functions locked:** _normalise_source, _join_source_lines, extract_paragraphs,
_is_area_a_paragraph, _mask_literals, _dispatch_inline, _parse_call
**Rule:** Any change to these functions is a gate regression. Do not touch.

### [2026-05-12] Known para delta — three programs
**Programs:** COACTUPC (85 vs 87), COACTVWC (34 vs 36), COCRDLIC (39 vs 41)
**Delta:** -2 each
**Root cause:** Implicit fallthrough paragraphs not counted — confirmed
**Decision:** Deferred to Section 3.4. NOT a bug to fix before then.
**Rule:** para_diff.py will always show these 3 warnings until 3.4 closes. This is expected.

### [2026-05-12] Gate anchor locked
**File:** audit\3_4_warning_baseline.json
**Rule:** DO NOT overwrite until Section 3.4 gate closes. This is the spec anchor.

### [2026-05-12] Schema version
**Current:** SCHEMA_VERSION = "1.2"
**Rule:** Bumps to "1.3" only when Section 3.4 gate closes. Do not bump early.

### [2026-05-12] Folder structure
**Native scripts:** C:\work\HermesCOBOL\scripts\ (flat)
**CarDemo imported:** C:\work\HermesCOBOL\scripts\carddemo_imported\
**Inventory:** scripts\SCRIPTS_INVENTORY.md (rev 4, living document)
**Batch 1:** 8 scripts promoted (independent, no carddemo deps) ✅
**Batch 2:** 5 scripts pending (pass1_annotate, extract_fallthrough,
validate_fallthrough, validate_pass1, assemble_v1_2) ⏳

### [2026-05-12] extract_byte_layout.py conflict
**Issue:** Both scripts\byte_layout.py (native) and scripts\extract_byte_layout.py
(CarDemo port) exist. Functionality overlaps.
**Decision:** Resolve which wins before using either in pipeline. Not yet decided.