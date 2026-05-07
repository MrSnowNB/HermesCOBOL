# HermesCOBOL Manual Runbook

This runbook documents the manual step-by-step local process.
**Do not automate these steps.** Each stage is run independently so you can
inspect outputs before proceeding.

---

## Prerequisites

| Tool | Version | Check |
|---|---|---|
| Python | 3.10+ | `python --version` |
| GnuCOBOL | 3.2+ | `cobc --version` |
| Java | 11+ | `java -version` |
| smojol-cli (COBOL-REKT) | latest | `java -jar tools/smojol-cli.jar --help` |

Install Python deps:
```
pip install -r requirements.txt
```

---

## Stage 0 — Verify raw inputs

Confirm your source files are present:
```
ls data/raw/cbl/      # should show *.cbl files
ls data/raw/cpy/      # should show *.cpy copybook files
```

Expected structure:
```
data/raw/
  cbl/
    CBACT01C.cbl
    CBACT02C.cbl
    ... (all programs)
  cpy/
    COPY01.cpy
    ... (all copybooks)
```

Nothing is generated at this stage.

---

## Stage 1 — cobc -E (copybook expansion)

`cobc -E` inlines all COPY statements, producing a single flat source file
per program. This is the input to both REKT and the Python extractor.

**Run manually for each program:**
```bash
mkdir -p data/preprocessed

cobc -E -I data/raw/cpy data/raw/cbl/CBACT01C.cbl > data/preprocessed/CBACT01C.cbl
```

**Or for all programs at once (PowerShell):**
```powershell
New-Item -ItemType Directory -Force data\preprocessed | Out-Null
Get-ChildItem data\raw\cbl\*.cbl | ForEach-Object {
    $out = "data\preprocessed\$($_.BaseName).cbl"
    cobc -E -I data\raw\cpy $_.FullName | Out-File -Encoding utf8 $out
    Write-Host "  -> $out"
}
```

**Or for all programs at once (bash):**
```bash
mkdir -p data/preprocessed
for f in data/raw/cbl/*.cbl; do
    prog=$(basename "$f" .cbl)
    cobc -E -I data/raw/cpy "$f" > "data/preprocessed/${prog}.cbl"
    echo "  -> data/preprocessed/${prog}.cbl"
done
```

**Validate:** Each file in `data/preprocessed/` should be larger than the
original (copybooks are expanded). Check for `# ` linemarker lines — they
are automatically filtered by `extract_facts.py`.

> `data/preprocessed/` is gitignored. It exists only on your local machine.

---

## Stage 2 — COBOL-REKT (smojol-cli)

COBOL-REKT performs static analysis and produces a Control Flow Graph (CFG)
per program as JSON. This is the input to the Python extractor for sentence
extraction and execution order.

**Download smojol-cli:**
- https://github.com/avishek-sen-gupta/cobol-rekt/releases
- Place `smojol-cli.jar` and dialect jars in a local `tools/` directory
  (tools/ is gitignored)

**Run manually for each program:**
```bash
java -jar tools/smojol-cli.jar export-unified \
  --source-dir data/raw/cbl \
  --copybook-dir data/raw/cpy \
  --program CBACT01C.cbl \
  --output-dir data/rekt \
  --dialect IBMCOBOL
```

**Run for all programs (bash):**
```bash
mkdir -p data/rekt
for f in data/raw/cbl/*.cbl; do
    prog=$(basename "$f")
    java -jar tools/smojol-cli.jar export-unified \
      --source-dir data/raw/cbl \
      --copybook-dir data/raw/cpy \
      --program "$prog" \
      --output-dir data/rekt \
      --dialect IBMCOBOL
done
```

**Expected output structure:**
```
data/rekt/
  CBACT01C.cbl.report/
    CBACT01C.cbl.report/        <- REKT double-nests on some versions
      cfg/
        cfg-CBACT01C.cbl.json   <- THIS is what extract_facts.py reads
      data_structures/
      flow_ast/
```

**Note:** REKT may produce a double-nested directory
(`CBACT01C.cbl.report/CBACT01C.cbl.report/cfg/...`).
`extract_facts.py` handles both flat and double-nested layouts automatically.

> `data/rekt/` is gitignored. It exists only on your local machine.

---

## Stage 3 — Python extraction (extract_facts.py)

The Python extractor reads raw source (for `cobc -E` inline call) and REKT
CFG JSON, then produces one `structured_facts.json` per program.

**Run from the repo root:**
```bash
# All programs:
python scripts/extract_facts.py

# Single program:
python scripts/extract_facts.py CBACT01C
```

**Expected console output per program:**
```
[CBACT01C] expanding source... 892 lines | loading REKT... 331 sentences | extracting... 40 paras | valid
  -> data/facts/CBACT01C.json
```

**What `extract_facts.py` does NOT do:**
- It does NOT run `cobc` as a compiler (only `-E` preprocessor mode)
- It does NOT run REKT (reads existing JSON output only)
- It does NOT call any LLM
- It does NOT start any server

> `data/facts/` is gitignored. It exists only on your local machine.

---

## Stage 4 — Validate outputs

Run the schema validator against all produced facts:
```bash
python scripts/schema.py
```

Expected output:
```
  OK   CBACT01C.json
  OK   CBACT02C.json
  ...
```

A `FAIL` line means a required key is missing. Check the program's error
output from Stage 3 and re-run.

---

## Folder state after all stages

```
data/
  raw/              <- committed (source of truth)
    cbl/
    cpy/
  preprocessed/     <- gitignored, local only (Stage 1 output)
  rekt/             <- gitignored, local only (Stage 2 output)
  facts/            <- gitignored, local only (Stage 3 output)
```

---

## What comes next (out of scope for this repo)

Once `data/facts/` is populated and validated:
- The Hermes agent layer reads `data/facts/*.json` as its evidence base
- LLM narration runs against facts JSON (not raw COBOL)
- API / oracle server is built in a separate repo

Do not add those layers here.
