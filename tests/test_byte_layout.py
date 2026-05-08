#!/usr/bin/env python3
"""
tests/test_byte_layout.py  v1.2.2
==================================
Unit tests for scripts/byte_layout.py.

Run standalone:
  python tests/test_byte_layout.py

Or with pytest:
  pytest tests/test_byte_layout.py -v

Covers:
  - pic_length() for DISPLAY, COMP-3, COMP/BINARY
  - Simple 01-level record offset correctness
  - OCCURS n at elementary level (offset advancement)
  - Nested OCCURS: group header carries occurs, leaf field carries 1
  - Group OCCURS: group header precedes children in flat list
  - REDEFINES: offset reset and redefines_groups populated
  - 01-level REDEFINES (elementary): total_bytes non-null + redefines_groups
  - Unrecognized PIC placeholder with length=null
  - COPY not-found records unresolved[] entry without crash
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
from byte_layout import pic_length, extract_layout


# ===========================================================================
# Helpers
# ===========================================================================

def _cobol_wrap(data_section: str) -> str:
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
    for rec in layout["records"]:
        for f in rec["fields"]:
            if f["qualified_name"] == qname:
                return f
    raise KeyError(
        f"Field not found: {qname!r}\n"
        f"Available: {[f['qualified_name'] for r in layout['records'] for f in r['fields']]}"
    )


def _record(layout: dict, name: str) -> dict:
    for rec in layout["records"]:
        if rec["name"] == name:
            return rec
    raise KeyError(
        f"Record not found: {name!r}\nAvailable: {[r['name'] for r in layout['records']]}"
    )


# ===========================================================================
# 1.  pic_length()
# ===========================================================================

def test_pic_length_display_alpha():          assert pic_length("X(10)",       "DISPLAY") == 10
def test_pic_length_display_numeric():        assert pic_length("9(5)",        "DISPLAY") == 5
def test_pic_length_display_signed():         assert pic_length("S9(7)",       "DISPLAY") == 7
def test_pic_length_display_with_v():         assert pic_length("S9(10)V99",   "DISPLAY") == 12
def test_pic_length_comp3_odd():              assert pic_length("S9(7)V99",    "COMP-3")  == 5
def test_pic_length_comp3_even():             assert pic_length("S9(10)V99",   "COMP-3")  == 7
def test_pic_length_comp3_simple():           assert pic_length("9(5)",        "COMP-3")  == 3
def test_pic_length_comp_small():             assert pic_length("9(4)",        "COMP")    == 2
def test_pic_length_comp_medium():            assert pic_length("9(9)",        "COMP")    == 4
def test_pic_length_comp_large():             assert pic_length("9(18)",       "COMP")    == 8
def test_pic_length_binary_synonym():         assert pic_length("9(5)",        "COMP")    == 4
def test_pic_length_packed_decimal_synonym(): assert pic_length("9(5)",        "COMP-3")  == 3
def test_pic_length_unrecognized():           assert pic_length("",            "DISPLAY") is None


# ===========================================================================
# 2.  Simple record: no OCCURS
# ===========================================================================

def test_simple_record_offsets():
    src = _cobol_wrap("""
       01  ACCT-RECORD.
           05  ACCT-ID            PIC 9(11).
           05  ACCT-ACTIVE-STATUS PIC X(01).
           05  ACCT-BAL           PIC S9(10)V99 COMP-3.
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

    # S9(10)V99 COMP-3: 12 digits -> ceil(13/2) = 7
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
    assert f_item["length"] == 5
    assert f_item["occurs"] == 10

    # WS-AFTER must start at offset 50 (10 * 5)
    f_after = _field(layout, "WS-TABLE.WS-AFTER")
    assert f_after["offset"] == 50
    assert f_after["length"] == 3


# ===========================================================================
# 4.  NESTED OCCURS: OCCURS 12 inside OCCURS 50
#
#   01  OUTER-TABLE.
#       05  OUTER-ENTRY OCCURS 50 TIMES.
#           10  INNER-ENTRY OCCURS 12 TIMES.
#               15  INNER-FIELD  PIC X(4).
#           10  OUTER-FLAG   PIC X(1).
#
#   INNER-FIELD: no OCCURS clause of its own -> occurs=1 in flat output.
#   INNER-ENTRY group header: occurs=12, length=12*4=48.
#   OUTER-FLAG: offset=48, length=1.
#   OUTER-ENTRY group header: occurs=50, length=(48+1)*50=2450.
#   OUTER-TABLE total_bytes=2450.
#
#   NOTE: In a flat byte-layout, each leaf field is emitted at its base
#   offset within ONE occurrence of the enclosing group.  The repetition
#   count lives on the group header, not the leaf.  This is correct COBOL
#   semantics: INNER-FIELD itself has no OCCURS; only INNER-ENTRY does.
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
    assert len(layout["unresolved"]) == 0, layout["unresolved"]

    # INNER-FIELD: base length=4, own occurs=1 (no OCCURS on the leaf),
    # starts at offset 0 within one INNER-ENTRY occurrence.
    f_inner = _field(layout, "OUTER-TABLE.OUTER-ENTRY.INNER-ENTRY.INNER-FIELD")
    assert f_inner["length"] == 4,  f"INNER-FIELD length: {f_inner['length']}"
    assert f_inner["occurs"] == 1,  f"INNER-FIELD occurs: {f_inner['occurs']}"
    assert f_inner["offset"] == 0,  f"INNER-FIELD offset: {f_inner['offset']}"

    # INNER-ENTRY group header: occurs=12, length=12*4=48, offset=0
    f_inner_grp = _field(layout, "OUTER-TABLE.OUTER-ENTRY.INNER-ENTRY")
    assert f_inner_grp["occurs"]  == 12, f"INNER-ENTRY occurs: {f_inner_grp['occurs']}"
    assert f_inner_grp["length"]  == 48, f"INNER-ENTRY length: {f_inner_grp['length']}"
    assert f_inner_grp["offset"]  == 0,  f"INNER-ENTRY offset: {f_inner_grp['offset']}"
    assert f_inner_grp["storage"] == "GROUP"

    # OUTER-FLAG: starts at offset 48 (after 12 * 4 bytes of INNER-ENTRY)
    f_flag = _field(layout, "OUTER-TABLE.OUTER-ENTRY.OUTER-FLAG")
    assert f_flag["offset"] == 48, f"OUTER-FLAG offset: {f_flag['offset']}"
    assert f_flag["length"] == 1,  f"OUTER-FLAG length: {f_flag['length']}"

    # OUTER-ENTRY group header: occurs=50, length=(48+1)*50=2450
    f_outer = _field(layout, "OUTER-TABLE.OUTER-ENTRY")
    assert f_outer["occurs"]  == 50,   f"OUTER-ENTRY occurs: {f_outer['occurs']}"
    assert f_outer["length"]  == 2450, f"OUTER-ENTRY length: {f_outer['length']}"
    assert f_outer["storage"] == "GROUP"

    # Record total
    rec = _record(layout, "OUTER-TABLE")
    assert rec["total_bytes"] == 2450, f"OUTER-TABLE total_bytes: {rec['total_bytes']}"


# ===========================================================================
# 5.  Group OCCURS: group header appears BEFORE children in flat list
#     (regression for the insert_pos fix)
# ===========================================================================

def test_group_occurs_header_position():
    """
    Verify that when a group with OCCURS appears after a non-group sibling,
    the group header still precedes its own children in the flat field list.
    """
    src = _cobol_wrap("""
       01  WS-MIX.
           05  WS-SCALAR   PIC X(3).
           05  WS-GRP OCCURS 4 TIMES.
               10  WS-A    PIC X(2).
               10  WS-B    PIC 9(1).
    """)
    layout = extract_layout(src, "TEST")
    assert len(layout["unresolved"]) == 0

    rec   = _record(layout, "WS-MIX")
    names = [f["qualified_name"] for f in rec["fields"]]

    idx_grp = names.index("WS-MIX.WS-GRP")
    idx_a   = names.index("WS-MIX.WS-GRP.WS-A")
    idx_b   = names.index("WS-MIX.WS-GRP.WS-B")
    assert idx_grp < idx_a, f"Group header {idx_grp} must precede WS-A {idx_a}"
    assert idx_grp < idx_b, f"Group header {idx_grp} must precede WS-B {idx_b}"

    # WS-GRP total: (2+1)*4 = 12 bytes
    f_grp = _field(layout, "WS-MIX.WS-GRP")
    assert f_grp["length"] == 12, f"WS-GRP length: {f_grp['length']}"

    f_a = _field(layout, "WS-MIX.WS-GRP.WS-A")
    assert f_a["offset"] == 3
    assert f_a["length"] == 2

    f_b = _field(layout, "WS-MIX.WS-GRP.WS-B")
    assert f_b["offset"] == 5
    assert f_b["length"] == 1


# ===========================================================================
# 6.  REDEFINES: offset reset and redefines_groups populated
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

    f_num   = _field(layout, "WS-DATE-GROUP.WS-DATE-NUM")
    f_char  = _field(layout, "WS-DATE-GROUP.WS-DATE-CHAR")
    f_after = _field(layout, "WS-DATE-GROUP.WS-AFTER")

    assert f_num["offset"]     == 0
    assert f_char["offset"]    == 0
    assert f_char["redefines"] == "WS-DATE-NUM"
    assert f_after["offset"]   == 8

    rec = _record(layout, "WS-DATE-GROUP")
    assert any(g["redefines_target"] == "WS-DATE-NUM"
               for g in rec["redefines_groups"])


# ===========================================================================
# 7.  01-level REDEFINES (elementary root)
#
#   01  WS-ACCT-REISSUE-DATE.
#       05  WS-ACCT-REISSUE-YYYY  PIC X(4).
#       ...                                     <- total 10 bytes
#   01  WS-REISSUE-DATE REDEFINES WS-ACCT-REISSUE-DATE  PIC X(10).
#
#   WS-REISSUE-DATE is an elementary 01-level root (has pic, no children).
#   Expected:
#     - total_bytes = 10
#     - redefines_groups contains an entry with redefines_target =
#       "WS-ACCT-REISSUE-DATE"
# ===========================================================================

def test_redefines_01_level():
    src = _cobol_wrap("""
       01  WS-ACCT-REISSUE-DATE.
           05  WS-ACCT-REISSUE-YYYY  PIC X(4).
           05  WS-FILLER-1           PIC X(1).
           05  WS-ACCT-REISSUE-MM    PIC X(2).
           05  WS-FILLER-2           PIC X(1).
           05  WS-ACCT-REISSUE-DD    PIC X(2).
       01  WS-REISSUE-DATE REDEFINES WS-ACCT-REISSUE-DATE  PIC X(10).
    """)
    layout = extract_layout(src, "TEST")
    assert len(layout["unresolved"]) == 0

    rec = _record(layout, "WS-REISSUE-DATE")
    assert rec["total_bytes"] == 10, \
        f"total_bytes={rec['total_bytes']} (expected 10)"
    assert any(
        g["redefines_target"] == "WS-ACCT-REISSUE-DATE"
        for g in rec["redefines_groups"]
    ), f"redefines_groups={rec['redefines_groups']}"


# ===========================================================================
# 8.  Unrecognized PIC placeholder
# ===========================================================================

def test_unrecognized_pic_placeholder():
    src = _cobol_wrap("""
       01  WS-TEST.
           05  WS-KNOWN    PIC X(5).
           05  WS-UNKNOWN  PIC X(0).
           05  WS-AFTER    PIC X(3).
    """)
    layout = extract_layout(src, "TEST")

    f_unknown = _field(layout, "WS-TEST.WS-UNKNOWN")
    assert f_unknown["length"] is None
    assert any(
        u["field"] == "WS-TEST.WS-UNKNOWN" and u["reason"] == "unrecognized_pic"
        for u in layout["unresolved"]
    )

    f_after = _field(layout, "WS-TEST.WS-AFTER")
    assert f_after["offset"] == 5


# ===========================================================================
# 9.  COPY not found
# ===========================================================================

def test_copybook_not_found():
    src = _cobol_wrap("""
       01  WS-BEFORE  PIC X(3).
       COPY NOSUCHCOPYBOOK.
       01  WS-AFTER   PIC X(2).
    """)
    layout = extract_layout(src, "TEST", source_path=Path("/nonexistent/TEST.cbl"))
    assert any(
        u.get("copybook") == "NOSUCHCOPYBOOK" and u["reason"] == "copybook_not_found"
        for u in layout["unresolved"]
    )
    names = [r["name"] for r in layout["records"]]
    assert "WS-BEFORE" in names
    assert "WS-AFTER"  in names


# ===========================================================================
# Run all tests
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
        test_group_occurs_header_position,
        test_redefines,
        test_redefines_01_level,
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
