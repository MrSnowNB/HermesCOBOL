import httpx
import json

QUERY_URL = "http://localhost:18000/v3/workspaces/cobol-ir/conclusions/query"
TOKEN = "your-token-here"

def test_query():
    payload = {
        "query": "search_query: EDIT MAP input validation",
        "top_k": 5,
        "filters": {
            "observer_id": "hermes",
            "observed_id": "hermes"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"Querying {QUERY_URL} for 'EDIT MAP input validation'...")
    
    try:
        response = httpx.post(QUERY_URL, json=payload, headers=headers, timeout=30.0)
        if response.status_code == 200:
            results = response.json()
            print(f"Found {len(results)} results:\n")
            for i, res in enumerate(results):
                content = res.get("content", "")
                # Truncate content for display
                display_content = (content[:200] + "..") if len(content) > 200 else content
                print(f"{i+1}. [ID: {res.get('id')}]")
                print(f"   {display_content}\n")
        else:
            print(f"Error: {response.status_code} {response.text}")
    except Exception as e:
        print(f"Query failed: {str(e)}")

if __name__ == "__main__":
    test_query()
