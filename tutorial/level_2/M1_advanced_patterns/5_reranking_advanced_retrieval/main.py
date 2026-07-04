"""L2-M1.5 — Reranking and Advanced Retrieval

Demonstrates two-stage retrieval: vector search for broad recall,
then reranking for high precision.  Uses the experimental OGX
/v1alpha/inference/rerank endpoint when available, otherwise falls
back to a simple keyword-overlap scorer to illustrate the concept.
"""

import sys

import httpx
from ogx_client import OgxClient

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"
STORE_NAME = "rerank-demo"

# Sample documents about machine learning concepts
DOCUMENTS = [
    ("ml-1", "Gradient descent is an optimization algorithm used to minimize a loss function by iteratively updating model parameters in the direction of steepest descent. The learning rate controls how large each step is."),
    ("ml-2", "Backpropagation computes the gradient of the loss function with respect to each weight by applying the chain rule layer by layer from output to input. It is the foundation of training neural networks."),
    ("ml-3", "Overfitting occurs when a model learns the training data too well, capturing noise rather than the underlying pattern. Techniques like dropout, regularization, and early stopping help prevent overfitting."),
    ("ml-4", "A decision tree splits data into branches based on feature values. Random forests combine many decision trees to reduce variance and improve prediction accuracy through ensemble averaging."),
    ("ml-5", "Convolutional neural networks (CNNs) use convolutional layers to detect spatial patterns in images. Pooling layers reduce dimensionality while preserving the most important features."),
    ("ml-6", "Transfer learning allows a model pre-trained on a large dataset to be fine-tuned on a smaller, domain-specific dataset. This dramatically reduces training time and data requirements."),
    ("ml-7", "The learning rate schedule adjusts the step size during training. Common strategies include step decay, cosine annealing, and warm-up followed by linear decay."),
    ("ml-8", "Batch normalization normalizes layer inputs to stabilize and accelerate training. It reduces internal covariate shift and allows higher learning rates without divergence."),
    ("ml-9", "Stochastic gradient descent (SGD) approximates the true gradient by computing it over a random mini-batch rather than the full dataset. This adds noise that can help escape local minima."),
    ("ml-10", "Attention mechanisms allow a model to focus on the most relevant parts of the input sequence. Transformers use self-attention to capture long-range dependencies without recurrence."),
]

QUERIES = [
    "How does gradient descent work?",
    "How can I prevent my model from overfitting?",
    "What are attention mechanisms in deep learning?",
]


def header(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def check_server(url: str) -> bool:
    for path in ("/v1/health", "/v1/models"):
        try:
            httpx.get(f"{url}{path}", timeout=5).raise_for_status()
            return True
        except Exception:
            continue
    return False


def check_rerank(url: str) -> bool:
    try:
        r = httpx.post(f"{url}/v1alpha/inference/rerank",
                       json={"model": MODEL, "query": "t", "documents": ["t"]},
                       timeout=10)
        return r.status_code != 404
    except Exception:
        return False


def do_rerank(query: str, docs: list[str], use_api: bool) -> list[dict]:
    """Call the OGX rerank endpoint or fall back to keyword overlap."""
    if use_api:
        r = httpx.post(f"{OGX_URL}/v1alpha/inference/rerank",
                       json={"model": MODEL, "query": query, "documents": docs},
                       timeout=30)
        r.raise_for_status()
        return r.json().get("results", [])
    # Simulated reranker: keyword-overlap scoring
    qtokens = set(query.lower().split())
    scored = []
    for idx, doc in enumerate(docs):
        overlap = len(qtokens & set(doc.lower().split()))
        scored.append({"index": idx, "score": overlap / max(len(qtokens), 1),
                       "document": doc})
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def preview(text: str, width: int = 65) -> str:
    return text[:width] + "..." if len(text) > width else text


# ------------------------------------------------------------------
# Steps
# ------------------------------------------------------------------

def step1_setup(client: OgxClient) -> str:
    header("Step 1: Setup -- create vector store and insert documents")
    test = client.embeddings.create(model=MODEL, input="test")
    dim = len(test.data[0].embedding)
    print(f"  Embedding dimension: {dim}")

    store = client.vector_stores.create(
        name=STORE_NAME,
        metadata={"embedding_model": MODEL,
                  "embedding_dimension": str(dim),
                  "provider_id": "qdrant"},
    )
    print(f"  Created: {store.name} (id={store.id})")

    texts = [t for _, t in DOCUMENTS]
    emb = client.embeddings.create(model=MODEL, input=texts)
    chunks = [{"chunk_id": did, "content": txt,
               "embedding": emb.data[i].embedding,
               "embedding_model": MODEL, "embedding_dimension": dim,
               "chunk_metadata": {"document_id": did}}
              for i, (did, txt) in enumerate(DOCUMENTS)]
    client.vector_io.insert(vector_store_id=store.id, chunks=chunks)
    print(f"  Inserted {len(chunks)} documents.\n")
    return store.id


def step2_baseline(client: OgxClient, sid: str) -> dict[str, list[tuple[str, float]]]:
    header("Step 2: Basic retrieval (baseline)")
    results: dict[str, list[tuple[str, float]]] = {}
    for q in QUERIES:
        print(f"\n  Query: \"{q}\"\n  {'-' * 50}")
        r = client.vector_io.query(vector_store_id=sid, query=q,
                                   params={"max_chunks": 5})
        ranked = []
        for i, (c, s) in enumerate(zip(r.chunks, r.scores), 1):
            txt = str(c.content)
            print(f"    #{i}  score={s:.4f}  {preview(txt)}")
            ranked.append((txt, s))
        results[q] = ranked
    print()
    return results


def step3_rerank(client: OgxClient, sid: str,
                 api: bool) -> dict[str, list[tuple[str, float]]]:
    header("Step 3: Rerank API")
    if api:
        print("  Using OGX endpoint: /v1alpha/inference/rerank")
    else:
        print("  Rerank endpoint not available -- using simulated reranker.")
    results: dict[str, list[tuple[str, float]]] = {}
    for q in QUERIES:
        r = client.vector_io.query(vector_store_id=sid, query=q,
                                   params={"max_chunks": 5})
        docs = [str(c.content) for c in r.chunks]
        ranked = do_rerank(q, docs, api)
        print(f"\n  Query: \"{q}\"\n  {'-' * 50}")
        items = []
        for i, item in enumerate(ranked, 1):
            doc = item.get("document", docs[item.get("index", 0)])
            sc = item.get("score", 0.0)
            print(f"    #{i}  score={sc:.4f}  {preview(doc)}")
            items.append((doc, sc))
        results[q] = items
    print()
    return results


def step4_pipeline(client: OgxClient, sid: str, api: bool) -> None:
    header("Step 4: Two-stage retrieval pipeline")
    q = "How does gradient descent work?"
    print(f"  Query: \"{q}\"\n")

    print("  Stage 1: Vector search top-10 (broad recall)")
    r = client.vector_io.query(vector_store_id=sid, query=q,
                               params={"max_chunks": 10})
    docs = [str(c.content) for c in r.chunks]
    for i, (txt, s) in enumerate(zip(docs, r.scores), 1):
        print(f"    #{i}  score={s:.4f}  {preview(txt, 55)}")

    print("\n  Stage 2: Rerank to top-3 (high precision)")
    ranked = do_rerank(q, docs, api)[:3]
    for i, item in enumerate(ranked, 1):
        doc = item.get("document", docs[item.get("index", 0)])
        print(f"    #{i}  score={item.get('score', 0):.4f}  {preview(doc, 55)}")
    print("\n  Pipeline narrows 10 candidates to the 3 most relevant.")


def step5_compare(baseline: dict[str, list[tuple[str, float]]],
                  reranked: dict[str, list[tuple[str, float]]]) -> None:
    header("Step 5: Quality comparison -- retrieval vs retrieval+rerank")
    for q in QUERIES:
        print(f"\n  Query: \"{q}\"\n  {'-' * 50}")
        base = [t[:55] for t, _ in baseline.get(q, [])]
        rerank = [t[:55] for t, _ in reranked.get(q, [])]
        print("  Retrieval-only:")
        for i, d in enumerate(base[:3], 1):
            print(f"    #{i}  {d}...")
        print("  After reranking:")
        for i, d in enumerate(rerank[:3], 1):
            tag = ""
            if d in base:
                old = base.index(d) + 1
                if i < old:
                    tag = f"  [UP from #{old}]"
                elif i > old:
                    tag = f"  [DOWN from #{old}]"
                else:
                    tag = "  [same]"
            print(f"    #{i}  {d}...{tag}")
    print()


def step6_guidance() -> None:
    header("Step 6: When to use reranking")
    print("""
  USE reranking when:
    - Large corpora (1000s+ docs) -- many near-ties in embedding space
    - Precision-critical apps (legal, medical, compliance)
    - Multi-topic corpora with overlapping subjects
    - Short queries + long documents (cross-encoders handle this better)

  SKIP reranking when:
    - Small corpora (<100 docs) -- vector search is sufficient
    - Latency-sensitive apps -- reranking adds 50-200ms per query
    - Embeddings already separate results well (top-1 accuracy >90%)

  Rule of thumb: retrieve 3-5x more than needed, rerank to final set.
""")


def step7_cleanup(client: OgxClient, sid: str) -> None:
    header("Step 7: Cleanup")
    r = client.vector_stores.delete(vector_store_id=sid)
    print(f"  Deleted: {r.id} (deleted={r.deleted})\n")


def main() -> None:
    print("\nL2-M1.5 — Reranking and Advanced Retrieval")
    print("=" * 60)
    print("\n  Two-stage retrieval: vector search + reranking.")

    print("\nChecking OGX server...")
    if not check_server(OGX_URL):
        print(f"  ERROR: OGX not reachable at {OGX_URL}")
        print("  Run: cd ogx-local && podman compose up -d")
        sys.exit(1)
    print(f"  OGX is reachable at {OGX_URL}")

    api = check_rerank(OGX_URL)
    print(f"  Rerank endpoint: {'AVAILABLE' if api else 'NOT AVAILABLE (simulated)'}")

    client = OgxClient(base_url=OGX_URL)

    sid = step1_setup(client)
    bl = step2_baseline(client, sid)
    rr = step3_rerank(client, sid, api)
    step4_pipeline(client, sid, api)
    step5_compare(bl, rr)
    step6_guidance()
    step7_cleanup(client, sid)

    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print("""
  You have successfully:
  1. Built a vector store with 10 ML-concept documents
  2. Performed baseline vector similarity retrieval
  3. Applied reranking to reorder candidates by relevance
  4. Ran a two-stage pipeline (top-10 retrieve, top-3 rerank)
  5. Compared retrieval-only vs retrieval+rerank quality
  6. Learned when reranking is worth the overhead

  Key insight: two-stage retrieval separates recall from precision.
  This is the standard pattern in production RAG systems.

  Next: L2-M1.6 — File Processors
""")


if __name__ == "__main__":
    main()
