# L1-M2.2 — Embeddings

**Level:** Essentials
**Duration:** 20 min

## Overview

In this lesson you will generate text embeddings through the OGX inference API, inspect their properties, embed multiple texts in a single batch call, and compute cosine similarity to measure how semantically related two pieces of text are. Embeddings are the foundation for RAG, which you will build in the next module.

## Prerequisites

- Completed: L1-M2.1 Chat and Completion
- Infrastructure running: OGX (port 8321), Ollama with `gemma4:e4b`

## Concepts

### What are embeddings?

An embedding is a dense vector of floating-point numbers that represents the meaning of a piece of text. Texts with similar meanings produce vectors that are close together in the embedding space, while unrelated texts produce vectors that are far apart.

### Embedding generation via `/v1/embeddings`

OGX exposes an OpenAI-compatible embeddings endpoint. You send one or more texts and receive back a list of vectors, one per input. The dimension of each vector depends on the model (e.g., 2048 dimensions for gemma4).

### Batch embedding

Instead of calling the API once per text, you can pass a list of texts in a single request. The server processes them together, which is more efficient for bulk ingestion.

### Cosine similarity

Cosine similarity measures the angle between two vectors, returning a value between -1 and 1. A value close to 1 means the texts are semantically similar; a value near 0 means they are unrelated. It is the standard metric for comparing embeddings.

### Use case: document embedding for RAG

Before a RAG system can retrieve relevant context, every document chunk must be embedded and stored in a vector database. At query time the user's question is also embedded, and the closest stored vectors are returned as context for the LLM.

## Step-by-Step

### Step 1: Generate a single embedding

Create the OGX client and embed a single sentence. The response contains the embedding vector in `response.data[0].embedding`.

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")

response = client.embeddings.create(
    model="ollama/gemma4:e4b",
    input="Artificial intelligence is transforming software development.",
)
embedding = response.data[0].embedding
```

### Step 2: Inspect embedding properties

Print the dimension, data type, and first few values to understand what an embedding looks like.

```python
print(f"Dimensions: {len(embedding)}")
print(f"Data type:  {type(embedding[0]).__name__}")
print(f"First 10:   {embedding[:10]}")
```

### Step 3: Batch embeddings

Pass a list of texts to embed them all in one API call.

```python
texts = [
    "Python is a popular programming language.",
    "Machine learning models learn from data.",
    "The weather is sunny today.",
]
response = client.embeddings.create(model="ollama/gemma4:e4b", input=texts)
# response.data has one entry per input text
```

### Step 4: Cosine similarity

Compare pairs of texts to see how similarity scores differ between related and unrelated content. Cosine similarity is computed using only the standard library (no numpy).

```python
import math

def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
```

- **"The cat sat on the mat"** vs **"A feline rested on the rug"** -- high similarity (semantically equivalent).
- **"The cat sat on the mat"** vs **"Stock markets rose today"** -- low similarity (unrelated topics).

### Step 5: Use-case preview

Embeddings are the building block for RAG. In the next module you will store embeddings in Qdrant and retrieve relevant context for grounded LLM answers.

## Running the Lesson

```bash
cd tutorial/level_1/M2_inference_api/2_embeddings
uv sync
uv run python main.py
```

## Expected Output

```
L1-M2.2 — Embeddings
============================================================

============================================================
Step 1: Generate a single embedding
============================================================
  Text: 'Artificial intelligence is transforming software development.'
  Model: ollama/gemma4:e4b
  Embedding generated successfully.

============================================================
Step 2: Embedding properties
============================================================
  Dimensions: 2048
  Data type:  float
  First 10 values: [0.0123, -0.0456, 0.0789, ...]

============================================================
Step 3: Batch embeddings (multiple texts at once)
============================================================
  Sent 3 texts in a single request.
  Received 3 embeddings.
    [0] "Python is a popular programming language." -> 2048 dims
    [1] "Machine learning models learn from data." -> 2048 dims
    [2] "The weather is sunny today." -> 2048 dims

============================================================
Step 4: Cosine similarity — measuring semantic relatedness
============================================================

  Pair 1:
    A: "The cat sat on the mat"
    B: "A feline rested on the rug"
    Cosine similarity: 0.9123  (similar)

  Pair 2:
    A: "The cat sat on the mat"
    B: "Stock markets rose today"
    Cosine similarity: 0.4567  (dissimilar)

============================================================
Step 5: What's next — embeddings power RAG
============================================================

  Embeddings are the foundation of Retrieval-Augmented Generation (RAG).
  In the next module (L1-M3) you will:
    1. Embed documents and store them in a vector database (Qdrant)
    2. Query the vector store with a question embedding
    3. Pass retrieved context to the LLM for grounded answers

Done!
```

> Note: Exact embedding values, dimensions, and similarity scores will vary depending on the model. The relative ordering (Pair 1 > Pair 2) should be consistent.

## Key Takeaways

- Embeddings are dense vector representations of text produced by the model.
- OGX exposes embeddings via an OpenAI-compatible `/v1/embeddings` endpoint.
- Batch embedding (passing a list) is more efficient than one-at-a-time calls.
- Cosine similarity measures semantic relatedness: high scores mean similar meaning.
- Embeddings are the foundation for RAG -- you will use them in the next module to build a retrieval pipeline.

## Next Steps

Continue to **L1-M3.1 Vector IO API**, where you will store embeddings in Qdrant and perform similarity search using the OGX Vector IO API.
