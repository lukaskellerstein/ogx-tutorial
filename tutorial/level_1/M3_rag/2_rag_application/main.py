"""L1-M3.2 — Building a RAG Application.

End-to-end Retrieval-Augmented Generation using OGX APIs:
  Stage 1 — Ingest: chunk documents, embed, store in Qdrant via Vector IO
  Stage 2 — Retrieve: query the vector store for relevant context
  Stage 3 — Generate: pass context + question to the inference API
"""

import sys

import httpx
from ogx_client import OgxClient

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"
EMBEDDING_MODEL = "ollama/all-minilm"
VECTOR_STORE_NAME = "rag-knowledge-base"

DOCUMENTS: list[dict[str, str]] = [
    {"id": "ogx-overview",
     "text": "OGX (Open GenAI Stack) is an open-source unified AI runtime that "
             "provides standardized APIs for inference, RAG, agents, tool calling, "
             "and MCP. It was rebranded from Llama Stack in April 2026."},
    {"id": "ogx-providers",
     "text": "OGX supports over 50 pluggable providers including 23 inference "
             "providers (vLLM, Ollama, OpenAI, Anthropic, AWS Bedrock, Azure) and "
             "15 vector store backends (Qdrant, ChromaDB, FAISS, pgvector, Milvus)."},
    {"id": "ogx-inference-api",
     "text": "The OGX Inference API provides chat completions, text completions, "
             "and embedding generation. It is fully OpenAI-compatible, so any "
             "OpenAI SDK or library like LangChain can connect to OGX directly."},
    {"id": "ogx-vector-io",
     "text": "Vector IO is OGX's abstraction over vector databases, providing "
             "insert and query operations across any backend. Use inline::qdrant "
             "for development and remote::qdrant for production."},
    {"id": "ogx-agents",
     "text": "The OGX Agents API creates agents with a model, instructions, and "
             "tools. Agents support multi-turn conversations through sessions and "
             "turns, and can access vector stores for RAG automatically."},
    {"id": "ogx-safety",
     "text": "OGX provides a Safety API with input and output shields. Input "
             "shields check user messages before processing. Built-in detectors "
             "include content classification, toxicity, and PII filters."},
    {"id": "ogx-tool-runtime",
     "text": "The Tool Runtime API enables tool calling within OGX. Register "
             "custom tools with function signatures or connect MCP servers as "
             "tool providers. Built-in tools include web search and code interpreter."},
    {"id": "ogx-deployment",
     "text": "OGX runs as a stateless HTTP server deployable with Podman or "
             "Kubernetes. A production stack typically uses Podman Compose with "
             "OGX, vLLM, Qdrant, and PostgreSQL."},
]


def check_server(url: str) -> bool:
    """Return True if the OGX server is reachable."""
    for path in ("/v1/health", "/v1/models"):
        try:
            httpx.get(f"{url}{path}", timeout=5).raise_for_status()
            return True
        except Exception:
            continue
    return False


def create_vector_store(client: OgxClient) -> None:
    """Create the vector store if it does not already exist."""
    for store in client.vector_stores.list().data:
        if store.name == VECTOR_STORE_NAME:
            print(f"  Vector store '{VECTOR_STORE_NAME}' already exists")
            return
    client.vector_stores.create(name=VECTOR_STORE_NAME)
    print(f"  Created vector store '{VECTOR_STORE_NAME}'")


def ingest_documents(client: OgxClient) -> None:
    """Stage 1: embed all document chunks and insert into the vector store."""
    print("=" * 60)
    print("Stage 1: Ingest — embedding and storing documents")
    print("=" * 60)
    create_vector_store(client)

    texts = [doc["text"] for doc in DOCUMENTS]
    print(f"  Generating embeddings for {len(texts)} chunks...")
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    embeddings = [item.embedding for item in resp.data]
    dim = len(embeddings[0])
    print(f"  Embedding dimension: {dim}")

    chunks = [
        {"chunk_id": doc["id"], "content": doc["text"], "embedding": emb,
         "embedding_model": EMBEDDING_MODEL, "embedding_dimension": dim,
         "chunk_metadata": {"document_id": doc["id"]}}
        for doc, emb in zip(DOCUMENTS, embeddings)
    ]
    print(f"  Inserting {len(chunks)} chunks into vector store...")
    client.vector_io.insert(vector_store_id=VECTOR_STORE_NAME, chunks=chunks)
    print("  Ingestion complete.\n")


def retrieve_context(
    client: OgxClient, question: str, top_k: int = 3,
) -> list[dict[str, object]]:
    """Stage 2: query the vector store and return the top-k chunks."""
    print(f"  Retrieving top-{top_k} chunks for: \"{question}\"")
    result = client.vector_io.query(
        vector_store_id=VECTOR_STORE_NAME,
        query=question,
        params={"max_chunks": top_k},
    )
    retrieved = []
    for chunk, score in zip(result.chunks, result.scores):
        content = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
        retrieved.append({"content": content, "score": score, "id": chunk.chunk_id})
        print(f"    [{score:.4f}] {chunk.chunk_id}: {content[:70]}...")
    print()
    return retrieved


def generate_answer(
    client: OgxClient, question: str, context_chunks: list[dict[str, object]],
) -> str:
    """Stage 3: build a RAG prompt from retrieved context and generate."""
    context_text = "\n\n".join(
        f"[Source: {c['id']}]\n{c['content']}" for c in context_chunks
    )
    system_prompt = (
        "You are a knowledgeable assistant. Answer the user's question using "
        "ONLY the provided context. If the context does not contain enough "
        "information, say so. Cite source IDs when possible.\n\n"
        f"Context:\n{context_text}"
    )
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content


def rag_turn(client: OgxClient, question: str, turn_label: str) -> None:
    """Run one full RAG turn: retrieve then generate."""
    print("=" * 60)
    print(turn_label)
    print("=" * 60)
    print("\n  --- Retrieve ---")
    chunks = retrieve_context(client, question)
    print("  --- Generate ---")
    answer = generate_answer(client, question, chunks)
    print(f"  Question: {question}")
    print(f"  Answer:   {answer}\n")


def print_comparison() -> None:
    """Print a brief comparison of OGX RAG vs LangChain RAG."""
    print("=" * 60)
    print("OGX RAG vs LangChain RAG")
    print("=" * 60)
    print()
    print("  OGX RAG:")
    print("    - Single API surface (inference + vector IO + embeddings)")
    print("    - Fewer dependencies — just ogx-client")
    print("    - Tighter integration between embedding, storage, and inference")
    print("    - Provider-agnostic: swap Qdrant for FAISS without code changes")
    print()
    print("  LangChain RAG:")
    print("    - Larger ecosystem of document loaders, splitters, retrievers")
    print("    - More flexibility in retrieval strategies (MMR, ensemble, etc.)")
    print("    - Rich chain composition for complex multi-step pipelines")
    print("    - Broader community and more third-party integrations")
    print()
    print("  Hybrid approach: use LangChain for document processing and")
    print("  chunking, then OGX for inference and retrieval at runtime.\n")


def main() -> None:
    print("\nL1-M3.2 — Building a RAG Application")
    print("=" * 60)
    print()

    if not check_server(OGX_URL):
        print(f"  ERROR: OGX server not reachable at {OGX_URL}")
        print("  Start infrastructure:  cd infra && podman compose up -d")
        sys.exit(1)
    print(f"  OGX server is reachable at {OGX_URL}\n")

    client = OgxClient(base_url=OGX_URL)

    # Stage 1 — Ingest
    ingest_documents(client)

    # Stage 2 + 3 — Retrieve and Generate (first question)
    rag_turn(client, "What inference providers does OGX support?",
             "Turn 1: Asking about OGX providers")

    # Multi-turn RAG — second question on a different facet
    rag_turn(client, "How does OGX handle tool calling and MCP integration?",
             "Turn 2: Follow-up about tools and MCP")

    # Comparison
    print_comparison()

    # Cleanup
    try:
        client.vector_stores.delete(VECTOR_STORE_NAME)
        print(f"  Cleaned up vector store '{VECTOR_STORE_NAME}'.")
    except Exception:
        pass

    # Summary
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print()
    print("  You have successfully:")
    print("  1. Ingested documents into a Qdrant vector store via OGX")
    print("  2. Retrieved relevant context using similarity search")
    print("  3. Generated answers grounded in retrieved context")
    print("  4. Run a multi-turn RAG conversation")
    print()
    print("  Next: L1-M4.1 — Tool Runtime API")
    print("  (custom tools, MCP integration, and tool calling with OGX)\n")


if __name__ == "__main__":
    main()
