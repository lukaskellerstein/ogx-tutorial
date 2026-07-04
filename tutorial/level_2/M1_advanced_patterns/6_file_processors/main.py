"""L2-M1.6 — File Processors

Demonstrates the experimental File Processors API for automated document
ingestion: upload files, chunk them, embed, and store in a vector store --
all through a single API call instead of the manual pipeline from L1-M3.
"""

import sys
import tempfile
from pathlib import Path

import httpx
from ogx_client import OgxClient

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"
VECTOR_STORE_NAME = "file-processors-demo"


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


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


def step1_check_file_processors() -> bool:
    """Check whether the File Processors API is available."""
    print_header("Step 1: Check File Processors availability")

    print("  The File Processors API is experimental and may not be")
    print("  available in all OGX distributions or versions.")
    print()
    print("  Probing GET /v1alpha/file_processors ...")

    try:
        resp = httpx.get(f"{OGX_URL}/v1alpha/file_processors", timeout=10)
        if resp.status_code == 200:
            print(f"  Status: {resp.status_code} -- File Processors available!")
            data = resp.json()
            if isinstance(data, list):
                print(f"  Registered processors: {len(data)}")
                for proc in data:
                    if isinstance(proc, dict):
                        pid = proc.get("processor_id", "unknown")
                        print(f"    - {pid}")
            return True
        elif resp.status_code == 404:
            print(f"  Status: {resp.status_code} -- endpoint not found.")
            print("  File Processors API is not available in this distribution.")
            return False
        else:
            print(f"  Status: {resp.status_code} -- unexpected response.")
            return False
    except Exception as e:
        print(f"  Error checking endpoint: {e}")
        return False


def step2_ingestion_pipeline() -> None:
    """Print the automated ingestion pipeline concept."""
    print_header("Step 2: Document ingestion pipeline")

    print("""
  The File Processors API automates the entire document ingestion
  pipeline into a single API call:

    +──────────+     +─────────+     +───────+     +───────+     +───────+
    │  Upload  │ --> │ Process │ --> │ Chunk │ --> │ Embed │ --> │ Store │
    │  File    │     │ (parse) │     │       │     │       │     │ (VDB) │
    +──────────+     +─────────+     +───────+     +───────+     +───────+

  Supported file types:
    - PDF (.pdf)           - parsed with layout-aware extraction
    - Word (.docx)         - text extracted from paragraphs/tables
    - HTML (.html)         - tags stripped, structure preserved
    - Markdown (.md)       - parsed with heading awareness
    - Plain text (.txt)    - split by configurable strategy

  Without File Processors, you must do each step manually (as in
  L1-M3.1 Vector IO API). File Processors unify this into one call.
""")


def step3_manual_ingestion_recap(client: OgxClient) -> None:
    """Show the manual ingestion approach from L1-M3 as a baseline."""
    print_header("Step 3: Manual ingestion recap (L1-M3 approach)")

    print("  In L1-M3.1 you learned the manual ingestion pipeline:")
    print()
    print("    1. Prepare documents as text strings")
    print("    2. Generate embeddings via client.embeddings.create()")
    print("    3. Build chunk objects with content + embedding")
    print("    4. Insert chunks via client.vector_io.insert()")
    print()

    # Demonstrate the manual steps with a small example
    sample_text = (
        "OGX provides a unified API for inference, RAG, agents, "
        "tool calling, and safety across multiple providers."
    )

    # Create a temporary vector store for the demo
    test_emb = client.embeddings.create(model=MODEL, input="test")
    embedding_dim = len(test_emb.data[0].embedding)

    store = client.vector_stores.create(
        name=VECTOR_STORE_NAME,
        metadata={
            "embedding_model": MODEL,
            "embedding_dimension": str(embedding_dim),
            "provider_id": "qdrant",
        },
    )
    print(f"  Created vector store: {store.name} (id={store.id})")

    # Generate embedding
    emb_response = client.embeddings.create(model=MODEL, input=sample_text)
    embedding = emb_response.data[0].embedding
    print(f"  Generated embedding: {len(embedding)} dimensions")

    # Insert manually
    client.vector_io.insert(
        vector_store_id=store.id,
        chunks=[
            {
                "chunk_id": "manual-doc-1",
                "content": sample_text,
                "embedding": embedding,
                "embedding_model": MODEL,
                "embedding_dimension": embedding_dim,
            }
        ],
    )
    print("  Inserted 1 chunk manually")

    # Verify retrieval
    result = client.vector_io.query(
        vector_store_id=store.id,
        query="What does OGX provide?",
        params={"max_chunks": 1},
    )
    if result.chunks:
        content = str(result.chunks[0].content)
        print(f"  Query result: \"{content[:70]}...\"")
    print()
    print("  This works, but requires 4+ steps for each document.")
    print("  For large document sets, this becomes tedious and error-prone.")

    # Cleanup
    client.vector_stores.delete(vector_store_id=store.id)
    print(f"  Cleaned up vector store: {store.name}")


def step4_file_processors_api(available: bool) -> None:
    """Demonstrate or explain the File Processors API."""
    print_header("Step 4: File Processors API")

    if available:
        print("  File Processors API is available -- demonstrating live usage.")
        print()
        _demo_file_processors_live()
    else:
        print("  File Processors API is not available in this distribution.")
        print("  Showing the expected API usage for reference:")
        print()
        _demo_file_processors_reference()


def _demo_file_processors_live() -> None:
    """Demonstrate the File Processors API with a real call."""
    # Create a sample text file
    sample_content = (
        "Introduction to OGX\n\n"
        "OGX (Open GenAI Stack) is an open-source unified AI runtime. "
        "It provides standardized APIs for inference, RAG, agents, "
        "tool calling, and MCP integration.\n\n"
        "Key Features\n\n"
        "Provider abstraction: OGX supports 23+ inference providers "
        "behind a unified API. You can switch from Ollama to vLLM "
        "without changing application code.\n\n"
        "Built-in RAG: The Vector IO API handles document embedding, "
        "storage, and retrieval across multiple vector database backends "
        "including Qdrant, ChromaDB, and pgvector.\n\n"
        "Agent framework: OGX provides a native Agents API with "
        "multi-turn conversations, tool calling, and memory management."
    )

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False
    ) as f:
        f.write(sample_content)
        tmp_path = f.name

    print(f"  Created sample file: {tmp_path}")
    print(f"  Content length: {len(sample_content)} characters")
    print()

    try:
        # Try uploading via the Files API
        with open(tmp_path, "rb") as f:
            resp = httpx.post(
                f"{OGX_URL}/v1/files",
                files={"file": ("sample.txt", f, "text/plain")},
                timeout=30,
            )

        if resp.status_code in (200, 201):
            file_data = resp.json()
            file_id = file_data.get("id", file_data.get("file_id"))
            print(f"  Uploaded file, ID: {file_id}")

            # Process via File Processors
            process_resp = httpx.post(
                f"{OGX_URL}/v1alpha/file_processors/process",
                json={
                    "file_id": file_id,
                    "chunking_strategy": "sentence",
                    "embedding_model": MODEL,
                },
                timeout=60,
            )

            if process_resp.status_code == 200:
                result = process_resp.json()
                chunks = result.get("chunks", [])
                print(f"  Processing complete: {len(chunks)} chunks generated")
                for i, chunk in enumerate(chunks[:5]):
                    text = chunk.get("content", str(chunk))[:60]
                    print(f"    Chunk {i + 1}: \"{text}...\"")
            else:
                print(f"  Processing returned status {process_resp.status_code}")
                print(f"  Response: {process_resp.text[:200]}")
        else:
            print(f"  File upload returned status {resp.status_code}")
            print(f"  Response: {resp.text[:200]}")
            print()
            print("  Falling back to reference API usage...")
            _demo_file_processors_reference()
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def _demo_file_processors_reference() -> None:
    """Print the expected API usage when the endpoint is not available."""
    print("""\
  # Expected File Processors API usage:
  # ────────────────────────────────────

  import httpx

  OGX_URL = "http://localhost:8321"

  # 1. Upload a file via the Files API
  with open("document.pdf", "rb") as f:
      resp = httpx.post(
          f"{OGX_URL}/v1/files",
          files={"file": ("document.pdf", f, "application/pdf")},
      )
  file_id = resp.json()["id"]

  # 2. Process the file: parse, chunk, embed, and store
  resp = httpx.post(
      f"{OGX_URL}/v1alpha/file_processors/process",
      json={
          "file_id": file_id,
          "chunking_strategy": "sentence",
          "embedding_model": "ollama/gemma4:e4b",
          "vector_store_id": "my-docs",
      },
  )
  result = resp.json()
  print(f"Generated {len(result['chunks'])} chunks")

  # 3. Query the vector store -- chunks are already embedded and stored
  from ogx_client import OgxClient
  client = OgxClient(base_url=OGX_URL)
  results = client.vector_io.query(
      vector_store_id="my-docs",
      query="What is OGX?",
  )

  Note: This replaces the 4-step manual pipeline (embed, build chunks,
  insert, query) with a single process call.
""")


def step5_chunking_strategies() -> None:
    """Explain different chunking strategies."""
    print_header("Step 5: Chunking strategies")

    print("""
  How a document is split into chunks significantly affects retrieval
  quality. File Processors support multiple chunking strategies:

  Strategy         | How It Works                      | Best For
  ─────────────────┼───────────────────────────────────┼──────────────────
  fixed-size       | Split every N tokens              | Uniform chunks,
                   | (e.g., 512 tokens per chunk)      | simple and fast
  ─────────────────┼───────────────────────────────────┼──────────────────
  sentence-based   | Split on sentence boundaries      | Natural text,
                   | using punctuation detection       | preserves meaning
  ─────────────────┼───────────────────────────────────┼──────────────────
  semantic         | Split on topic shifts detected    | Long documents,
                   | by embedding similarity           | best quality

  Choosing the right strategy:

    - Fixed-size: Use when you need predictable chunk sizes for
      token-budget management. Fast but may split mid-sentence.

    - Sentence-based: Default choice for most text. Preserves
      sentence-level meaning. Good balance of quality and speed.

    - Semantic: Best retrieval quality but slower (requires embedding
      similarity computation during chunking). Use for high-value
      documents where retrieval accuracy matters most.

  Overlap:

    Most strategies support an overlap parameter (e.g., 50 tokens)
    that repeats content at chunk boundaries. This prevents losing
    context that spans two chunks. Typical overlap: 10-20% of chunk
    size.
""")


def step6_comparison_table() -> None:
    """Print a comparison of manual vs File Processors ingestion."""
    print_header("Step 6: Manual ingestion vs File Processors")

    print("""
  Feature               | Manual (L1-M3)              | File Processors
  ──────────────────────┼─────────────────────────────┼─────────────────────
  File parsing          | You handle it               | Built-in (PDF, DOCX,
                        | (read text yourself)        | HTML, MD, TXT)
  ──────────────────────┼─────────────────────────────┼─────────────────────
  Chunking              | You split the text          | Configurable strategy
                        |                             | (fixed, sentence,
                        |                             | semantic)
  ──────────────────────┼─────────────────────────────┼─────────────────────
  Embedding             | client.embeddings.create()  | Automatic (specify
                        | (explicit call)             | embedding_model)
  ──────────────────────┼─────────────────────────────┼─────────────────────
  Storage               | client.vector_io.insert()   | Automatic (specify
                        | (build chunk objects)       | vector_store_id)
  ──────────────────────┼─────────────────────────────┼─────────────────────
  Lines of code         | ~30-50 lines                | ~10 lines
  ──────────────────────┼─────────────────────────────┼─────────────────────
  Control               | Full control over every     | Less control, but
                        | step of the pipeline        | faster to implement
  ──────────────────────┼─────────────────────────────┼─────────────────────
  Best for              | Custom pipelines, non-      | Standard document
                        | standard formats, fine-     | ingestion, rapid
                        | grained tuning              | prototyping

  When to use each:

    Manual:
      - You need custom preprocessing (e.g., cleaning HTML, extracting
        tables, language detection)
      - You want to control chunk boundaries precisely
      - Your documents are already in memory as text

    File Processors:
      - You have files on disk in standard formats
      - You want the fastest path from file to searchable vector store
      - You are prototyping and want to minimize boilerplate
""")


def step7_limitations() -> None:
    """Note experimental status and limitations."""
    print_header("Step 7: Limitations and maturity")

    print("""
  The File Processors API is experimental (v1alpha). Keep in mind:

    1. API stability: The endpoint path, request format, and response
       schema may change between OGX versions without notice.

    2. Distribution support: Not all OGX distributions include file
       processor providers. Check your distribution's capabilities.

    3. File size limits: Large files (100+ MB) may time out or exceed
       memory limits. For large-scale ingestion, use the manual
       pipeline with batching.

    4. Format support: While PDF, DOCX, HTML, MD, and TXT are
       targeted, parsing quality varies by format and complexity.
       Complex PDFs with tables/images may not parse perfectly.

    5. No streaming: Unlike inference, file processing does not
       support streaming responses. You submit the job and wait
       for completion.

  Recommendation:

    Use File Processors for prototyping and standard documents.
    For production workloads with strict quality requirements,
    consider the manual pipeline with custom parsing logic --
    you can always switch between the two since both end up
    in the same vector store format.
""")


def main() -> None:
    print()
    print("L2-M1.6 — File Processors")
    print("=" * 60)
    print()
    print("  This lesson explores the experimental File Processors API")
    print("  for automated document ingestion: upload, parse, chunk,")
    print("  embed, and store -- all in a single API call.")

    # Check server
    print()
    print("Checking OGX server connectivity...")
    if not check_server_reachable(OGX_URL):
        print(f"  ERROR: OGX server is not reachable at {OGX_URL}\n")
        print("  Make sure the infrastructure is running:")
        print("    cd ogx-local && podman compose up -d\n")
        print("  Then wait ~30-60 seconds for OGX to start and retry.")
        sys.exit(1)
    print(f"  OGX is reachable at {OGX_URL}")

    client = OgxClient(base_url=OGX_URL)

    # Step 1: Check if File Processors API exists
    fp_available = step1_check_file_processors()

    # Step 2: Explain the ingestion pipeline concept
    step2_ingestion_pipeline()

    # Step 3: Recap manual ingestion from L1-M3
    step3_manual_ingestion_recap(client)

    # Step 4: File Processors API (live or reference)
    step4_file_processors_api(fp_available)

    # Step 5: Chunking strategies
    step5_chunking_strategies()

    # Step 6: Comparison table
    step6_comparison_table()

    # Step 7: Limitations
    step7_limitations()

    # Summary
    print_header("Summary")
    print("""
  File Processors provide an automated alternative to manual
  document ingestion:

    1. Upload a file via /v1/files
    2. Process it via /v1alpha/file_processors/process
    3. Query the resulting chunks via Vector IO

  Manual ingestion (L1-M3) gives you full control; File Processors
  give you speed and simplicity. Choose based on your use case.

  Note: This is an experimental (v1alpha) API -- monitor OGX
  release notes for changes.

  Next: L2-M1.7 -- Production Deployment
""")


if __name__ == "__main__":
    main()
