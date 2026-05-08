#!/usr/bin/env python3
"""
tests/test_data_flow.py  --  Section 2/3 unit tests.
Run with:  python tests/test_data_flow.py
"""

import sys
import unittest
from pathlib import Path

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
        source = """
       PROCEDURE DIVISION.
       MAIN-PARA.
           PERFORM VARYING I FROM 1 BY 1 UNTIL I > 10
               DISPLAY I
           END-PERFORM.
           GOBACK.
"""
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
        source = """
       PROCEDURE DIVISION.
       1300-POPUL-ACCT-RECORD.
           MOVE   ACCT-REISSUE-DATE  TO  CODATECN-INP-DATE
                                         WS-REISSUE-DATE.
           EXIT.
       1350-WRITE-ACCT-RECORD.
           WRITE OUT-ACCT-REC.
           EXIT.
"""
        lines = _normalise_source(source)
        paras = extract_paragraphs(lines)
        para_names = [k for k in paras if k != '__MAIN__']
        self.assertIn('1300-POPUL-ACCT-RECORD', para_names)
        self.assertIn('1350-WRITE-ACCT-RECORD', para_names)
        self.assertNotIn('WS-REISSUE-DATE', para_names)

    def test_real_paragraphs_all_detected(self):
        """
        All 16 CardDemo CBACT01C paragraph names must be detected when
        processing the inline snippet.
        """
        expected = [
            '1300-POPUL-ACCT-RECORD',
            '1350-WRITE-ACCT-RECORD',
            '1500-POPUL-VBRC-RECORD',
        ]
        source = """
       PROCEDURE DIVISION.
       1300-POPUL-ACCT-RECORD.
           MOVE ACCT-ID TO CODATECN-INP-DATE
                           WS-REISSUE-DATE.
           EXIT.
       1350-WRITE-ACCT-RECORD.
           WRITE OUT-ACCT-REC.
           EXIT.
       1500-POPUL-VBRC-RECORD.
           MOVE ACCT-ID TO VB1-ACCT-ID
                           VB2-ACCT-ID.
           EXIT.
"""
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
            "000001 PROCEDURE DIVISION.\n"
            "000002 MAIN-PARA.\n"
            "000003            MOVE A TO B.\n"
            "000004 PROCESS-RECORDS.\n"
            "000005            MOVE B TO C.\n"
            "000006 FINALIZE-PARA.\n"
            "000007            STOP RUN.\n"
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
        # WS-REISSUE-DATE. is indented (Area B) — must not become a paragraph.
        source = (
            "000001 PROCEDURE DIVISION.\n"
            "000002 MAIN-PARA.\n"
            "000003            MOVE ACCT-DATE TO CODATECN-DATE\n"
            "000004                             WS-REISSUE-DATE.\n"
            "000005 NEXT-PARA.\n"
            "000006            STOP RUN.\n"
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
    detected as paragraphs.  They appear in Area A and match the
    superficial pattern but must be excluded.
    """
    def test_working_storage_section_not_paragraph(self):
        self.assertFalse(
            _is_area_a_paragraph('WORKING-STORAGE SECTION.'),
            'WORKING-STORAGE SECTION. must not be a paragraph header'
        )

    def test_linkage_section_not_paragraph(self):
        self.assertFalse(
            _is_area_a_paragraph('LINKAGE SECTION.'),
            'LINKAGE SECTION. must not be a paragraph header'
        )

    def test_file_section_not_paragraph(self):
        self.assertFalse(
            _is_area_a_paragraph('FILE SECTION.'),
            'FILE SECTION. must not be a paragraph header'
        )

    def test_procedure_section_not_paragraph(self):
        # A user-defined section inside PROCEDURE DIVISION: 1000-MAIN SECTION.
        # Policy (V12_VALIDATION_GATES.md): SECTION headers are NOT paragraphs.
        self.assertFalse(
            _is_area_a_paragraph('1000-MAIN SECTION.'),
            '1000-MAIN SECTION. is a SECTION header, not a paragraph'
        )


class TestDivisionHeaderNotParagraph(unittest.TestCase):
    """
    Division header lines (PROCEDURE DIVISION., DATA DIVISION. etc.) must
    never be detected as paragraphs, including forms with USING clauses.
    """
    def test_procedure_division_not_paragraph(self):
        self.assertFalse(
            _is_area_a_paragraph('PROCEDURE DIVISION.'),
            'PROCEDURE DIVISION. must not be a paragraph'
        )

    def test_data_division_not_paragraph(self):
        self.assertFalse(
            _is_area_a_paragraph('DATA DIVISION.'),
            'DATA DIVISION. must not be a paragraph'
        )

    def test_identification_division_not_paragraph(self):
        self.assertFalse(
            _is_area_a_paragraph('IDENTIFICATION DIVISION.'),
            'IDENTIFICATION DIVISION. must not be a paragraph'
        )

    def test_procedure_division_using_not_paragraph(self):
        # PROCEDURE DIVISION USING X.  -- does not even match _PARA_HEADER_RE
        # (multiple tokens before period), but we verify defensively.
        self.assertFalse(
            _is_area_a_paragraph('PROCEDURE DIVISION USING X.'),
            'PROCEDURE DIVISION USING X. must not be a paragraph'
        )


class TestLevel01NotParagraph(unittest.TestCase):
    """
    Level-number data items (01 WS-REC., 05 FILLER., 77 WS-CTR.) start
    in Area A but are data definitions, never paragraph names.
    """
    def test_level_01_not_paragraph(self):
        self.assertFalse(
            _is_area_a_paragraph('01 WS-REC.'),
            '01 WS-REC. is a data item, not a paragraph'
        )

    def test_level_77_not_paragraph(self):
        self.assertFalse(
            _is_area_a_paragraph('77 WS-CTR.'),
            '77 WS-CTR. is a data item, not a paragraph'
        )

    def test_level_05_not_paragraph(self):
        # 05 starts in Area B normally, but test defensively
        self.assertFalse(
            _is_area_a_paragraph('05 FILLER.'),
            '05 FILLER. is a data item, not a paragraph'
        )


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(__import__('__main__'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
