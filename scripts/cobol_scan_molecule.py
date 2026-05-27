from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from atoms.path_normalize_atom import normalize_path as normalize
from atoms.fs_read_atom import read_file
from atoms.shell_run_atom import run_command as run_shell

def cobol_scan_molecule(target_dir: str) -> dict:
    # Stage 1: normalize path
    p = normalize(target_dir)
    if p["status"] != "ok":
        return {"status": "failed", "stage": "normalize", "detail": p}

    resolved = p["resolved"]

    # Stage 2: find .cbl files
    find = run_shell(f'dir /b /s "{resolved}\\*.cbl"', timeout=10)
    if find["returncode"] != 0:
        return {"status": "failed", "stage": "find_cbl", "detail": find}

    cbl_files = [ln.strip() for ln in find["stdout"].splitlines() if ln.strip()]

    # Stage 3: read first file as proof-of-life
    if not cbl_files:
        return {"status": "ok", "files_found": 0, "sample": None}

    sample = read_file(cbl_files[0])

    return {
        "status": "ok",
        "resolved_dir": resolved,
        "files_found": len(cbl_files),
        "sample_file": cbl_files[0],
        "sample_preview": sample.get("content", "")[:300] if sample["status"] == "ok" else None,
        "sample_status": sample["status"]
    }

if __name__ == "__main__":
    import json
    result = cobol_scan_molecule(r"C:\work\HermesCOBOL\data\raw\cbl")
    print(json.dumps(result, indent=2))
