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
    # 3.2 CALL test fixtures
    'WS-DATE-FIELDS': [{'field': 'WS.WS-DATE-FIELDS', 'record': 'WS',
                        'copybook': None, 'offset': 0, 'length': 8}],
    'WS-RETURN-CODE': [{'field': 'WS.WS-RETURN-CODE', 'record': 'WS',
                        'copybook': None, 'offset': 8, 'length': 4}],
    'WS-INPUT-DATE':  [{'field': 'WS.WS-INPUT-DATE',  'record': 'WS',
                        'copybook': None, 'offset': 0, 'length': 8}],
    'WS-OUTPUT-DATE': [{'field': 'WS.WS-OUTPUT-DATE', 'record': 'WS',
                        'copybook': None, 'offset': 8, 'length': 8}],
    'WS-RC':          [{'field': 'WS.WS-RC',          'record': 'WS',
                        'copybook': None, 'offset': 12, 'length': 4}],
}


def _run(stmt, context=None):
    reads, mutates, unresolved = [], [], []
    ctx = set(context or [])
    classify_statement(1, stmt, _QMAP, ctx, reads, mutates, unresolved)
    return reads, mutates, unresolved


def _run_call(stmt, context=None):
    """Run classify_statement and also return call_targets."""
    reads, mutates, unresolved, call_targets = [], [], [], []
    ctx = set(context or [])
    classify_statement(1, stmt, _QMAP, ctx, reads, mutates, unresolved, call_targets)
    return reads, mutates, unresolved, call_targets


# ---------------------------------------------------------------------------
# _normalise_source column-layout diagnostic tests  (Section 3.1)
# ---------------------------------------------------------------------------

class TestNormaliseSourceColumnLayout(unittest.TestCase):
    def test_digit_sequence_area_a_paragraph(self):
        raw = "000100 0000-ACCTFILE-OPEN.\n"
        result = _normalise_source(raw)
        self.assertEqual(len(result), 1)
        lineno, text = result[0]
        self.assertEqual(text, '0000-ACCTFILE-OPEN.')
        self.assertEqual(text[0], '0')

    def test_blank_sequence_area_a_paragraph(self):
        raw = "       0000-ACCTFILE-OPEN.\n"
        result = _normalise_source(raw)
        self.assertEqual(len(result), 1)
        lineno, text = result[0]
        self.assertEqual(text, '0000-ACCTFILE-OPEN.')
        self.assertEqual(text[0], '0')

    def test_area_b_line_has_leading_spaces(self):
        raw = "000040                             WS-REISSUE-DATE.\n"
        result = _normalise_source(raw)
        self.assertEqual(len(result), 1)
        lineno, text = result[0]
        self.assertEqual(text[0], ' ')
        self.assertIn('WS-REISSUE-DATE', text)

    def test_comment_line_skipped(self):
        raw = "000001*This is a comment\n"
        result = _normalise_source(raw)
        self.assertEqual(result, [])

    def test_short_line_skipped(self):
        raw = "short\n"
        result = _normalise_source(raw)
        self.assertEqual(result, [])


# ---------------------------------------------------------------------------
# Golden integration test: real CBACT01C file on disk  (Section 3.1)
# ---------------------------------------------------------------------------

class TestCbact01cRealFileParagraphCount(unittest.TestCase):
    _CBL = Path('data/raw/cbl/CBACT01C.cbl')
    _EXPECTED = [
        '0000-ACCTFILE-OPEN', '1000-ACCTFILE-GET-NEXT', '1100-DISPLAY-ACCT-RECORD',
        '1300-POPUL-ACCT-RECORD', '1350-WRITE-ACCT-RECORD', '1400-POPUL-ARRAY-RECORD',
        '1450-WRITE-ARRY-RECORD', '1500-POPUL-VBRC-RECORD', '1550-WRITE-VB1-RECORD',
        '1575-WRITE-VB2-RECORD', '2000-OUTFILE-OPEN', '3000-ARRFILE-OPEN',
        '4000-VBRFILE-OPEN', '9000-ACCTFILE-CLOSE', '9910-DISPLAY-IO-STATUS',
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
        self.assertEqual(len(names), 16, f'Expected 16, got {len(names)}: {names}')
        for expected in self._EXPECTED:
            self.assertIn(expected, names)


# ---------------------------------------------------------------------------
# Section 2 tests
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
    def test_display_literal_containing_verb_keyword(self):
        stmt = "DISPLAY 'ACCOUNT FILE WRITE STATUS IS:'  OUTFILE-STATUS"
        reads, mutates, unresolved = [], [], []
        _dispatch_inline(245, stmt, _QMAP, set(), reads, mutates, unresolved)
        rf = [e['field'] for e in reads]
        self.assertIn('OUTFILE-STATUS', rf)
        self.assertEqual(unresolved, [])


class TestScopeTerminatorsNotParagraphs(unittest.TestCase):
    def test_end_perform_not_paragraph(self):
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
        expected = ['1300-POPUL-ACCT-RECORD', '1350-WRITE-ACCT-RECORD', '1500-POPUL-VBRC-RECORD']
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


class TestNonPrefixedParagraphDetection(unittest.TestCase):
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
        self.assertIn('MAIN-PARA', para_names)
        self.assertIn('PROCESS-RECORDS', para_names)
        self.assertIn('FINALIZE-PARA', para_names)
        self.assertEqual(len(para_names), 3)


class TestAreaBContinuationStillFused(unittest.TestCase):
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
        self.assertNotIn('WS-REISSUE-DATE', para_names)
        self.assertIn('MAIN-PARA', para_names)
        self.assertIn('NEXT-PARA', para_names)
        self.assertEqual(len(para_names), 2)


class TestSectionHeaderNotFalseParagraph(unittest.TestCase):
    def test_working_storage_section_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('WORKING-STORAGE SECTION.'))

    def test_linkage_section_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('LINKAGE SECTION.'))

    def test_file_section_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('FILE SECTION.'))

    def test_procedure_section_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('1000-MAIN SECTION.'))


class TestDivisionHeaderNotParagraph(unittest.TestCase):
    def test_procedure_division_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('PROCEDURE DIVISION.'))

    def test_data_division_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('DATA DIVISION.'))

    def test_identification_division_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('IDENTIFICATION DIVISION.'))

    def test_procedure_division_using_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('PROCEDURE DIVISION USING X.'))


class TestLevel01NotParagraph(unittest.TestCase):
    def test_level_01_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('01 WS-REC.'))

    def test_level_77_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('77 WS-CTR.'))

    def test_level_05_not_paragraph(self):
        self.assertFalse(_is_area_a_paragraph('05 FILLER.'))


# ---------------------------------------------------------------------------
# Section 3.2 tests -- CALL USING mode-aware classification
# ---------------------------------------------------------------------------

class TestCallUsingByReference(unittest.TestCase):
    """
    BY REFERENCE (default mode when no keyword given, and explicit BY REFERENCE):
    operand must appear in BOTH reads AND mutates.
    """
    def test_call_by_reference_default(self):
        """No BY keyword -> defaults to BY REFERENCE -> read + mutate."""
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING WS-DATE-FIELDS')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-DATE-FIELDS', rf, 'BY REFERENCE default must produce a read')
        self.assertIn('WS.WS-DATE-FIELDS', mf, 'BY REFERENCE default must produce a mutate')
        self.assertEqual(u, [], f'Unexpected unresolved: {u}')

    def test_call_explicit_by_reference(self):
        """Explicit BY REFERENCE -> read + mutate."""
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING BY REFERENCE WS-DATE-FIELDS')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-DATE-FIELDS', rf)
        self.assertIn('WS.WS-DATE-FIELDS', mf)
        self.assertEqual(u, [])

    def test_call_target_recorded(self):
        """Call target must be captured in call_targets."""
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING WS-DATE-FIELDS')
        self.assertIn('COBDATFT', ct, f'Expected COBDATFT in call_targets, got {ct}')


class TestCallUsingByContent(unittest.TestCase):
    """
    BY CONTENT -> read only, NOT mutate.
    """
    def test_call_by_content_read_only(self):
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING BY CONTENT WS-INPUT-DATE')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-INPUT-DATE', rf, 'BY CONTENT must produce a read')
        self.assertNotIn('WS.WS-INPUT-DATE', mf, 'BY CONTENT must NOT produce a mutate')
        self.assertEqual(u, [])


class TestCallUsingByValue(unittest.TestCase):
    """
    BY VALUE -> read only, NOT mutate.
    """
    def test_call_by_value_read_only(self):
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING BY VALUE WS-INPUT-DATE')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-INPUT-DATE', rf, 'BY VALUE must produce a read')
        self.assertNotIn('WS.WS-INPUT-DATE', mf, 'BY VALUE must NOT produce a mutate')
        self.assertEqual(u, [])


class TestCallReturning(unittest.TestCase):
    """
    RETURNING -> mutate only, NOT read.
    """
    def test_call_returning_mutate_only(self):
        """CALL with RETURNING and NO USING: identifier is mutate only."""
        r, m, u, ct = _run_call("CALL 'X' RETURNING WS-RETURN-CODE")
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertNotIn('WS.WS-RETURN-CODE', rf, 'RETURNING must NOT produce a read')
        self.assertIn('WS.WS-RETURN-CODE', mf, 'RETURNING must produce a mutate')
        self.assertEqual(u, [])

    def test_call_using_then_returning(self):
        """Mixed: USING BY REFERENCE (read+mutate) then RETURNING (mutate only)."""
        r, m, u, ct = _run_call(
            'CALL \'COBDATFT\' USING BY REFERENCE WS-INPUT-DATE RETURNING WS-RETURN-CODE'
        )
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-INPUT-DATE', rf)
        self.assertIn('WS.WS-INPUT-DATE', mf)
        self.assertNotIn('WS.WS-RETURN-CODE', rf)
        self.assertIn('WS.WS-RETURN-CODE', mf)
        self.assertEqual(u, [])

    def test_call_returning_no_using_call_target_recorded(self):
        """CALL 'ABENDPGM' RETURNING WS-RC: target captured + operand mutated."""
        r, m, u, ct = _run_call("CALL 'ABENDPGM' RETURNING WS-RC")
        mf = [e['field'] for e in m]
        self.assertIn('ABENDPGM', ct,
                      f'Expected ABENDPGM in call_targets, got {ct}')
        self.assertIn('WS.WS-RC', mf,
                      f'Expected WS.WS-RC in mutates, got {mf}')
        self.assertEqual(u, [])


class TestCallMixedModes(unittest.TestCase):
    """
    Multiple BY mode switches within a single CALL USING clause.
    """
    def test_call_mixed_reference_and_content(self):
        """
        CALL 'X' USING BY REFERENCE WS-OUTPUT-DATE
                       BY CONTENT   WS-INPUT-DATE
        WS-OUTPUT-DATE -> read + mutate
        WS-INPUT-DATE  -> read only
        """
        r, m, u, ct = _run_call(
            "CALL 'X' USING BY REFERENCE WS-OUTPUT-DATE BY CONTENT WS-INPUT-DATE"
        )
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-OUTPUT-DATE', rf)
        self.assertIn('WS.WS-OUTPUT-DATE', mf)
        self.assertIn('WS.WS-INPUT-DATE', rf)
        self.assertNotIn('WS.WS-INPUT-DATE', mf)
        self.assertEqual(u, [])


class TestCallGraphCbact01c(unittest.TestCase):
    """
    End-to-end: CBACT01C.call_graph must include COBDATFT as a called program.
    """
    _CBL = Path('data/raw/cbl/CBACT01C.cbl')

    def setUp(self):
        if not self._CBL.exists():
            self.skipTest(f'Real corpus file not found: {self._CBL}')

    def test_call_graph_contains_cobdatft(self):
        import importlib
        import sys as _sys
        from pathlib import Path as P
        sys_path_backup = _sys.path[:]
        _sys.path.insert(0, str(P(__file__).parent.parent / 'scripts'))
        df = importlib.import_module('data_flow')
        _sys.path[:] = sys_path_backup

        layout = P('data/byte_layouts/CBACT01C.json')
        result = df.extract_data_flow(self._CBL, layout)
        cg = result.get('call_graph', {})
        called = cg.get('CBACT01C', [])
        self.assertIn(
            'COBDATFT', called,
            f'Expected COBDATFT in call_graph[CBACT01C], got: {called}'
        )


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(__import__('__main__'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
