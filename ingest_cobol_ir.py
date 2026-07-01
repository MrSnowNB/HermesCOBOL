import json
import httpx
import sys
from pathlib import Path

MANIFEST_PATH = Path("docs/COACTUPC_Honcho_Load_Manifest_v2.json")
BASE_URL = "http://localhost:18000/v3/workspaces/cobol-ir/conclusions"
TOKEN = "your-token-here"

def chunk_text(text, chunk_size=1500, overlap=200):
    chunks = []
    if not text:
        return chunks
    
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunks.append(text[start:end])
        start += (chunk_size - overlap)
        if start >= len(text):
            break
    return chunks

def ingest():
    if not MANIFEST_PATH.exists():
        print(f"Error: Manifest not found at {MANIFEST_PATH}")
        return

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    units = manifest.get("units", [])
    total_units = len(units)
    total_chunks = 0
    success_chunks = 0
    fail_chunks = 0

    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }

    print(f"Starting ingestion of {total_units} units (with chunking) to {BASE_URL}...")

    with httpx.Client(timeout=30.0) as client:
        for i, unit in enumerate(units):
            key = unit.get("key") # e.g. COACTUPC/0000-MAIN
            value = unit.get("value")
            
            # Clean paragraph name for ID
            paragraph_name = key.split("/")[-1]
            
            content_str = json.dumps(value)
            chunks = chunk_text(content_str)
            
            print(f"[{i+1}/{total_units}] Processing {key} -> {len(chunks)} chunks")
            
            for chunk_idx, chunk_data in enumerate(chunks):
                total_chunks += 1
                
                payload = {
                    "conclusions": [
                        {
                            "content": f"search_document: ID: {key}/chunk_{chunk_idx}\nSOURCE: {key}\nDATA: {chunk_data}",
                            "observer_id": "hermes",
                            "observed_id": "hermes"
                        }
                    ]
                }
                
                try:
                    response = client.post(BASE_URL, json=payload, headers=headers)
                    if response.status_code in (200, 201):
                        success_chunks += 1
                    else:
                        fail_chunks += 1
                        print(f"  Chunk {chunk_idx} Failed: {response.status_code} {response.text}")
                except Exception as e:
                    fail_chunks += 1
                    print(f"  Chunk {chunk_idx} Error: {str(e)}")

    print("\nIngestion Complete")
    print(f"Total Units: {total_units}")
    print(f"Total Chunks: {total_chunks}")
    print(f"Success Chunks: {success_chunks}")
    print(f"Fail Chunks: {fail_chunks}")

if __name__ == "__main__":
    ingest()
