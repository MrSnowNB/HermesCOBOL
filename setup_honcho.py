import httpx
import sys

BASE_URL = "http://localhost:18000/v3"

def bootstrap():
    print("Bootstrapping Honcho workspaces and peers...")
    try:
        # Create workspaces
        workspaces = ["hermes", "cobol-ir"]
        for ws in workspaces:
            r = httpx.post(f"{BASE_URL}/workspaces", json={"id": ws})
            if r.status_code in (200, 201):
                print(f"  Workspace '{ws}' created.")
            elif r.status_code == 409 or "already exists" in r.text.lower():
                print(f"  Workspace '{ws}' already exists.")
            else:
                print(f"  Failed to create workspace '{ws}': {r.status_code} {r.text}")
        
        # Create peers
        peers = [("cobol-ir", "hermes"), ("hermes", "hermes")]
        for ws, peer in peers:
            r = httpx.post(f"{BASE_URL}/workspaces/{ws}/peers", json={"id": peer})
            if r.status_code in (200, 201):
                print(f"  Peer '{peer}' registered in workspace '{ws}'.")
            elif r.status_code == 409 or "already exists" in r.text.lower():
                print(f"  Peer '{peer}' already exists in workspace '{ws}'.")
            else:
                print(f"  Failed to register peer '{peer}' in workspace '{ws}': {r.status_code} {r.text}")
                
        print("Honcho bootstrap complete.\n")
    except Exception as e:
        print(f"Error during Honcho bootstrap: {str(e)}", file=sys.stderr)
        print("Ensure the Honcho server is running at http://localhost:18000", file=sys.stderr)

if __name__ == "__main__":
    bootstrap()
