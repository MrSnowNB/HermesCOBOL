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

### [2026-05-13] Gate anchor — main (post PR #8 merge)

- **Branch:** main
- **Test gate:** 113/113 PASS
- **Schema version:** 1.3
- **COACTUPC unresolved:** 0
- **Byte layouts:** 31/31 programs in data/byte_layouts/
- **carddemo_imported:** scripts present, NOT promoted — run in-place only

### [2026-05-13] Step B1 — DONE (confirmed on audit/3.4-local-second-opinion)

- Branch was audit/3.4-local-second-opinion at time of B1 execution (acceptable)
- validate_byte_layout.py: EXISTS, 12894 bytes, syntax OK
- extract_file_control.py: EXISTS, 18128 bytes, syntax OK
- git status: clean at time of B1

### [2026-05-13] Remaining unresolved counts — post three-patch cleanup

BMS/online class:

| Program | Unresolved |
|---|---|
| COCRDLIC | 384 |
| COTRN00C | 355 |
| COUSR00C | 350 |
| COTRN02C | 328 |
| COACTVWC | 195 |
| CORPT00C | 195 |
| COBIL00C | 123 |
| COSGN00C | 47 |

Batch class:

| Program | Unresolved |
|---|---|
| CBSTM03A | 106 |
| CBTRN02C | 31 |
| CBTRN03C | 26 |
| CBIMPORT | 22 |
| CBTRN01C | 21 |

### [2026-05-13] Stage 2 invariants

- Read-only diagnostic only — no pipeline changes, no promotions
- Files that may be written: `.clinerules/scratchpad.md` and `tmp_validate_byte_layout_out.txt` only
- Working tree must be clean after every step except B5

---

## EXECUTION PLAN — Stage 2: Diagnostic Run

---

### STEP B1 [DONE]

**Goal:** Verify diagnostic scripts exist and pass syntax check.

**RESULT:**
- Branch: audit/3.4-local-second-opinion (acceptable — main not yet checked out)
- git status: clean
- validate_byte_layout.py: 12894 bytes, syntax OK
- extract_file_control.py: 18128 bytes, syntax OK

---

### STEP B2 [IN_PROGRESS]

**Goal:**
Run `validate_byte_layout.py` in-place across all programs and capture output.
Separate "copybook not expanded" from "genuine missing field."

**Assumption:**
Script is in `scripts/carddemo_imported/validate_byte_layout.py`.
Byte layouts are in `data/byte_layouts/`.
Source files are under `data/raw/`.
Copybooks are in `data/raw/cpy`, `data/raw/cpy-bms`, `data/raw/cpy-stubs`.

**Exact commands:**

```powershell
# B2a — inspect help first
python scripts/carddemo_imported/validate_byte_layout.py --help 2>&1

# B2b — run with correct flags (adjust from --help output)
python scripts/carddemo_imported/validate_byte_layout.py `
    --layout-dir data/byte_layouts `
    --source-dir data/raw `
    --copybook-dirs data/raw/cpy,data/raw/cpy-bms,data/raw/cpy-stubs `
    2>&1 | Tee-Object -FilePath C:\work\HermesCOBOL\tmp_validate_byte_layout_out.txt

# B2c — extract summary lines
Get-Content C:\work\HermesCOBOL\tmp_validate_byte_layout_out.txt |
    Select-String "PASS|WARN|ERROR|FAIL|unresolved|missing|copybook" |
    Select-Object -First 60
```

**Pass condition:**
Script runs to completion. Output file is non-empty. Per-program status lines visible.

**On failure:**
Paste error under RESULT. Mark BLOCKED. Save scratchpad. STOP.

**RESULT:**
<!-- Qwen appends actual output here -->

---

### STEP B3 [PENDING]

**Goal:**
Run `extract_file_control.py` on the five batch programs only.
Inventory FD record names and REDEFINES chains.

**Target programs:** CBSTM03A, CBTRN01C, CBTRN02C, CBTRN03C, CBIMPORT

**Exact commands:**

```powershell
# B3a — inspect help
python scripts/carddemo_imported/extract_file_control.py --help 2>&1

# B3b — locate source files
Get-ChildItem -Recurse data\raw -Include "CBSTM03A*","CBTRN01C*","CBTRN02C*","CBTRN03C*","CBIMPORT*" |
    Select-Object FullName, Length

# B3c — run on each batch program (adjust path from B3b output)
$progs = @(
    "data/raw/app/CBSTM03A.cbl",
    "data/raw/app/CBTRN01C.cbl",
    "data/raw/app/CBTRN02C.cbl",
    "data/raw/app/CBTRN03C.cbl",
    "data/raw/app/CBIMPORT.cbl"
)
foreach ($p in $progs) {
    if (Test-Path $p) {
        Write-Host "=== $p ==="
        python scripts/carddemo_imported/extract_file_control.py $p 2>&1
    } else { Write-Host "NOT FOUND: $p" }
} | Tee-Object -FilePath C:\work\HermesCOBOL\tmp_extract_file_control_out.txt

# B3d — show FD and REDEFINES entries
Get-Content C:\work\HermesCOBOL\tmp_extract_file_control_out.txt |
    Select-String "FD|REDEFINES|SELECT|ASSIGN" -CaseSensitive:$false |
    Select-Object -First 40
```

**Pass condition:**
Script runs on at least 3 of 5 programs. FD/REDEFINES output captured in tmp file.

**On failure:**
If source paths are wrong, locate with `Get-ChildItem -Recurse data\raw -Filter "CBSTM03A.cbl"`.
Paste error under RESULT. Mark BLOCKED. STOP.

**RESULT:**
<!-- Qwen appends actual output here -->

---

### STEP B4 [PENDING]

**Goal:**
Synthesize findings from B2 and B3. Append `DIAGNOSTIC FINDINGS — Stage 2` section
to this scratchpad with actual classifications.

**Exact commands:**

```powershell
# Confirm output files exist
Get-Item C:\work\HermesCOBOL\tmp_validate_byte_layout_out.txt | Select-Object Name, Length
Get-Item C:\work\HermesCOBOL\tmp_extract_file_control_out.txt | Select-Object Name, Length

# WARN/ERROR summary from validate_byte_layout
Get-Content C:\work\HermesCOBOL\tmp_validate_byte_layout_out.txt |
    Select-String "WARN|ERROR|FAIL|missing|unresolved" |
    Select-Object -First 40

# FD summary from extract_file_control
Get-Content C:\work\HermesCOBOL\tmp_extract_file_control_out.txt |
    Select-String "FD |REDEFINES" | Select-Object -First 30
```

Then append the following section to this scratchpad with actual findings filled in:
DIAGNOSTIC FINDINGS — Stage 2
validate_byte_layout.py — per-program classification
[Qwen fills in: program name → copybook gap / genuine missing field / clean]

extract_file_control.py — FD/REDEFINES inventory
[Qwen fills in: FD record names and REDEFINES chains per batch program]

Recommended next stage
[Qwen states which fix addresses the most unresolveds based on evidence]

text

**Pass condition:**
Both tmp files non-empty. Findings section appended with real data (no placeholders).
Only `.clinerules/scratchpad.md` is modified.

**On failure:**
If either tmp file is empty, return to B2 or B3. Mark BLOCKED.

**RESULT:**
<!-- Qwen appends actual output here -->

---

### STEP B5 [PENDING]

**Goal:**
Commit scratchpad with findings. Verify clean tree. No other files committed.

**Exact commands:**

```powershell
git status --short
# Must show ONLY: M .clinerules/scratchpad.md
# If any other file is modified — STOP, do not commit, mark BLOCKED

git add .clinerules/scratchpad.md
git diff --cached --name-only
git commit -m "docs(scratchpad): Stage 2 diagnostic findings — validate_byte_layout + extract_file_control"
git push origin main
git log --oneline -1
git status --short
```

**Pass condition:**
Only scratchpad committed. Push succeeds to `origin/main`. Tree clean after push.

**On failure:**
If unexpected files are staged, run `git reset HEAD` and identify them. Mark BLOCKED.

**RESULT:**
<!-- Qwen appends actual output here -->

---

## CURRENT STATE

**Stage:** 2 — Diagnostic Run
**Status:** STEP B2 IN_PROGRESS
**Branch:** main
**Last action:** Scratchpad restored and reseeded by cloud planning agent after pull overwrite.
**Next action:** Execute STEP B2 only. Stop after appending RESULT. Do not begin B3.
**Blocker:** None.