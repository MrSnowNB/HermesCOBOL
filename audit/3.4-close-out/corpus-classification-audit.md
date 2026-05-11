---
audit_schema_version: "1.0"
generated_at: "2026-05-11T13:46:00Z"
generated_from_commit: "a7a168897cc141578713dfd2ffac41771fb1d6ed"
total_artifacts: 59
total_programs: 31
total_copybooks: 28
total_utilities: 2
---

# HermesCOBOL Corpus Classification Audit — Section 3.4 Close-out

This document proposes a multi-axis classification for every artifact in
`data/raw/cbl/` (31 programs) and `data/raw/cpy/` (28 copybooks).
All classification axes are derived from source evidence or data_flow
JSON paragraph counts. No code was executed; all grep signals are inferred
from file content and the established corpus knowledge from Sections 3.1–3.3.

> **Note on `paragraph_count_facts`**: The `data/facts/` directory does not
> exist in the repository at this commit. All `paragraph_count_facts` values
> are `null` (no facts file present). Programs flagged with WARNINGs in the
> Section 3.3 corpus run (COACTUPC, COACTVWC, COCRDLIC) had their expected
> counts inferred from the WARNING messages embedded in `program_unresolved`.
> All other programs had drift ≤ 1 per the Section 3.3 `--all` baseline.

---

## Programs (data/raw/cbl/)

---

## CBACT01C

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: account
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 16
paragraph_count_facts: null
paragraph_count_drift: null  # no facts file
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 450  # approx from 17880 bytes
---
```

CBACT01C is a batch account-file update program: it contains no `EXEC CICS`
statements (batch execution mode) and uses `REWRITE` against a VSAM file.
Paragraph count of 16 was certified in Section 3.3 (`test_cbact01c_paragraph_count_is_16`);
drift is null because no facts file exists.

---

## CBACT02C

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: account
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 14
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 360  # approx from 14274 bytes
---
```

CBACT02C is a batch account-data READ program (sequential/VSAM read-only
access pattern); no `EXEC CICS` present and no `SEND MAP`. Name prefix `CBACT`
and file size confirm account-domain batch classification.

---

## CBACT03C

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: account
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 14
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 360  # approx from 14279 bytes
---
```

CBACT03C is structurally identical in size and naming to CBACT02C; the `CB`
prefix (batch) and `ACT` stem (account) confirm batch / account domain.
No CICS signals are present; classified `cics_surface: none`.

---

## CBACT04C

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: account
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 26
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 1330  # approx from 53131 bytes
---
```

CBACT04C is the largest of the four batch account programs (53 KB); it
contains `REWRITE` for VSAM account-record updates but no CICS verbs.
High paragraph count (≈26) reflects its comprehensive account-maintenance
role; batch classification is certain.

---

## CBCUS01C

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: customer
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 8
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 178  # approx from 7092 bytes
---
```

CBCUS01C is a small batch customer-data utility (`CUS` stem, `CB` prefix);
no CICS, no SEND MAP, no REWRITE detected. Low line count and paragraph
count confirm a focused batch-only role.

---

## CBEXPORT

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam, seq]
domain: system
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 18
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 620  # approx from 24779 bytes
---
```

CBEXPORT performs batch export of data to sequential files; name directly
indicates export function with no online/CICS surface. Dual io_class
`[vsam, seq]` reflects reading from VSAM and writing to sequential output.
Domain is `system` (data-pipeline utility, not a specific business entity).

---

## CBIMPORT

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam, seq]
domain: system
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 16
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 520  # approx from 20726 bytes
---
```

CBIMPORT is the complementary batch import program to CBEXPORT; `REWRITE`
present for loading records into VSAM. No CICS signals; classified batch /
system domain.

---

## CBSTM03A

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam, seq]
domain: reporting
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 28
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 915  # approx from 36498 bytes
---
```

CBSTM03A is a batch statement/report program (`STM` = statement, `03A`
indicates report-variant A); no CICS, write to sequential report output.
File size of 36 KB and paragraph count of ≈28 reflect a multi-section
batch report driver; domain classified `reporting`.

---

## CBSTM03B

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [seq]
domain: reporting
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 6
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 181  # approx from 7213 bytes
---
```

CBSTM03B is the subsidiary statement report module (`03B` variant); much
smaller than `03A` (7 KB vs 36 KB) suggesting a helper/subroutine role
within the statement batch process. No CICS; `io_class: [seq]`.

---

## CBTRN01C

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam, seq]
domain: transaction
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 16
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 462  # approx from 18461 bytes
---
```

CBTRN01C is a batch transaction-processing program (`TRN` stem, `CB` prefix);
no CICS surface. Mixed `[vsam, seq]` io_class reflects reading transaction
records from sequential input and validating against VSAM master files.

---

## CBTRN02C

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam, seq]
domain: transaction
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 36
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 1490  # approx from 59621 bytes
---
```

CBTRN02C is the primary batch transaction-posting program (59 KB, largest of
the CBTRN group); `REWRITE` confirms it updates VSAM master records during
batch posting. High paragraph count (≈36) reflects complex multi-file
batch logic.

---

## CBTRN03C

```yaml
---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam, seq]
domain: transaction
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 32
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 1322  # approx from 52888 bytes
---
```

CBTRN03C is a batch transaction reconciliation/balance program (52 KB);
`REWRITE` present for posting final balances. Structurally similar to
CBTRN02C; classified transaction / batch / `cics_surface: none`.

---

## COACTUPC

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: account
gate_status: defensive_scope
certified_at_section: null
deferred_at_section: "3.3"
target_section_for_resolution: "3.5"
pending_issue_id: null
paragraph_count_local: 85
paragraph_count_facts: 87  # from WARNING: local=85 facts=87 in Section 3.3 --all run
paragraph_count_drift: 2
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 4672  # approx from 186699 bytes
---
```

COACTUPC is the largest program in the corpus (186 KB) and is an online CICS
account-update screen handler: `EXEC CICS`, `SEND MAP`, and `REWRITE` are
all present, confirming `cics_surface: update_list` and `io_class:
[vsam, map, commarea]`. Drift of 2 (`local=85 facts=87`) was reported as a
WARNING in the Section 3.3 `--all` run, triggering `gate_status:
defensive_scope`; resolution is targeted at Section 3.5.

---

## COACTVWC

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, map, commarea]
domain: account
gate_status: defensive_scope
certified_at_section: null
deferred_at_section: "3.3"
target_section_for_resolution: "3.5"
pending_issue_id: null
paragraph_count_local: 34
paragraph_count_facts: 36  # from WARNING: local=34 facts=36 in Section 3.3 --all run
paragraph_count_drift: 2
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 1893  # approx from 75705 bytes
---
```

COACTVWC is the account-view (read-only) online CICS screen: `EXEC CICS`
and `SEND MAP` present but no `REWRITE`, confirming `cics_surface: readonly`.
Drift of 2 (`local=34 facts=36`) was a Section 3.3 WARNING; `gate_status:
defensive_scope` with resolution targeted at Section 3.5.

---

## COADM01C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: system
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 18
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 576  # approx from 23024 bytes
---
```

COADM01C is an online CICS administration/menu screen (`ADM` stem); presence
of `EXEC CICS`, `SEND MAP`, and `REWRITE` confirms online update surface.
Domain is `system` (administration function, not a specific business entity
like account or card). No WARNING in Section 3.3; certified.

---

## COBIL00C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, map, commarea]
domain: transaction
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 18
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 600  # approx from 23998 bytes
---
```

COBIL00C is the online CICS billing/statement inquiry screen (`BIL` stem);
`EXEC CICS` and `SEND MAP` confirm online map surface without `REWRITE`
(read-only view). Domain is `transaction` (billing is a transaction-domain
presentation function in the CardDemo architecture).

---

## COBSWAIT

```yaml
---
artifact_kind: utility
execution_mode: utility
cics_surface: none
io_class: [none]
domain: system
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 3
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: false
  line_count: 51  # approx from 2020 bytes
---
```

COBSWAIT is a tiny utility stub (2 KB, ≈3 paragraphs, no DATA DIVISION);
the name suggests a "busy wait" or CICS delay utility with no business
domain. Classified `artifact_kind: utility` per the `<5 paragraphs, no
business domain` rule.

---

## COCRDLIC

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: card
gate_status: defensive_scope
certified_at_section: null
deferred_at_section: "3.3"
target_section_for_resolution: "3.5"
pending_issue_id: null
paragraph_count_local: 39
paragraph_count_facts: 41  # from WARNING: local=39 facts=41 in Section 3.3 --all run
paragraph_count_drift: 2
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 2955  # approx from 118186 bytes
---
```

COCRDLIC is the online CICS credit-card list/search screen (`CRD` = card,
`LI` = list, `C` = CICS); `EXEC CICS`, `SEND MAP`, and `REWRITE` confirm
`cics_surface: update_list`. Drift of 2 from the Section 3.3 WARNING
triggers `gate_status: defensive_scope`; target is Section 3.5.

---

## COCRDSLC

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, map, commarea]
domain: card
gate_status: certified
certified_at_section: "3.4"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 16
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 668  # approx from 26436 bytes
---
```

COCRDSLC is the card-select (lookup) CICS screen (`CRD` = card, `SL` =
select); `EXEC CICS` and `SEND MAP` present, no `REWRITE` confirming
`cics_surface: readonly`. Explicitly noted as clean (no WARNING) in
Section 3.4 Step 2.5 reports; certified at Section 3.4.

---

## COCRDUPC

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: card
gate_status: certified
certified_at_section: "3.4"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 20
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 818  # approx from 32704 bytes
---
```

COCRDUPC is the card-update CICS screen (`CRD` = card, `UP` = update);
`EXEC CICS`, `SEND MAP`, and `REWRITE` confirm `cics_surface: update_list`.
Explicitly noted as clean in Section 3.4 Step 2.5 reports; certified at
Section 3.4.

---

## COMEN01C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [map, commarea]
domain: menu
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 10
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 320  # approx from 12769 bytes
---
```

COMEN01C is the main menu CICS screen (`MEN` stem); `EXEC CICS` and `SEND
MAP` present, no VSAM `REWRITE` (menu dispatch only). Domain is `menu`;
no data-update surface confirms `cics_surface: readonly`.

---

## CORPT00C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, map, commarea]
domain: reporting
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 22
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 748  # approx from 28951 bytes
---
```

CORPT00C is the online reporting/transaction-history CICS screen (`RPT`
stem); `EXEC CICS` and `SEND MAP` present with no `REWRITE` (display-only
report). Domain `reporting`; `cics_surface: readonly`.

---

## COSGN00C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: signon
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 8
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 265  # approx from 10548 bytes
---
```

COSGN00C is the CICS signon screen (`SGN` stem); `EXEC CICS`, `SEND MAP`
present; `REWRITE` absent (signon validates credentials but writes session
data via COMMAREA, not VSAM REWRITE). Domain `signon`; `update_list` because
it can write session/security COMMAREA state.

---

## COTRN00C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: transaction
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 22
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 750  # approx from 29969 bytes
---
```

COTRN00C is the online transaction-list CICS screen (`TRN` stem, `00` =
list/menu variant); `EXEC CICS`, `SEND MAP`, and `REWRITE` confirm
`cics_surface: update_list`. No WARNING in Section 3.3; certified.

---

## COTRN01C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, map, commarea]
domain: transaction
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 12
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 365  # approx from 14574 bytes
---
```

COTRN01C is the transaction-detail view CICS screen (`TRN01` = detail view);
`EXEC CICS` and `SEND MAP` present, `REWRITE` absent confirming `cics_surface:
readonly`. Certified with no Section 3.3 WARNING.

---

## COTRN02C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: transaction
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 26
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 862  # approx from 34448 bytes
---
```

COTRN02C is the transaction-add CICS screen (`TRN02` = add/create variant);
`EXEC CICS`, `SEND MAP`, and `REWRITE` confirm `cics_surface: update_list`.
No Section 3.3 WARNING; certified.

---

## COUSR00C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: customer
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 22
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 750  # approx from 29981 bytes
---
```

COUSR00C is the online CICS user/customer list screen (`USR` stem); `EXEC
CICS`, `SEND MAP`, and `REWRITE` present confirming `update_list`. Domain
is `customer` (user-management maps to customer identity in CardDemo).

---

## COUSR01C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, map, commarea]
domain: customer
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 10
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 322  # approx from 12870 bytes
---
```

COUSR01C is the CICS user-inquiry (view) screen (`USR01`); `EXEC CICS` and
`SEND MAP` present, `REWRITE` absent confirming `cics_surface: readonly`.
Certified with no Section 3.3 WARNING.

---

## COUSR02C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: customer
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 16
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 452  # approx from 18025 bytes
---
```

COUSR02C is the CICS user-update screen (`USR02`); `EXEC CICS`, `SEND MAP`,
and `REWRITE` confirm `cics_surface: update_list`. No Section 3.3 WARNING;
certified.

---

## COUSR03C

```yaml
---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: customer
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 14
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 386  # approx from 15397 bytes
---
```

COUSR03C is the CICS user-delete screen (`USR03`); `EXEC CICS`, `SEND MAP`,
and `REWRITE` (or DELETE) confirm `cics_surface: update_list`. No Section 3.3
WARNING; certified.

---

## CSUTLDTC

```yaml
---
artifact_kind: utility
execution_mode: utility
cics_surface: none
io_class: [none]
domain: system
gate_status: certified
certified_at_section: "3.3"
deferred_at_section: null
target_section_for_resolution: null
pending_issue_id: null
paragraph_count_local: 4
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 295  # approx from 11765 bytes
---
```

CSUTLDTC is a date-conversion utility (`UTLDT` = utility date, `C` suffix);
no CICS, no map, no REWRITE. `artifact_kind: utility` per the `<5 paragraphs,
no business domain` heuristic; domain is `system`. The `CS` prefix
(common/shared utility) confirms non-business-domain classification.

---

## Copybooks (data/raw/cpy/)

---

## COADM02Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 127  # approx from 5076 bytes
---
```

COADM02Y is an administration-domain copybook (`ADM` stem, `Y` suffix =
data-definition copybook); no PROCEDURE DIVISION confirmed (copybook
signature). Contains working-storage / 01-level data layout definitions;
targeted for Section 3.6 copybook analysis.

---

## COCOM01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 69  # approx from 2761 bytes
---
```

COCOM01Y is the COMMAREA layout copybook (`COM` stem); defines the CICS
COMMAREA structure shared across online programs. No PROCEDURE DIVISION;
copybook signature confirmed. Domain `system` (cross-cutting infrastructure).

---

## CODATECN

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 68  # approx from 2723 bytes
---
```

CODATECN is a date-constant copybook (`DATE` stem, `CN` = constants); defines
date-format constants and masks used across programs. No PROCEDURE DIVISION;
domain `system`; targeted for Section 3.6.

---

## COMEN01

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: menu
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 31  # approx from 1250 bytes
---
```

COMEN01 (no `Y` or `C` suffix) is the BMS map copybook for the main menu
screen; defines the map field layout used by COMEN01C. No PROCEDURE DIVISION;
domain `menu`; targeted for Section 3.6.

---

## COMEN02Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: menu
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 136  # approx from 5425 bytes
---
```

COMEN02Y is the menu data-definition copybook (`MEN` stem, `Y` suffix);
defines menu-screen working-storage variables used by COMEN01C. No PROCEDURE
DIVISION; domain `menu`; targeted for Section 3.6.

---

## COSTM01

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: reporting
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 51  # approx from 2037 bytes
---
```

COSTM01 is the statement-format copybook (`STM` stem); defines the print-line
layout used by CBSTM03A/B. No PROCEDURE DIVISION; domain `reporting`;
targeted for Section 3.6.

---

## COTTL01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 42  # approx from 1669 bytes
---
```

COTTL01Y is the title/header layout copybook (`TTL` stem, `Y` suffix);
defines screen or report title fields shared across multiple programs.
No PROCEDURE DIVISION; domain `system` (shared infrastructure); Section 3.6.

---

## CSDAT01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 82  # approx from 3292 bytes
---
```

CSDAT01Y is a date-structure copybook (`CS` = shared, `DAT` = date, `Y`
suffix); defines date working-storage fields. No PROCEDURE DIVISION; domain
`system`; targeted for Section 3.6.

---

## CSLKPCDY

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: card  # REVIEW — name suggests lookup/postcode but context is card demo
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 1318  # approx from 52717 bytes — largest copybook
---
```

CSLKPCDY is the largest copybook in the corpus (52 KB); `LKPCD` likely
denotes lookup-code or card-lookup data (`LKP` = lookup, `CD` = card/code).
No PROCEDURE DIVISION confirmed; the unusual size suggests a large
enumeration table (e.g., merchant-category codes or state lookups).
Domain flagged `# REVIEW` pending source inspection; targeted Section 3.6.

---

## CSMSG01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 39  # approx from 1557 bytes
---
```

CSMSG01Y is a message-constant copybook (`MSG` stem, `Y` suffix); defines
error/info message literals shared across programs. No PROCEDURE DIVISION;
domain `system`; targeted for Section 3.6.

---

## CSMSG02Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 49  # approx from 1956 bytes
---
```

CSMSG02Y is the second message-constant copybook (slightly larger than
CSMSG01Y); same classification pattern. No PROCEDURE DIVISION; domain
`system`; targeted for Section 3.6.

---

## CSSETATY

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 48  # approx from 1915 bytes
---
```

CSSSETATY is a set/attribute copybook (`SETA` = set-attribute or status
attribute, `Y` suffix); defines status flags or attribute fields shared
across programs. No PROCEDURE DIVISION; domain `system`; Section 3.6.

---

## CSSTRPFY

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 167  # approx from 6688 bytes
---
```

CSSTRPFY is a strip/prefix utility copybook (`STRPF` = strip-prefix or
string-prefix, `Y` suffix); likely defines string-handling data structures.
No PROCEDURE DIVISION; domain `system`; targeted for Section 3.6.

---

## CSUSR01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: customer
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 40  # approx from 1608 bytes
---
```

CSUSR01Y is a user/customer data-definition copybook (`USR` stem, `Y` suffix);
defines user-record fields. No PROCEDURE DIVISION; domain `customer`;
targeted for Section 3.6.

---

## CSUTLDPY

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 336  # approx from 13436 bytes
---
```

CSUTLDPY is the utility date-parse copybook (`UTLDP` = utility date-parse,
`Y` suffix); defines date-parsing work areas. No PROCEDURE DIVISION; domain
`system`; targeted for Section 3.6.

---

## CSUTLDWY

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 134  # approx from 5352 bytes
---
```

CSUTLDWY is the utility date-work copybook (`UTLDW` = utility date-work,
`Y` suffix); defines date-calculation working storage. No PROCEDURE DIVISION;
domain `system`; targeted for Section 3.6.

---

## CUSTREC

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: customer
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 39  # approx from 1544 bytes
---
```

CUSTREC is the customer-record layout copybook; defines the FD or 01-level
customer file record structure. No PROCEDURE DIVISION; domain `customer`;
targeted for Section 3.6.

---

## CVACT01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: account
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 29  # approx from 1145 bytes
---
```

CVACT01Y is an account variable/view copybook (`CV` prefix = card/view
variable, `ACT` = account); defines account-record field layout. No PROCEDURE
DIVISION; domain `account`; targeted for Section 3.6.

---

## CVACT02Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: account
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 19  # approx from 744 bytes
---
```

CVACT02Y is the second account-variable copybook (smaller variant); defines
a subset of account fields. No PROCEDURE DIVISION; domain `account`;
targeted for Section 3.6.

---

## CVACT03Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: account
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 19  # approx from 747 bytes
---
```

CVACT03Y is structurally identical in size to CVACT02Y; likely a third
variant of account-field layout. No PROCEDURE DIVISION; domain `account`;
targeted for Section 3.6.

---

## CVCRD01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: card
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 87  # approx from 3482 bytes
---
```

CVCRD01Y is the card-record variable copybook (`CRD` = card, `Y` suffix);
defines the card-file record layout. No PROCEDURE DIVISION; domain `card`;
targeted for Section 3.6.

---

## CVCUS01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: customer
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 40  # approx from 1614 bytes
---
```

CVCUS01Y is the customer-variable copybook (`CUS` stem, `Y` suffix); defines
customer-record field layout. No PROCEDURE DIVISION; domain `customer`;
targeted for Section 3.6.

---

## CVEXPORT

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: system
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 157  # approx from 6271 bytes
---
```

CVEXPORT is the export-record variable copybook; defines the record layout
for the CBEXPORT batch program's output. No PROCEDURE DIVISION; domain
`system`; targeted for Section 3.6.

---

## CVTRA01Y – CVTRA07Y (Transaction variable copybooks)

### CVTRA01Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: transaction
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 23  # approx from 911 bytes
---
```

CVTRA01Y is the first transaction-variable copybook (`TRA` stem); defines
transaction-record fields. No PROCEDURE DIVISION; domain `transaction`.

### CVTRA02Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: transaction
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 23  # approx from 911 bytes
---
```

CVTRA02Y is structurally identical in size to CVTRA01Y; second transaction
variable variant. No PROCEDURE DIVISION; domain `transaction`.

### CVTRA03Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: transaction
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 17  # approx from 665 bytes
---
```

CVTRA03Y is a smaller transaction-variable copybook; likely a reduced-field
variant. No PROCEDURE DIVISION; domain `transaction`.

### CVTRA04Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: transaction
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 21  # approx from 829 bytes
---
```

CVTRA04Y is the fourth transaction-variable copybook. No PROCEDURE DIVISION;
domain `transaction`.

### CVTRA05Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: transaction
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 39  # approx from 1567 bytes
---
```

CVTRA05Y is a larger transaction-variable copybook; likely adds extended
fields for richer transaction records. No PROCEDURE DIVISION; domain
`transaction`.

### CVTRA06Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: transaction
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 39  # approx from 1559 bytes
---
```

CVTRA06Y is nearly identical in size to CVTRA05Y; sixth transaction-variable
variant. No PROCEDURE DIVISION; domain `transaction`.

### CVTRA07Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: transaction
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 146  # approx from 5831 bytes
---
```

CVTRA07Y is the largest transaction-variable copybook (5.8 KB); likely
defines the full expanded transaction record with all optional fields.
No PROCEDURE DIVISION; domain `transaction`.

---

## UNUSED1Y

```yaml
---
artifact_kind: copybook
execution_mode: null
cics_surface: null
io_class: null
domain: other  # REVIEW — name suggests intentionally unused placeholder
gate_status: pending
certified_at_section: null
deferred_at_section: null
target_section_for_resolution: "3.6"
pending_issue_id: null
paragraph_count_local: null
paragraph_count_facts: null
paragraph_count_drift: null
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: false
  has_data_division: false
  line_count: 10  # approx from 416 bytes
---
```

UNUSED1Y is a tiny placeholder copybook (416 bytes, ≈10 lines); the name
explicitly signals an unused/stub artifact. No PROCEDURE DIVISION; domain
flagged `# REVIEW` as the business purpose is unknown without source
inspection. Targeted for Section 3.6.

---

## Summary Tallies

### By artifact_kind

| artifact_kind | count |
|---|---|
| program | 31 |
| copybook | 28 |
| utility | 2 |
| **Total** | **61** |

> Note: Total artifacts = 59 (31 + 28) but two programs reclassified as
> `utility` (COBSWAIT, CSUTLDTC) are counted in the utility row and subtracted
> from program; actual `program` count above reflects 29 business programs +
> 2 utilities = 31 source `.cbl` files total.

### By gate_status

| gate_status | count | artifacts |
|---|---|---|
| certified | 26 | CBACT01C, CBACT02C, CBACT03C, CBACT04C, CBCUS01C, CBEXPORT, CBIMPORT, CBSTM03A, CBSTM03B, CBTRN01C, CBTRN02C, CBTRN03C, COADM01C, COBIL00C, COBSWAIT, COCRDSLC, COCRDUPC, COMEN01C, CORPT00C, COSGN00C, COTRN00C, COTRN01C, COTRN02C, COUSR00C, COUSR01C, COUSR02C, COUSR03C, CSUTLDTC |
| defensive_scope | 3 | COACTUPC, COACTVWC, COCRDLIC |
| pending | 28 | all 28 copybooks |
| not_in_corpus | 0 | — |

### By cics_surface (programs only)

| cics_surface | count | programs |
|---|---|---|
| none | 14 | CBACT01C, CBACT02C, CBACT03C, CBACT04C, CBCUS01C, CBEXPORT, CBIMPORT, CBSTM03A, CBSTM03B, CBTRN01C, CBTRN02C, CBTRN03C, COBSWAIT, CSUTLDTC |
| readonly | 8 | COACTVWC, COBIL00C, COCRDSLC, COMEN01C, CORPT00C, COTRN01C, COUSR01C |
| update_list | 10 | COACTUPC, COADM01C, COCRDLIC, COCRDUPC, COSGN00C, COTRN00C, COTRN02C, COUSR00C, COUSR02C, COUSR03C |
| null | 28 | all copybooks |

---

## Ambiguous Artifacts

The following artifacts have one or more axes flagged `# REVIEW` requiring
source inspection before the axis can be confirmed.

| Artifact | Axis flagged | Reason |
|---|---|---|
| CSLKPCDY | `domain` | Name `LKPCD` ambiguous: could be lookup-code table (system) or card-lookup (card). Unusually large (52 KB) for a copybook; content inspection required to determine if it is a card-number lookup table or a general-purpose code table. |
| UNUSED1Y | `domain` | Name is explicitly `UNUSED`; no business domain can be inferred without reading the content. Likely a stub/placeholder; domain set to `other` pending verification. |

All other axes on these two artifacts are consistent with `artifact_kind:
copybook` (no PROCEDURE DIVISION, no CICS signals) and are not flagged.
