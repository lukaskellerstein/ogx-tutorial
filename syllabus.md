# OGX (Open GenAI Stack) Tutorial: Syllabus

## Purpose

Learn OGX (formerly Llama Stack) — the open-source unified AI runtime providing standardized APIs for inference, RAG, agents, tool calling, and MCP. This sub-tutorial covers OGX independently before you use the OGX Operator on OpenShift AI.

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

*Goal: Understand OGX APIs, run inference, build RAG, create agents.*
*Estimated time: ~8-10 hours*

---

## L1-M1: OGX Fundamentals

### L1-1.1 — What is OGX? Architecture Overview
**Duration:** 30 min
**Topics:**
- OGX: unified AI runtime with standardized APIs
- API surface:
  - `/v1/inference` — text generation, chat, embeddings
  - `/v1/memory` — conversation history and context management
  - `/v1/tool_runtime` — tool calling and MCP integration
  - `/v1/vector_io` — vector database operations (insert, query)
  - `/v1/safety` — content moderation and guardrails
  - `/v1alpha/agents` — agent creation and execution
- Provider-agnostic: 23 inference providers (vLLM, Ollama, OpenAI, Anthropic, Bedrock, etc.)
- Distribution concept: pre-configured bundles of providers for specific use cases
- Comparison with direct vLLM: OGX adds RAG, agents, memory, safety on top

**Deliverables:**
- Architecture diagram: OGX API layers and providers
- API surface overview table

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
- First API call: chat completion through OGX

**Deliverables:**
- OGX server running as Podman container with vLLM backend
- vLLM serving `gemma-4-E4B-it` model
- Python client calling the inference API

---

## L1-M2: Inference API

### L1-2.1 — Chat and Completion
**Duration:** 30 min
**Topics:**
- Chat completions: `/v1/inference/chat_completion`
- Text completions: `/v1/inference/completion`
- Streaming responses
- System prompts and conversation history
- Parameters: temperature, max_tokens, top_p
- Model selection and registration
- Comparing with direct vLLM API: OGX adds RAG, agents, memory, safety, tools on top
- Model: `google/gemma-4-E4B-it` (4B effective params) via vLLM

**Deliverables:**
- Chat and completion calls via OGX client
- Streaming example

---

### L1-2.2 — Embeddings
**Duration:** 20 min
**Topics:**
- Embedding generation: `/v1/inference/embeddings`
- Supported embedding models
- Batch embedding generation
- Use case: generating embeddings for RAG document ingestion

**Deliverables:**
- Embeddings generated via OGX
- Similarity comparison between text pairs

---

## L1-M3: RAG with OGX

### L1-3.1 — Vector IO API
**Duration:** 45 min
**Topics:**
- Vector IO: OGX's abstraction over vector databases
- Operations:
  - `vector_io.insert` — add documents with embeddings
  - `vector_io.query` — similarity search
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
  1. Ingest: chunk documents → embed → store via Vector IO
  2. Retrieve: query Vector IO for relevant context
  3. Generate: pass context + question to inference API
- Memory API for conversation history in multi-turn RAG
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
- Defining tools: function signatures, parameter schemas
- Built-in tools: web search, code interpreter
- Custom tool registration
- Tool execution flow: LLM decides → OGX executes → result returned
- MCP integration: connecting MCP servers as tool providers
- Comparing with direct MCP: OGX provides a unified tool + inference layer

**Deliverables:**
- Custom tools registered and called through OGX
- MCP server connected as a tool provider

---

## L1-M5: Agents API

### L1-5.1 — Creating Agents
**Duration:** 1 hour
**Topics:**
- Agents API: `/v1alpha/agents`
- Agent creation: `agents.create()`
  - Model selection
  - System prompt (instructions)
  - Available tools
  - Safety configuration
- Agent sessions: `agents.session.create()`
- Agent turns: `agents.turn.create()`
  - Single-turn and multi-turn conversations
  - Tool calling within turns
  - Streaming agent responses
- Agent lifecycle management
- Comparing with LangGraph agents:
  - OGX agents: simpler API, less flexible, native tool/safety integration
  - LangGraph agents: complex state machines, conditional routing, more control

**Deliverables:**
- OGX agent with tools, multi-turn conversation
- Comparison: same task with OGX agent vs LangGraph agent

---

### L1-5.2 — Agents with RAG
**Duration:** 45 min
**Topics:**
- Combining agents with RAG:
  - Agent uses Vector IO for retrieval
  - Automatic context injection into agent conversations
- Memory API integration: agent remembers conversation across sessions
- Use case: knowledge assistant that answers questions from a document corpus
- RAG + Tools: agent retrieves context AND calls tools as needed

**Deliverables:**
- RAG-powered agent answering questions from ingested documents
- Agent using both retrieval and tool calling

---

## L1-M6: Safety API

### L1-6.1 — Content Moderation
**Duration:** 30 min
**Topics:**
- Safety API: `/v1/safety`
- Input shields: checking user messages before processing
- Output shields: checking model responses before returning
- Built-in detectors: content classification, toxicity, PII
- Configuring safety for agents: shields applied automatically
- Integration with NeMo Guardrails and Llama Guard

**Deliverables:**
- Safety shields configured for an OGX agent
- Demonstration: blocked harmful content

---

### Level 1 Summary

| Module | Lessons | Estimated Time |
|--------|---------|---------------|
| M1: Fundamentals | 2 lessons | ~1.25 hours |
| M2: Inference API | 2 lessons | ~50 min |
| M3: RAG | 2 lessons | ~1.75 hours |
| M4: Tool Calling & MCP | 1 lesson | ~45 min |
| M5: Agents API | 2 lessons | ~1.75 hours |
| M6: Safety API | 1 lesson | ~30 min |
| **Total** | **10 lessons** | **~7-8 hours** |

---

# LEVEL 2 — PRACTITIONER

*Goal: Advanced patterns, multi-provider, production configuration.*
*Estimated time: ~4-5 hours*

---

## L2-M1: Advanced Patterns

### L2-1.1 — Multi-Provider Configuration
**Duration:** 45 min
**Topics:**
- Configuring multiple inference providers in one OGX instance
- Routing: different models for different tasks (chat vs embedding vs safety)
- Fallback chains: primary → secondary provider
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

### L2-1.3 — Production Deployment
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

### Level 2 Summary

| Module | Lessons | Estimated Time |
|--------|---------|---------------|
| M1: Advanced Patterns | 3 lessons | ~2.5 hours |
| **Total** | **3 lessons** | **~2.5-3 hours** |

---

# Complete Course Summary

| Level | Focus | Lessons | Time |
|-------|-------|---------|------|
| **Level 1 — Essentials** | APIs, RAG, agents, tools, safety | 10 lessons | ~7-8 hours |
| **Level 2 — Practitioner** | Multi-provider, custom extensions, production | 3 lessons | ~2.5-3 hours |
| **Total** | | **13 lessons** | **~9-11 hours** |
