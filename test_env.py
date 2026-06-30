import os
from dotenv import load_dotenv
import requests

load_dotenv()

base_url = os.getenv("OPENAI_API_BASE")
model = os.getenv("OPENAI_MODEL")
embed_model = os.getenv("OPENAI_EMBED_MODEL")

print(f"Testing with Base URL: {base_url}")
print(f"Model: {model}")
print(f"Embed Model: {embed_model}")

# Test Chat
try:
    resp = requests.post(
        f"{base_url}/chat/completions",
        json={
            "model": model,
            "messages": [{"role": "user", "content": "Hello"}]
        },
        timeout=60
    )
    print(f"Chat Response Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Chat Response: {resp.json()['choices'][0]['message']['content'][:50]}...")
    else:
        print(f"Chat Error: {resp.text}")
except Exception as e:
    print(f"Chat Exception: {e}")

# Test Embeddings
try:
    resp = requests.post(
        f"{base_url}/embeddings",
        json={
            "model": embed_model,
            "input": "test"
        },
        timeout=10
    )
    print(f"Embeddings Response Status: {resp.status_code}")
    if resp.status_code == 200:
        print(f"Embeddings Successful: {len(resp.json()['data'][0]['embedding'])} dims")
    else:
        print(f"Embeddings Error: {resp.text}")
except Exception as e:
    print(f"Embeddings Exception: {e}")
