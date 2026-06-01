import httpx
import redis
import numpy as np
from redis.commands.search.query import Query
import sys

LEMONADE_EMBED_URL = "http://localhost:8000/v1/embeddings"
MODEL_NAME = "nomic-embed-text-v2-moe-GGUF"
REDIS_HOST = "localhost"
REDIS_PORT = 6380
REDIS_PASSWORD = "cobol123"
INDEX_NAME = "cobol_ir"

def get_embedding(text):
    try:
        response = httpx.post(LEMONADE_EMBED_URL,
            json={"input": text, "model": MODEL_NAME}, timeout=30.0)
        response.raise_for_status()
        data = response.json()
        if "data" in data and len(data["data"]) > 0:
            return data["data"][0]["embedding"]
        return None
    except Exception as e:
        print(f"Embedding error: {e}", file=sys.stderr)
        return None

def query_ir(query_text, top_k=5):
    embedding = get_embedding(query_text)
    if not embedding:
        return []
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, 
        password=REDIS_PASSWORD, protocol=2)
    query_vector = np.array(embedding, dtype=np.float32).tobytes()
    q = Query(f"*=>[KNN {top_k} @embedding $vec AS score]")         .sort_by("score")         .return_fields("paragraph_name", "content", "score")         .dialect(2)
    try:
        results = r.ft(INDEX_NAME).search(q, query_params={"vec": query_vector})
        return results.docs
    except Exception as e:
        print(f"Redis search error: {e}", file=sys.stderr)
        return []

if __name__ == "__main__":
    user_query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "EDIT MAP input validation"
    print(f"Querying Redis COBOL IR for: '{user_query}'")
    docs = query_ir(user_query)
    print(f"Found {len(docs)} results:")
    for i, doc in enumerate(docs):
        para = getattr(doc, 'paragraph_name', 'Unknown')
        content = getattr(doc, 'content', '')
        score = getattr(doc, 'score', 'N/A')
        print(f"
{i+1}. [Score: {score}] Para: {para}")
        print(f"   {content[:200].replace(chr(10), ' ')}...")
