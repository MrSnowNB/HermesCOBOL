# COBOL Statement-Level IR Specification (v1)

**Program**: HermesCOBOL  
**Component**: Statement-Level Intermediate Representation  
**Version**: 1.1  
**Status**: Approved (pending implementation)  
**Date**: 2026-05-27

---

## 1. Purpose

This specification defines a **statement-level Intermediate Representation (IR)** for COBOL programs designed to support deterministic simulation and execution tracing.

---

## 2. Source Inputs (Priority Order)

| Priority | Artifact | Purpose | Notes |
|----------|----------|---------|-------|
| 1 (Primary) | `data/preprocessed/<PROG>.cob` | Copybook-resolved field names | Preferred for field resolution |
| 2 | `data/raw/cbl/<PROG>.cbl` | Original source line numbers | Trace mapping |
| 3 | `data/cfg/` + `data/data_flow/` | Existing partial graph data | Avoid recomputation |

Every field carries a `source_artifact` tag.

---

## 3. Atomic Unit: Paragraph

Each paragraph is independently retrievable from Honcho via:

```
{program_id}/{paragraph_name}
```

---

## 4. IR Schema (v1)

```json
{
  "program": "COACTUPC",
  "paragraph": "1205-COMPARE-OLD-NEW",
  "source_lines": [1240, 1268],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": "1200-EDIT-MAP-INPUTS",
  "statements": [ ... ],
  "reads": [...],
  "mutates": [...],
  "performs": [
    {"target": "1210-EDIT-ACCOUNT", "form": "simple"}
  ],
  "goto_targets": []
}
```

### Paragraph-Level Fields

| Field | Type | Description |
|-------|------|-------------|
| `next_paragraph` | string \| null | Next paragraph on fall-through or GO TO (null if PERFORM caller determines return) |
| `performs` | array[object] | PERFORM targets with form (see below) |

---

## 5. Statement Object

### PERFORM Statement

```json
// Simple PERFORM
{
  "line": 850,
  "verb": "PERFORM",
  "text": "PERFORM 1205-COMPARE-OLD-NEW",
  "target": "1205-COMPARE-OLD-NEW",
  "form": "simple",
  "reads": [],
  "mutates": []
}

// PERFORM UNTIL
{
  "line": 920,
  "verb": "PERFORM",
  "text": "PERFORM 4000-READ-LOOP UNTIL END-OF-FILE = 'Y'",
  "target": "4000-READ-LOOP",
  "form": "until",
  "until_condition": {
    "text": "END-OF-FILE = 'Y'",
    "reads": ["END-OF-FILE"]
  }
}

// PERFORM THRU
{
  "line": 1050,
  "verb": "PERFORM",
  "text": "PERFORM 8100-OPEN THRU 8100-EXIT",
  "target": "8100-OPEN",
  "thru": "8100-EXIT",
  "form": "thru"
}
```

### EVALUATE Statement

```json
{
  "line": 680,
  "verb": "EVALUATE",
  "text": "EVALUATE EIBAID",
  "subject": {
    "text": "EIBAID",
    "reads": ["EIBAID"]
  },
  "branches": [
    {
      "when": "DFHENTER",
      "statements": [ ... ]
    },
    {
      "when": "DFHPF3",
      "statements": [ ... ]
    },
    {
      "when": "OTHER",
      "statements": [ ... ]
    }
  ]
}
```

### IF Statement

```json
{
  "line": 1240,
  "verb": "IF",
  "text": "IF ACUP-OLD-CUST-LAST-NAME NOT = ACSLNAMEI",
  "reads": ["ACUP-OLD-CUST-LAST-NAME", "ACSLNAMEI"],
  "mutates": [],
  "branches": {
    "true": [ ... ],
    "false": [ ... ]
  }
}
```

### GO TO Statement

```json
{
  "line": 1321,
  "verb": "GO TO",
  "text": "GO TO COMMON-RETURN",
  "branches": {
    "unconditional": "COMMON-RETURN"
  }
}
```

---

## 6. Verb Coverage (v1)

Supported in v1:
- `MOVE`, `IF`/`ELSE`, `PERFORM`, `GO TO`, `SET`, `COMPUTE`, `ADD`, `SUBTRACT`, `MULTIPLY`, `DIVIDE`, `EXEC CICS`, `EVALUATE`

Deferred to v2: `SEARCH`, `STRING`, `UNSTRING`, `INSPECT`

---

## 7. Constraints

- Paragraph is the atomic retrieval unit
- `source_artifact` required on every field
- Soft target: **< 200 statements per paragraph** (flag larger paragraphs for review)
- Paragraph-level `reads`/`mutates` must aggregate from all statements and branch bodies

---

## 8. Example (Full Paragraph)

```json
{
  "program": "COACTUPC",
  "paragraph": "1205-COMPARE-OLD-NEW",
  "source_lines": [1240, 1268],
  "source_artifact": "data/preprocessed/COACTUPC.cob",
  "next_paragraph": null,
  "statements": [
    {
      "line": 1240,
      "verb": "IF",
      "text": "IF ACUP-OLD-CUST-LAST-NAME NOT = ACSLNAMEI",
      "reads": ["ACUP-OLD-CUST-LAST-NAME", "ACSLNAMEI"],
      "mutates": [],
      "branches": {
        "true": [
          {
            "line": 1241,
            "verb": "SET",
            "text": "SET DATA-WAS-CHANGED-BEFORE-UPDATE TO TRUE",
            "mutates": ["DATA-WAS-CHANGED-BEFORE-UPDATE"]
          }
        ],
        "false": []
      }
    }
  ],
  "reads": ["ACUP-OLD-CUST-LAST-NAME", "ACSLNAMEI"],
  "mutates": ["DATA-WAS-CHANGED-BEFORE-UPDATE"],
  "performs": [],
  "goto_targets": []
}
```

---

*Approved for implementation pending extractor development.*
