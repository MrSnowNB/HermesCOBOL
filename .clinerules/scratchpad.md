# HermesCOBOL — Agent Scratchpad

---

## AGENT PROTOCOL (INVARIANT)

1. Cloud agent writes scratchpad fresh per stage — never inherit prior stage context
2. Every kickoff includes FIRST-PRINCIPLES LOOP block before any step
3. Context reset between every step — one Cline session per step
4. **RESULT:** = actual output only, never expected output
5. STOP on 2 consecutive failures — mark BLOCKED, push, await human

---

## FIRST-PRINCIPLES PROBLEM-SOLVING LOOP

- Verify what is actually true on disk before assuming anything
- State your assumption explicitly before acting on it
- Every step must prove its own result before the next step begins
- Surfaced failure is always preferred over silent pass
- If expected output does not match actual output — STOP and reclassify
- **RESULT:** = actual command output only, never expected output
- Never mark a step DONE without pasting real command output

---

## FROZEN GROUND TRUTH

> APPEND ONLY. Never delete. Never edit existing entries.
> This section survives compaction. It is institutional memory.

### [2026-05-13] Gate anchor — main (post PR #8 merge)

- **Branch:** main
- **Test gate:** 113/113 PASS
- **Schema version:** 1.3
- **COACTUPC unresolved:** 0
- **Byte layouts:** 31/31 programs in `data/byte_layouts/`
- **carddemo_imported:** scripts present, NOT promoted — do not touch

### [2026-05-13] Stage 2 diagnostic findings — COMPLETE

**validate_byte_layout.py:** All 31 programs passed T-PASS1-BYTES with 0 failures. Byte layouts are structurally sound.

**extract_file_control.py:** 27 file_control entries across 5 batch programs. No REDEFINES found in any batch program.

**Program classification:**

| Program | Unresolved | Class |
|---|---|---|
| COCRDLIC | 384 | COPYBOOK_GAP |
| COTRN00C | 355 | COPYBOOK_GAP |
| COUSR00C | 350 | COPYBOOK_GAP |
| COTRN02C | 328 | COPYBOOK_GAP |
| COACTVWC | 195 | COPYBOOK_GAP |
| CORPT00C | 195 | COPYBOOK_GAP |
| COBIL00C | 123 | COPYBOOK_GAP |
| COSGN00C | 47 | COPYBOOK_GAP |
| CBSTM03A | 106 | CBSTM03A_CLASS |
| CBTRN02C | 31 | FD_GAP |
| CBTRN03C | 26 | FD_GAP |
| CBIMPORT | 22 | FD_GAP |
| CBTRN01C | 21 | FD_GAP |

**Root cause decisions:**
- COPYBOOK_GAP: fix = `pass1_annotate.py` `cobc -E` preprocessing (Stage 4+)
- FD_GAP: fix = FD record names fed to byte_layout resolver (Stage 4+)
- CBSTM03A_CLASS: inspect deep REDEFINES chains before prescribing fix

**Artifacts:** `audit/stage2/` — 7 files archived, working tree clean.

### [2026-05-13] Stage 3 invariants

- **Goal:** Add 12 architectural test vectors to `tests/test_data_flow.py` only
- **Do NOT modify:** `scripts/data_flow.py`
- **Do NOT promote:** any script from `scripts/carddemo_imported/`
- **Failures are expected and correct** — record them, do not fix them
- **Files committed this stage:** `tests/test_data_flow.py`, `.clinerules/scratchpad.md` only
- **Architectural non-goals (never implement):**
  - T03 scoring
  - Schema version bumping
  - Control-flow tracking inside data_flow.py
  - Heuristic first-match QMAP resolution
  - Probabilistic failure handling

---

## EXECUTION PLAN — Stage 3: 12-Vector Test Backfill

---

### STEP C1 [DONE]

**Goal:**
Read `tests/test_data_flow.py` to understand its current structure, import patterns, fixture names, and how existing tests invoke the data_flow module. Do not modify anything.

**Assumption:**
`tests/test_data_flow.py` exists and currently passes 113 tests. The import pattern and fixture setup must be understood before adding new tests.

**Exact commands:**

```powershell
git branch --show-current
git status --short

# Show file size and line count
Get-Item tests\test_data_flow.py | Select-Object Name, Length
(Get-Content tests\test_data_flow.py).Count

# Show first 60 lines (imports, fixtures, first test)
Get-Content tests\test_data_flow.py | Select-Object -First 60

# Show all test function names
Select-String -Path tests\test_data_flow.py -Pattern "^def test_" | Select-Object LineNumber, Line

# Show how data_flow module is imported
Select-String -Path tests\test_data_flow.py -Pattern "^import|^from" | Select-Object -First 20

# Show how byte_layout data is injected or mocked (if at all)
Select-String -Path tests\test_data_flow.py -Pattern "mock|patch|layout|byte_layout|inject" -CaseSensitive:$false | Select-Object -First 20

# Confirm current test gate
python -m pytest tests/test_data_flow.py -q 2>&1 | Select-Object -Last 5
```

**Pass condition:**
- `git branch --show-current` prints `main`
- `git status --short` is clean
- Import pattern and fixture structure are visible
- Test gate confirms 113 passing before any changes

**On failure:**
- If branch is not `main`: run `git checkout main && git pull origin main` then rerun
- If test gate is not 113: STOP, mark BLOCKED, do not proceed
- Paste actual output under RESULT, mark DONE only when gate confirmed

**RESULT:**
- Branch: main
- Tree clean: yes (git status --short returned empty)
- test_data_flow.py line count: 935
- Test functions found: 61 tests (test_digit_sequence_area_a_paragraph, test_blank_sequence_area_a_paragraph, test_area_b_line_has_leading_spaces, test_comment_line_skipped, test_short_line_skipped, test_cbact01c_paragraph_count_is_16, test_move_single_target, test_move_multiple_targets, test_move_corresponding, test_add_to, test_add_giving, test_compute_expression, test_initialize, test_read_into, test_write_from, test_if_condition_reads, test_unresolved_name, test_qualified_name_disambiguation, test_display_literal, test_display_mixed_literal_and_var, test_display_literal_containing_verb_keyword, test_end_perform_not_paragraph, test_move_continuation_not_a_paragraph, test_real_paragraphs_all_detected, test_non_prefixed_paragraphs_detected, test_indented_ws_reissue_date_fused, test_working_storage_section_not_paragraph, test_linkage_section_not_paragraph, test_file_section_not_paragraph, test_procedure_section_not_paragraph, test_procedure_division_not_paragraph, test_data_division_not_paragraph, test_identification_division_not_paragraph, test_procedure_division_using_not_paragraph, test_level_01_not_paragraph, test_level_77_not_paragraph, test_level_05_not_paragraph, test_call_by_reference_default, test_call_explicit_by_reference, test_call_target_recorded, test_call_by_content_read_only, test_call_by_value_read_only, test_call_returning_mutate_only, test_call_using_then_returning, test_call_returning_no_using_call_target_recorded, test_call_mixed_reference_and_content, test_call_graph_contains_cobdatft, test_inspect_tallying, test_inspect_replacing, test_sort_using_giving, test_merge_using_giving, test_release_from, test_release_no_from, test_return_into, test_return_no_from, test_paragraph_before_any_section_has_null_section_name, test_paragraph_under_section_has_section_name, test_paragraphs_under_two_different_sections_have_distinct_section_names, test_duplicate_paragraph_name_across_sections_is_disambiguated_by_section, test_back_to_back_section_headers_with_no_paragraphs_in_between, test_schema_version_field_is_1_3_when_section_name_present)
- Import pattern: from data_flow import (classify_statement, extract_paragraphs, _normalise_source, is_literal, _join_source_lines, _is_para_header_line, _is_area_a_paragraph, _dispatch_inline)
- Key API functions visible: classify_statement, extract_paragraphs
- Mock/layout injection pattern: Uses _QMAP fixtures (dictionary of field/record mappings) to inject test data; no mock/patch patterns used
- Gate confirmation: Ran 61 tests in 0.029s — OK

---

### STEP C2 [PENDING]

**Goal:**
Add V01 through V04 to `tests/test_data_flow.py`. Run pytest on these four vectors only. Record pass/fail per vector. Do NOT fix failures.

**Vectors to add:**

```python
# V01 — Direct Assignment
def test_v01_direct_assignment():
    """MOVE VAR-A TO VAR-B: reads=[VAR-A], mutates=[VAR-B]"""
    from scripts.data_flow import classify_statement
    result = classify_statement("MOVE VAR-A TO VAR-B", layout={})
    assert "VAR-A" in result["reads"], f"VAR-A not in reads: {result}"
    assert "VAR-B" in result["mutates"], f"VAR-B not in mutates: {result}"
    assert "VAR-B" not in result["reads"], f"VAR-B should not be in reads: {result}"

# V02 — Literal Rejection
def test_v02_literal_rejection():
    """MOVE literal TO VAR-B: reads=[], mutates=[VAR-B]"""
    from scripts.data_flow import classify_statement
    result = classify_statement("MOVE 'HARDCODED-LITERAL' TO VAR-B", layout={})
    assert result["reads"] == [], f"reads should be empty for literal: {result}"
    assert "VAR-B" in result["mutates"], f"VAR-B not in mutates: {result}"

# V03 — COMPUTE Decomposition
def test_v03_compute_decomposition():
    """COMPUTE VAR-X = (VAR-A * VAR-B) - VAR-C: reads contains all operands"""
    from scripts.data_flow import classify_statement
    result = classify_statement(
        "COMPUTE VAR-X = (VAR-A * VAR-B) - VAR-C", layout={}
    )
    for var in ["VAR-A", "VAR-B", "VAR-C"]:
        assert var in result["reads"], f"{var} not in reads: {result}"
    assert "VAR-X" in result["mutates"], f"VAR-X not in mutates: {result}"
    assert "VAR-X" not in result["reads"], f"VAR-X should not be in reads: {result}"

# V04 — Implicit Mutation (ADD compound)
def test_v04_implicit_mutation_add():
    """ADD 1 TO COUNTER-VAR: COUNTER-VAR in both reads and mutates"""
    from scripts.data_flow import classify_statement
    result = classify_statement("ADD 1 TO COUNTER-VAR", layout={})
    assert "COUNTER-VAR" in result["reads"], f"COUNTER-VAR not in reads: {result}"
    assert "COUNTER-VAR" in result["mutates"], f"COUNTER-VAR not in mutates: {result}"
```

**Important:** Before writing, inspect the actual `classify_statement` (or equivalent) API from C1 output. Adjust the function name and call signature to match what actually exists in `scripts/data_flow.py`. If the API differs, adapt the test to match the real interface — do not invent an API that doesn't exist.

**Exact commands:**

```powershell
# Add V01-V04 to end of tests/test_data_flow.py (after last existing test)
# Then run only the new vectors:
python -m pytest tests/test_data_flow.py -k "v01 or v02 or v03 or v04" -v 2>&1

# Also confirm existing tests still pass
python -m pytest tests/test_data_flow.py -q 2>&1 | Select-Object -Last 5
```

**Pass condition:**
- At least one of V01–V04 runs (even if it fails)
- Existing 113 tests still pass (count must not drop)
- Each vector result (PASS or FAIL) is recorded

**On failure:**
- If `classify_statement` does not exist, identify the correct function name from C1 output and adapt
- If a vector cannot be wired to any real API, mark that vector BLOCKED with reason
- Do not modify `scripts/data_flow.py` under any circumstance
- Record all failures — they are the Stage 4 punchlist

**RESULT:**
<!-- Qwen appends actual command output here before marking DONE -->

---

### STEP C3 [PENDING]

**Goal:**
Add V05 and V06 (STRING/UNSTRING bidirectional) to `tests/test_data_flow.py`. Run pytest on V05 and V06 only. Record pass/fail.

**Vectors to add:**

```python
# V05 — STRING Pointer Bidirectional
def test_v05_string_pointer_bidirectional():
    """STRING: PTR-VAR in both reads and mutates, DEST-VAR in mutates, SRC-A in reads"""
    from scripts.data_flow import classify_statement
    stmt = (
        "STRING SRC-A DELIMITED BY SIZE "
        "INTO DEST-VAR WITH POINTER PTR-VAR"
    )
    result = classify_statement(stmt, layout={})
    assert "SRC-A" in result["reads"], f"SRC-A not in reads: {result}"
    assert "DEST-VAR" in result["mutates"], f"DEST-VAR not in mutates: {result}"
    assert "PTR-VAR" in result["reads"], f"PTR-VAR not in reads: {result}"
    assert "PTR-VAR" in result["mutates"], f"PTR-VAR not in mutates: {result}"

# V06 — UNSTRING Global Tally
def test_v06_unstring_global_tally():
    """UNSTRING: reads include SRC/DELIM/PTR/TALLY, mutates include destinations/counts/tally/ptr"""
    from scripts.data_flow import classify_statement
    stmt = (
        "UNSTRING SRC-VAR DELIMITED BY DELIM-VAR "
        "INTO DEST-A COUNT IN CNT-A "
        "INTO DEST-B COUNT IN CNT-B "
        "TALLYING IN TALLY-VAR "
        "WITH POINTER PTR-VAR"
    )
    result = classify_statement(stmt, layout={})
    for var in ["SRC-VAR", "DELIM-VAR", "PTR-VAR", "TALLY-VAR"]:
        assert var in result["reads"], f"{var} not in reads: {result}"
    for var in ["DEST-A", "CNT-A", "DEST-B", "CNT-B", "TALLY-VAR", "PTR-VAR"]:
        assert var in result["mutates"], f"{var} not in mutates: {result}"
```

**Exact commands:**

```powershell
python -m pytest tests/test_data_flow.py -k "v05 or v06" -v 2>&1
python -m pytest tests/test_data_flow.py -q 2>&1 | Select-Object -Last 5
```

**Pass condition:**
- Both vectors run (PASS or FAIL — either is acceptable)
- Existing test count does not drop below 113
- Results recorded under RESULT

**On failure:**
- If STRING/UNSTRING is handled by a different dispatcher, adapt call signature
- If vector cannot be wired, mark BLOCKED with reason
- Do not modify `scripts/data_flow.py`

**RESULT:**
<!-- Qwen appends actual command output here before marking DONE -->

---

### STEP C4 [PENDING]

**Goal:**
Add V07 and V08 (EXEC CICS masking + MOVE CORRESPONDING dual-tree) to `tests/test_data_flow.py`. Run pytest on V07 and V08 only. Record pass/fail.

**Vectors to add:**

```python
# V07 — EXEC CICS Masking
def test_v07_exec_cics_masking():
    """EXEC CICS: INTO and RESP targets appear in mutates; DATASET/READ/literal excluded"""
    from scripts.data_flow import classify_statement
    stmt = (
        "EXEC CICS READ DATASET('FILE') "
        "INTO(LOCAL-VAR) RESP(CODE-VAR) "
        "END-EXEC"
    )
    result = classify_statement(stmt, layout={})
    assert "LOCAL-VAR" in result["mutates"], f"LOCAL-VAR not in mutates: {result}"
    assert "CODE-VAR" in result["mutates"], f"CODE-VAR not in mutates: {result}"
    for noise in ["FILE", "DATASET", "READ"]:
        assert noise not in result["reads"], f"{noise} should not be in reads: {result}"
        assert noise not in result["mutates"], f"{noise} should not be in mutates: {result}"

# V08 — MOVE CORRESPONDING Dual-Tree
def test_v08_move_corresponding_dual_tree():
    """MOVE CORR: only matching non-FILLER children transferred; non-matching excluded"""
    from scripts.data_flow import classify_statement

    mock_layout = {
        "ROOT-A": {
            "name": "ROOT-A", "level": "01", "offset": 0, "length": 30,
            "children": [
                {"name": "CHILD-X", "level": "05", "offset": 0, "length": 10,
                 "children": [], "redefines": None},
                {"name": "CHILD-Y", "level": "05", "offset": 10, "length": 10,
                 "children": [], "redefines": None},
                {"name": "FILLER", "level": "05", "offset": 20, "length": 10,
                 "children": [], "redefines": None},
            ],
            "redefines": None
        },
        "ROOT-B": {
            "name": "ROOT-B", "level": "01", "offset": 0, "length": 30,
            "children": [
                {"name": "CHILD-X", "level": "05", "offset": 0, "length": 10,
                 "children": [], "redefines": None},
                {"name": "CHILD-Z", "level": "05", "offset": 10, "length": 10,
                 "children": [], "redefines": None},
                {"name": "FILLER", "level": "05", "offset": 20, "length": 10,
                 "children": [], "redefines": None},
            ],
            "redefines": None
        }
    }

    result = classify_statement(
        "MOVE CORRESPONDING ROOT-A TO ROOT-B", layout=mock_layout
    )
    assert "CHILD-X" in result["reads"], f"CHILD-X not in reads: {result}"
    assert "CHILD-X" in result["mutates"], f"CHILD-X not in mutates: {result}"
    assert "CHILD-Y" not in result["mutates"], f"CHILD-Y should not be in mutates: {result}"
    assert "CHILD-Z" not in result["reads"], f"CHILD-Z should not be in reads: {result}"
    assert "FILLER" not in result["reads"], f"FILLER should not be in reads: {result}"
    assert "FILLER" not in result["mutates"], f"FILLER should not be in mutates: {result}"
```

**Exact commands:**

```powershell
python -m pytest tests/test_data_flow.py -k "v07 or v08" -v 2>&1
python -m pytest tests/test_data_flow.py -q 2>&1 | Select-Object -Last 5
```

**Pass condition:**
- Both vectors run (PASS or FAIL)
- Existing test count does not drop below 113
- Results recorded

**On failure:**
- EXEC CICS handling may require a different dispatcher — adapt from C1 findings
- MOVE CORR may require layout injection at a different call site — adapt accordingly
- Do not modify `scripts/data_flow.py`
- Mark BLOCKED with reason if API is entirely absent

**RESULT:**
<!-- Qwen appends actual command output here before marking DONE -->

---

### STEP C5 [PENDING]

**Goal:**
Add V09 and V10 (QMAP nearest-enclosing scope + ambiguous conflict flagging) to `tests/test_data_flow.py`. Run pytest on V09 and V10 only. Record pass/fail.

**Vectors to add:**

```python
# V09 — Nearest-Enclosing Scope
def test_v09_nearest_enclosing_scope():
    """Duplicate field name: resolves to nearest enclosing group, not first match"""
    from scripts.data_flow import classify_statement

    mock_layout = {
        "GROUP-A": {
            "name": "GROUP-A", "level": "01", "offset": 0, "length": 20,
            "children": [
                {"name": "FIELD-X", "level": "05", "offset": 0, "length": 10,
                 "children": [], "redefines": None},
            ],
            "redefines": None
        },
        "GROUP-B": {
            "name": "GROUP-B", "level": "01", "offset": 20, "length": 20,
            "children": [
                {"name": "FIELD-X", "level": "05", "offset": 20, "length": 10,
                 "children": [], "redefines": None},
            ],
            "redefines": None
        }
    }

    result = classify_statement(
        "MOVE FIELD-X TO DEST",
        layout=mock_layout,
        context_group="GROUP-A"
    )
    resolved = result.get("resolved_reads", result.get("reads", []))
    assert any("GROUP-A" in str(r) for r in resolved), (
        f"Expected GROUP-A.FIELD-X resolution, got: {result}"
    )
    assert not any("GROUP-B" in str(r) for r in resolved), (
        f"GROUP-B.FIELD-X should not resolve when GROUP-A is context: {result}"
    )

# V10 — Ambiguous Conflict Flagging
def test_v10_ambiguous_conflict_flagging():
    """Duplicate field name with no context: goes to unresolved with reason=ambiguous, no heuristic"""
    from scripts.data_flow import classify_statement

    mock_layout = {
        "GROUP-A": {
            "name": "GROUP-A", "level": "01", "offset": 0, "length": 20,
            "children": [
                {"name": "FIELD-DUP", "level": "05", "offset": 0, "length": 10,
                 "children": [], "redefines": None},
            ],
            "redefines": None
        },
        "GROUP-B": {
            "name": "GROUP-B", "level": "01", "offset": 20, "length": 20,
            "children": [
                {"name": "FIELD-DUP", "level": "05", "offset": 20, "length": 10,
                 "children": [], "redefines": None},
            ],
            "redefines": None
        }
    }

    result = classify_statement(
        "MOVE FIELD-DUP TO DEST",
        layout=mock_layout
    )
    resolved_reads = result.get("reads", [])
    unresolved = result.get("unresolved_reads", result.get("unresolved", []))

    assert "FIELD-DUP" not in resolved_reads, (
        f"FIELD-DUP should not be in resolved reads (ambiguous): {result}"
    )
    unresolved_names = [
        u if isinstance(u, str) else u.get("name", str(u))
        for u in unresolved
    ]
    assert "FIELD-DUP" in unresolved_names, (
        f"FIELD-DUP should appear in unresolved: {result}"
    )
    if isinstance(unresolved, dict):
        reasons = [u.get("reason", "") for u in unresolved if
                   u.get("name") == "FIELD-DUP"]
        assert any("ambiguous" in r.lower() for r in reasons), (
            f"Expected reason=ambiguous for FIELD-DUP: {unresolved}"
        )
```

**Exact commands:**

```powershell
python -m pytest tests/test_data_flow.py -k "v09 or v10" -v 2>&1
python -m pytest tests/test_data_flow.py -q 2>&1 | Select-Object -Last 5
```

**Pass condition:**
- Both vectors run (PASS or FAIL)
- Existing test count does not drop below 113
- Results recorded

**On failure:**
- `context_group` parameter may not exist yet — if so, V09 will FAIL; record as Stage 4 punchlist item
- Ambiguous flagging with `reason` field may not exist yet — V10 may FAIL; record as Stage 4 punchlist item
- These are expected failures — do not implement the missing API
- Mark BLOCKED only if the test itself cannot be written/parsed

**RESULT:**
<!-- Qwen appends actual command output here before marking DONE -->

---

### STEP C6 [PENDING]

**Goal:**
Add V11 and V12 (column-aware paragraph lexing + SECTION boundary encapsulation) to `tests/test_data_flow.py`. Run pytest on V11 and V12 only. Record pass/fail.

**Vectors to add:**

```python
# V11 — Column-Aware Paragraph Lexing
def test_v11_column_aware_paragraph_lexing():
    """Fixed-form COBOL: only valid Area A paragraph names extracted"""
    from scripts.data_flow import extract_paragraphs

    synthetic_cobol = (
        "000010 IDENTIFICATION DIVISION.                                         \n"
        "000020 PROGRAM-ID. TESTPROG.                                            \n"
        "000030 PROCEDURE DIVISION.                                              \n"
        "000040 MAIN-PARA.                                                       \n"
        "000050*    THIS IS A COMMENT LINE — should produce no paragraph         \n"
        "000060     MOVE A TO B.                                                 \n"
        "000070-    CONTINUED-LINE.                                              \n"
        "000080 SECOND-PARA.                                                     \n"
        "000090     MOVE C TO D.                                                 \n"
    )

    paragraphs = extract_paragraphs(synthetic_cobol)
    para_names = [p["name"] for p in paragraphs]

    assert "MAIN-PARA" in para_names, f"MAIN-PARA not found: {para_names}"
    assert "SECOND-PARA" in para_names, f"SECOND-PARA not found: {para_names}"
    assert "000010" not in para_names, f"Sequence number misclassified: {para_names}"
    assert "000050" not in para_names, f"Comment line misclassified: {para_names}"
    assert "CONTINUED-LINE" not in para_names, (
        f"Continuation line should not be a paragraph: {para_names}"
    )

# V12 — SECTION Boundary Encapsulation
def test_v12_section_boundary_encapsulation():
    """Paragraphs inherit section_name from enclosing SECTION"""
    from scripts.data_flow import extract_paragraphs

    synthetic_cobol = (
        "000010 PROCEDURE DIVISION.                                              \n"
        "000020 MAIN-SECTION SECTION.                                           \n"
        "000030 PARA-A.                                                         \n"
        "000040     MOVE VAR-X TO VAR-Y.                                        \n"
        "000050 PARA-B.                                                         \n"
        "000060     MOVE VAR-Z TO VAR-W.                                        \n"
    )

    paragraphs = extract_paragraphs(synthetic_cobol)
    para_map = {p["name"]: p for p in paragraphs}

    assert "PARA-A" in para_map, f"PARA-A not found: {list(para_map.keys())}"
    assert "PARA-B" in para_map, f"PARA-B not found: {list(para_map.keys())}"
    assert para_map["PARA-A"].get("section_name") == "MAIN-SECTION", (
        f"PARA-A section_name wrong: {para_map['PARA-A']}"
    )
    assert para_map["PARA-B"].get("section_name") == "MAIN-SECTION", (
        f"PARA-B section_name wrong: {para_map['PARA-B']}"
    )
```

**Important:** Before writing V11/V12, confirm the exact name of the paragraph extraction function from C1 output. Adjust `extract_paragraphs` import to match what actually exists in `scripts/data_flow.py`.

**Exact commands:**

```powershell
python -m pytest tests/test_data_flow.py -k "v11 or v12" -v 2>&1
python -m pytest tests/test_data_flow.py -q 2>&1 | Select-Object -Last 5
```

**Pass condition:**
- Both vectors run (PASS or FAIL)
- Existing test count does not drop below 113
- Results recorded

**On failure:**
- `section_name` field may not exist yet in paragraph records — V12 will FAIL; this is expected
- Do not add `section_name` to `scripts/data_flow.py`
- Mark BLOCKED only if the test cannot be parsed

**RESULT:**
<!-- Qwen appends actual command output here before marking DONE -->

---

### STEP C7 [PENDING]

**Goal:**
Run the full test suite. Record total pass/fail count. List every failing vector by name. This list becomes the Stage 4 punchlist.

**Exact commands:**

```powershell
# Full verbose run
python -m pytest tests/ -v 2>&1 | Tee-Object -FilePath C:\work\HermesCOBOL\tmp_stage3_results.txt

# Summary line
Get-Content C:\work\HermesCOBOL\tmp_stage3_results.txt | Select-Object -Last 10

# Failing tests only
Get-Content C:\work\HermesCOBOL\tmp_stage3_results.txt |
    Select-String "FAILED|ERROR" |
    Select-Object -First 30
```

**Then append the following section to this scratchpad:**
