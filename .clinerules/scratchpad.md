TASK: Run validate_roundtrip.py and confirm all gates still pass after the data_flow.py Area-B paragraph fix in commit 65af9b3.

Do NOT modify any file. Do NOT commit anything.

Run the following commands in order and capture all output:

STEP 1 — Run full roundtrip validation:
  cd C:\work\HermesCOBOL
  python scripts/validate_roundtrip.py 2>&1

STEP 2 — Confirm walker baseline unchanged:
  python scripts/audit_cobol_walker.py 2>&1

STEP 3 — Spot-check the three CICS programs specifically:
  python -c "
import json
from pathlib import Path
for prog in ['COACTUPC', 'COACTVWC', 'COCRDLIC']:
    c = json.loads(Path(f'data/canonical/{prog}.canonical.json').read_text())
    para_count = len(c.get('paragraphs', []))
    print(f'{prog}: paragraph_count={para_count}')
"

OUTPUT REQUIRED:
  - Final PASS/FAIL line from validate_roundtrip.py
  - Total programs: N passed, M failed
  - Walker baseline: MATCH or DIVERGED
  - Paragraph counts for the 3 CICS programs

Do NOT write any files. Do NOT commit.