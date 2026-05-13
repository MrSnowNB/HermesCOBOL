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
    # 3.3 verb test fixtures
    'TALLY-CTR':      [{'field': 'WS.TALLY-CTR',      'record': 'WS',
                        'copybook': None, 'offset': 0, 'length': 4}],
    'SORT-FILE':      [{'field': 'SORT-FILE',          'record': 'SORT-FILE',
                        'copybook': None, 'offset': 0, 'length': 100}],
    'IN-FILE':        [{'field': 'IN-FILE',            'record': 'IN-FILE',
                        'copybook': None, 'offset': 0, 'length': 100}],
    'OUT-FILE':       [{'field': 'OUT-FILE',           'record': 'OUT-FILE',
                        'copybook': None, 'offset': 0, 'length': 100}],
    'SORT-REC':       [{'field': 'SORT-REC',           'record': 'SORT-REC',
                        'copybook': None, 'offset': 0, 'length': 100}],
    'WS-SOURCE':      [{'field': 'WS.WS-SOURCE',       'record': 'WS',
                        'copybook': None, 'offset': 0, 'length': 20}],
    'RETURN-FILE':    [{'field': 'RETURN-FILE',        'record': 'RETURN-FILE',
                        'copybook': None, 'offset': 0, 'length': 100}],
    'WS-INTO':        [{'field': 'WS.WS-INTO',         'record': 'WS',
                        'copybook': None, 'offset': 0, 'length': 20}],
}


def _run(stmt, context=None):
    reads, mutates, unresolved = [], [], []
    ctx = set(context or [])
    classify_statement(1, stmt, _QMAP, ctx, reads, mutates, unresolved)
    return reads, mutates, unresolved


def _run_call(stmt, context=None):
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
    def test_call_by_reference_default(self):
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING WS-DATE-FIELDS')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-DATE-FIELDS', rf)
        self.assertIn('WS.WS-DATE-FIELDS', mf)
        self.assertEqual(u, [])

    def test_call_explicit_by_reference(self):
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING BY REFERENCE WS-DATE-FIELDS')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-DATE-FIELDS', rf)
        self.assertIn('WS.WS-DATE-FIELDS', mf)
        self.assertEqual(u, [])

    def test_call_target_recorded(self):
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING WS-DATE-FIELDS')
        self.assertIn('COBDATFT', ct)


class TestCallUsingByContent(unittest.TestCase):
    def test_call_by_content_read_only(self):
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING BY CONTENT WS-INPUT-DATE')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-INPUT-DATE', rf)
        self.assertNotIn('WS.WS-INPUT-DATE', mf)
        self.assertEqual(u, [])


class TestCallUsingByValue(unittest.TestCase):
    def test_call_by_value_read_only(self):
        r, m, u, ct = _run_call('CALL \'COBDATFT\' USING BY VALUE WS-INPUT-DATE')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('WS.WS-INPUT-DATE', rf)
        self.assertNotIn('WS.WS-INPUT-DATE', mf)
        self.assertEqual(u, [])


class TestCallReturning(unittest.TestCase):
    def test_call_returning_mutate_only(self):
        r, m, u, ct = _run_call("CALL 'X' RETURNING WS-RETURN-CODE")
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertNotIn('WS.WS-RETURN-CODE', rf)
        self.assertIn('WS.WS-RETURN-CODE', mf)
        self.assertEqual(u, [])

    def test_call_using_then_returning(self):
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
        r, m, u, ct = _run_call("CALL 'ABENDPGM' RETURNING WS-RC")
        mf = [e['field'] for e in m]
        self.assertIn('ABENDPGM', ct)
        self.assertIn('WS.WS-RC', mf)
        self.assertEqual(u, [])


class TestCallMixedModes(unittest.TestCase):
    def test_call_mixed_reference_and_content(self):
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
        called = result.get('call_graph', {}).get('CBACT01C', [])
        self.assertIn('COBDATFT', called)


# ---------------------------------------------------------------------------
# Section 3.3 tests -- INSPECT, SORT, MERGE, RELEASE, RETURN
# ---------------------------------------------------------------------------

class TestInspect(unittest.TestCase):
    """
    INSPECT source [TALLYING tally FOR ...]
    source -> read; tally -> mutate
    """
    def test_inspect_tallying(self):
        r, m, u = _run('INSPECT A TALLYING TALLY-CTR FOR ALL SPACES')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('REC-A.A',    rf, 'INSPECT source must be a read')
        self.assertIn('WS.TALLY-CTR', mf, 'INSPECT TALLYING target must be a mutate')
        self.assertEqual(u, [], f'Unexpected unresolved: {u}')

    def test_inspect_replacing(self):
        """
        INSPECT source REPLACING ALL 'X' BY 'Y'
        source -> read; source is also mutated in-place (REPLACING modifies it)
        """
        r, m, u = _run("INSPECT A REPLACING ALL 'X' BY 'Y'")
        rf = [e['field'] for e in r]
        self.assertIn('REC-A.A', rf, 'INSPECT source must be a read')
        # unresolved may be empty; we do not require a mutate for REPLACING
        # (target is the same as source but REPLACING is in-place, handled by read)


class TestSort(unittest.TestCase):
    """
    SORT sort-file ON ASCENDING KEY key USING in-file GIVING out-file
    sort-file -> mutate; in-file -> read; out-file -> mutate
    """
    def test_sort_using_giving(self):
        r, m, u = _run('SORT SORT-FILE ON ASCENDING KEY A USING IN-FILE GIVING OUT-FILE')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('SORT-FILE', mf, 'SORT sort-file must be a mutate')
        self.assertIn('IN-FILE',   rf, 'SORT USING file must be a read')
        self.assertIn('OUT-FILE',  mf, 'SORT GIVING file must be a mutate')
        self.assertEqual(u, [], f'Unexpected unresolved: {u}')


class TestMerge(unittest.TestCase):
    """
    MERGE sort-file ON ASCENDING KEY key USING in-file GIVING out-file
    sort-file -> mutate; in-file -> read; out-file -> mutate
    """
    def test_merge_using_giving(self):
        r, m, u = _run('MERGE SORT-FILE ON ASCENDING KEY A USING IN-FILE GIVING OUT-FILE')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('SORT-FILE', mf, 'MERGE sort-file must be a mutate')
        self.assertIn('IN-FILE',   rf, 'MERGE USING file must be a read')
        self.assertIn('OUT-FILE',  mf, 'MERGE GIVING file must be a mutate')
        self.assertEqual(u, [], f'Unexpected unresolved: {u}')


class TestRelease(unittest.TestCase):
    """
    RELEASE record-name [FROM source]
    record-name -> mutate; source -> read
    """
    def test_release_from(self):
        r, m, u = _run('RELEASE SORT-REC FROM WS-SOURCE')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('SORT-REC',   mf, 'RELEASE record must be a mutate')
        self.assertIn('WS.WS-SOURCE', rf, 'RELEASE FROM source must be a read')
        self.assertEqual(u, [], f'Unexpected unresolved: {u}')

    def test_release_no_from(self):
        r, m, u = _run('RELEASE SORT-REC')
        mf = [e['field'] for e in m]
        self.assertIn('SORT-REC', mf, 'RELEASE record must be a mutate even without FROM')
        self.assertEqual(u, [])


class TestReturn(unittest.TestCase):
    """
    RETURN file-name [INTO target]
    file-name -> mutate; INTO target -> mutate
    """
    def test_return_into(self):
        r, m, u = _run('RETURN RETURN-FILE INTO WS-INTO')
        mf = [e['field'] for e in m]
        self.assertIn('RETURN-FILE', mf, 'RETURN file must be a mutate')
        self.assertIn('WS.WS-INTO',  mf, 'RETURN INTO target must be a mutate')
        self.assertEqual(u, [], f'Unexpected unresolved: {u}')

    def test_return_no_into(self):
        r, m, u = _run('RETURN RETURN-FILE')
        mf = [e['field'] for e in m]
        self.assertIn('RETURN-FILE', mf, 'RETURN file must be a mutate without INTO')
        self.assertEqual(u, [])


# ---------------------------------------------------------------------------
# Section 3.4 tests -- section_name threading and SCHEMA_VERSION 1.3
# ---------------------------------------------------------------------------

def _extract_synthetic(source: str) -> dict:
    """
    Run extract_data_flow on an in-memory synthetic COBOL source string.
    Uses a temporary file so extract_data_flow's Path-based API is satisfied.
    No byte_layouts file is provided (empty qmap path); all fields will be
    unresolved, which is fine -- these tests only inspect structural metadata.
    """
    import importlib
    import tempfile
    import sys as _sys
    from pathlib import Path as P

    sys_path_backup = _sys.path[:]
    _sys.path.insert(0, str(P(__file__).parent.parent / 'scripts'))
    df = importlib.import_module('data_flow')
    _sys.path[:] = sys_path_backup

    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.cbl', delete=False, encoding='utf-8'
    ) as fh:
        fh.write(source)
        tmp_path = P(fh.name)

    try:
        # Pass a non-existent layout path so build_qmap returns empty dicts
        result = df.extract_data_flow(tmp_path, P('/nonexistent/layout.json'))
    finally:
        tmp_path.unlink(missing_ok=True)

    return result


class TestSectionNameSchema(unittest.TestCase):
    """
    Section 3.4: section_name threading and SCHEMA_VERSION bump to "1.3".

    All fixtures use blank-sequence-area inline source format (Section 3.1 lock):
      cols 1-6  : spaces (sequence area)
      col  7    : space  (indicator)
      cols 8-72 : code area (Area A at col 8, Area B at col 12+)
    """

    # ------------------------------------------------------------------
    # Shared synthetic sources
    # ------------------------------------------------------------------

    # One paragraph before any SECTION header
    _SRC_NO_SECTION = (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. TESTSECT.\n"
        "       PROCEDURE DIVISION.\n"
        "       FIRST-PARA.\n"
        "           CONTINUE.\n"
    )

    # One SECTION containing one paragraph
    _SRC_ONE_SECTION = (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. TESTSECT.\n"
        "       PROCEDURE DIVISION.\n"
        "       ALPHA SECTION.\n"
        "       ALPHA-PARA.\n"
        "           CONTINUE.\n"
    )

    # Two SECTIONs each with one paragraph
    _SRC_TWO_SECTIONS = (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. TESTSECT.\n"
        "       PROCEDURE DIVISION.\n"
        "       ALPHA SECTION.\n"
        "       P1.\n"
        "           CONTINUE.\n"
        "       BETA SECTION.\n"
        "       P2.\n"
        "           CONTINUE.\n"
    )

    # Duplicate paragraph name across two sections
    _SRC_DUPLICATE_PARA = (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. TESTSECT.\n"
        "       PROCEDURE DIVISION.\n"
        "       ALPHA SECTION.\n"
        "       READ-RECORD.\n"
        "           CONTINUE.\n"
        "       BETA SECTION.\n"
        "       READ-RECORD.\n"
        "           CONTINUE.\n"
    )

    # Back-to-back SECTIONs: A has no paragraphs, B has one
    _SRC_BACK_TO_BACK = (
        "       IDENTIFICATION DIVISION.\n"
        "       PROGRAM-ID. TESTSECT.\n"
        "       PROCEDURE DIVISION.\n"
        "       ALPHA SECTION.\n"
        "       BETA SECTION.\n"
        "       BETA-PARA.\n"
        "           CONTINUE.\n"
    )

    # ------------------------------------------------------------------
    # Test 1: paragraph before any SECTION has section_name == None
    # ------------------------------------------------------------------

    def test_paragraph_before_any_section_has_null_section_name(self):
        """
        A paragraph appearing before any SECTION header in PROCEDURE DIVISION
        must have section_name == None (JSON null sentinel).
        Step 2 must add section_name threading to extract_paragraphs / extract_data_flow.
        """
        result = _extract_synthetic(self._SRC_NO_SECTION)
        pdf = result.get('paragraph_data_flow', {})
        self.assertIn(
            'FIRST-PARA', pdf,
            f'Expected FIRST-PARA in paragraph_data_flow, got keys: {list(pdf.keys())}'
        )
        entry = pdf['FIRST-PARA']
        self.assertIn(
            'section_name', entry,
            'paragraph_data_flow entry must contain section_name key (Step 2 adds this)'
        )
        self.assertIsNone(
            entry['section_name'],
            f'Paragraph before any SECTION must have section_name=None, got: {entry["section_name"]}'
        )

    # ------------------------------------------------------------------
    # Test 2: paragraph under a SECTION has its section's name
    # ------------------------------------------------------------------

    def test_paragraph_under_section_has_section_name(self):
        """
        A paragraph appearing after a SECTION header must have section_name
        equal to the section name (without the trailing SECTION keyword,
        without the trailing period).
        """
        result = _extract_synthetic(self._SRC_ONE_SECTION)
        pdf = result.get('paragraph_data_flow', {})
        self.assertIn(
            'ALPHA-PARA', pdf,
            f'Expected ALPHA-PARA in paragraph_data_flow, got: {list(pdf.keys())}'
        )
        entry = pdf['ALPHA-PARA']
        self.assertIn(
            'section_name', entry,
            'paragraph_data_flow entry must contain section_name key'
        )
        self.assertEqual(
            entry['section_name'], 'ALPHA',
            f'Expected section_name="ALPHA", got: {entry.get("section_name")}'
        )

    # ------------------------------------------------------------------
    # Test 3: paragraphs under two different sections have distinct names
    # ------------------------------------------------------------------

    def test_paragraphs_under_two_different_sections_have_distinct_section_names(self):
        """
        P1 under ALPHA SECTION -> section_name='ALPHA'
        P2 under BETA SECTION  -> section_name='BETA'
        """
        result = _extract_synthetic(self._SRC_TWO_SECTIONS)
        pdf = result.get('paragraph_data_flow', {})

        self.assertIn('P1', pdf, f'Expected P1 in pdf, got: {list(pdf.keys())}')
        self.assertIn('P2', pdf, f'Expected P2 in pdf, got: {list(pdf.keys())}')

        self.assertIn('section_name', pdf['P1'], 'P1 entry must have section_name')
        self.assertIn('section_name', pdf['P2'], 'P2 entry must have section_name')

        self.assertEqual(
            pdf['P1']['section_name'], 'ALPHA',
            f'P1 must have section_name="ALPHA", got: {pdf["P1"].get("section_name")}'
        )
        self.assertEqual(
            pdf['P2']['section_name'], 'BETA',
            f'P2 must have section_name="BETA", got: {pdf["P2"].get("section_name")}'
        )
        self.assertNotEqual(
            pdf['P1']['section_name'], pdf['P2']['section_name'],
            'P1 and P2 must have different section_name values'
        )

    # ------------------------------------------------------------------
    # Test 4: duplicate paragraph name across sections is disambiguated
    # ------------------------------------------------------------------

    def test_duplicate_paragraph_name_across_sections_is_disambiguated_by_section(self):
        """
        ALPHA SECTION has READ-RECORD; BETA SECTION also has READ-RECORD.
        The output must carry evidence of both occurrences with different section_name.

        TODO (Step 2): Choose disambiguation key representation.
        Options:
          a) paragraph_data_flow keyed as "ALPHA.READ-RECORD" / "BETA.READ-RECORD"
          b) paragraph_data_flow values include a list-of-entries form
        The test below is intentionally a placeholder that forces Step 2 to
        define the representation before this can pass.
        """
        src = (
            "       IDENTIFICATION DIVISION.\n"
            "       PROGRAM-ID. TESTPROG.\n"
            "       PROCEDURE DIVISION.\n"
            "       ALPHA SECTION.\n"
            "       READ-RECORD.\n"
            "           MOVE 1 TO WS-VAR.\n"
            "       BETA SECTION.\n"
            "       READ-RECORD.\n"
            "           MOVE 1 TO WS-VAR.\n"
        )
        result = _extract_synthetic(src)
        pdf = result.get('paragraph_data_flow', {})

        self.assertIn(
            'ALPHA::READ-RECORD', pdf,
            f'Expected compound key "ALPHA::READ-RECORD" in paragraph_data_flow, got: {list(pdf.keys())}'
        )
        self.assertIn(
            'BETA::READ-RECORD', pdf,
            f'Expected compound key "BETA::READ-RECORD" in paragraph_data_flow, got: {list(pdf.keys())}'
        )
        self.assertNotIn(
            'READ-RECORD', pdf,
            f'Plain key "READ-RECORD" must be absent when cross-section collision exists, got: {list(pdf.keys())}'
        )
        self.assertEqual(
            pdf['ALPHA::READ-RECORD']['section_name'], 'ALPHA',
            f'ALPHA::READ-RECORD must have section_name="ALPHA", got: {pdf.get("ALPHA::READ-RECORD", {}).get("section_name")}'
        )
        self.assertEqual(
            pdf['BETA::READ-RECORD']['section_name'], 'BETA',
            f'BETA::READ-RECORD must have section_name="BETA", got: {pdf.get("BETA::READ-RECORD", {}).get("section_name")}'
        )

    # ------------------------------------------------------------------
    # Test 5: back-to-back SECTION headers, empty first section
    # ------------------------------------------------------------------

    def test_back_to_back_section_headers_with_no_paragraphs_in_between(self):
        """
        ALPHA SECTION immediately followed by BETA SECTION (no paragraphs under ALPHA).
        BETA-PARA appears under BETA SECTION.
        Assert: no paragraph has section_name == 'ALPHA';
                BETA-PARA has section_name == 'BETA';
                no parse errors.
        """
        result = _extract_synthetic(self._SRC_BACK_TO_BACK)
        pdf = result.get('paragraph_data_flow', {})

        # No paragraph should claim section_name == 'ALPHA'
        alpha_paras = [
            k for k, v in pdf.items()
            if isinstance(v, dict) and v.get('section_name') == 'ALPHA'
        ]
        self.assertEqual(
            alpha_paras, [],
            f'No paragraph should be under empty ALPHA section, got: {alpha_paras}'
        )

        # BETA-PARA must exist and be under BETA
        self.assertIn(
            'BETA-PARA', pdf,
            f'Expected BETA-PARA in paragraph_data_flow, got: {list(pdf.keys())}'
        )
        entry = pdf['BETA-PARA']
        self.assertIn('section_name', entry, 'BETA-PARA must have section_name key')
        self.assertEqual(
            entry['section_name'], 'BETA',
            f'BETA-PARA must have section_name="BETA", got: {entry.get("section_name")}'
        )

        # No program-level errors
        self.assertEqual(
            result.get('program_unresolved', []), [],
            f'Unexpected program_unresolved errors: {result.get("program_unresolved")}'
        )

    # ------------------------------------------------------------------
    # Test 6: SCHEMA_VERSION must be "1.3" once section_name is present
    # ------------------------------------------------------------------

    def test_schema_version_field_is_1_3_when_section_name_present(self):
        """
        After Step 2 bumps SCHEMA_VERSION, extract_data_flow output must
        return schema_version == "1.3". This test will fail in Step 1
        because the production code has not been modified yet (still "1.2").
        """
        result = _extract_synthetic(self._SRC_ONE_SECTION)
        schema_ver = result.get('schema_version')
        self.assertEqual(
            schema_ver, '1.3',
            f'Expected schema_version="1.3" (Step 2 bumps this), got: "{schema_ver}"'
        )


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(__import__('__main__'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)


# ── Stage 3 vectors ────────────────────────────────────────────────────────


class TestV01DirectAssignment(unittest.TestCase):
    """V01: MOVE VAR-A TO VAR-B — reads=[VAR-A], mutates=[VAR-B]"""

    def test_v01_direct_assignment(self):
        r, m, u = _run('MOVE VAR-A TO VAR-B')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('VAR-A', rf, f"VAR-A not in reads: {r}")
        self.assertIn('VAR-B', mf, f"VAR-B not in mutates: {m}")
        self.assertNotIn('VAR-B', rf, f"VAR-B should not be in reads: {r}")


class TestV02LiteralRejection(unittest.TestCase):
    """V02: MOVE literal TO VAR-B — reads=[], mutates=[VAR-B]"""

    def test_v02_literal_rejection(self):
        r, m, u = _run("MOVE 'HARDCODED-LITERAL' TO VAR-B")
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertEqual(rf, [], f"reads should be empty for literal: {r}")
        self.assertIn('VAR-B', mf, f"VAR-B not in mutates: {m}")


class TestV03ComputeDecomposition(unittest.TestCase):
    """V03: COMPUTE VAR-X = (VAR-A * VAR-B) - VAR-C — reads has all RHS operands"""

    def test_v03_compute_decomposition(self):
        r, m, u = _run('COMPUTE VAR-X = (VAR-A * VAR-B) - VAR-C')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        for var in ["VAR-A", "VAR-B", "VAR-C"]:
            self.assertIn(var, rf, f"{var} not in reads: {r}")
        self.assertIn('VAR-X', mf, f"VAR-X not in mutates: {m}")
        self.assertNotIn('VAR-X', rf, f"VAR-X should not be in reads: {r}")


class TestV04ImplicitMutationAdd(unittest.TestCase):
    """V04: ADD 1 TO COUNTER-VAR — COUNTER-VAR in both reads and mutates"""

    def test_v04_implicit_mutation_add(self):
        r, m, u = _run('ADD 1 TO COUNTER-VAR')
        rf = [e['field'] for e in r]
        mf = [e['field'] for e in m]
        self.assertIn('COUNTER-VAR', rf, f"COUNTER-VAR not in reads: {r}")
        self.assertIn('COUNTER-VAR', mf, f"COUNTER-VAR not in mutates: {m}")
