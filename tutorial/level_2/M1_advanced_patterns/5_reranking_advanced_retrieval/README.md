# L2-M1.5 — Reranking and Advanced Retrieval

**Level:** Practitioner
**Duration:** 30 min

## Overview

In this lesson you will learn how to improve RAG retrieval quality with a two-stage pipeline: first use vector similarity search for broad recall, then apply a reranker to select the most precise results. You will use the experimental OGX `/v1alpha/inference/rerank` endpoint when available, and a simulated reranker as a fallback, then compare quality side-by-side.

## Prerequisites

- Completed: L2-M1.4 Evaluation and RAG Benchmarks
- Infrastructure running: OGX (port 8321), Qdrant (port 6333), Ollama with `gemma4:e4b`
- Familiarity with the Vector Stores API (covered in L1-M3.1)

## Concepts

### The problem with single-stage retrieval

Vector similarity search is a bi-encoder approach: the query and each document are embedded independently, then compared by cosine distance. This is fast but imprecise -- it finds documents in the same semantic neighborhood without deeply comparing query-document relevance. When your corpus is large or documents cover overlapping topics, the top-k results often contain near-ties that are ranked by embedding noise rather than true relevance.

### Two-stage retrieval

The solution used in production RAG systems is two-stage retrieval:

1. **Stage 1 -- Retrieve (broad recall):** Use vector similarity search to fetch a generous set of candidates (e.g., top-10 or top-20). This is fast because the vector index is pre-built.
2. **Stage 2 -- Rerank (high precision):** Pass the candidates through a cross-encoder reranker that scores each query-document pair jointly. This is slower but far more accurate, because the model sees the query and document together.

The result: you get the speed of vector search with the accuracy of a cross-encoder.

### Experimental Rerank API

OGX exposes an experimental reranking endpoint at `/v1alpha/inference/rerank`. It accepts a query and a list of document strings, and returns them reordered by relevance score. Because this API is experimental, it may not be available in all OGX distributions -- the lesson handles this gracefully with a simulated fallback.

```python
resp = httpx.post(f"{OGX_URL}/v1alpha/inference/rerank", json={
    "model": MODEL,
    "query": "How does gradient descent work?",
    "documents": ["doc1 text...", "doc2 text...", ...],
})
```

### When to use reranking

| Scenario | Recommendation |
|----------|---------------|
| Large corpus (1000s+ docs) | Use reranking -- embedding similarity produces many near-ties |
| Precision-critical (legal, medical) | Use reranking -- wrong results have real consequences |
| Small corpus (<100 docs) | Skip -- vector search alone is usually sufficient |
| Latency-sensitive | Skip -- reranking adds 50-200ms per query |

## Step-by-Step

### Step 1: Setup documents

Create a Qdrant-backed vector store and populate it with 10 documents about machine learning concepts. Each document is embedded and inserted as a chunk.

```python
store = client.vector_stores.create(
    name="rerank-demo",
    metadata={
        "embedding_model": MODEL,
        "embedding_dimension": str(embedding_dim),
        "provider_id": "qdrant",
    },
)
client.vector_io.insert(vector_store_id=store.id, chunks=chunks)
```

### Step 2: Basic retrieval (baseline)

Query the vector store for each test query, returning the top-5 results with similarity scores. This is your baseline -- pure vector similarity ranking.

```python
response = client.vector_io.query(
    vector_store_id=store_id,
    query="How does gradient descent work?",
    params={"max_chunks": 5},
)
```

### Step 3: Rerank API

Pass the retrieved candidates through the reranker. If the experimental endpoint is available, call it directly. Otherwise, a simulated keyword-overlap scorer demonstrates the concept.

```python
resp = httpx.post(f"{OGX_URL}/v1alpha/inference/rerank", json={
    "model": MODEL,
    "query": query,
    "documents": [str(c.content) for c in response.chunks],
})
```

### Step 4: Two-stage retrieval pipeline

Run the full pipeline end-to-end for a single query:
- Stage 1: vector search for top-10 candidates (broad recall)
- Stage 2: rerank down to top-3 (high precision)

This demonstrates the standard production pattern: retrieve more than you need, then let the reranker pick the best.

### Step 5: Quality comparison

Compare retrieval-only vs retrieval+rerank ordering for three queries. The output shows which documents moved up or down after reranking, making the quality difference visible.

### Step 6: When to use reranking

Prints practical guidance on when reranking helps (large corpora, precision-critical apps) vs when it is unnecessary overhead (small corpora, latency-sensitive apps).

### Step 7: Cleanup

Delete the vector store to clean up resources.

## Running the Lesson

```bash
cd tutorial/level_2/M1_advanced_patterns/5_reranking_advanced_retrieval
uv sync
uv run python main.py
```

## Expected Output

```
L2-M1.5 — Reranking and Advanced Retrieval
============================================================

  This lesson demonstrates two-stage retrieval: vector search
  for broad recall, then reranking for high precision.

Checking OGX server connectivity...
  OGX is reachable at http://localhost:8321
  Rerank endpoint: NOT AVAILABLE (will use simulated reranker)

============================================================
Step 1: Setup -- create vector store and insert documents
============================================================
  Embedding dimension: 2048
  Created vector store: rerank-demo (id=...)
  Inserted 10 documents.

============================================================
Step 2: Basic retrieval (baseline)
============================================================

  Query: "How does gradient descent work?"
  --------------------------------------------------
    #1  score=0.8234  Gradient descent is an optimization algorithm...
    #2  score=0.7891  Stochastic gradient descent (SGD) approximates...
    #3  score=0.7456  The learning rate schedule adjusts the step...
    ...

============================================================
Step 3: Rerank API
============================================================
  Rerank endpoint not available -- using simulated keyword reranker.

  Query: "How does gradient descent work?"
  --------------------------------------------------
    #1  score=0.6667  Gradient descent is an optimization algorithm...
    #2  score=0.5000  Stochastic gradient descent (SGD) approximates...
    ...

============================================================
Step 4: Two-stage retrieval pipeline
============================================================
  Query: "How does gradient descent work?"

  Stage 1: Vector search for top-10 candidates (broad recall)
    #1  score=0.8234  Gradient descent is an optimization...
    ...
    #10 score=0.4012  Attention mechanisms allow a model...

  Stage 2: Rerank to top-3 candidates (high precision)
    #1  score=0.6667  Gradient descent is an optimization...
    #2  score=0.5000  Stochastic gradient descent (SGD)...
    #3  score=0.3333  The learning rate schedule adjusts...

============================================================
Step 5: Quality comparison -- retrieval vs retrieval+rerank
============================================================

  Query: "How does gradient descent work?"
  --------------------------------------------------
  Retrieval-only order:
    #1  Gradient descent is an optimization algorithm...
    #2  Stochastic gradient descent (SGD) approximates...
    #3  The learning rate schedule adjusts the step si...
  Retrieval+Rerank order:
    #1  Gradient descent is an optimization algorithm...  [unchanged]
    #2  Stochastic gradient descent (SGD) approximates...  [unchanged]
    #3  The learning rate schedule adjusts the step si...  [unchanged]
  ...

============================================================
Step 6: When to use reranking
============================================================
  [Guidance on when reranking helps vs when to skip it]

============================================================
Step 7: Cleanup
============================================================
  Deleted vector store: ... (deleted=True)

============================================================
Done!
============================================================
```

> Note: Exact scores and ordering depend on the embedding model and whether the real rerank endpoint is available. With the simulated reranker, changes in ordering demonstrate the concept even though a cross-encoder model would produce better results.

## Key Takeaways

- Two-stage retrieval (retrieve then rerank) is the standard pattern for production RAG systems -- it separates recall from precision.
- The OGX experimental `/v1alpha/inference/rerank` endpoint provides reranking as a first-class API when available.
- Retrieve 3-5x more candidates than you need, then rerank down to the final set.
- Reranking helps most with large corpora and precision-critical applications; skip it for small corpora or latency-sensitive use cases.
- Even without a dedicated reranker, the two-stage architecture is valuable -- any re-scoring function (keyword overlap, LLM-as-judge, BM25) can serve as the second stage.

## Next Steps

Continue to **L2-M1.6 -- File Processors**, where you will use the experimental `/v1alpha/file_processors` API to automate document ingestion, chunking, and embedding into vector stores.
