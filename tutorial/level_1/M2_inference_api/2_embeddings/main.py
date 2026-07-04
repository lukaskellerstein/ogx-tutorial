"""L1-M2.2 — Embeddings

Generate embeddings via OGX, inspect their properties, batch-embed
multiple texts, and measure semantic similarity with cosine similarity.
"""

import math

from ogx_client import OgxClient


OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Compute cosine similarity between two vectors (no numpy)."""
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def main() -> None:
    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------
    print()
    print("L1-M2.2 — Embeddings")
    print("=" * 60)

    client = OgxClient(base_url=OGX_URL)

    # ------------------------------------------------------------------
    # Step 1: Single embedding
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Step 1: Generate a single embedding")
    print("=" * 60)

    text = "Artificial intelligence is transforming software development."
    response = client.embeddings.create(model=MODEL, input=text)
    embedding = response.data[0].embedding

    print(f"  Text: {text!r}")
    print(f"  Model: {MODEL}")
    print(f"  Embedding generated successfully.")

    # ------------------------------------------------------------------
    # Step 2: Embedding properties
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Step 2: Embedding properties")
    print("=" * 60)

    print(f"  Dimensions: {len(embedding)}")
    print(f"  Data type:  {type(embedding[0]).__name__}")
    print(f"  First 10 values: {embedding[:10]}")

    # ------------------------------------------------------------------
    # Step 3: Batch embeddings
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Step 3: Batch embeddings (multiple texts at once)")
    print("=" * 60)

    texts = [
        "Python is a popular programming language.",
        "Machine learning models learn from data.",
        "The weather is sunny today.",
    ]

    response = client.embeddings.create(model=MODEL, input=texts)

    print(f"  Sent {len(texts)} texts in a single request.")
    print(f"  Received {len(response.data)} embeddings.")
    for i, item in enumerate(response.data):
        print(f"    [{i}] \"{texts[i][:50]}\" -> {len(item.embedding)} dims")

    # ------------------------------------------------------------------
    # Step 4: Cosine similarity
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Step 4: Cosine similarity — measuring semantic relatedness")
    print("=" * 60)

    pairs = [
        ("The cat sat on the mat", "A feline rested on the rug"),
        ("The cat sat on the mat", "Stock markets rose today"),
    ]

    all_texts = [t for pair in pairs for t in pair]
    response = client.embeddings.create(model=MODEL, input=all_texts)
    embeddings = [item.embedding for item in response.data]

    for idx, (text_a, text_b) in enumerate(pairs):
        vec_a = embeddings[idx * 2]
        vec_b = embeddings[idx * 2 + 1]
        similarity = cosine_similarity(vec_a, vec_b)
        label = "similar" if similarity > 0.8 else "dissimilar"
        print()
        print(f"  Pair {idx + 1}:")
        print(f"    A: \"{text_a}\"")
        print(f"    B: \"{text_b}\"")
        print(f"    Cosine similarity: {similarity:.4f}  ({label})")

    # ------------------------------------------------------------------
    # Step 5: Use-case preview
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("Step 5: What's next — embeddings power RAG")
    print("=" * 60)
    print()
    print("  Embeddings are the foundation of Retrieval-Augmented Generation (RAG).")
    print("  In the next module (L1-M3) you will:")
    print("    1. Embed documents and store them in a vector database (Qdrant)")
    print("    2. Query the vector store with a question embedding")
    print("    3. Pass retrieved context to the LLM for grounded answers")
    print()
    print("Done! Next: L1-M3.1 — Vector Stores API")
    print()


if __name__ == "__main__":
    main()
