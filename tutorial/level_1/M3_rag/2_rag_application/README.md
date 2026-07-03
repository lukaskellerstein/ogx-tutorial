# L1-M3.2 — Building a RAG Application

**Level:** Essentials
**Duration:** 1 hour

## Overview

This lesson builds an end-to-end Retrieval-Augmented Generation (RAG) application using OGX APIs. You will ingest a knowledge base into a Qdrant vector store, retrieve relevant context for user questions, and generate grounded answers through the OGX inference API. The lesson also demonstrates multi-turn RAG conversations and compares OGX RAG with the LangChain approach.

## Prerequisites

- Completed: L1-M3.1 Vector IO API
- Infrastructure running: OGX (port 8321), Qdrant (port 6333), Ollama
- Python 3.10+ with `uv` installed

## Concepts

### What is RAG?

RAG (Retrieval-Augmented Generation) is a pattern that grounds LLM responses in real data. Instead of relying solely on what the model learned during training, RAG retrieves relevant documents from a knowledge base and injects them into the prompt as context. This reduces hallucination and lets the model answer questions about your specific data.

### The RAG Pipeline

A RAG application has three stages:

1. **Ingest** — Prepare your knowledge base by chunking documents, generating embeddings for each chunk, and storing them in a vector database.
2. **Retrieve** — When a user asks a question, embed the question and perform a similarity search against the vector store to find the most relevant chunks.
3. **Generate** — Build a prompt that includes the retrieved context alongside the user question, then send it to the LLM for a grounded answer.

### Why OGX for RAG?

OGX provides all three capabilities (embeddings, vector storage, inference) through a single API surface. You do not need separate libraries for embedding generation, vector database access, and LLM inference. The `ogx-client` SDK handles everything.

### Multi-Turn RAG

In a real application, users ask follow-up questions. Each turn goes through the same retrieve-then-generate cycle. This ensures every answer is grounded in the knowledge base, not just the model's memory of the conversation.

## Step-by-Step

### Step 1: Define the Knowledge Base

We create a list of document chunks about OGX. Each chunk has an `id` and `text` field. In a production application, these chunks would come from document loaders and text splitters; here we define them inline for clarity.

```python
DOCUMENTS = [
    {
        "id": "ogx-overview",
        "text": "OGX (Open GenAI Stack) is an open-source unified AI runtime..."
    },
    # ... 7 more chunks covering providers, APIs, agents, safety, etc.
]
```

### Step 2: Create a Vector Store

Before ingesting documents, create a named vector store. OGX routes this to the configured backend (Qdrant in our case).

```python
store = client.vector_stores.create(name=VECTOR_STORE_NAME)
```

### Step 3: Generate Embeddings and Ingest

Generate embeddings for all chunks using the OGX Embeddings API, then insert them into the vector store via Vector IO.

```python
# Generate embeddings
response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
embeddings = [item.embedding for item in response.data]

# Build chunk objects and insert
client.vector_io.insert(
    vector_store_id=vector_store_id,
    chunks=[
        {
            "chunk_id": doc["id"],
            "content": doc["text"],
            "embedding": emb,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": len(emb),
            "chunk_metadata": {"document_id": doc["id"]},
        }
        for doc, emb in zip(DOCUMENTS, embeddings)
    ],
)
```

### Step 4: Retrieve Relevant Context

When a question comes in, query the vector store for the top-3 most relevant chunks. OGX handles embedding the query and performing similarity search.

```python
result = client.vector_io.query(
    vector_store_id=vector_store_id,
    query=question,
    params={"max_chunks": 3},
)
```

Each result includes a chunk and a relevance score.

### Step 5: Generate a Grounded Answer

Build a system prompt that injects the retrieved context, then call chat completion. The model answers using only the provided context.

```python
system_prompt = (
    "Answer using ONLY the provided context. "
    "Cite source IDs when possible.\n\n"
    f"Context:\n{context_text}"
)

response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": question},
    ],
)
```

### Step 6: Multi-Turn RAG

A second question runs through the same retrieve-then-generate cycle. Each turn independently fetches relevant context, so the model always has fresh, grounded information.

## Running the Lesson

```bash
cd tutorial/level_1/M3_rag/2_rag_application
uv sync
uv run python main.py
```

## Expected Output

```
L1-M3.2 — Building a RAG Application
============================================================

  OGX server is reachable at http://localhost:8321

============================================================
Stage 1: Ingest — embedding and storing documents
============================================================
  Created vector store 'rag-knowledge-base' (id=...)
  Generating embeddings for 8 chunks...
  Embedding dimension: 384
  Inserting 8 chunks into vector store...
  Ingestion complete.

============================================================
Turn 1: Asking about OGX providers
============================================================

  --- Retrieve ---
  Retrieving top-3 chunks for: "What inference providers does OGX support?"
    [0.8923] ogx-providers: OGX supports over 50 pluggable providers including 23 inf...
    [0.7841] ogx-inference-api: The OGX Inference API provides chat completions, text...
    [0.6512] ogx-overview: OGX (Open GenAI Stack) is an open-source unified AI runtim...

  --- Generate ---
  Question: What inference providers does OGX support?
  Answer:   According to the context, OGX supports over 50 pluggable providers
            including 23 inference providers such as vLLM, Ollama, OpenAI,
            Anthropic, AWS Bedrock, and Azure [Source: ogx-providers].

============================================================
Turn 2: Follow-up about tools and MCP
============================================================

  --- Retrieve ---
  Retrieving top-3 chunks for: "How does OGX handle tool calling and MCP integration?"
    [0.8756] ogx-tool-runtime: The Tool Runtime API enables tool calling within OGX...
    [0.7234] ogx-agents: The OGX Agents API lets you create agents with a model, syst...
    [0.5891] ogx-overview: OGX (Open GenAI Stack) is an open-source unified AI runtim...

  --- Generate ---
  Question: How does OGX handle tool calling and MCP integration?
  Answer:   OGX provides a Tool Runtime API that enables tool calling. You can
            register custom tools with function signatures or connect MCP servers
            as tool providers. Built-in tools include web search and code
            interpreter [Source: ogx-tool-runtime].

============================================================
OGX RAG vs LangChain RAG
============================================================

  OGX RAG:
    - Single API surface (inference + vector IO + embeddings)
    - Fewer dependencies — just ogx-client
    - Tighter integration between embedding, storage, and inference
    - Provider-agnostic: swap Qdrant for FAISS without code changes

  LangChain RAG:
    - Larger ecosystem of document loaders, splitters, retrievers
    - More flexibility in retrieval strategies (MMR, ensemble, etc.)
    - Rich chain composition for complex multi-step pipelines
    - Broader community and more third-party integrations

  Hybrid approach: use LangChain for document processing and
  chunking, then OGX for inference and retrieval at runtime.

  Cleaned up vector store 'rag-knowledge-base'.

============================================================
Done!
============================================================

  You have successfully:
  1. Ingested documents into a Qdrant vector store via OGX
  2. Retrieved relevant context using similarity search
  3. Generated answers grounded in retrieved context
  4. Run a multi-turn RAG conversation

  Next: L1-M4.1 — Tool Runtime API
  (custom tools, MCP integration, and tool calling with OGX)
```

Note: Exact scores and answer text will vary depending on the model and embedding configuration.

## Key Takeaways

- **RAG = Retrieve + Generate**: always ground LLM answers in your own data to reduce hallucination.
- **OGX unifies the RAG stack**: embeddings, vector storage, and inference through a single client -- no need to wire up separate libraries.
- **Vector IO abstracts the backend**: the same code works whether you use Qdrant, FAISS, ChromaDB, or any other supported vector store.
- **Context injection via system prompt**: retrieved chunks are formatted into the system message so the model treats them as authoritative context.
- **Multi-turn RAG re-retrieves each turn**: every question gets fresh, relevant context from the knowledge base.

## Next Steps

Continue to **L1-M4.1 -- Tool Runtime API**, where you will learn how to register custom tools, connect MCP servers, and enable tool calling within OGX. In Level 2, we will explore advanced RAG patterns including hybrid search, re-ranking, and production deployment with a dedicated Qdrant server.
