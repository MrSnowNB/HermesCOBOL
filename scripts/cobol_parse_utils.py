"""
cobol_parse_utils.py — Shared COBOL parsing primitives (Single Source of Truth)

This module centralizes low-level paragraph detection and text processing logic
used across the HermesCOBOL extraction pipeline.

Purpose:
    Provide reusable, well-tested primitives for identifying paragraphs,
    filtering noise tokens (scope terminators, keywords, etc.), and slicing
    COBOL source divisions. This prevents duplication and divergence bugs
    (such as the missing_paragraphs inconsistency fixed in Stage 5-F).

Expected Consumers:
    - scripts/extract_facts.py
    - scripts/validate_roundtrip.py

DO NOT ADD:
    - Program-level business logic or enrichment (belongs in extract_facts.py)
    - CICS-specific detection or command parsing (belongs in pass1_annotate.py)
    - Data flow, call graph, or mutation analysis (belongs in data_flow.py)
    - Canonical IR assembly logic (belongs in assemble_canonical.py)
    - Any higher-level orchestration or schema merging

Legacy Note:
    scripts/hermes_v11_combined_extractor.py intentionally retains its own
    copy of these primitives as it is a legacy monolith. It is NOT considered
    a consumer of this module. New code should import from cobol_parse_utils
    instead of hermes_v11_combined_extractor.

This module should remain focused on pure, stateless parsing utilities.
"""

from __future__ import annotations
import re

# ---------------------------------------------------------------------------
# Compiled regex patterns
# ---------------------------------------------------------------------------
RE_PARAGRAPH = re.compile(
    r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]*)[ \t]*\.[ \t]*(?:\*.*)?$",
    re.MULTILINE,
)
RE_SECTION = re.compile(
    r"^[ ]{0,11}([A-Z0-9][A-Z0-9-]*)[ \t]+SECTION[ \t]*\.[ \t]*$",
    re.MULTILINE | re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Filter sets
# ---------------------------------------------------------------------------
RESERVED_WORDS = frozenset([
    "IDENTIFICATION", "ENVIRONMENT", "DATA", "PROCEDURE",
    "CONFIGURATION", "INPUT-OUTPUT", "FILE", "WORKING-STORAGE",
    "LINKAGE", "LOCAL-STORAGE", "REPORT", "SCREEN",
    "PROGRAM-ID", "AUTHOR", "INSTALLATION", "DATE-WRITTEN",
    "DATE-COMPILED", "SECURITY", "REMARKS",
    "FD", "SD", "RD",
    # Common statement keywords that cannot be paragraph names
    "STOP", "EXIT", "GOBACK", "MOVE",
])

PARAGRAPH_NOISE = frozenset([
    # Scope terminators
    "END-IF", "END-EVALUATE", "END-PERFORM", "END-READ", "END-WRITE",
    "END-REWRITE", "END-DELETE", "END-START", "END-CALL", "END-STRING",
    "END-UNSTRING", "END-COMPUTE", "END-ADD", "END-SUBTRACT",
    "END-MULTIPLY", "END-DIVIDE", "END-EXEC", "END-SEARCH",
    # Division/section markers not caught by RESERVED_WORDS
    "FILE-CONTROL", "FILE-SECTION", "I-O-CONTROL",
    # Statement keywords that appear line-solo
    "GOBACK", "EXIT", "CONTINUE", "STOP",
    # Common false-positive paragraph-name matches
    "FILLER",
])

PERFORM_NON_TARGETS = frozenset([
    "UNTIL", "VARYING", "TIMES", "WITH", "TEST",
    "THRU", "THROUGH", "BEFORE", "AFTER",
])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def strip_cobol_comments(text: str) -> str:
    """Remove COBOL comment lines (col 7 = '*' or '/')."""
    out = []
    for line in text.splitlines():
        if len(line) >= 7 and line[6] in ("*", "/"):
            continue
        if line.strip():
            out.append(line)
    return "\n".join(out)


def slice_procedure_division(text: str) -> str:
    """Return only the text from PROCEDURE DIVISION onward."""
    m = re.search(
        r"^[ \t]*PROCEDURE[ \t]+DIVISION\b",
        text, re.MULTILINE | re.IGNORECASE,
    )
    return text[m.start():] if m else text


def extract_paragraphs(text: str) -> set[str]:
    """
    Extract paragraph names from COBOL source text.

    Applies full filtering pipeline:
    1. Strip comments
    2. Slice to PROCEDURE DIVISION only
    3. Match RE_PARAGRAPH
    4. Filter RESERVED_WORDS, PARAGRAPH_NOISE, *-DIVISION suffixes
    5. Remove section names (RE_SECTION)

    Returns a set of upper-cased paragraph name strings.
    """
    clean = strip_cobol_comments(text)
    proc  = slice_procedure_division(clean)

    paragraphs: set[str] = set()
    for m in RE_PARAGRAPH.finditer(proc):
        name = m.group(1).upper()
        if (name not in RESERVED_WORDS
                and name not in PARAGRAPH_NOISE
                and not name.endswith("-DIVISION")):
            paragraphs.add(name)

    for m in RE_SECTION.finditer(proc):
        paragraphs.discard(m.group(1).upper())

    return paragraphs
