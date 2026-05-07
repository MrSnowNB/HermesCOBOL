from pathlib import Path

# ---------------------------------------------------------------------------
# HermesCOBOL path configuration
# All paths are relative to the repo root.
# Run scripts from the repo root: python scripts/extract_facts.py
# ---------------------------------------------------------------------------

# Raw inputs — committed to the repo
RAW_DIR   = Path("data/raw")
SRC_DIR   = RAW_DIR / "cbl"          # raw .cbl source files
CPY_DIR   = RAW_DIR / "cpy"          # raw copybook files

# Intermediate artifacts — gitignored, produced locally by manual steps
PREPROC_DIR = Path("data/preprocessed")  # cobc -E output (Stage 1)
REKT_DIR    = Path("data/rekt")          # COBOL-REKT CFG JSON (Stage 2)
FACTS_DIR   = Path("data/facts")         # structured_facts.json (Stage 3)

# Pipeline caps — keep extraction output manageable
MAX_REKT_SENTENCES = 20      # max REKT sentences stored per program
MAX_01_ITEMS       = 30      # max working-storage 01-levels stored per program
