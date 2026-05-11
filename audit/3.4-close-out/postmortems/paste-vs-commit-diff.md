# Paste.txt vs Commit Diff Report

---
generated_at: "2026-05-11T13:18:00Z"
working_tree_sha256: "D977A52BFD1E32964EC5691D3C81B35DBC058198752D769CABE3CF88DC683352"
commit_sha256: "D977A52BFD1E32964EC5691D3C81B35DBC058198752D769CABE3CF88DC683352"
files_identical: true
working_tree_branch_head: "035ca7c"
---

## Section 1 — Hash Comparison

Working tree SHA256: `D977A52BFD1E32964EC5691D3C81B35DBC058198752D769CABE3CF88DC683352`

Commit 1e5c1ff SHA256: `D977A52BFD1E32964EC5691D3C81B35DBC058198752D769CABE3CF88DC683352`

**Result:** Files are identical. The working tree audit file is byte-identical to the committed version at 1e5c1ff.

---

## Section 2 — Working-tree Gate_status Frequencies

| Count | Name |
|-------|------|
| 31 | gate_status: certified |
| 48 | gate_status: pending |

**Dominant gate_status value among programs:** `certified` (31 programs + 1 utility = 32 certified artifacts)

---

## Section 3 — Diff Summary

Files identical; no diff to render.

---

## Section 4 — Implications for Post-mortem Corrections

(a) The actual gate_status value distribution in the canonical audit file is: 31 artifacts with `certified` status (30 programs + 1 utility) and 48 artifacts with `pending` status (all copybooks).

(b) The Failure Mode 1 wording "universal defensive_scope" in local-run-2026-05-11.md contradicts the measured frequencies. The post-mortem incorrectly stated that "all artifacts received `gate_status: pending`" when in fact 31 artifacts (39% of the total) received `gate_status: certified`. The 48 artifacts with `pending` status are all copybooks that require resolution at section 3.6, which is the correct behavior for copybooks that cannot be automatically classified.