# L2-M1.6 — File Processors

**Level:** Practitioner
**Duration:** 30 min

## Overview

In this lesson you will learn how to use the experimental File Processors API to automate document ingestion. Instead of the multi-step manual pipeline from L1-M3 (parse, chunk, embed, insert), File Processors handle the entire flow in a single API call: upload a file and let OGX parse, chunk, embed, and store the resulting vectors automatically.

## Prerequisites

- Completed: L2-M1.5 Reranking and Advanced Retrieval
- Completed: L1-M3.1 Vector IO API (manual ingestion baseline)
- Infrastructure running: OGX (port 8321), Ollama with `gemma4:e4b`

## Concepts

### The document ingestion problem

In L1-M3.1 you learned to ingest documents manually: read text, generate embeddings, build chunk objects, and insert them into a vector store. This works well for small datasets, but becomes tedious when you need to process files in standard formats (PDF, DOCX, HTML) at scale. Each format requires its own parsing logic, and the embed-then-insert boilerplate repeats for every document.

### File Processors API

The File Processors API (`/v1alpha/file_processors`) automates this pipeline:

```
Upload file --> Parse --> Chunk --> Embed --> Store in vector store
```

You upload a file via the Files API, then call the processor endpoint with a chunking strategy and embedding model. OGX handles parsing, chunking, embedding, and storage internally.

### Supported file types

| Format | Extension | Notes |
|--------|-----------|-------|
| Plain text | `.txt` | Split by configured strategy |
| Markdown | `.md` | Heading-aware parsing |
| HTML | `.html` | Tags stripped, structure preserved |
| PDF | `.pdf` | Layout-aware extraction |
| Word | `.docx` | Text from paragraphs and tables |

### Chunking strategies

How a document is split into chunks affects retrieval quality:

- **Fixed-size** -- split every N tokens. Simple and fast, but may cut mid-sentence.
- **Sentence-based** -- split on sentence boundaries using punctuation detection. Good balance of quality and speed.
- **Semantic** -- split on topic shifts detected by embedding similarity. Best retrieval quality, but slower.

Most strategies support an overlap parameter (typically 10-20% of chunk size) that repeats content at boundaries to prevent losing cross-chunk context.

### Experimental status

The File Processors API lives under `/v1alpha/`, indicating it is experimental. The endpoint path, request format, and response schema may change between OGX versions. Not all OGX distributions include file processor providers.

## Step-by-Step

### Step 1: Check File Processors availability

Probe `GET /v1alpha/file_processors` to see if the endpoint exists in your OGX distribution. A 404 means the API is not available -- the lesson handles this gracefully and shows reference usage instead.

```python
resp = httpx.get(f"{OGX_URL}/v1alpha/file_processors", timeout=10)
if resp.status_code == 200:
    print("File Processors available!")
elif resp.status_code == 404:
    print("Not available in this distribution.")
```

### Step 2: Document ingestion pipeline

Understand the conceptual pipeline that File Processors automate: upload, parse, chunk, embed, store. This replaces the 4+ step manual process.

### Step 3: Manual ingestion recap

Revisit the manual approach from L1-M3.1 as a baseline comparison. This step creates a temporary vector store, manually embeds a sample document, inserts it, and queries it -- exactly the process File Processors aim to simplify.

```python
# Manual pipeline (L1-M3 approach)
emb_response = client.embeddings.create(model=MODEL, input=text)
client.vector_io.insert(
    vector_store_id=store.id,
    chunks=[{
        "chunk_id": "doc-1",
        "content": text,
        "embedding": emb_response.data[0].embedding,
        "embedding_model": MODEL,
        "embedding_dimension": dim,
    }],
)
```

### Step 4: File Processors API

If the API is available, demonstrate it live: create a sample text file, upload it via `/v1/files`, and process it via `/v1alpha/file_processors/process`. If the API is not available, print the expected usage pattern:

```python
# Upload file
resp = httpx.post(
    f"{OGX_URL}/v1/files",
    files={"file": ("document.txt", f, "text/plain")},
)
file_id = resp.json()["id"]

# Process: parse, chunk, embed, and optionally store
resp = httpx.post(
    f"{OGX_URL}/v1alpha/file_processors/process",
    json={
        "file_id": file_id,
        "chunking_strategy": "sentence",
        "embedding_model": "ollama/gemma4:e4b",
        "vector_store_id": "my-docs",
    },
)
chunks = resp.json()["chunks"]
```

### Step 5: Chunking strategies

Compare fixed-size, sentence-based, and semantic chunking. Each has tradeoffs between speed, quality, and predictability.

### Step 6: Manual vs File Processors comparison

A side-by-side table comparing the two approaches across file parsing, chunking, embedding, storage, lines of code, and level of control.

### Step 7: Limitations

Review the maturity caveats: API instability, distribution support, file size limits, format parsing quality, and lack of streaming.

## Running the Lesson

```bash
cd tutorial/level_2/M1_advanced_patterns/6_file_processors
uv sync
uv run python main.py
```

## Expected Output

```
L2-M1.6 — File Processors
============================================================

  This lesson explores the experimental File Processors API
  for automated document ingestion: upload, parse, chunk,
  embed, and store -- all in a single API call.

Checking OGX server connectivity...
  OGX is reachable at http://localhost:8321

============================================================
Step 1: Check File Processors availability
============================================================
  Probing GET /v1alpha/file_processors ...
  Status: 404 -- endpoint not found.
  File Processors API is not available in this distribution.

============================================================
Step 2: Document ingestion pipeline
============================================================
  [Pipeline diagram: Upload -> Process -> Chunk -> Embed -> Store]

============================================================
Step 3: Manual ingestion recap (L1-M3 approach)
============================================================
  Created vector store: file-processors-demo (id=...)
  Generated embedding: 2048 dimensions
  Inserted 1 chunk manually
  Query result: "OGX (Open GenAI Stack) is an open-source unified AI..."
  Cleaned up vector store: file-processors-demo

============================================================
Step 4: File Processors API
============================================================
  File Processors API is not available in this distribution.
  Showing the expected API usage for reference:
  [Reference code for file upload and processing]

============================================================
Step 5: Chunking strategies
============================================================
  [Comparison table: fixed-size vs sentence-based vs semantic]

============================================================
Step 6: Manual ingestion vs File Processors
============================================================
  [Side-by-side feature comparison table]

============================================================
Step 7: Limitations and maturity
============================================================
  [Experimental status caveats and recommendations]

============================================================
Summary
============================================================
  File Processors provide an automated alternative to manual
  document ingestion...
```

> Note: If your OGX distribution includes file processor providers, Step 1 will report "available" and Step 4 will demonstrate live file processing instead of showing reference code.

## Key Takeaways

- The File Processors API (`/v1alpha/file_processors`) automates the entire document ingestion pipeline: parse, chunk, embed, and store in one call.
- It supports common file formats (PDF, DOCX, HTML, Markdown, plain text) with configurable chunking strategies (fixed-size, sentence-based, semantic).
- Manual ingestion (L1-M3) gives you full control over every step; File Processors trade control for simplicity and speed.
- The API is experimental (`v1alpha`) -- not all distributions include it, and the interface may change between versions.
- Both approaches produce the same result: embedded chunks in a vector store queryable via Vector IO. You can mix manual and automated ingestion in the same store.

## Next Steps

Continue to **L2-M1.7 -- Production Deployment**, where you will configure OGX for production with PostgreSQL for memory, Qdrant server for vector storage, health checks, logging, and container orchestration.
