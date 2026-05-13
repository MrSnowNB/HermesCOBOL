2#!/usr/bin/env python3
"""Fix Failure Mode 2 section in the post-mortem file."""

import os

# Absolute path to the post-mortem file
file_path = r"C:\work\HermesCOBOL\HermesCOBOL\audit\3.4-close-out\postmortems\local-run-2026-05-11.md"

print(f"Target file: {file_path}")
print(f"File exists: {os.path.exists(file_path)}")

# Read the original file
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Total lines in file: {len(lines)}")

# Find the line with the old heading (## Section 3 — Failure Mode 2: Null Paragraph Counts)
old_heading = "## Section 3 — Failure Mode 2: Null Paragraph Counts"
new_heading = "### Failure Mode 2 — Absence of copybook-specific classification logic"

found_idx = None
for i, line in enumerate(lines):
    if old_heading in line:
        found_idx = i
        print(f"Found old heading at line {i+1}: {repr(line)}")
        break

if found_idx is None:
    print("Old heading NOT found!")
    # Check what's actually in the file
    for i, line in enumerate(lines):
        if "Failure Mode 2" in line:
            print(f"Line {i+1} contains 'Failure Mode 2': {repr(line)}")
    exit(1)

# Find the next heading to know where the section ends
next_heading_idx = None
for i in range(found_idx + 1, len(lines)):
    if lines[i].startswith("## "):
        next_heading_idx = i
        print(f"Found next heading at line {i+1}: {repr(lines[i])}")
        break

print(f"\nSection to replace: lines {found_idx+1} to {next_heading_idx}")

# Extract the section
old_section = "".join(lines[found_idx:next_heading_idx])
print("\n=== Old section to replace ===")
print(old_section)

# New section content (full section including heading)
new_section = f"""### Failure Mode 2 — Absence of copybook-specific classification logic
Evidence Block E5 measured 48 nulls per `paragraph_count_*` field. 48 equals the total copybook count (31 data copybooks in `data/raw/cpy/` plus 17 BMS map copybooks in `data/raw/cpy-bms/`). Copybooks have no PROCEDURE DIVISION and no paragraphs, so `paragraph_count_local: null` is **schema-appropriate** for every copybook entry, not a defect. The helper script correctly read schema-1.3 JSON artifacts for the 31 programs (their paragraph counts are populated, not null).
The actual failure: the script applied program-shaped heuristics to all 79 artifacts, leaving copybook-specific evidence axes unread. A correct deterministic classifier must branch on `artifact_kind`:
- For `program`: read `data/data_flow/<name>.json` to populate `paragraph_count_local`; compute drift against `data/facts/<name>.json`.
- For `copybook_data` (under `data/raw/cpy/`): scan for level-01 / level-77 data definitions; classify by record-layout signals (file structures, COMMAREA layouts, work areas).
- For `copybook_bms_map` (under `data/raw/cpy-bms/`): scan for `DFHMSD` (map-set), `DFHMDI` (map item), `DFHMDF` (field) macros; classify by screen-attribute signals.
The earlier characterization in this post-mortem stating "helper script deleted before JSON access" is retracted: the script did read JSON for programs (E5 shows program paragraph_count fields populated, only copybook fields null). The defect is missing branches, not missing reads.

---

"""

# Build the new content
new_lines = lines[:found_idx] + [new_section] + lines[next_heading_idx:]
new_content = "".join(new_lines)

print(f"\n=== New section ===")
print(new_section)

# Write the updated content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"\nFile updated successfully!")
print(f"Total lines after update: {len(new_lines)}")