# L1-M3.1 — Vector IO API

**Level:** Essentials
**Duration:** 45 min

## Overview

OGX provides a **Vector IO API** that abstracts over vector databases, giving you a single interface for inserting document chunks and querying by similarity. In this lesson you will create a vector store backed by Qdrant, insert embedded documents, and retrieve them with natural language queries — all through OGX's unified API.

## Prerequisites

- Completed: L1-M2.2 Embeddings
- Infrastructure running: OGX (port 8321), Qdrant (port 6333), Ollama with `gemma4:e4b`
- See `ogx-local/` in the repository root for setup instructions

## Concepts

### Vector IO: A Unified Vector Database Abstraction

Vector IO is OGX's abstraction layer over vector databases. Instead of writing code directly against Qdrant, ChromaDB, or FAISS APIs, you use OGX's `vector_io` and `vector_stores` endpoints. This means you can swap backends without changing your application code.

There are two related API surfaces:

| Namespace | Purpose |
|---|---|
| `client.vector_stores` | Manage stores (create, list, retrieve, delete) — OpenAI-compatible |
| `client.vector_io` | Low-level chunk operations (insert, query) — OGX-native |

### Qdrant as the Vector Backend

OGX supports Qdrant in two modes:

| Mode | Provider ID | Use case |
|---|---|---|
| **Embedded** | `inline::qdrant` | Zero-config, in-process. Great for development. |
| **Server** | `remote::qdrant` | Separate Qdrant container. Persistent storage, dashboard, production-ready. |

This tutorial uses `remote::qdrant` via the Podman Compose setup. Qdrant's dashboard is available at `http://localhost:6333/dashboard`.

### Other Supported Backends

OGX's provider-agnostic design supports many vector databases:
- **ChromaDB** — lightweight, embedded
- **FAISS** — Meta's similarity search library
- **pgvector** — PostgreSQL extension
- **Milvus** — distributed vector database
- **Weaviate** — AI-native vector search
- **Elasticsearch** — with vector search capabilities

Switching backends requires changing only the `provider_id` in your configuration.

### Document Chunking and Embedding Pipeline

The typical workflow for storing documents in a vector store:

1. **Chunk** your documents into smaller pieces (paragraphs, sections)
2. **Embed** each chunk using `client.embeddings.create()` to get a vector
3. **Insert** the chunks with their embeddings via `client.vector_io.insert()`
4. **Query** by passing natural language text — OGX auto-embeds the query and finds similar chunks

Note that `vector_io.insert()` requires pre-computed embeddings, while `vector_io.query()` automatically embeds the query text using the store's configured embedding model.

### Configuring Qdrant in run.yaml

When running OGX with a remote Qdrant instance, the configuration in `run.yaml` looks like:

```yaml
vector_io:
  - provider_id: qdrant
    provider_type: remote::qdrant
    config:
      url: http://qdrant:6333
```

The `ogx-local/` Podman Compose setup handles this configuration automatically.

## Step-by-Step

### Step 1: Create a Vector Store

First, create a vector store backed by Qdrant. The `embedding_model`, `embedding_dimension`, and `provider_id` are passed via the `metadata` dict.

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")

# Detect embedding dimension dynamically
test_response = client.embeddings.create(model="ollama/gemma4:e4b", input="test")
embedding_dim = len(test_response.data[0].embedding)

store = client.vector_stores.create(
    name="tutorial-docs",
    metadata={
        "embedding_model": "ollama/gemma4:e4b",
        "embedding_dimension": str(embedding_dim),
        "provider_id": "qdrant",
    },
)
print(f"Created: {store.name} (id={store.id})")
```

### Step 2: List Vector Stores

Verify the store was created by listing all registered vector stores:

```python
stores = client.vector_stores.list()
for store in stores:
    print(f"  - {store.name} (id={store.id}, status={store.status})")
```

### Step 3: Insert Documents

Generate embeddings for your documents using `client.embeddings.create()`, then insert them as chunks via `client.vector_io.insert()`. Each chunk requires a `chunk_id`, `content`, `embedding`, `embedding_model`, `embedding_dimension`, and `chunk_metadata`.

```python
# Generate embeddings in a batch
texts = ["Decorators in Python are...", "List comprehensions provide..."]
emb_response = client.embeddings.create(model="ollama/gemma4:e4b", input=texts)

# Build and insert chunks
chunks = [
    {
        "chunk_id": f"doc-{i}",
        "content": text,
        "embedding": emb_response.data[i].embedding,
        "embedding_model": "ollama/gemma4:e4b",
        "embedding_dimension": len(emb_response.data[i].embedding),
        "chunk_metadata": {"document_id": f"doc-{i}", "source": "tutorial"},
    }
    for i, text in enumerate(texts)
]

client.vector_io.insert(vector_store_id=store.id, chunks=chunks)
```

### Step 4: Query by Similarity

Query the vector store with a natural language question. OGX automatically embeds the query using the store's configured embedding model and returns the most similar chunks with their similarity scores.

```python
response = client.vector_io.query(
    vector_store_id=store.id,
    query="How do decorators work in Python?",
    params={"max_chunks": 3},
)

for chunk, score in zip(response.chunks, response.scores):
    print(f"  score={score:.4f}  {chunk.content[:80]}...")
```

### Step 5: Cleanup

Delete the vector store when you are done:

```python
result = client.vector_stores.delete(vector_store_id=store.id)
print(f"Deleted: {result.id} (deleted={result.deleted})")
```

## Running the Lesson

```bash
cd tutorial/level_1/M3_rag/1_vector_io_api
uv sync
uv run python main.py
```

## Expected Output

```
L1-M3.1 — Vector IO API
============================================================

Checking OGX server connectivity...
  OGX is reachable at http://localhost:8321

============================================================
Step 1: Create a vector store
============================================================
  Detected embedding dimension: 3072
  Created vector store: tutorial-docs
  Store ID: vs_abc123...
  Status: completed

============================================================
Step 2: List vector stores
============================================================
  - tutorial-docs (id=vs_abc123..., status=completed)
  Total: 1 vector store(s)

============================================================
Step 3: Insert documents
============================================================
  Generating embeddings for 5 documents...
  Inserting 5 chunks into store vs_abc123...
  Successfully inserted 5 chunks.
    - doc-1: "Decorators in Python are a powerful way to modify or extend..."
    - doc-2: "List comprehensions provide a concise way to create lists i..."
    - doc-3: "Generators in Python are functions that use the yield keywo..."
    - doc-4: "Context managers in Python use the with statement to manage..."
    - doc-5: "Type hints in Python allow you to annotate function paramet..."

============================================================
Step 4: Query by similarity
============================================================

  Query: "How do decorators work in Python?"
  --------------------------------------------------
    #1  score=0.8234  Decorators in Python are a powerful way to modify or extend the behavior of fu...
    #2  score=0.6102  Context managers in Python use the with statement to manage resources like file...
    #3  score=0.5891  Type hints in Python allow you to annotate function parameters and return valu...

  Query: "What is lazy evaluation in Python?"
  --------------------------------------------------
    #1  score=0.7856  Generators in Python are functions that use the yield keyword to produce a seq...
    #2  score=0.6043  List comprehensions provide a concise way to create lists in Python. They cons...
    #3  score=0.5512  Decorators in Python are a powerful way to modify or extend the behavior of fu...

  Query: "How do I add type annotations to my code?"
  --------------------------------------------------
    #1  score=0.8102  Type hints in Python allow you to annotate function parameters and return valu...
    #2  score=0.5934  List comprehensions provide a concise way to create lists in Python. They cons...
    #3  score=0.5621  Decorators in Python are a powerful way to modify or extend the behavior of fu...

============================================================
Step 5: Cleanup — delete the vector store
============================================================
  Deleted: vs_abc123... (deleted=True)

============================================================
Done!
============================================================

  You have successfully:
  1. Created a Qdrant-backed vector store via OGX
  2. Listed the registered vector stores
  3. Generated embeddings and inserted document chunks
  4. Queried for similar documents by natural language
  5. Cleaned up the vector store

  Key insight: OGX's Vector IO provides a unified abstraction
  over vector databases. You can swap Qdrant for ChromaDB,
  FAISS, or pgvector by changing a single provider_id —
  your application code stays the same.

  Next: L1-M3.2 — Building a RAG Application (combining
  Vector IO with inference for grounded Q&A)
```

Note: Store IDs, similarity scores, and embedding dimensions will vary depending on the model and infrastructure configuration. The important thing is that the decorator document ranks highest for the decorator query, the generator document for the lazy evaluation query, and the type hints document for the annotations query.

## Key Takeaways

- **Vector IO** is OGX's unified abstraction over vector databases. You use the same API regardless of the backend (Qdrant, ChromaDB, FAISS, pgvector, etc.).
- **Two namespaces**: `client.vector_stores` manages stores (create, list, delete); `client.vector_io` handles chunk operations (insert, query).
- **Insert requires pre-computed embeddings**: use `client.embeddings.create()` to generate vectors, then pass them in each chunk.
- **Query auto-embeds**: you pass a plain text query and OGX embeds it using the store's configured model before performing similarity search.
- **Qdrant** runs as a separate container in the `ogx-local/` setup, accessible at port 6333 with a web dashboard.

## Next Steps

In the next lesson, **L1-M3.2 — Building a RAG Application**, you will combine Vector IO with the Inference API to build an end-to-end RAG pipeline: ingest documents, retrieve relevant context for a question, and generate grounded answers using the LLM. You will also explore multi-turn RAG conversations with OGX's Memory API.
