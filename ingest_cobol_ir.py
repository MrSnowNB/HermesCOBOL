import json
import httpx
import sys
from pathlib import Path

MANIFEST_PATH = Path("docs/COACTUPC_Honcho_Load_Manifest_v2.json")
BASE_URL = "http://localhost:18000/v3/workspaces/cobol-ir/conclusions"
TOKEN = "your-token-here"

def ingest():
    if not MANIFEST_PATH.exists():
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        return

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    units = manifest.get("units", [])
    total = len(units)
    success = 0
    fail = 0

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    # Create hermes peer if it doesn't exist
    PEER_URL = "http://localhost:18000/v3/workspaces/cobol-ir/peers"
    with httpx.Client(timeout=10.0) as client:
        try:
            print(f"Ensuring peer 'hermes' exists in 'cobol-ir'...")
            resp = client.post(PEER_URL, json={"id": "hermes"}, headers=headers)
            if resp.status_code in (200, 201):
                print("Peer 'hermes' is ready.")
            else:
                print(f"Warning creating peer: {resp.status_code} {resp.text}")
        except Exception as e:
            print(f"Error checking/creating peer: {str(e)}")

    print(f"Starting ingestion of {total} units to {BASE_URL}...")

    with httpx.Client(timeout=30.0) as client:
        for i, unit in enumerate(units):
            key = unit.get("key")
            value = unit.get("value")
            
            # Construct the Conclusion payload in batch format
            payload = {
                "conclusions": [
                    {
                        "content": f"KEY: {key}\nDATA: {json.dumps(value)}",
                        "observer_id": "hermes",
                        "observed_id": "hermes"
                    }
                ]
            }
            
            try:
                response = client.post(BASE_URL, json=payload, headers=headers)
                if response.status_code in (200, 201):
                    success += 1
                    print(f"[{i+1}/{total}] Success: {key}")
                else:
                    fail += 1
                    print(f"[{i+1}/{total}] Failed: {key} - {response.status_code} {response.text}")
            except Exception as e:
                fail += 1
                print(f"[{i+1}/{total}] Error: {key} - {str(e)}")

    print("\nIngestion Complete")
    print(f"Total: {total}")
    print(f"Success: {success}")
    print(f"Fail: {fail}")

if __name__ == "__main__":
    ingest()
