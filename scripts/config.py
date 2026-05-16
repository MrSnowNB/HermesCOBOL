#!/usr/bin/env python3
"""
config.py — Canonical path definitions for HermesCOBOL.

All scripts import paths from here. Do NOT hard-code paths elsewhere.
No stubs, translators, or synthetic copybooks are referenced here.
"""

from pathlib import Path

# Repository root — resolved from this file's location
REPO_ROOT       = Path(__file__).resolve().parent.parent

# Raw source inputs (committed, never generated)
RAW_CBL_DIR     = REPO_ROOT / "data" / "raw" / "cbl"       # COBOL programs
RAW_CPY_DIR     = REPO_ROOT / "data" / "raw" / "cpy"       # non-BMS copybooks
RAW_CPY_BMS_DIR = REPO_ROOT / "data" / "raw" / "cpy-bms"   # BMS map copybooks

# Generated outputs (gitignored — produced locally by running each stage)
FACTS_DIR       = REPO_ROOT / "data" / "facts"             # Stage 3 output
REKT_DIR        = REPO_ROOT / "data" / "rekt"              # Stage 2 output
PREPROC_DIR     = REPO_ROOT / "data" / "preprocessed"      # Stage 1 output

# Validator outputs (gitignored)
VALID_DIR       = REPO_ROOT / "validation"
RECON_CBL_DIR   = VALID_DIR / "reconstructed" / "cbl"
REPORTS_DIR     = VALID_DIR / "reports"

# Generated data directories (Stage 5-B / 5-D / 5-E outputs)
DATA_DIR                 = REPO_ROOT / "data"
CFG_DIR                  = DATA_DIR / "cfg"
FALLTHROUGH_DIR          = DATA_DIR / "fallthrough"
PASS1_ANNOTATIONS_DIR    = VALID_DIR / "pass1"
CANONICAL_DIR            = DATA_DIR / "canonical"  # Stage 5-G / 5-H Canonical IR

# Schema version — must match extract_facts.py
SCHEMA_VERSION  = "1.0"
