# L2-M1.4 — Evaluation and RAG Benchmarks

**Level:** Practitioner
**Duration:** 45 min

## Overview

Learn how to evaluate model quality and benchmark RAG retrieval pipelines through OGX. You will define eval datasets, score model responses with keyword matching, measure retrieval quality using precision, recall, and MRR, compare retrieval configurations, and understand how to build automated regression tests for your RAG pipelines.

## Prerequisites

- Completed: L2-M1.3 Telemetry and Observability
- Infrastructure running: OGX (port 8321), Qdrant (port 6333), Ollama
- Familiarity with OGX Vector IO and inference APIs (L1-M2, L1-M3)

## Concepts

### Why evaluate?

AI applications need measurable quality signals. Without evaluation, you cannot tell whether a configuration change improved or degraded your system. This lesson introduces two complementary evaluation approaches:

1. **Model evaluation** — Does the model produce correct answers? We use simple keyword matching against expected responses to compute accuracy.

2. **RAG retrieval evaluation** — Does the retrieval step surface the right documents? We measure this with standard information retrieval metrics:
   - **Precision@k** — Of the k retrieved documents, how many are relevant?
   - **Recall** — Did we retrieve the relevant document at all?
   - **MRR (Mean Reciprocal Rank)** — How high does the relevant document rank? A score of 1.0 means it is always the first result.

### Comparing configurations

By running the same eval dataset against different retrieval settings (e.g., top-3 vs top-5), you can make data-driven decisions about your RAG pipeline. More retrieved chunks may improve recall but reduce precision.

### Regression testing

Once you have baseline metrics, you can detect regressions automatically. If a change to your embedding model, chunk size, or document corpus causes recall to drop below a threshold, your CI pipeline can flag it before deployment.

## Step-by-Step

### Step 1: Define the eval dataset

We define a set of question-answer pairs where each expected answer is a keyword phrase. The model's response is scored by checking whether the keyword appears in the output.

```python
EVAL_DATASET = [
    {"question": "What is Python?", "expected": "programming language"},
    {"question": "What is OGX?", "expected": "unified AI runtime"},
    ...
]
```

### Step 2: Run model evaluation

For each question, we call `client.chat.completions.create()` and check the response against the expected keyword. This gives us a simple accuracy metric.

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "Answer concisely in one or two sentences."},
        {"role": "user", "content": question},
    ],
    max_tokens=150,
)
answer = response.choices[0].message.content
match = expected.lower() in answer.lower()
```

### Step 3: Set up the RAG benchmark

We create a vector store with known documents and define QA pairs that map each question to the document that should be retrieved. This lets us measure whether the retrieval step finds the right content.

```python
RAG_EVAL_PAIRS = [
    {"question": "What is Python used for?", "relevant_doc": "doc-python"},
    {"question": "How does RAG work?", "relevant_doc": "doc-rag"},
    ...
]
```

### Step 4: Measure retrieval quality

For each QA pair, we query the vector store and check whether the relevant document appears in the top-k results. We compute three metrics:

- **Precision@k** = (relevant docs in top-k) / k
- **Recall** = 1 if the relevant doc is in the results, else 0
- **MRR** = 1 / rank of the first relevant result (0 if not found)

### Step 5: Compare retrieval configurations

We run the same eval dataset with two configurations — top-3 and top-5 retrieval — and compare the metrics side by side. This shows the tradeoff between precision and recall.

### Step 6: Regression testing concept

The lesson explains how to save baseline metrics and compare them on code changes, forming the foundation of automated RAG quality assurance.

## Running the Lesson

```bash
cd tutorial/level_2/M1_advanced_patterns/4_evaluation_rag_benchmarks
uv sync
uv run python main.py
```

## Expected Output

```
L2-M1.4 — Evaluation and RAG Benchmarks
============================================================

  OGX server is reachable at http://localhost:8321

============================================================
Step 1: Model evaluation — keyword matching
============================================================
  [PASS] Q1: What is Python?
         Expected keyword: "programming language"
         Answer: Python is a high-level, interpreted programming language...

  [PASS] Q2: What is OGX?
         Expected keyword: "unified AI runtime"
         Answer: OGX is an open-source unified AI runtime...
  ...

  Model accuracy: 6/6 = 100.0%

============================================================
Step 2: RAG evaluation setup
============================================================
  Created vector store: eval-rag-bench
  Inserted 7 chunks.

============================================================
Step 3: RAG benchmark — comparing configurations
============================================================
  Config A (top-3):
    Precision@3: 0.333
    Recall:      1.000
    MRR:         0.950

  Config B (top-5):
    Precision@5: 0.200
    Recall:      1.000
    MRR:         0.950

============================================================
Step 4: Results summary
============================================================

  Model Evaluation
  Metric                        Value
  ------------------------- ----------
  Keyword-match accuracy       100.0%

  RAG Retrieval Benchmark
  Config                Prec@k   Recall      MRR     Time
  -------------------- -------- -------- -------- --------
  Config A (top-3)        0.333    1.000    0.950    0.45s
  Config B (top-5)        0.200    1.000    0.950    0.52s

============================================================
Step 5: Regression testing for RAG pipelines
============================================================
  (Workflow explanation and thresholds)

============================================================
Done!
============================================================
```

Note: Exact scores depend on the embedding model and may vary slightly between runs.

## Key Takeaways

- **Simple scoring works**: keyword matching catches obvious failures without the cost of LLM-as-judge evaluation. Start simple and add sophistication as needed.
- **Retrieval metrics matter**: precision@k, recall, and MRR give you quantitative signals about your RAG pipeline's retrieval quality.
- **Configuration comparison is data-driven**: running the same eval set against different top-k values (or chunk sizes, embedding models) lets you make informed decisions.
- **Regression testing prevents silent degradation**: save baseline metrics and compare them automatically when the pipeline changes.
- **Evaluation is an ongoing process**: as your document corpus grows and your model changes, re-run benchmarks to ensure quality stays high.

## Next Steps

L2-M1.5 — Reranking and Advanced Retrieval: use the experimental Rerank API (`/v1alpha/inference/rerank`) for two-stage retrieval that improves precision without sacrificing recall.
