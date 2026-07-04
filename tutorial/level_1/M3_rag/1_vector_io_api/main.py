"""L1-M3.1 — Vector IO API

Demonstrates OGX's Vector IO API for working with vector databases:
create a vector store, generate embeddings, insert document chunks,
and query by similarity.
"""

import sys

import httpx
from ogx_client import OgxClient

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"
VECTOR_STORE_NAME = "tutorial-docs"

# Sample documents about Python programming concepts
DOCUMENTS = [
    {
        "id": "doc-1",
        "text": (
            "Decorators in Python are a powerful way to modify or extend the "
            "behavior of functions or methods without changing their source code. "
            "A decorator is a function that takes another function as input, adds "
            "some functionality, and returns a new function. You apply a decorator "
            "using the @symbol above a function definition."
        ),
    },
    {
        "id": "doc-2",
        "text": (
            "List comprehensions provide a concise way to create lists in Python. "
            "They consist of brackets containing an expression followed by a for "
            "clause and zero or more if clauses. List comprehensions are generally "
            "faster than equivalent for-loops because they are optimized internally."
        ),
    },
    {
        "id": "doc-3",
        "text": (
            "Generators in Python are functions that use the yield keyword to "
            "produce a sequence of values lazily, one at a time. Unlike lists, "
            "generators do not store all values in memory at once, making them "
            "ideal for processing large datasets or infinite sequences."
        ),
    },
    {
        "id": "doc-4",
        "text": (
            "Context managers in Python use the with statement to manage resources "
            "like files, database connections, and locks. They ensure that setup "
            "and teardown code runs reliably, even if an exception occurs. You can "
            "create custom context managers using __enter__ and __exit__ methods "
            "or the contextlib.contextmanager decorator."
        ),
    },
    {
        "id": "doc-5",
        "text": (
            "Type hints in Python allow you to annotate function parameters and "
            "return values with expected types. While Python remains dynamically "
            "typed at runtime, type hints enable static analysis tools like mypy "
            "to catch type errors before the code runs, improving code quality "
            "and documentation."
        ),
    },
]


def check_server_reachable(url: str) -> bool:
    """Check that the OGX server is reachable before making API calls."""
    try:
        resp = httpx.get(f"{url}/v1/health", timeout=5)
        resp.raise_for_status()
        return True
    except Exception:
        try:
            resp = httpx.get(f"{url}/v1/models", timeout=5)
            resp.raise_for_status()
            return True
        except Exception:
            return False


def create_vector_store(client: OgxClient) -> str:
    """Create a vector store backed by Qdrant."""
    print("=" * 60)
    print("Step 1: Create a vector store")
    print("=" * 60)

    # Determine embedding dimension by generating a test embedding
    test_response = client.embeddings.create(model=MODEL, input="test")
    embedding_dim = len(test_response.data[0].embedding)
    print(f"  Detected embedding dimension: {embedding_dim}")

    # Create the vector store with Qdrant as the backend.
    # The embedding_model, embedding_dimension, and provider_id are
    # passed via the metadata dict — OGX extracts them to configure
    # the underlying vector index.
    store = client.vector_stores.create(
        name=VECTOR_STORE_NAME,
        metadata={
            "embedding_model": MODEL,
            "embedding_dimension": str(embedding_dim),
            "provider_id": "qdrant",
        },
    )

    print(f"  Created vector store: {store.name}")
    print(f"  Store ID: {store.id}")
    print(f"  Status: {store.status}")
    print()
    return store.id


def list_vector_stores(client: OgxClient) -> None:
    """List all existing vector stores."""
    print("=" * 60)
    print("Step 2: List vector stores")
    print("=" * 60)

    stores = client.vector_stores.list()
    count = 0
    for store in stores:
        count += 1
        print(f"  - {store.name} (id={store.id}, status={store.status})")
    print(f"  Total: {count} vector store(s)")
    print()


def insert_documents(client: OgxClient, store_id: str) -> None:
    """Generate embeddings and insert document chunks into the vector store."""
    print("=" * 60)
    print("Step 3: Insert documents")
    print("=" * 60)

    # Generate embeddings for all documents in a single batch
    texts = [doc["text"] for doc in DOCUMENTS]
    print(f"  Generating embeddings for {len(texts)} documents...")
    emb_response = client.embeddings.create(model=MODEL, input=texts)

    # Build chunks with their embeddings
    embedding_dim = len(emb_response.data[0].embedding)
    chunks = []
    for i, doc in enumerate(DOCUMENTS):
        chunks.append(
            {
                "chunk_id": doc["id"],
                "content": doc["text"],
                "embedding": emb_response.data[i].embedding,
                "embedding_model": MODEL,
                "embedding_dimension": embedding_dim,
                "chunk_metadata": {
                    "document_id": doc["id"],
                    "source": "python-tutorial",
                },
            }
        )

    # Insert chunks into the vector store
    print(f"  Inserting {len(chunks)} chunks into store {store_id}...")
    client.vector_io.insert(vector_store_id=store_id, chunks=chunks)

    print(f"  Successfully inserted {len(chunks)} chunks.")
    for doc in DOCUMENTS:
        print(f"    - {doc['id']}: \"{doc['text'][:60]}...\"")
    print()


def query_documents(client: OgxClient, store_id: str) -> None:
    """Query the vector store for similar documents."""
    print("=" * 60)
    print("Step 4: Query by similarity")
    print("=" * 60)

    queries = [
        "How do decorators work in Python?",
        "What is lazy evaluation in Python?",
        "How do I add type annotations to my code?",
    ]

    for query_text in queries:
        print(f"\n  Query: \"{query_text}\"")
        print("  " + "-" * 50)

        # vector_io.query auto-embeds the query text using the store's
        # configured embedding model — you just pass the string.
        response = client.vector_io.query(
            vector_store_id=store_id,
            query=query_text,
            params={"max_chunks": 3},
        )

        for rank, (chunk, score) in enumerate(
            zip(response.chunks, response.scores), start=1
        ):
            content = str(chunk.content)
            preview = content[:80] + "..." if len(content) > 80 else content
            print(f"    #{rank}  score={score:.4f}  {preview}")

    print()


def cleanup_vector_store(client: OgxClient, store_id: str) -> None:
    """Delete the vector store to clean up."""
    print("=" * 60)
    print("Step 5: Cleanup — delete the vector store")
    print("=" * 60)

    result = client.vector_stores.delete(vector_store_id=store_id)
    print(f"  Deleted: {result.id} (deleted={result.deleted})")
    print()


def main() -> None:
    print()
    print("L1-M3.1 — Vector IO API")
    print("=" * 60)
    print()

    # ------------------------------------------------------------------
    # Check server connectivity
    # ------------------------------------------------------------------
    print("Checking OGX server connectivity...")
    if not check_server_reachable(OGX_URL):
        print(f"  ERROR: OGX server is not reachable at {OGX_URL}\n")
        print("  Make sure the infrastructure is running:")
        print("    cd ogx-local && podman compose up -d\n")
        print("  Then wait ~30-60 seconds for OGX to start and retry.")
        sys.exit(1)
    print(f"  OGX is reachable at {OGX_URL}\n")

    client = OgxClient(base_url=OGX_URL)

    # ------------------------------------------------------------------
    # Run lesson steps
    # ------------------------------------------------------------------
    store_id = create_vector_store(client)
    list_vector_stores(client)
    insert_documents(client, store_id)
    query_documents(client, store_id)
    cleanup_vector_store(client, store_id)

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print("""
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
""")


if __name__ == "__main__":
    main()
