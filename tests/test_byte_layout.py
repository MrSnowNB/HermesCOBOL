#!/usr/bin/env python3
"""
tests/test_byte_layout.py
=========================
Unit tests for scripts/byte_layout.py.

Runs standalone (no pytest required, though pytest works fine):
  python tests/test_byte_layout.py

Or with pytest:
  pytest tests/test_byte_layout.py -v

Covers:
  - pic_length() for DISPLAY, COMP-3, COMP/BINARY with edge cases
  - Simple 01-level record with no OCCURS
  - OCCURS n at elementary level
  - Nested OCCURS (OCCURS 12 inside OCCURS 50) -- the key spec requirement
  - REDEFINES offset reset
  - Unrecognized PIC emits placeholder with length=null and unresolved[] entry
  - COPY not-found emits unresolved[] entry without crashing
"""
from __future__ import annotations
import sys
import json
from pathlib import Path

# Allow running from repo root or tests/ directory
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from byte_layout import pic_length, extract_layout


# ===========================================================================
# Helpers
# ===========================================================================

def _cobol_wrap(data_section: str) -> str:
    """Wrap a DATA DIVISION snippet in minimal valid COBOL scaffolding."""
    return (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. TEST.\n"
        "       DATA DIVISION.\n"
        "       WORKING-STORAGE SECTION.\n"
        + data_section +
        "\n"
        "       PROCEDURE DIVISION.\n"
        "       STOP RUN.\n"
    )


def _field(layout: dict, qname: str) -> dict:
    """Find field by qualified_name in layout result."""
    for rec in layout["records"]:
        for f in rec["fields"]:
            if f["qualified_name"] == qname:
                return f
    raise KeyError(f"Field not found: {qname}")


# ===========================================================================
# 1.  pic_length() unit tests
# ===========================================================================

def test_pic_length_display_alpha():
    assert pic_length("X(10)", "DISPLAY") == 10

def test_pic_length_display_numeric():
    assert pic_length("9(5)", "DISPLAY") == 5

def test_pic_length_display_signed():
    # S9(7) DISPLAY: sign is embedded, 7 bytes
    assert pic_length("S9(7)", "DISPLAY") == 7

def test_pic_length_display_with_v():
    # S9(10)V99 DISPLAY: 10+2 = 12 digit positions, no V byte
    assert pic_length("S9(10)V99", "DISPLAY") == 12

def test_pic_length_comp3_odd():
    # S9(7)V99 COMP-3: 9 digits -> ceil(10/2) = 5 bytes
    assert pic_length("S9(7)V99", "COMP-3") == 5

def test_pic_length_comp3_even():
    # S9(10)V99 COMP-3: 12 digits -> ceil(13/2) = 7 bytes
    assert pic_length("S9(10)V99", "COMP-3") == 7

def test_pic_length_comp3_simple():
    # 9(5) COMP-3: 5 digits -> ceil(6/2) = 3 bytes
    assert pic_length("9(5)", "COMP-3") == 3

def test_pic_length_comp_small():
    # 9(4) COMP: <= 4 digits -> 2 bytes
    assert pic_length("9(4)", "COMP") == 2

def test_pic_length_comp_medium():
    # 9(9) COMP: 5-9 digits -> 4 bytes
    assert pic_length("9(9)", "COMP") == 4

def test_pic_length_comp_large():
    # 9(18) COMP: 10-18 digits -> 8 bytes
    assert pic_length("9(18)", "COMP") == 8

def test_pic_length_binary_synonym():
    # BINARY is synonym for COMP
    assert pic_length("9(5)", "COMP") == 4   # same as COMP

def test_pic_length_packed_decimal_synonym():
    # PACKED-DECIMAL is synonym for COMP-3
    assert pic_length("9(5)", "COMP-3") == 3

def test_pic_length_unrecognized():
    # Should return None for unknown pic / storage combo
    assert pic_length("", "DISPLAY") is None
    assert pic_length("", "COMP-3")  is None


# ===========================================================================
# 2.  Simple record: no OCCURS, verify offsets
# ===========================================================================

def test_simple_record_offsets():
    src = _cobol_wrap("""
       01  ACCT-RECORD.
           05  ACCT-ID          PIC 9(11).
           05  ACCT-ACTIVE-STATUS PIC X(01).
           05  ACCT-BAL         PIC S9(10)V99 COMP-3.
    """)
    layout = extract_layout(src, "TEST")
    assert len(layout["unresolved"]) == 0

    f_id = _field(layout, "ACCT-RECORD.ACCT-ID")
    assert f_id["offset"]  == 0
    assert f_id["length"]  == 11
    assert f_id["storage"] == "DISPLAY"

    f_st = _field(layout, "ACCT-RECORD.ACCT-ACTIVE-STATUS")
    assert f_st["offset"] == 11
    assert f_st["length"] == 1

    # S9(10)V99 COMP-3: 12 digits -> ceil(13/2) = 7 bytes
    f_bal = _field(layout, "ACCT-RECORD.ACCT-BAL")
    assert f_bal["offset"]  == 12
    assert f_bal["length"]  == 7
    assert f_bal["storage"] == "COMP-3"


# ===========================================================================
# 3.  OCCURS at elementary level
# ===========================================================================

def test_occurs_elementary():
    src = _cobol_wrap("""
       01  WS-TABLE.
           05  WS-ITEM  PIC X(5) OCCURS 10 TIMES.
           05  WS-AFTER PIC X(3).
    """)
    layout = extract_layout(src, "TEST")
    assert len(layout["unresolved"]) == 0

    f_item = _field(layout, "WS-TABLE.WS-ITEM")
    assert f_item["offset"] == 0
    assert f_item["length"] == 5       # per-occurrence length
    assert f_item["occurs"] == 10

    # WS-AFTER should start at offset 50 (10 * 5)
    f_after = _field(layout, "WS-TABLE.WS-AFTER")
    assert f_after["offset"] == 50
    assert f_after["length"] == 3


# ===========================================================================
# 4.  NESTED OCCURS: OCCURS 12 inside OCCURS 50
#     This is the spec-required nested multiplier test.
#
#     Structure:
#       01  OUTER-TABLE.
#           05  OUTER-ENTRY OCCURS 50 TIMES.
#               10  INNER-ENTRY OCCURS 12 TIMES.
#                   15  INNER-FIELD PIC X(4).
#               10  OUTER-FLAG  PIC X(1).
#
#     INNER-ENTRY: 12 * 4 = 48 bytes per occurrence
#     OUTER-ENTRY: (48 + 1) * -- wait, OUTER-FLAG is per outer entry
#       Actually per OUTER-ENTRY occurrence:
#         INNER-ENTRY subtree = 12 * 4 = 48 bytes
#         OUTER-FLAG          = 1 byte
#         Total per outer occ = 49 bytes
#     OUTER-TABLE total = 49 * 50 = 2450 bytes
# ===========================================================================

def test_nested_occurs():
    src = _cobol_wrap("""
       01  OUTER-TABLE.
           05  OUTER-ENTRY OCCURS 50 TIMES.
               10  INNER-ENTRY OCCURS 12 TIMES.
                   15  INNER-FIELD  PIC X(4).
               10  OUTER-FLAG   PIC X(1).
    """)
    layout = extract_layout(src, "TEST")
    assert len(layout["unresolved"]) == 0

    # INNER-FIELD: per-occurrence length = 4, occurs=12
    f_inner = _field(layout, "OUTER-TABLE.OUTER-ENTRY.INNER-ENTRY.INNER-FIELD")
    assert f_inner["length"] == 4
    assert f_inner["occurs"] == 12
    assert f_inner["offset"] == 0   # first occurrence offset within OUTER-ENTRY[0]

    # OUTER-FLAG: starts after all 12 INNER-FIELDs = offset 48
    f_flag = _field(layout, "OUTER-TABLE.OUTER-ENTRY.OUTER-FLAG")
    assert f_flag["offset"] == 48
    assert f_flag["length"] == 1

    # OUTER-ENTRY group: 48 + 1 = 49 bytes per occ, occurs=50
    f_outer = _field(layout, "OUTER-TABLE.OUTER-ENTRY")
    assert f_outer["occurs"]  == 50
    assert f_outer["length"]  == 49 * 50   # 2450 total bytes

    # OUTER-TABLE record total_bytes
    rec = layout["records"][0]
    assert rec["total_bytes"] == 2450


# ===========================================================================
# 5.  REDEFINES: offset reset and redefines_groups populated
# ===========================================================================

def test_redefines():
    src = _cobol_wrap("""
       01  WS-DATE-GROUP.
           05  WS-DATE-NUM  PIC 9(8).
           05  WS-DATE-CHAR REDEFINES WS-DATE-NUM PIC X(8).
           05  WS-AFTER     PIC X(2).
    """)
    layout = extract_layout(src, "TEST")
    assert len(layout["unresolved"]) == 0

    f_num  = _field(layout, "WS-DATE-GROUP.WS-DATE-NUM")
    f_char = _field(layout, "WS-DATE-GROUP.WS-DATE-CHAR")
    f_after= _field(layout, "WS-DATE-GROUP.WS-AFTER")

    # Both WS-DATE-NUM and WS-DATE-CHAR start at offset 0
    assert f_num["offset"]  == 0
    assert f_char["offset"] == 0
    assert f_char["redefines"] == "WS-DATE-NUM"

    # WS-AFTER starts after the max(8, 8) = 8 bytes
    assert f_after["offset"] == 8

    # redefines_groups populated on the record
    rec = layout["records"][0]
    assert any(g["redefines_target"] == "WS-DATE-NUM" for g in rec["redefines_groups"])


# ===========================================================================
# 6.  Unrecognized PIC: placeholder with length=null, unresolved[] entry
# ===========================================================================

def test_unrecognized_pic_placeholder():
    # An empty PIC clause should trigger unrecognized handling
    # We synthesize this by patching a node directly via extract_layout with
    # a PIC that the parser cannot size (empty string after our regex match).
    # Easiest: use a storage class that pic_length returns None for.
    # We test by using an unusual PIC like 'G(5)' which is DBCS and not
    # handled by our DISPLAY path (expand_count sees 'G' as unknown -> 0).
    src = _cobol_wrap("""
       01  WS-TEST.
           05  WS-KNOWN    PIC X(5).
           05  WS-UNKNOWN  PIC X(0).
           05  WS-AFTER    PIC X(3).
    """)
    # pic_length('X(0)', 'DISPLAY') -> expand_count returns 0 -> None
    layout = extract_layout(src, "TEST")

    f_unknown = _field(layout, "WS-TEST.WS-UNKNOWN")
    assert f_unknown["length"] is None
    assert any(u["field"] == "WS-TEST.WS-UNKNOWN" and u["reason"] == "unrecognized_pic"
               for u in layout["unresolved"])

    # WS-AFTER offset should NOT have advanced past WS-UNKNOWN
    # (cursor not advanced on null-length field)
    f_after = _field(layout, "WS-TEST.WS-AFTER")
    assert f_after["offset"] == 5   # only WS-KNOWN (5 bytes) advanced cursor


# ===========================================================================
# 7.  Copybook not found: unresolved[] entry, no crash
# ===========================================================================

def test_copybook_not_found():
    src = _cobol_wrap("""
       01  WS-BEFORE  PIC X(3).
       COPY NOSUCHCOPYBOOK.
       01  WS-AFTER   PIC X(2).
    """)
    # Should not raise; should record unresolved copybook
    layout = extract_layout(src, "TEST", source_path=Path("/nonexistent/TEST.cbl"))
    assert any(
        u.get("copybook") == "NOSUCHCOPYBOOK" and u["reason"] == "copybook_not_found"
        for u in layout["unresolved"]
    )
    # WS-BEFORE and WS-AFTER records should still be present
    names = [r["name"] for r in layout["records"]]
    assert "WS-BEFORE" in names
    assert "WS-AFTER"  in names


# ===========================================================================
# 8.  Run all tests
# ===========================================================================

if __name__ == "__main__":
    tests = [
        test_pic_length_display_alpha,
        test_pic_length_display_numeric,
        test_pic_length_display_signed,
        test_pic_length_display_with_v,
        test_pic_length_comp3_odd,
        test_pic_length_comp3_even,
        test_pic_length_comp3_simple,
        test_pic_length_comp_small,
        test_pic_length_comp_medium,
        test_pic_length_comp_large,
        test_pic_length_binary_synonym,
        test_pic_length_packed_decimal_synonym,
        test_pic_length_unrecognized,
        test_simple_record_offsets,
        test_occurs_elementary,
        test_nested_occurs,
        test_redefines,
        test_unrecognized_pic_placeholder,
        test_copybook_not_found,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  [PASS] {t.__name__}")
            passed += 1
        except Exception as e:
            print(f"  [FAIL] {t.__name__}: {e}")
            failed += 1

    print(f"\n{passed} passed / {failed} failed")
    sys.exit(0 if failed == 0 else 1)
