#!/usr/bin/env python3
"""
tests/test_data_flow.py  --  Section 2/3 unit tests.
Run with:  python tests/test_data_flow.py
"""

import sys
import unittest
from pathlib import Path

# Make scripts/ importable regardless of working directory.
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from data_flow import (
    classify_statement, extract_paragraphs, _normalise_source,
    is_literal, _join_source_lines, _is_para_header_line,
    _is_area_a_paragraph, _dispatch_inline,
)

_QMAP = {
    'A': [{'field': 'REC-A.A', 'record': 'REC-A', 'copybook': None, 'offset': 0,  'length': 5}],
    'B': [{'field': 'REC-B.B', 'record': 'REC-B', 'copybook': None, 'offset': 5,  'length': 5}],
    'C': [{'field': 'REC-C.C', 'record': 'REC-C', 'copybook': None, 'offset': 10, 'length': 5}],
    'X': [{'field': 'REC-X.X', 'record': 'REC-X', 'copybook': None, 'offset': 0,  'length': 4}],
    'CTR': [{'field': 'WS.CTR', 'record': 'WS',   'copybook': None, 'offset': 0,  'length': 4}],
    'R': [{'field': 'R',       'record': 'R',     'copybook': None, 'offset': 0,  'length': 10}],
    'S': [{'field': 'S',       'record': 'S',     'copybook': None, 'offset': 0,  'length': 10}],
    'F': [{'field': 'F',       'record': 'F',     'copybook': None, 'offset': 0,  'length': 80}],
    'REC': [{'field': 'REC',   'record': 'REC',   'copybook': None, 'offset': 0,  'length': 80}],
    'ACCT-ID': [
        {'field': 'ACCOUNT-RECORD.ACCT-ID', 'record': 'ACCOUNT-RECORD', 'copybook': 'CVACT01Y', 'offset': 0,  'length': 11},
        {'field': 'CARD-RECORD.ACCT-ID',    'record': 'CARD-RECORD',    'copybook': 'CVCRD01Y', 'offset': 5,  'length': 11},
    ],
    'GROUP1': [{'field': 'GROUP1', 'record': 'GROUP1', 'copybook': None, 'offset': 0, 'length': 20}],
    'GROUP2': [{'field': 'GROUP2', 'record': 'GROUP2', 'copybook': None, 'offset': 0, 'length': 20}],
    'OUTFILE-STATUS': [{'field': 'OUTFILE-STATUS', 'record': 'OUTFILE-STATUS',
                        'copybook': None, 'offset': 0, 'length': 2}],
}


def _run(stmt, context=None):
    reads, mutates, unresolved = [], [], []
    ctx = set(context or [])
    classify_statement(1, stmt, _QMAP, ctx, reads, mutates, unresolved)
    return reads, mutates, unresolved


# ---------------------------------------------------------------------------
# _normalise_source column-layout diagnostic tests  (Section 3.1 new)
# ---------------------------------------------------------------------------

class TestNormaliseSourceColumnLayout(unittest.TestCase):
    """
    Verify that _normalise_source uses FIXED COBOL column positions
    (cols 1-6 = sequence, col 7 = indicator, cols 8-72 = code area)
    unconditionally, regardless of whether the sequence area contains
    digits or blanks.
    """

    def test_digit_sequence_area_a_paragraph(self):
        """Line with 6-digit sequence: col 8 content must be text[0]."""
        raw = "000100 0000-ACCTFILE-OPEN.\n"
        result = _normalise_source(raw)
        self.assertEqual(len(result), 1, 'Expected exactly one normalised line')
        lineno, text = result[0]
        self.assertEqual(text, '0000-ACCTFILE-OPEN.',
                         f'code area mismatch: got {repr(text)}')
        self.assertEqual(text[0], '0',
                         'First char must be Area-A content, not a space')

    def test_blank_sequence_area_a_paragraph(self):
        """Line with blank sequence area (7 leading spaces): same result."""
        # cols 1-6 = spaces, col 7 = space (indicator), cols 8+ = paragraph name
        raw = "       0000-ACCTFILE-OPEN.\n"
        result = _normalise_source(raw)
        self.assertEqual(len(result), 1, 'Expected exactly one normalised line')
        lineno, text = result[0]
        self.assertEqual(text, '0000-ACCTFILE-OPEN.',
                         f'code area mismatch: got {repr(text)}')
        self.assertEqual(text[0], '0',
                         'First char must be Area-A content, not a space')

    def test_area_b_line_has_leading_spaces(self):
        """Area-B line must have text[0]==' ' after normalisation."""
        raw = "000040                             WS-REISSUE-DATE.\n"
        result = _normalise_source(raw)
        self.assertEqual(len(result), 1)
        lineno, text = result[0]
        self.assertEqual(text[0], ' ',
                         'Area-B line must start with a space after normalisation')
        self.assertIn('WS-REISSUE-DATE', text)

    def test_comment_line_skipped(self):
        """Lines with '*' in col 7 must be skipped."""
        raw = "000001*This is a comment\n"
        result = _normalise_source(raw)
        self.assertEqual(result, [], 'Comment lines must produce no output')

    def test_short_line_skipped(self):
        """Lines shorter than 7 chars must be silently skipped."""
        raw = "short\n"
        result = _normalise_source(raw)
        self.assertEqual(result, [], 'Short lines must produce no output')


# ---------------------------------------------------------------------------
# Golden integration test: real CBACT01C file on disk  (Section 3.1 new)
# ---------------------------------------------------------------------------

class TestCbact01cRealFileParagraphCount(unittest.TestCase):
    """
    End-to-end gate: read data/raw/cbl/CBACT01C.cbl from disk, run
    extract_paragraphs, and assert exactly 16 paragraphs with the
    exact names known from facts/CBACT01C.json.

    This test MUST exercise the same _normalise_source code path as the
    corpus run.  It is the ground truth for 3.1 gating.
    """

    _CBL = Path('data/raw/cbl/CBACT01C.cbl')
    _EXPECTED = [
        '0000-ACCTFILE-OPEN',
        '1000-ACCTFILE-GET-NEXT',
        '1100-DISPLAY-ACCT-RECORD',
        '1300-POPUL-ACCT-RECORD',
        '1350-WRITE-ACCT-RECORD',
        '1400-POPUL-ARRAY-RECORD',
        '1450-WRITE-ARRY-RECORD',
        '1500-POPUL-VBRC-RECORD',
        '1550-WRITE-VB1-RECORD',
        '1575-WRITE-VB2-RECORD',
        '2000-OUTFILE-OPEN',
        '3000-ARRFILE-OPEN',
        '4000-VBRFILE-OPEN',
        '9000-ACCTFILE-CLOSE',
        '9910-DISPLAY-IO-STATUS',
        '9999-ABEND-PROGRAM',
    ]

    def setUp(self):
        if not self._CBL.exists():
            self.skipTest(f'Real corpus file not found: {self._CBL}')

    def test_cbact01c_paragraph_count_is_16(self):
        raw   = self._CBL.read_text(encoding='utf-8', errors='replace')
        lines = _normalise_source(raw)
        paras = extract_paragraphs(lines)
        names = sorted(k for k in paras if k != '__MAIN__')
        self.assertEqual(
            len(names), 16,
            f'Expected 16 paragraphs, got {len(names)}: {names}'
        )
        for expected in self._EXPECTED:
            self.assertIn(
                expected, names,
                f'Missing paragraph: {expected}  (found: {names})'
            )


# ---------------------------------------------------------------------------
# Section 2 tests (must remain green)
# ---------------------------------------------------------------------------

class TestMoveSingleTarget(unittest.TestCase):
    def test_move_single_target(self):
        r, m, u = _run('MOVE A TO B')
        self.assertEqual([e['field'] for e in r], ['REC-A.A'])
        self.assertEqual([e['field'] for e in m], ['REC-B.B'])
        self.assertEqual(u, [])


class TestMoveMultipleTargets(unittest.TestCase):
    def test_move_multiple_targets(self):
        r, m, u = _run('MOVE A TO B C')
        self.assertEqual([e['field'] for e in r], ['REC-A.A'])
        self.assertEqual([e['field'] for e in m], ['REC-B.B', 'REC-C.C'])
        self.assertEqual(u, [])


class TestMoveCorresponding(unittest.TestCase):
    def test_move_corresponding(self):
        r, m, u = _run('MOVE CORRESPONDING GROUP1 TO GROUP2')
        self.assertIn('GROUP1', [e['field'] for e in r])
        self.assertIn('GROUP2', [e['field'] for e in m])


class TestAddTo(unittest.TestCase):
    def test_add_to(self):
        r, m, u = _run('ADD 1 TO CTR')
        self.assertIn('WS.CTR', [e['field'] for e in m])
        self.assertIn('WS.CTR', [e['field'] for e in r])
        self.assertEqual(u, [])


class TestAddGiving(unittest.TestCase):
    def test_add_giving(self):
        r, m, u = _run('ADD A B GIVING C')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('REC-A.A', rf)
        self.assertIn('REC-B.B', rf)
        self.assertIn('REC-C.C', mf)
        self.assertEqual(u, [])


class TestComputeExpression(unittest.TestCase):
    def test_compute_expression(self):
        r, m, u = _run('COMPUTE X = A + B * C')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('REC-A.A', rf)
        self.assertIn('REC-B.B', rf)
        self.assertIn('REC-C.C', rf)
        self.assertIn('REC-X.X', mf)
        self.assertEqual(u, [])


class TestInitialize(unittest.TestCase):
    def test_initialize(self):
        r, m, u = _run('INITIALIZE R')
        self.assertEqual(r, [])
        self.assertIn('R', [e['field'] for e in m])
        self.assertEqual(u, [])


class TestReadInto(unittest.TestCase):
    def test_read_into(self):
        r, m, u = _run('READ F INTO REC')
        mf = [e['field'] for e in m]
        self.assertIn('F',   mf)
        self.assertIn('REC', mf)


class TestWriteFrom(unittest.TestCase):
    def test_write_from(self):
        r, m, u = _run('WRITE R FROM S')
        self.assertIn('S', [e['field'] for e in r])
        self.assertIn('R', [e['field'] for e in m])


class TestIfConditionReads(unittest.TestCase):
    def test_if_condition_reads(self):
        r, m, u = _run('IF A > B')
        rf = [e['field'] for e in r]
        self.assertIn('REC-A.A', rf)
        self.assertIn('REC-B.B', rf)
        self.assertEqual(m, [])


class TestUnresolvedName(unittest.TestCase):
    def test_unresolved_name(self):
        r, m, u = _run('MOVE GHOST-FIELD TO B')
        self.assertTrue(len(u) > 0)
        self.assertEqual(u[0]['line_no'], 1)
        self.assertIn('GHOST-FIELD', u[0]['reason'])


class TestQualifiedNameDisambiguation(unittest.TestCase):
    def test_qualified_name_disambiguation(self):
        r, m, u = _run('MOVE ACCT-ID TO B', context={'ACCOUNT-RECORD'})
        rf = [e['field'] for e in r]
        self.assertIn('ACCOUNT-RECORD.ACCT-ID', rf)
        self.assertNotIn('CARD-RECORD.ACCT-ID', rf)


class TestDisplayLiteralNoUnresolved(unittest.TestCase):
    def test_display_literal(self):
        r, m, u = _run("DISPLAY 'HELLO WORLD'")
        self.assertEqual(r, [])
        self.assertEqual(u, [])

    def test_display_mixed_literal_and_var(self):
        """DISPLAY literal followed by an identifier: only the identifier is a read."""
        r, m, u = _run("DISPLAY 'VALUE IS:' A")
        rf = [e['field'] for e in r]
        self.assertIn('REC-A.A', rf)
        for entry in u:
            self.assertNotIn('__LIT__', entry.get('reason', ''))
            self.assertNotIn("'VALUE", entry.get('reason', ''))


class TestDisplayLiteralInVerbSplit(unittest.TestCase):
    """
    CBACT01C line 245: the literal 'ACCOUNT FILE WRITE STATUS IS:' contains
    the word WRITE.  _dispatch_inline must not split on that embedded keyword.
    """
    def test_display_literal_containing_verb_keyword(self):
        stmt = "DISPLAY 'ACCOUNT FILE WRITE STATUS IS:'  OUTFILE-STATUS"
        reads, mutates, unresolved = [], [], []
        _dispatch_inline(245, stmt, _QMAP, set(), reads, mutates, unresolved)
        rf = [e['field'] for e in reads]
        self.assertIn('OUTFILE-STATUS', rf)
        self.assertEqual(unresolved, [])


class TestScopeTerminatorsNotParagraphs(unittest.TestCase):
    def test_end_perform_not_paragraph(self):
        # Inline source uses blank sequence area (7 leading spaces = 6 blank
        # seq cols + 1 indicator space), matching files without sequence numbers.
        # _normalise_source treats col 7 (index 6) as indicator unconditionally.
        source = (
            "       PROCEDURE DIVISION.\n"
            "       MAIN-PARA.\n"
            "           PERFORM VARYING I FROM 1 BY 1 UNTIL I > 10\n"
            "               DISPLAY I\n"
            "           END-PERFORM.\n"
            "           GOBACK.\n"
        )
        lines = _normalise_source(source)
        paras = extract_paragraphs(lines)
        para_names = [k for k in paras if k != '__MAIN__']
        self.assertIn('MAIN-PARA', para_names)
        self.assertNotIn('END-PERFORM', para_names)
        self.assertNotIn('GOBACK', para_names)


class TestContinuationJoin(unittest.TestCase):
    def test_move_continuation_not_a_paragraph(self):
        """
        A MOVE target sitting alone on its own line (no 4-digit prefix,
        indented in Area B) must be fused into the MOVE, not become
        a paragraph header.
        """
        source = (
            "       PROCEDURE DIVISION.\n"
            "       1300-POPUL-ACCT-RECORD.\n"
            "           MOVE   ACCT-REISSUE-DATE  TO  CODATECN-INP-DATE\n"
            "                                         WS-REISSUE-DATE.\n"
            "           EXIT.\n"
            "       1350-WRITE-ACCT-RECORD.\n"
            "           WRITE OUT-ACCT-REC.\n"
            "           EXIT.\n"
        )
        lines = _normalise_source(source)
        paras = extract_paragraphs(lines)
        para_names = [k for k in paras if k != '__MAIN__']
        self.assertIn('1300-POPUL-ACCT-RECORD', para_names)
        self.assertIn('1350-WRITE-ACCT-RECORD', para_names)
        self.assertNotIn('WS-REISSUE-DATE', para_names)

    def test_real_paragraphs_all_detected(self):
        """
        Paragraph names from a CBACT01C-style snippet must all be detected,
        and Area-B MOVE continuation targets must NOT become paragraphs.
        """
        expected = [
            '1300-POPUL-ACCT-RECORD',
            '1350-WRITE-ACCT-RECORD',
            '1500-POPUL-VBRC-RECORD',
        ]
        source = (
            "       PROCEDURE DIVISION.\n"
            "       1300-POPUL-ACCT-RECORD.\n"
            "           MOVE ACCT-ID TO CODATECN-INP-DATE\n"
            "                           WS-REISSUE-DATE.\n"
            "           EXIT.\n"
            "       1350-WRITE-ACCT-RECORD.\n"
            "           WRITE OUT-ACCT-REC.\n"
            "           EXIT.\n"
            "       1500-POPUL-VBRC-RECORD.\n"
            "           MOVE ACCT-ID TO VB1-ACCT-ID\n"
            "                           VB2-ACCT-ID.\n"
            "           EXIT.\n"
        )
        lines = _normalise_source(source)
        paras = extract_paragraphs(lines)
        para_names = [k for k in paras if k != '__MAIN__']
        for name in expected:
            self.assertIn(name, para_names)
        self.assertNotIn('WS-REISSUE-DATE', para_names)
        self.assertNotIn('VB2-ACCT-ID', para_names)


# ---------------------------------------------------------------------------
# Section 3.1 NEW tests
# ---------------------------------------------------------------------------

class TestNonPrefixedParagraphDetection(unittest.TestCase):
    """
    Programs that use free-form (non-4-digit) paragraph names must have
    all their paragraphs detected correctly.
    COADM01C pattern: MAIN-PARA., PROCESS-ENTER-KEY., SEND-MENU-SCREEN. etc.
    """
    def test_non_prefixed_paragraphs_detected(self):
        source = (
            "       PROCEDURE DIVISION.\n"
            "       MAIN-PARA.\n"
            "           MOVE A TO B.\n"
            "       PROCESS-RECORDS.\n"
            "           MOVE B TO C.\n"
            "       FINALIZE-PARA.\n"
            "           STOP RUN.\n"
        )
        lines = _normalise_source(source)
        paras = extract_paragraphs(lines)
        para_names = [k for k in paras if k != '__MAIN__']
        self.assertIn('MAIN-PARA', para_names,
                      'MAIN-PARA must be detected as a paragraph')
        self.assertIn('PROCESS-RECORDS', para_names,
                      'PROCESS-RECORDS must be detected as a paragraph')
        self.assertIn('FINALIZE-PARA', para_names,
                      'FINALIZE-PARA must be detected as a paragraph')
        self.assertEqual(len(para_names), 3,
                         f'Expected 3 paragraphs, got: {para_names}')


class TestAreaBContinuationStillFused(unittest.TestCase):
    """
    An Area-B line (indented) that looks like a paragraph header must be
    fused as a continuation of the preceding open statement, NOT treated
    as a new paragraph.
    """
    def test_indented_ws_reissue_date_fused(self):
        source = (
            "       PROCEDURE DIVISION.\n"
            "       MAIN-PARA.\n"
            "           MOVE ACCT-DATE TO CODATECN-DATE\n"
            "                            WS-REISSUE-DATE.\n"
            "       NEXT-PARA.\n"
            "           STOP RUN.\n"
        )
        lines = _normalise_source(source)
        paras = extract_paragraphs(lines)
        para_names = [k for k in paras if k != '__MAIN__']
        self.assertNotIn('WS-REISSUE-DATE', para_names,
                         'Indented WS-REISSUE-DATE. must be fused as continuation')
        self.assertIn('MAIN-PARA', para_names)
        self.assertIn('NEXT-PARA', para_names)
        self.assertEqual(len(para_names), 2)


class TestSectionHeaderNotFalseParagraph(unittest.TestCase):
    """
    WORKING-STORAGE SECTION. and similar section headers must never be
    detected as paragraphs.  Called directly with stripped text (no leading
    spaces) to test the exclusion logic independently of the Area-A rule.
    """
    def test_working_storage_section_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('WORKING-STORAGE SECTION.'))

    def test_linkage_section_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('LINKAGE SECTION.'))

    def test_file_section_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('FILE SECTION.'))

    def test_procedure_section_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('1000-MAIN SECTION.'))


class TestDivisionHeaderNotParagraph(unittest.TestCase):
    """
    Division headers must never be detected as paragraphs.
    Called directly with stripped text.
    """
    def test_procedure_division_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('PROCEDURE DIVISION.'))

    def test_data_division_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('DATA DIVISION.'))

    def test_identification_division_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('IDENTIFICATION DIVISION.'))

    def test_procedure_division_using_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('PROCEDURE DIVISION USING X.'))


class TestLevel01NotParagraph(unittest.TestCase):
    """
    Level-number data items must never be detected as paragraphs.
    Called directly with stripped text.
    """
    def test_level_01_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('01 WS-REC.'))

    def test_level_77_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('77 WS-CTR.'))

    def test_level_05_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('05 FILLER.'))


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(__import__('__main__'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
