# OGX (Open GenAI Stack) Tutorial: Syllabus

## Purpose

Learn OGX (formerly Llama Stack) — the open-source unified AI runtime providing standardized, OpenAI-compatible APIs for inference, RAG, agents, tool calling, and MCP. This sub-tutorial covers OGX independently before you use the OGX Operator on OpenShift AI.

## Why a Separate Tutorial?

OGX provides a full API surface for building AI applications: inference, memory, RAG, safety, agents, and tool calling — all through a single, unified API. It supports 23 inference providers (not limited to Llama models). Understanding its APIs and patterns locally is essential before deploying it on OpenShift AI.

## Naming Note

The project was originally called "Llama Stack" (by Meta). In April 2026, it was rebranded to **OGX (Open GenAI Stack)** to reflect its provider-agnostic nature. OpenShift AI 3.4 still uses "Llama Stack Operator" in some places; 3.5 introduces the "OGX Operator". This tutorial uses "OGX" throughout.

## Target Audience

- Developers building AI applications (RAG, agents, tool calling)
- Anyone preparing for OpenShift AI L2-M1 (RAG) and L2-M3 (Agent Deployment)

## Technical Stack

- **OGX**: Latest (v1.1.3+), runs as a Docker/Podman container
- **Python**: 3.10+
- **Package Manager**: `uv` (each lesson is a standalone `uv` project)
- **Inference Backend**: vLLM (primary, Docker container) — Ollama as optional fallback for Apple Silicon dev
- **Model**: `google/gemma-4-E4B-it` (4B effective params, ~3 GB at Q4) via vLLM
- **Vector DB**: Qdrant — via OGX `inline::qdrant` (embedded, dev) or `remote::qdrant` (server, production)
- **Memory / KVStore**: SQLite (dev, default) / PostgreSQL (production)
- **Agent API**: Responses API (`/v1/responses`) — the primary agent orchestration interface
- **Agent Frameworks**: LangChain v1.0+, LangGraph (latest), DeepAgents
- **MCP**: OGX Tool Runtime with MCP integration
- **Container Runtime**: Podman (not Docker)

## Reference Sources

- **OGX GitHub**: https://github.com/ogx-ai/ogx
- **OGX Documentation**: https://ogx-ai.github.io/docs
- **OGX Providers**: https://ogx-ai.github.io/docs/providers
- **OGX Python Client**: `pip install ogx-client`
- **OGX K8s Operator**: https://github.com/ogx-ai/ogx-k8s-operator
- **vLLM Docker**: https://hub.docker.com/r/vllm/vllm-openai
- **vLLM Docs**: https://docs.vllm.ai/
- **Qdrant Docs**: https://qdrant.tech/documentation/
- **LangChain samples**: `/Users/lkellers/Projects/github/lukaskellerstein/ai-agents-course/Version_2/6_langchain-ai`
- **MCP samples**: `/Users/lkellers/Projects/github/lukaskellerstein/ai-agents-course/Version_2/2_MCP`
- **OpenShift AI OGX Operator**: https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.4

---

# LEVEL 1 — ESSENTIALS

*Goal: Understand OGX APIs, run inference, build RAG, create agents with the Responses API.*
*Estimated time: ~9-11 hours*

---

## L1-M1: OGX Fundamentals

### L1-1.1 — What is OGX? Architecture Overview
**Duration:** 30 min
**Topics:**
- OGX: unified AI runtime with standardized, OpenAI-compatible APIs
- API surface — **Stable APIs:**
  - `/v1/chat/completions` — chat-style inference (OpenAI-compatible)
  - `/v1/completions` — text completions
  - `/v1/embeddings` — embedding generation
  - `/v1/responses` — agent orchestration with tool use and multi-turn (**primary agent API**)
  - `/v1/models` — model listing and management
  - `/v1/files` — file upload and management
  - `/v1/vector_stores` — document storage and semantic search
  - `/v1/batches` — offline batch processing
  - `/v1/admin/tools` — tool listing and management
  - `/v1/conversations` — conversation state management
  - `/v1/prompts` — prompt templates and versioning
- API surface — **Experimental APIs:**
  - `/v1alpha/admin` — providers, routes, health, version
  - `/v1alpha/inference/rerank` — document reranking
  - `/v1alpha/file_processors` — document ingestion and chunking
  - `/v1alpha/interactions` — Google Interactions API compatibility
  - `/v1alpha/admin/connectors` — external tool/service connectors
- Note: older docs may reference legacy paths (`/v1/inference`, `/v1/memory`, `/v1/vector_io`, `/v1/safety`, `/v1alpha/agents`) — the new API is OpenAI-compatible
- Provider-agnostic: 23 inference providers (vLLM, Ollama, OpenAI, Anthropic, Bedrock, etc.)
- Distribution concept: pre-configured bundles of providers for specific use cases
- Comparison with direct vLLM: OGX adds RAG, agents, memory, safety on top

**Deliverables:**
- Architecture diagram: OGX API layers and providers
- Full API surface overview table (stable + experimental)

---

### L1-1.2 — Installing and Running OGX
**Duration:** 45 min
**Topics:**
- Installation: `uv pip install ogx[starter]` or run as container
- Running OGX as a Podman container:
  ```
  podman run -it -p 8321:8321 llamastack/distribution-starter
  ```
- Choosing a distribution:
  - `starter` — general-purpose (recommended)
  - `remote-vllm` — pointing to a separate vLLM server (production)
- vLLM as inference backend:
  - Run vLLM in a separate container: `vllm/vllm-openai` with `google/gemma-4-E4B-it`
  - Configure OGX `remote::vllm` provider to connect
- Ollama as fallback (Apple Silicon dev): `inline::ollama`
- Configuration: `run.yaml` with provider settings
- Python client: `OGXClient`
- First API call: chat completion through OGX using `/v1/chat/completions`
- Verify: list models via `/v1/models`

**Deliverables:**
- OGX server running as Podman container with vLLM backend
- vLLM serving `gemma-4-E4B-it` model
- Python client calling the inference API via OpenAI-compatible endpoint

---

## L1-M2: Inference API

### L1-2.1 — Chat and Completion
**Duration:** 30 min
**Topics:**
- Chat completions: `/v1/chat/completions` (was `/v1/inference/chat_completion`)
- Text completions: `/v1/completions` (was `/v1/inference/completion`)
- Streaming responses
- System prompts and conversation history
- Parameters: temperature, max_tokens, top_p
- Model selection and registration via `/v1/models`
- Comparing with direct vLLM API: OGX adds RAG, agents, memory, safety, tools on top
- Model: `google/gemma-4-E4B-it` (4B effective params) via vLLM

**Deliverables:**
- Chat and completion calls via OGX client
- Streaming example

---

### L1-2.2 — Embeddings
**Duration:** 20 min
**Topics:**
- Embedding generation: `/v1/embeddings` (was `/v1/inference/embeddings`)
- Supported embedding models
- Batch embedding generation
- Use case: generating embeddings for RAG document ingestion

**Deliverables:**
- Embeddings generated via OGX
- Similarity comparison between text pairs

---

## L1-M3: RAG with OGX

### L1-3.1 — Vector Stores API
**Duration:** 45 min
**Topics:**
- Vector Stores: OGX's abstraction over vector databases
- API path: `/v1/vector_stores` (was `/v1/vector_io`)
- Operations:
  - Create/list/delete vector stores
  - Insert documents with embeddings
  - Similarity search and retrieval
- Qdrant as vector backend:
  - `inline::qdrant` — embedded mode (zero-config, great for dev)
  - `remote::qdrant` — server mode (production, Docker container)
- Other supported backends: ChromaDB, FAISS, pgvector, Milvus, Weaviate, Elasticsearch
- Configuring Qdrant as the vector store in `run.yaml`
- Document chunking and embedding pipeline
- Metadata filtering and hybrid search with Qdrant

**Deliverables:**
- Qdrant configured as OGX vector store
- Documents inserted and similarity search returning relevant chunks

---

### L1-3.2 — Building a RAG Application
**Duration:** 1 hour
**Topics:**
- End-to-end RAG with OGX APIs:
  1. Ingest: chunk documents, embed, store via `/v1/vector_stores`
  2. Retrieve: query vector store for relevant context
  3. Generate: pass context + question to `/v1/chat/completions`
- Conversations API (`/v1/conversations`) for multi-turn RAG
- Comparing with LangChain RAG:
  - OGX: single API surface, fewer dependencies, tighter integration
  - LangChain: more flexibility, larger ecosystem of retrievers/splitters
- Hybrid approach: LangChain for document processing, OGX for inference + retrieval

**Deliverables:**
- RAG application using OGX APIs
- Multi-turn conversation with retrieval context

---

## L1-M4: Tool Calling and MCP

### L1-4.1 — Tool Runtime API
**Duration:** 45 min
**Topics:**
- Tool Runtime: OGX's tool calling infrastructure
- Tool management via `/v1/admin/tools`
- Defining tools: function signatures, parameter schemas
- Built-in tools: web search, code interpreter
- Custom tool registration
- Tool execution flow: LLM decides, OGX executes, result returned
- MCP integration: connecting MCP servers as tool providers
- Comparing with direct MCP: OGX provides a unified tool + inference layer
- Preview: the Responses API (`/v1/responses`) combines tool calling with multi-turn agent orchestration — covered in L1-M5

**Deliverables:**
- Custom tools registered and called through OGX
- MCP server connected as a tool provider

---

## L1-M5: Responses API and Agents

### L1-5.1 — Responses API
**Duration:** 1 hour
**Topics:**
- The Responses API (`/v1/responses`) — OGX's **primary agent orchestration interface**
- Why Responses API: combines inference, tool use, and multi-turn conversation in a single endpoint
- Creating responses with tool definitions
- Multi-turn conversations via `previous_response_id`
- Built-in tool types: web search, file search, code interpreter, MCP tools
- Streaming responses with tool call events
- Comparison: Responses API vs old Agents API (`/v1alpha/agents`)
  - Responses API: OpenAI-compatible, single-endpoint, stateless or stateful, production-ready
  - Old Agents API: required separate create/session/turn calls, now deprecated/legacy
- Comparing with LangGraph agents:
  - OGX Responses: simpler API, native tool/safety integration
  - LangGraph agents: complex state machines, conditional routing, more control

**Deliverables:**
- OGX Responses-based agent with tools, multi-turn conversation
- Comparison: same task with Responses API vs LangGraph agent

---

### L1-5.2 — Agents with RAG
**Duration:** 45 min
**Topics:**
- Combining Responses API with RAG:
  - Agent uses file search tool backed by vector stores
  - Automatic context injection into agent conversations
- Conversations API (`/v1/conversations`) for persistent agent state
- Use case: knowledge assistant that answers questions from a document corpus
- RAG + Tools: agent retrieves context AND calls tools as needed

**Deliverables:**
- RAG-powered agent using Responses API, answering questions from ingested documents
- Agent using both retrieval and tool calling

---

## L1-M6: Safety API

### L1-6.1 — Content Moderation
**Duration:** 30 min
**Topics:**
- Safety configuration in OGX
- Input shields: checking user messages before processing
- Output shields: checking model responses before returning
- Built-in detectors: content classification, toxicity, PII
- Configuring safety for Responses API agents: shields applied automatically
- Integration with NeMo Guardrails and Llama Guard

**Deliverables:**
- Safety shields configured for an OGX agent
- Demonstration: blocked harmful content

---

## L1-M7: Additional APIs

### L1-7.1 — Files, Batches, Conversations, and Prompts
**Duration:** 30 min
**Topics:**
- Files API (`/v1/files`): uploading and managing files for use with agents and RAG
  - Upload, list, retrieve, delete files
  - File types and size limits
- Batches API (`/v1/batches`): offline batch processing
  - Submitting batch inference jobs
  - Monitoring batch status and retrieving results
  - Use case: bulk document classification, large-scale embedding generation
- Conversations API (`/v1/conversations`): managing conversation state
  - Creating, listing, and retrieving conversations
  - Linking conversations to Responses API calls
  - Persistent conversation history across sessions
- Prompts API (`/v1/prompts`): prompt templates and versioning
  - Creating reusable prompt templates
  - Parameterized prompts
  - Version management for prompt iteration

**Deliverables:**
- File uploaded and used in a Responses API call
- Batch job submitted and results retrieved
- Conversation state persisted and retrieved
- Prompt template created and used

---

### Level 1 Summary

| Module | Lessons | Estimated Time |
|--------|---------|---------------|
| M1: Fundamentals | 2 lessons | ~1.25 hours |
| M2: Inference API | 2 lessons | ~50 min |
| M3: RAG | 2 lessons | ~1.75 hours |
| M4: Tool Calling & MCP | 1 lesson | ~45 min |
| M5: Responses API & Agents | 2 lessons | ~1.75 hours |
| M6: Safety API | 1 lesson | ~30 min |
| M7: Additional APIs | 1 lesson | ~30 min |
| **Total** | **11 lessons** | **~9-10 hours** |

---

# LEVEL 2 — PRACTITIONER

*Goal: Advanced patterns, multi-provider, telemetry, evals, production configuration, OGX on OpenShift AI.*
*Estimated time: ~7-9 hours*

---

## L2-M1: Advanced Patterns

### L2-1.1 — Multi-Provider Configuration
**Duration:** 45 min
**Topics:**
- Configuring multiple inference providers in one OGX instance
- Routing: different models for different tasks (chat vs embedding vs safety)
- Fallback chains: primary to secondary provider
- Provider configuration in `run.yaml`
- Custom distributions: bundling providers for specific use cases

**Deliverables:**
- OGX instance with 2+ providers configured
- Routing: chat model vs embedding model

---

### L2-1.2 — Custom Providers and Extensions
**Duration:** 1 hour
**Topics:**
- Building custom providers (e.g., wrapping a local model or API)
- Provider interface: what methods to implement
- Registering custom providers
- Building custom safety detectors
- Plugin architecture

**Deliverables:**
- Custom inference provider wrapping an external API

---

### L2-1.3 — Telemetry and Observability
**Duration:** 45 min
**Topics:**
- OGX OpenTelemetry (OTel) integration for tracing
- Enabling telemetry in `run.yaml`
- Tracing inference calls, tool executions, and Responses API turns
- Exporting traces to Jaeger or compatible backends
- Structured logging: request IDs, latency, token counts
- Correlating OGX traces with downstream provider traces (e.g., vLLM)
- Dashboard setup: visualizing OGX request flows

**Deliverables:**
- OGX instance with OTel tracing enabled
- Traces exported to Jaeger, visualized in the Jaeger UI
- End-to-end trace of a Responses API call with tool use

---

### L2-1.4 — Evaluation and RAG Benchmarks
**Duration:** 45 min
**Topics:**
- OGX evaluation capabilities
- Defining eval tasks: question-answer pairs, expected outputs
- Running evals against different models and providers
- RAG benchmarking through OGX:
  - Measuring retrieval quality (precision, recall, MRR)
  - End-to-end RAG evaluation (retrieval + generation)
  - Comparing retrieval configurations (chunk size, overlap, embedding model)
- Automated regression testing for RAG pipelines

**Deliverables:**
- Eval suite defined and run against an OGX-served model
- RAG benchmark comparing two retrieval configurations
- Results report with metrics

---

### L2-1.5 — Reranking and Advanced Retrieval
**Duration:** 30 min
**Topics:**
- Experimental Rerank API: `/v1alpha/inference/rerank`
- Two-stage retrieval: vector search then rerank for higher relevance
- Configuring reranking models in OGX
- Combining reranking with Vector Stores API for better RAG results
- Comparing retrieval quality: with and without reranking
- When to use reranking: large document corpora, precision-critical applications

**Deliverables:**
- Reranking pipeline: vector search + rerank
- Side-by-side comparison: RAG quality with and without reranking

---

### L2-1.6 — File Processors
**Duration:** 30 min
**Topics:**
- Experimental File Processors API: `/v1alpha/file_processors`
- Document ingestion pipeline via OGX
- Supported file types: PDF, DOCX, HTML, Markdown, plain text
- Chunking strategies: fixed-size, sentence-based, semantic
- Processing flow: upload file, process, chunk, embed, store in vector store
- Comparing with manual ingestion (L1-M3): File Processors automate the pipeline
- Limitations and maturity of the experimental API

**Deliverables:**
- Document ingested via File Processors API
- Chunks stored in vector store and queryable

---

### L2-1.7 — Production Deployment
**Duration:** 45 min
**Topics:**
- Containerizing OGX for production with Podman
- Podman Compose: OGX + vLLM + Qdrant + PostgreSQL
- Configuration for production: logging, metrics, health checks
- PostgreSQL backend for KVStore memory (production-recommended), Qdrant for vector storage
- Scaling considerations: stateless OGX server, external Qdrant + PostgreSQL
- Preview: deployment on OpenShift AI via OGX Operator (ogx-k8s-operator)

**Deliverables:**
- Containerized OGX deployment (Podman)
- Production configuration with PostgreSQL KVStore + Qdrant vector store

---

## L2-M2: OGX on OpenShift AI

### L2-2.1 — OGX Operator Deployment
**Duration:** 45 min
**Topics:**
- Installing the OGX/Llama Stack Operator via DataScienceCluster component (`llamastackoperator`)
- OGX CRDs: LlamaStackServer, LlamaStackDistribution
- Configuring the OGX distribution on OpenShift
- Connecting OGX to vLLM models served via KServe
- Operator lifecycle: upgrades, health monitoring
- Prerequisites: OpenShift AI installed, vLLM model serving configured

**Deliverables:**
- OGX Operator installed via DSC component
- OGX server deployed on OpenShift via CRD
- OGX connected to KServe-served vLLM model

---

### L2-2.2 — OGX + vLLM Integration on OpenShift
**Duration:** 45 min
**Topics:**
- Serving through OGX on OpenShift: Routes, Services, and API access
- Connecting to KServe-deployed models: configuring `remote::vllm` provider with in-cluster URLs
- Using the Responses API on the cluster: agent orchestration at scale
- Streamable HTTP transport for long-running agent interactions
- Configuring vector stores on OpenShift: persistent storage for Qdrant
- Autoscaling OGX pods based on request load
- Testing: calling OGX APIs from outside the cluster via OpenShift Routes

**Deliverables:**
- OGX serving Responses API on OpenShift with vLLM backend
- Agent orchestration running on-cluster with tool use
- External access via OpenShift Route

---

### L2-2.3 — OGX + Safety on OpenShift
**Duration:** 45 min
**Topics:**
- Integrating OGX safety shields on OpenShift
- NeMo Guardrails integration: deploying alongside OGX
- TrustyAI detectors: connecting OGX to TrustyAI for bias/fairness checks
- Guardrails Orchestrator: routing requests through safety checks before OGX inference
- Llama Guard via OGX safety API: content moderation at scale
- Configuration: safety providers in `run.yaml` on OpenShift
- End-to-end flow: request hits safety shield, passes to OGX inference, response checked before return

**Deliverables:**
- OGX with safety shields running on OpenShift
- End-to-end demo: harmful input blocked, safe input processed
- Safety pipeline integrated with Guardrails Orchestrator

---

### Level 2 Summary

| Module | Lessons | Estimated Time |
|--------|---------|---------------|
| M1: Advanced Patterns | 7 lessons | ~4.5 hours |
| M2: OGX on OpenShift AI | 3 lessons | ~2.25 hours |
| **Total** | **10 lessons** | **~7-8 hours** |

---

# Complete Course Summary

| Level | Focus | Lessons | Time |
|-------|-------|---------|------|
| **Level 1 — Essentials** | APIs, RAG, Responses API agents, tools, safety | 11 lessons | ~9-10 hours |
| **Level 2 — Practitioner** | Multi-provider, telemetry, evals, production, OGX on OpenShift AI | 10 lessons | ~7-8 hours |
| **Total** | | **21 lessons** | **~16-18 hours** |
