"""L2-M1.4 — Evaluation and RAG Benchmarks

Demonstrates how to evaluate model quality and benchmark RAG pipelines
through OGX: define eval datasets, score model responses with keyword
matching, measure retrieval quality (precision@k, recall, MRR), and
compare retrieval configurations side by side.
"""

import sys
import time

import httpx
from ogx_client import OgxClient

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"
VECTOR_STORE_NAME = "eval-rag-bench"


# ---------------------------------------------------------------------------
# Eval dataset — question/answer pairs for model evaluation
# ---------------------------------------------------------------------------
EVAL_DATASET: list[dict[str, str]] = [
    {"question": "What is Python?",
     "expected": "programming language"},
    {"question": "What is OGX?",
     "expected": "unified AI runtime"},
    {"question": "What does RAG stand for?",
     "expected": "retrieval augmented generation"},
    {"question": "What is a vector database used for?",
     "expected": "similarity search"},
    {"question": "What is vLLM?",
     "expected": "inference engine"},
    {"question": "What is an embedding?",
     "expected": "numerical representation"},
]

# ---------------------------------------------------------------------------
# RAG knowledge base — documents with known content for benchmarking
# ---------------------------------------------------------------------------
RAG_DOCUMENTS: list[dict[str, str]] = [
    {"id": "doc-python",
     "text": "Python is a high-level, interpreted programming language known "
             "for its readability and versatility. It supports multiple "
             "paradigms including object-oriented and functional programming."},
    {"id": "doc-ogx",
     "text": "OGX (Open GenAI Stack) is an open-source unified AI runtime "
             "providing standardized APIs for inference, RAG, agents, tool "
             "calling, and MCP integration across 23 providers."},
    {"id": "doc-rag",
     "text": "Retrieval Augmented Generation (RAG) combines a retrieval step "
             "with a generation step. Documents are embedded and stored in a "
             "vector database, then relevant chunks are retrieved and passed "
             "as context to a language model for grounded answers."},
    {"id": "doc-vector-db",
     "text": "A vector database stores high-dimensional embeddings and "
             "enables fast similarity search. Popular options include Qdrant, "
             "ChromaDB, FAISS, and Milvus. They are essential for RAG."},
    {"id": "doc-vllm",
     "text": "vLLM is a high-throughput inference engine for large language "
             "models. It uses PagedAttention for efficient memory management "
             "and supports continuous batching for production deployments."},
    {"id": "doc-embeddings",
     "text": "An embedding is a dense numerical representation of text in a "
             "high-dimensional vector space. Similar texts have embeddings "
             "that are close together, enabling semantic similarity search."},
    {"id": "doc-mcp",
     "text": "The Model Context Protocol (MCP) is a standard for connecting "
             "AI models to external tools and data sources. OGX integrates "
             "MCP servers as tool providers for agent workflows."},
]

# RAG eval pairs — each question maps to the document ID that should be
# retrieved in the top results for a correct answer.
RAG_EVAL_PAIRS: list[dict[str, str]] = [
    {"question": "What is Python used for?", "relevant_doc": "doc-python"},
    {"question": "What does OGX provide?", "relevant_doc": "doc-ogx"},
    {"question": "How does RAG work?", "relevant_doc": "doc-rag"},
    {"question": "What is a vector database?", "relevant_doc": "doc-vector-db"},
    {"question": "How does vLLM handle inference?", "relevant_doc": "doc-vllm"},
    {"question": "What are embeddings?", "relevant_doc": "doc-embeddings"},
]


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def check_server(url: str) -> bool:
    """Return True if the OGX server is reachable."""
    for path in ("/v1/health", "/v1/models"):
        try:
            httpx.get(f"{url}{path}", timeout=5).raise_for_status()
            return True
        except Exception:
            continue
    return False


# ---------------------------------------------------------------------------
# Step 1 — Model evaluation with keyword matching
# ---------------------------------------------------------------------------

def keyword_match(response_text: str, expected: str) -> bool:
    """Check whether the expected keyword phrase appears in the response."""
    return expected.lower() in response_text.lower()


def step1_model_eval(client: OgxClient) -> float:
    """Run the eval dataset against the model and return accuracy."""
    print_header("Step 1: Model evaluation — keyword matching")
    print("  Sending each question to the model and checking if the")
    print("  response contains the expected keyword.\n")

    correct = 0
    total = len(EVAL_DATASET)

    for i, item in enumerate(EVAL_DATASET, start=1):
        question = item["question"]
        expected = item["expected"]

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system",
                 "content": "Answer concisely in one or two sentences."},
                {"role": "user", "content": question},
            ],
            max_tokens=150,
        )
        answer = response.choices[0].message.content
        match = keyword_match(answer, expected)
        if match:
            correct += 1

        status = "PASS" if match else "FAIL"
        print(f"  [{status}] Q{i}: {question}")
        print(f"         Expected keyword: \"{expected}\"")
        print(f"         Answer: {answer[:100]}...")
        print()

    accuracy = correct / total if total > 0 else 0.0
    print(f"  Model accuracy: {correct}/{total} = {accuracy:.1%}")
    return accuracy


# ---------------------------------------------------------------------------
# Step 2 — RAG evaluation helpers
# ---------------------------------------------------------------------------

def setup_vector_store(client: OgxClient) -> None:
    """Create the vector store and ingest RAG documents."""
    # Clean up any leftover store from a previous run
    try:
        client.vector_stores.delete(VECTOR_STORE_NAME)
    except Exception:
        pass

    client.vector_stores.create(name=VECTOR_STORE_NAME)
    print(f"  Created vector store: {VECTOR_STORE_NAME}")

    texts = [doc["text"] for doc in RAG_DOCUMENTS]
    print(f"  Generating embeddings for {len(texts)} documents...")
    emb_resp = client.embeddings.create(model=MODEL, input=texts)
    embeddings = [item.embedding for item in emb_resp.data]
    dim = len(embeddings[0])

    chunks = [
        {
            "chunk_id": doc["id"],
            "content": doc["text"],
            "embedding": emb,
            "embedding_model": MODEL,
            "embedding_dimension": dim,
            "chunk_metadata": {"document_id": doc["id"]},
        }
        for doc, emb in zip(RAG_DOCUMENTS, embeddings)
    ]
    client.vector_io.insert(vector_store_id=VECTOR_STORE_NAME, chunks=chunks)
    print(f"  Inserted {len(chunks)} chunks.\n")


def compute_retrieval_metrics(
    client: OgxClient, top_k: int,
) -> dict[str, float]:
    """Evaluate retrieval quality at the given top_k.

    Returns a dict with precision_at_k, recall, and MRR.
    """
    total_precision = 0.0
    total_recall = 0.0
    total_rr = 0.0  # reciprocal rank

    for pair in RAG_EVAL_PAIRS:
        question = pair["question"]
        relevant = pair["relevant_doc"]

        result = client.vector_io.query(
            vector_store_id=VECTOR_STORE_NAME,
            query=question,
            params={"max_chunks": top_k},
        )

        retrieved_ids = [chunk.chunk_id for chunk in result.chunks]

        # Precision@k: fraction of retrieved docs that are relevant
        relevant_in_top_k = 1.0 if relevant in retrieved_ids else 0.0
        precision = relevant_in_top_k / top_k
        total_precision += precision

        # Recall: did we find the relevant document at all?
        total_recall += relevant_in_top_k

        # MRR: reciprocal of the rank of the first relevant result
        if relevant in retrieved_ids:
            rank = retrieved_ids.index(relevant) + 1
            total_rr += 1.0 / rank
        # else rr stays 0

    n = len(RAG_EVAL_PAIRS)
    return {
        "precision_at_k": total_precision / n,
        "recall": total_recall / n,
        "mrr": total_rr / n,
    }


# ---------------------------------------------------------------------------
# Step 3 — RAG benchmark: compare retrieval configurations
# ---------------------------------------------------------------------------

def step3_rag_benchmark(client: OgxClient) -> dict[str, dict[str, float]]:
    """Benchmark retrieval at different top-k values and return results."""
    print_header("Step 2: RAG evaluation setup")
    setup_vector_store(client)

    print_header("Step 3: RAG benchmark — comparing configurations")
    print("  Config A: top-3 retrieval")
    print("  Config B: top-5 retrieval\n")

    configs: dict[str, int] = {"Config A (top-3)": 3, "Config B (top-5)": 5}
    all_results: dict[str, dict[str, float]] = {}

    for label, k in configs.items():
        print(f"  Running retrieval evaluation for {label}...")
        start = time.perf_counter()
        metrics = compute_retrieval_metrics(client, top_k=k)
        elapsed = time.perf_counter() - start
        metrics["latency_sec"] = round(elapsed, 2)
        all_results[label] = metrics

        print(f"    Precision@{k}: {metrics['precision_at_k']:.3f}")
        print(f"    Recall:        {metrics['recall']:.3f}")
        print(f"    MRR:           {metrics['mrr']:.3f}")
        print(f"    Time:          {metrics['latency_sec']:.2f}s")
        print()

    return all_results


# ---------------------------------------------------------------------------
# Step 4 — Results summary table
# ---------------------------------------------------------------------------

def step4_results_table(
    model_accuracy: float, rag_results: dict[str, dict[str, float]],
) -> None:
    """Print a formatted results table."""
    print_header("Step 4: Results summary")

    print(f"\n  Model Evaluation")
    print(f"  {'Metric':<25} {'Value':>10}")
    print(f"  {'-'*25} {'-'*10}")
    print(f"  {'Keyword-match accuracy':<25} {model_accuracy:>9.1%}")

    print(f"\n  RAG Retrieval Benchmark")
    print(f"  {'Config':<20} {'Prec@k':>8} {'Recall':>8} {'MRR':>8} {'Time':>8}")
    print(f"  {'-'*20} {'-'*8} {'-'*8} {'-'*8} {'-'*8}")
    for label, m in rag_results.items():
        print(
            f"  {label:<20} {m['precision_at_k']:>8.3f} "
            f"{m['recall']:>8.3f} {m['mrr']:>8.3f} "
            f"{m['latency_sec']:>7.2f}s"
        )
    print()


# ---------------------------------------------------------------------------
# Step 5 — Regression testing concept
# ---------------------------------------------------------------------------

def step5_regression_testing() -> None:
    """Explain how to build a regression testing workflow."""
    print_header("Step 5: Regression testing for RAG pipelines")
    print("""
  In production, you want to detect when changes to your RAG
  pipeline (new embedding model, different chunk size, updated
  documents) cause quality regressions.

  Workflow:
    1. Define a fixed eval dataset (questions + expected docs).
    2. Run the benchmark and record baseline metrics:
         baseline = {"precision_at_3": 0.333, "recall": 1.0, "mrr": 0.95}
    3. After a change, re-run the benchmark and compare:
         if new_metrics["recall"] < baseline["recall"] - TOLERANCE:
             raise RegressionError("Recall dropped!")
    4. Integrate into CI: run the eval script on every PR that
       touches the RAG pipeline or document corpus.

  Thresholds to watch:
    - Recall drop > 5%  -> retrieval is missing relevant docs
    - MRR drop > 0.1    -> relevant docs are ranking lower
    - Latency increase > 2x -> performance regression

  This simple keyword-match approach works for smoke tests.
  For deeper evaluation, consider LLM-as-judge (using a second
  model to score answer quality) — but that adds cost and
  complexity. Start simple, add sophistication as needed.
""")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    print()
    print("L2-M1.4 — Evaluation and RAG Benchmarks")
    print("=" * 60)
    print()
    print("  This lesson demonstrates how to evaluate model quality")
    print("  and benchmark RAG retrieval pipelines through OGX.")

    if not check_server(OGX_URL):
        print(f"\n  ERROR: OGX server not reachable at {OGX_URL}")
        print("  Start infrastructure:  cd ogx-local && podman compose up -d")
        sys.exit(1)
    print(f"  OGX server is reachable at {OGX_URL}\n")

    client = OgxClient(base_url=OGX_URL)

    # Step 1: Model evaluation
    model_accuracy = step1_model_eval(client)

    # Steps 2-3: RAG benchmark
    rag_results = step3_rag_benchmark(client)

    # Step 4: Summary table
    step4_results_table(model_accuracy, rag_results)

    # Step 5: Regression testing concept
    step5_regression_testing()

    # Cleanup
    try:
        client.vector_stores.delete(VECTOR_STORE_NAME)
        print(f"  Cleaned up vector store '{VECTOR_STORE_NAME}'.")
    except Exception:
        pass

    print_header("Done!")
    print("""
  You have successfully:
  1. Evaluated model quality with keyword-match scoring
  2. Set up a RAG knowledge base for benchmarking
  3. Measured retrieval quality: precision@k, recall, MRR
  4. Compared two retrieval configurations side by side
  5. Learned how to build regression tests for RAG pipelines

  Next: L2-M1.5 — Reranking and Advanced Retrieval
  (two-stage retrieval with the experimental Rerank API)
""")


if __name__ == "__main__":
    main()
