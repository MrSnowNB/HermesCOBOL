import httpx
import redis
import numpy as np
from redis.commands.search.query import Query
import sys

# Configuration
LEMONADE_EMBED_URL = "http://localhost:8000/v1/embeddings"
MODEL_NAME = "nomic-embed-text-v2-moe-GGUF"
REDIS_HOST = "localhost"
REDIS_PORT = 6380
REDIS_PASSWORD = "cobol123"
INDEX_NAME = "cobol_ir"

def get_embedding(text):
    try:
        response = httpx.post(
            LEMONADE_EMBED_URL,
            json={"input": text, "model": MODEL_NAME},
            timeout=30.0
        )
        response.raise_for_status()
        return response.json()["data"][0]["embedding"]
    except Exception as e:
        print(f"Embedding error: {e}")
        return None

def main():
    query_text = "EDIT MAP input validation"
    print(f"Query: {query_text}")
    
    embedding = get_embedding(query_text)
    if not embedding:
        sys.exit(1)
        
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, protocol=2)
    
    # KNN Search
    # * => [KNN 5 @embedding $query_vector AS score]
    # We need to pass the query_vector as a blob
    query_vector = np.array(embedding, dtype=np.float32).tobytes()
    
    q = Query("*=>[KNN 5 @embedding $vec AS score]") \
        .sort_by("score") \
        .return_fields("paragraph_name", "content", "score") \
        .dialect(2)
    
    params = {"vec": query_vector}
    
    results = r.ft(INDEX_NAME).search(q, query_params=params)
    
    print(f"Debug: results type: {type(results)}")
    print(f"Debug: results total: {getattr(results, 'total', 'N/A')}")
    print(f"Debug: results docs len: {len(results.docs)}")
    
    print(f"\nTop {len(results.docs)} results:")
    for doc in results.docs:
        score = getattr(doc, 'score', 'N/A')
        para_name = getattr(doc, 'paragraph_name', 'Unknown')
        content = getattr(doc, 'content', '')
        snippet = content[:200].replace('\n', ' ') + "..."
        print(f"\n[Score: {score}] Para: {para_name}")
        print(f"Snippet: {snippet}")

if __name__ == "__main__":
    main()
