import json
import httpx
import redis
import numpy as np
from redis.commands.search.field import VectorField, TextField, NumericField
from redis.commands.search.index_definition import IndexDefinition, IndexType
import sys

# Configuration
MANIFEST_PATH = "docs/COACTUPC_Honcho_Load_Manifest_v2.json"
LEMONADE_EMBED_URL = "http://localhost:8000/v1/embeddings"
MODEL_NAME = "nomic-embed-text-v2-moe-GGUF"
REDIS_HOST = "localhost"
REDIS_PORT = 6380
REDIS_PASSWORD = "cobol123"
INDEX_NAME = "cobol_ir"
VECTOR_DIM = 768
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150

def get_embeddings_batch(texts):
    if not texts:
        return []
    try:
        response = httpx.post(
            LEMONADE_EMBED_URL,
            json={"input": texts, "model": MODEL_NAME},
            timeout=60.0
        )
        response.raise_for_status()
        data = response.json()
        if "data" in data:
            return [item["embedding"] for item in data["data"]]
        print(f"Unexpected response structure: {data}")
        return []
    except Exception as e:
        print(f"Embedding batch error: {e}")
        return []

def chunk_text(text, size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    if not text:
        return chunks
    
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start += (size - overlap)
    return chunks

def setup_redis():
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    try:
        r.ft(INDEX_NAME).info()
        print(f"Index {INDEX_NAME} already exists. Dropping...")
        r.ft(INDEX_NAME).dropindex()
    except:
        pass

    schema = (
        TextField("paragraph_name"),
        NumericField("chunk_index"),
        TextField("content"),
        VectorField(
            "embedding",
            "HNSW",
            {
                "TYPE": "FLOAT32",
                "DIM": VECTOR_DIM,
                "DISTANCE_METRIC": "COSINE",
                "INITIAL_CAP": 1000,
            },
        ),
    )
    
    r.ft(INDEX_NAME).create_index(
        fields=schema,
        definition=IndexDefinition(prefix=["cobol:para:"], index_type=IndexType.HASH)
    )
    print(f"Created index {INDEX_NAME}")
    return r

def main():
    print(f"Reading manifest: {MANIFEST_PATH}")
    with open(MANIFEST_PATH, 'r') as f:
        data = json.load(f)

    r = setup_redis()
    total_chunks = 0
    
    # Manifest v2 structure: {"program": "...", "units": [{"key": "...", "value": {"paragraph": "...", "statements": [{"raw": "..."}]}}]}
    for unit in data["units"]:
        val = unit.get("value", unit)
        para_name = val.get("paragraph", "UNKNOWN")
        
        # Reconstruct paragraph content from statements
        statements = val.get("statements", [])
        para_content = "\n".join([s.get("raw", "") for s in statements])
        
        if not para_content.strip():
            continue
            
        chunks = chunk_text(para_content)
        print(f"Processing {para_name}: {len(chunks)} chunks")
        
        # Batch embedding for all chunks in this paragraph
        prefixed_chunks = [f"search_document: {c}" for c in chunks]
        embeddings = get_embeddings_batch(prefixed_chunks)
        
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            # Redis expects bytes for the vector field
            embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
            
            mapping = {
                "paragraph_name": para_name,
                "chunk_index": i,
                "content": chunk,
                "embedding": embedding_bytes
            }
            
            r.hset(f"cobol:para:{para_name}:{i}", mapping=mapping)
            total_chunks += 1
                
        print(f"Indexed {para_name}")

    print(f"\nFinished! Total chunks indexed: {total_chunks}")

if __name__ == "__main__":
    main()
