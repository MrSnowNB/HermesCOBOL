#!/usr/bin/env python3
"""
tests/test_data_flow.py  --  Section 2 unit tests for data_flow.py

All fixtures are corpus-independent; a minimal inline qmap is injected.
Run with:  python tests/test_data_flow.py
"""

import json
import sys
import traceback
import unittest
from pathlib import Path

# Make sure scripts/ is importable from repo root
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from data_flow import (
    classify_statement,
    extract_paragraphs,
    _normalise_source,
    is_literal,
)

# ---------------------------------------------------------------------------
# Minimal inline qmap fixture
# ---------------------------------------------------------------------------

_QMAP = {
    'A': [{'field': 'REC-A.A', 'record': 'REC-A', 'copybook': None, 'offset': 0,  'length': 5}],
    'B': [{'field': 'REC-B.B', 'record': 'REC-B', 'copybook': None, 'offset': 5,  'length': 5}],
    'C': [{'field': 'REC-C.C', 'record': 'REC-C', 'copybook': None, 'offset': 10, 'length': 5}],
    'X': [{'field': 'REC-X.X', 'record': 'REC-X', 'copybook': None, 'offset': 0,  'length': 4}],
    'CTR': [{'field': 'WS.CTR', 'record': 'WS', 'copybook': None, 'offset': 0, 'length': 4}],
    'R': [{'field': 'R', 'record': 'R', 'copybook': None, 'offset': 0, 'length': 10}],
    'S': [{'field': 'S', 'record': 'S', 'copybook': None, 'offset': 0, 'length': 10}],
    'F': [{'field': 'F', 'record': 'F', 'copybook': None, 'offset': 0, 'length': 80}],
    'REC': [{'field': 'REC', 'record': 'REC', 'copybook': None, 'offset': 0, 'length': 80}],
    # Ambiguous name in two copybooks
    'ACCT-ID': [
        {'field': 'ACCOUNT-RECORD.ACCT-ID', 'record': 'ACCOUNT-RECORD', 'copybook': 'CVACT01Y', 'offset': 0,  'length': 11},
        {'field': 'CARD-RECORD.ACCT-ID',    'record': 'CARD-RECORD',    'copybook': 'CVCRD01Y', 'offset': 5,  'length': 11},
    ],
    'GROUP1': [{'field': 'GROUP1', 'record': 'GROUP1', 'copybook': None, 'offset': 0, 'length': 20}],
    'GROUP2': [{'field': 'GROUP2', 'record': 'GROUP2', 'copybook': None, 'offset': 0, 'length': 20}],
}


def _run(stmt: str, context=None) -> tuple:
    """Helper: run classify_statement and return (reads, mutates, unresolved)."""
    reads, mutates, unresolved = [], [], []
    ctx = set(context or [])
    classify_statement(1, stmt, _QMAP, ctx, reads, mutates, unresolved)
    return reads, mutates, unresolved


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestMoveSingleTarget(unittest.TestCase):
    def test_move_single_target(self):
        reads, mutates, unresolved = _run('MOVE A TO B')
        self.assertEqual([e['field'] for e in reads],   ['REC-A.A'])
        self.assertEqual([e['field'] for e in mutates], ['REC-B.B'])
        self.assertEqual(unresolved, [])


class TestMoveMultipleTargets(unittest.TestCase):
    def test_move_multiple_targets(self):
        reads, mutates, unresolved = _run('MOVE A TO B C')
        self.assertEqual([e['field'] for e in reads],   ['REC-A.A'])
        self.assertEqual([e['field'] for e in mutates], ['REC-B.B', 'REC-C.C'])
        self.assertEqual(unresolved, [])


class TestMoveCorresponding(unittest.TestCase):
    def test_move_corresponding(self):
        reads, mutates, unresolved = _run('MOVE CORRESPONDING GROUP1 TO GROUP2')
        # GROUP1 should appear in reads, GROUP2 in mutates
        read_fields   = [e['field'] for e in reads]
        mutate_fields = [e['field'] for e in mutates]
        self.assertIn('GROUP1', read_fields)
        self.assertIn('GROUP2', mutate_fields)


class TestAddTo(unittest.TestCase):
    def test_add_to(self):
        reads, mutates, unresolved = _run('ADD 1 TO CTR')
        mutate_fields = [e['field'] for e in mutates]
        read_fields   = [e['field'] for e in reads]
        self.assertIn('WS.CTR', mutate_fields)  # CTR is mutated
        self.assertIn('WS.CTR', read_fields)    # prior value read
        self.assertEqual(unresolved, [])


class TestAddGiving(unittest.TestCase):
    def test_add_giving(self):
        reads, mutates, unresolved = _run('ADD A B GIVING C')
        read_fields   = [e['field'] for e in reads]
        mutate_fields = [e['field'] for e in mutates]
        self.assertIn('REC-A.A', read_fields)
        self.assertIn('REC-B.B', read_fields)
        self.assertIn('REC-C.C', mutate_fields)
        self.assertEqual(unresolved, [])


class TestComputeExpression(unittest.TestCase):
    def test_compute_expression(self):
        reads, mutates, unresolved = _run('COMPUTE X = A + B * C')
        read_fields   = [e['field'] for e in reads]
        mutate_fields = [e['field'] for e in mutates]
        self.assertIn('REC-A.A', read_fields)
        self.assertIn('REC-B.B', read_fields)
        self.assertIn('REC-C.C', read_fields)
        self.assertIn('REC-X.X', mutate_fields)
        self.assertEqual(unresolved, [])


class TestInitialize(unittest.TestCase):
    def test_initialize(self):
        reads, mutates, unresolved = _run('INITIALIZE R')
        self.assertEqual(reads, [])
        mutate_fields = [e['field'] for e in mutates]
        self.assertIn('R', mutate_fields)
        self.assertEqual(unresolved, [])


class TestReadInto(unittest.TestCase):
    def test_read_into(self):
        reads, mutates, unresolved = _run('READ F INTO REC')
        self.assertEqual(reads, [])
        mutate_fields = [e['field'] for e in mutates]
        self.assertIn('F',   mutate_fields)  # file record
        self.assertIn('REC', mutate_fields)  # INTO target


class TestWriteFrom(unittest.TestCase):
    def test_write_from(self):
        reads, mutates, unresolved = _run('WRITE R FROM S')
        read_fields   = [e['field'] for e in reads]
        mutate_fields = [e['field'] for e in mutates]
        self.assertIn('S', read_fields)
        self.assertIn('R', mutate_fields)


class TestIfConditionReads(unittest.TestCase):
    def test_if_condition_reads(self):
        reads, mutates, unresolved = _run('IF A > B')
        read_fields = [e['field'] for e in reads]
        self.assertIn('REC-A.A', read_fields)
        self.assertIn('REC-B.B', read_fields)
        self.assertEqual(mutates, [])


class TestUnresolvedName(unittest.TestCase):
    def test_unresolved_name(self):
        reads, mutates, unresolved = _run('MOVE GHOST-FIELD TO B')
        # GHOST-FIELD is not in qmap -> must land in unresolved with line number
        self.assertTrue(len(unresolved) > 0)
        u = unresolved[0]
        self.assertIn('line_no', u)
        self.assertEqual(u['line_no'], 1)
        self.assertIn('GHOST-FIELD', u['reason'])


class TestQualifiedNameDisambiguation(unittest.TestCase):
    def test_qualified_name_disambiguation(self):
        # With ACCOUNT-RECORD already in context, ACCT-ID should resolve to ACCOUNT-RECORD.ACCT-ID
        reads, mutates, unresolved = _run('MOVE ACCT-ID TO B', context={'ACCOUNT-RECORD'})
        read_fields = [e['field'] for e in reads]
        self.assertIn('ACCOUNT-RECORD.ACCT-ID', read_fields)
        self.assertNotIn('CARD-RECORD.ACCT-ID', read_fields)


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    loader  = unittest.TestLoader()
    suite   = loader.loadTestsFromModule(sys.modules[__name__])
    runner  = unittest.TextTestRunner(verbosity=2)
    result  = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
