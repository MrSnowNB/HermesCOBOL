# This file is superseded by hermes_v11_combined_extractor.py
# It is kept as a thin re-export shim for backward compatibility with any
# external scripts that import from semantic_extract.
#
# DO NOT add logic here.  Extend hermes_v11_combined_extractor.py instead.

from scripts.hermes_v11_combined_extractor import (
    enrich,
    PARAGRAPH_NOISE,
    extract_paragraphs_defined,
    extract_paragraphs_referenced,
    build_cfg_text_scan,
    build_cfg_from_rekt,
    extract_cics,
    extract_file_lineage,
    extract_file_operations,
    classify_paragraph_actions,
)

__all__ = [
    "enrich",
    "PARAGRAPH_NOISE",
    "extract_paragraphs_defined",
    "extract_paragraphs_referenced",
    "build_cfg_text_scan",
    "build_cfg_from_rekt",
    "extract_cics",
    "extract_file_lineage",
    "extract_file_operations",
    "classify_paragraph_actions",
]
