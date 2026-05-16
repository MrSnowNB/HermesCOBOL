"""Unit tests for cobol_parse_utils.py primitives."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

import pytest

from cobol_parse_utils import (
    extract_paragraphs,
    slice_procedure_division,
    strip_cobol_comments,
    PARAGRAPH_NOISE,
    RESERVED_WORDS,
)


def test_extract_paragraphs_clean_non_cics():
    """Should extract real paragraphs and exclude noise tokens."""
    source = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TESTPGM.
       PROCEDURE DIVISION.
       1000-MAIN-PARA.
           DISPLAY 'HELLO'.
       2000-PROCESS-DATA.
           MOVE 1 TO WS-COUNT.
       STOP RUN.
    """
    paragraphs = extract_paragraphs(source)
    assert "1000-MAIN-PARA" in paragraphs
    assert "2000-PROCESS-DATA" in paragraphs
    assert "STOP" not in paragraphs
    assert "EXIT" not in paragraphs


def test_extract_paragraphs_ignores_cics_keywords():
    """CICS keywords should never be treated as paragraph names."""
    source = """
       PROCEDURE DIVISION.
       1000-MAIN.
           EXEC CICS RETURN END-EXEC.
       2000-NEXT-PARA.
           DISPLAY 'DONE'.
    """
    paragraphs = extract_paragraphs(source)
    assert "1000-MAIN" in paragraphs
    assert "2000-NEXT-PARA" in paragraphs
    assert "RETURN" not in paragraphs
    assert "EXEC" not in paragraphs


def test_slice_procedure_division_excludes_earlier_divisions():
    """Text before PROCEDURE DIVISION should be excluded."""
    source = """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. TEST.
       DATA DIVISION.
       WORKING-STORAGE SECTION.
       01 WS-VAR PIC X.
       PROCEDURE DIVISION.
       MAIN-PARA.
           DISPLAY 'HELLO'.
    """
    proc_text = slice_procedure_division(source)
    assert "IDENTIFICATION DIVISION" not in proc_text
    assert "DATA DIVISION" not in proc_text
    assert "MAIN-PARA" in proc_text


def test_strip_cobol_comments_removes_column_7_comments():
    """Lines with '*' in column 7 should be stripped."""
    source = """       IDENTIFICATION DIVISION.
      * This is a comment
       PROGRAM-ID. TEST.
      *Another comment
       PROCEDURE DIVISION.
    """
    cleaned = strip_cobol_comments(source)
    assert "This is a comment" not in cleaned
    assert "Another comment" not in cleaned
    assert "PROGRAM-ID" in cleaned


def test_paragraph_noise_contains_expected_tokens():
    """PARAGRAPH_NOISE should contain common noise tokens but not real paragraphs."""
    assert "STOP" in PARAGRAPH_NOISE
    assert "EXIT" in PARAGRAPH_NOISE
    assert "END-IF" in PARAGRAPH_NOISE
    assert "GOBACK" in PARAGRAPH_NOISE
    assert "1000-MAIN-PARA" not in PARAGRAPH_NOISE
    assert "PROCESS-DATA" not in PARAGRAPH_NOISE


def test_reserved_words_membership():
    """RESERVED_WORDS should contain common COBOL keywords."""
    assert "STOP" in RESERVED_WORDS
    assert "EXIT" in RESERVED_WORDS
    assert "GOBACK" in RESERVED_WORDS
    assert "MOVE" in RESERVED_WORDS
    assert "1000-MAIN" not in RESERVED_WORDS
