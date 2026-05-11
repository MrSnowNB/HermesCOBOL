# Corpus Classification Audit - Local Second Opinion

---
audit_schema_version: "1.3"
generated_at: "2026-05-11T11:38:00Z"
generated_from_commit: a7a1688
generated_by: cline-local
total_artifacts: 79
total_programs: 30
total_copybooks: 48
total_utilities: 1
---

## CBACT01C

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: account
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 16
paragraph_count_facts: 16
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 430
---

**Justification:** Program without EXEC CICS, 430 lines, domain: account (cics_surface: none).

## CBACT02C

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: account
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 5
paragraph_count_facts: 5
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 178
---

**Justification:** Program without EXEC CICS, 178 lines, domain: account (cics_surface: none).

## CBACT03C

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: account
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 5
paragraph_count_facts: 5
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 178
---

**Justification:** Program without EXEC CICS, 178 lines, domain: account (cics_surface: none).

## CBACT04C

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: account
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 22
paragraph_count_facts: 22
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 652
---

**Justification:** Program without EXEC CICS, 652 lines, domain: account (cics_surface: none).

## CBCUS01C

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: customer
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 5
paragraph_count_facts: 5
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 178
---

**Justification:** Program without EXEC CICS, 178 lines, domain: customer (cics_surface: none).

## CBEXPORT

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: other
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 21
paragraph_count_facts: 21
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 582
---

**Justification:** Program without EXEC CICS, 582 lines, domain: other (cics_surface: none).

## CBIMPORT

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: other
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 16
paragraph_count_facts: 16
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 487
---

**Justification:** Program without EXEC CICS, 487 lines, domain: other (cics_surface: none).

## CBSTM03A

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: other
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 25
paragraph_count_facts: 25
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 924
---

**Justification:** Program without EXEC CICS, 924 lines, domain: other (cics_surface: none).

## CBSTM03B

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: other
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 14
paragraph_count_facts: 14
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 230
---

**Justification:** Program without EXEC CICS, 230 lines, domain: other (cics_surface: none).

## CBTRN01C

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: transaction
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 18
paragraph_count_facts: 18
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 494
---

**Justification:** Program without EXEC CICS, 494 lines, domain: transaction (cics_surface: none).

## CBTRN02C

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: transaction
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 26
paragraph_count_facts: 26
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 731
---

**Justification:** Program without EXEC CICS, 731 lines, domain: transaction (cics_surface: none).

## CBTRN03C

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [vsam]
domain: transaction
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 26
paragraph_count_facts: 26
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 649
---

**Justification:** Program without EXEC CICS, 649 lines, domain: transaction (cics_surface: none).

## COACTUPC

---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, map, commarea]
domain: account
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 86
paragraph_count_facts: 86
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 4236
---

**Justification:** Program with EXEC CICS, 4236 lines, domain: account (cics_surface: update_list).

## COACTVWC

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, map, commarea]
domain: account
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 35
paragraph_count_facts: 35
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 941
---

**Justification:** Program with EXEC CICS, 941 lines, domain: account (cics_surface: readonly).

## COADM01C

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, commarea]
domain: system
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 8
paragraph_count_facts: 8
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 288
---

**Justification:** Program with EXEC CICS, 288 lines, domain: system (cics_surface: readonly).

## COBIL00C

---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, commarea]
domain: account
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 16
paragraph_count_facts: 16
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 572
---

**Justification:** Program with EXEC CICS, 572 lines, domain: account (cics_surface: update_list).

## COCRDLIC

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, map, commarea]
domain: card
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 40
paragraph_count_facts: 40
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 1469
---

**Justification:** Program with EXEC CICS, 1469 lines, domain: card (cics_surface: readonly).

## COCRDSLC

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [map, commarea]
domain: card
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 9
paragraph_count_facts: 9
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 325
---

**Justification:** Program with EXEC CICS, 325 lines, domain: card (cics_surface: readonly).

## COCRDUPC

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [map, commarea]
domain: card
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 13
paragraph_count_facts: 13
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 402
---

**Justification:** Program with EXEC CICS, 402 lines, domain: card (cics_surface: readonly).

## COMEN01C

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, commarea]
domain: menu
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 7
paragraph_count_facts: 7
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 308
---

**Justification:** Program with EXEC CICS, 308 lines, domain: menu (cics_surface: readonly).

## CORPT00C

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, commarea, seq]
domain: reporting
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 10
paragraph_count_facts: 10
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 649
---

**Justification:** Program with EXEC CICS, 649 lines, domain: reporting (cics_surface: readonly).

## COSGN00C

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, commarea]
domain: signon
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 6
paragraph_count_facts: 6
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 260
---

**Justification:** Program with EXEC CICS, 260 lines, domain: signon (cics_surface: readonly).

## COTRN00C

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, commarea]
domain: transaction
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 16
paragraph_count_facts: 16
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 699
---

**Justification:** Program with EXEC CICS, 699 lines, domain: transaction (cics_surface: readonly).

## COTRN01C

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, commarea]
domain: transaction
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 9
paragraph_count_facts: 9
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 330
---

**Justification:** Program with EXEC CICS, 330 lines, domain: transaction (cics_surface: readonly).

## COTRN02C

---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, commarea]
domain: transaction
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 18
paragraph_count_facts: 18
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 783
---

**Justification:** Program with EXEC CICS, 783 lines, domain: transaction (cics_surface: update_list).

## COUSR00C

---
artifact_kind: program
execution_mode: online
cics_surface: readonly
io_class: [vsam, commarea]
domain: customer
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 16
paragraph_count_facts: 16
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 695
---

**Justification:** Program with EXEC CICS, 695 lines, domain: customer (cics_surface: readonly).

## COUSR01C

---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, commarea]
domain: customer
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 9
paragraph_count_facts: 9
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 299
---

**Justification:** Program with EXEC CICS, 299 lines, domain: customer (cics_surface: update_list).

## COUSR02C

---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, commarea]
domain: customer
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 11
paragraph_count_facts: 11
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: true
  has_procedure_division: true
  has_data_division: true
  line_count: 414
---

**Justification:** Program with EXEC CICS, 414 lines, domain: customer (cics_surface: update_list).

## COUSR03C

---
artifact_kind: program
execution_mode: online
cics_surface: update_list
io_class: [vsam, commarea]
domain: customer
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 11
paragraph_count_facts: 11
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: true
  has_send_map: true
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 359
---

**Justification:** Program with EXEC CICS, 359 lines, domain: customer (cics_surface: update_list).

## CSUTLDTC

---
artifact_kind: program
execution_mode: batch
cics_surface: none
io_class: [none]
domain: system
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 2
paragraph_count_facts: 2
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 157
---

**Justification:** Program without EXEC CICS, 157 lines, domain: system (cics_surface: none).

## COBSWAIT

---
artifact_kind: utility
execution_mode: batch
cics_surface: none
io_class: [none]
domain: other
gate_status: certified
certified_at_section: 3.4
deferred_at_section: None
target_section_for_resolution: None
pending_issue_id: None
paragraph_count_local: 0
paragraph_count_facts: 0
paragraph_count_drift: 0
schema_version: "1.3"
evidence:
  has_exec_cics: false
  has_send_map: false
  has_rewrite: false
  has_procedure_division: true
  has_data_division: true
  line_count: 41
---

**Justification:** Utility program with 41 lines and 0 paragraphs, no business domain-specific functionality.

## COACTUP.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 668
---

**Justification:** Copybook with 668 lines, no PROCEDURE DIVISION.

## COACTVW.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 464
---

**Justification:** Copybook with 464 lines, no PROCEDURE DIVISION.

## COADM01.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 260
---

**Justification:** Copybook with 260 lines, no PROCEDURE DIVISION.

## COADM02Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 62
---

**Justification:** Copybook with 62 lines, no PROCEDURE DIVISION.

## COBIL00.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 140
---

**Justification:** Copybook with 140 lines, no PROCEDURE DIVISION.

## COCOM01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 47
---

**Justification:** Copybook with 47 lines, no PROCEDURE DIVISION.

## COCRDLI.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 560
---

**Justification:** Copybook with 560 lines, no PROCEDURE DIVISION.

## COCRDSL.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 200
---

**Justification:** Copybook with 200 lines, no PROCEDURE DIVISION.

## COCRDUP.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 224
---

**Justification:** Copybook with 224 lines, no PROCEDURE DIVISION.

## CODATECN.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 52
---

**Justification:** Copybook with 52 lines, no PROCEDURE DIVISION.

## COMEN01.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 260
---

**Justification:** Copybook with 260 lines, no PROCEDURE DIVISION.

## COMEN01.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 37
---

**Justification:** Copybook with 37 lines, no PROCEDURE DIVISION.

## COMEN02Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 101
---

**Justification:** Copybook with 101 lines, no PROCEDURE DIVISION.

## CORPT00.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 224
---

**Justification:** Copybook with 224 lines, no PROCEDURE DIVISION.

## COSGN00.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 152
---

**Justification:** Copybook with 152 lines, no PROCEDURE DIVISION.

## COSTM01.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 38
---

**Justification:** Copybook with 38 lines, no PROCEDURE DIVISION.

## COTRN00.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 728
---

**Justification:** Copybook with 728 lines, no PROCEDURE DIVISION.

## COTRN01.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 272
---

**Justification:** Copybook with 272 lines, no PROCEDURE DIVISION.

## COTRN02.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 272
---

**Justification:** Copybook with 272 lines, no PROCEDURE DIVISION.

## COTTL01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 27
---

**Justification:** Copybook with 27 lines, no PROCEDURE DIVISION.

## COUSR00.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 728
---

**Justification:** Copybook with 728 lines, no PROCEDURE DIVISION.

## COUSR01.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 164
---

**Justification:** Copybook with 164 lines, no PROCEDURE DIVISION.

## COUSR02.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 164
---

**Justification:** Copybook with 164 lines, no PROCEDURE DIVISION.

## COUSR03.CPY

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 152
---

**Justification:** Copybook with 152 lines, no PROCEDURE DIVISION.

## CSDAT01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 58
---

**Justification:** Copybook with 58 lines, no PROCEDURE DIVISION.

## CSLKPCDY.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 1318
---

**Justification:** Copybook with 1318 lines, no PROCEDURE DIVISION.

## CSMSG01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 24
---

**Justification:** Copybook with 24 lines, no PROCEDURE DIVISION.

## CSMSG02Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 35
---

**Justification:** Copybook with 35 lines, no PROCEDURE DIVISION.

## CSSETATY.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 30
---

**Justification:** Copybook with 30 lines, no PROCEDURE DIVISION.

## CSSTRPFY.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 85
---

**Justification:** Copybook with 85 lines, no PROCEDURE DIVISION.

## CSUSR01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 26
---

**Justification:** Copybook with 26 lines, no PROCEDURE DIVISION.

## CSUTLDPY.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 375
---

**Justification:** Copybook with 375 lines, no PROCEDURE DIVISION.

## CSUTLDWY.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 89
---

**Justification:** Copybook with 89 lines, no PROCEDURE DIVISION.

## CUSTREC.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 26
---

**Justification:** Copybook with 26 lines, no PROCEDURE DIVISION.

## CVACT01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 20
---

**Justification:** Copybook with 20 lines, no PROCEDURE DIVISION.

## CVACT02Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 14
---

**Justification:** Copybook with 14 lines, no PROCEDURE DIVISION.

## CVACT03Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 11
---

**Justification:** Copybook with 11 lines, no PROCEDURE DIVISION.

## CVCRD01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 46
---

**Justification:** Copybook with 46 lines, no PROCEDURE DIVISION.

## CVCUS01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 26
---

**Justification:** Copybook with 26 lines, no PROCEDURE DIVISION.

## CVEXPORT.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 103
---

**Justification:** Copybook with 103 lines, no PROCEDURE DIVISION.

## CVTRA01Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 13
---

**Justification:** Copybook with 13 lines, no PROCEDURE DIVISION.

## CVTRA02Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 13
---

**Justification:** Copybook with 13 lines, no PROCEDURE DIVISION.

## CVTRA03Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 10
---

**Justification:** Copybook with 10 lines, no PROCEDURE DIVISION.

## CVTRA04Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 12
---

**Justification:** Copybook with 12 lines, no PROCEDURE DIVISION.

## CVTRA05Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 21
---

**Justification:** Copybook with 21 lines, no PROCEDURE DIVISION.

## CVTRA06Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 21
---

**Justification:** Copybook with 21 lines, no PROCEDURE DIVISION.

## CVTRA07Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 73
---

**Justification:** Copybook with 73 lines, no PROCEDURE DIVISION.

## UNUSED1Y.cpy

---
artifact_kind: copybook
execution_mode: None
cics_surface: None
io_class: null
domain: None
gate_status: pending
certified_at_section: None
deferred_at_section: None
target_section_for_resolution: 3.6
pending_issue_id: None
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
  line_count: 10
---

**Justification:** Copybook with 10 lines, no PROCEDURE DIVISION.

## Summary by artifact_kind

| artifact_kind | count |
|---------------|-------|
| program | 30 |
| copybook | 48 |
| utility | 1 |

## Summary by gate_status

| gate_status | count |
|-------------|-------|
| certified | 31 |
| pending | 48 |

## Summary by cics_surface

| cics_surface | count |
|--------------|-------|
| none | 14 |
| readonly | 11 |
| update_list | 6 |

## Ambiguous artifacts

No ambiguous artifacts detected - all artifacts have sufficient evidence for classification.
