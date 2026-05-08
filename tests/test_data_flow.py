#!/usr/bin/env python3
"""
tests/test_data_flow.py  --  Section 2 unit tests.
All fixtures are corpus-independent; a minimal inline qmap is injected.
Run with:  python tests/test_data_flow.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from data_flow import classify_statement, extract_paragraphs, _normalise_source, is_literal

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
}


def _run(stmt, context=None):
    reads, mutates, unresolved = [], [], []
    ctx = set(context or [])
    classify_statement(1, stmt, _QMAP, ctx, reads, mutates, unresolved)
    return reads, mutates, unresolved


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
    """DISPLAY with a quoted literal must not produce any unresolved entries."""
    def test_display_literal(self):
        r, m, u = _run("DISPLAY 'HELLO WORLD'")
        self.assertEqual(r, [], "DISPLAY of a literal should produce no reads")
        self.assertEqual(u, [], "DISPLAY of a literal should produce no unresolved entries")

    def test_display_mixed_literal_and_var(self):
        """DISPLAY literal followed by an identifier: only the identifier is a read."""
        r, m, u = _run("DISPLAY 'VALUE IS:' A")
        rf = [e['field'] for e in r]
        self.assertIn('REC-A.A', rf, "A should be resolved as a read")
        # the literal fragment should NOT appear in unresolved
        for entry in u:
            self.assertNotIn('__LIT__', entry.get('reason', ''))
            self.assertNotIn("'VALUE", entry.get('reason', ''))


# ---------------------------------------------------------------------------
# Para extraction: scope terminators must NOT become paragraph headers
# ---------------------------------------------------------------------------
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
        from data_flow import _normalise_source, extract_paragraphs
        lines = _normalise_source(source)
        paras = extract_paragraphs(lines)
        para_names = [k for k in paras if k != '__MAIN__']
        self.assertIn('MAIN-PARA', para_names)
        self.assertNotIn('END-PERFORM', para_names)
        self.assertNotIn('GOBACK', para_names)


if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(__import__('__main__'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
