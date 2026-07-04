---
globs: ["tutorial/**/*.py"]
---

# OGX Patterns and APIs

## OGX Client

The Python client class is `OgxClient` (from `ogx_client`). It exposes OpenAI-compatible methods.

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")
```

The model ID for Ollama-backed inference is `ollama/gemma4:e4b`. For vLLM it is `google/gemma-4-E4B-it`.

## Core APIs by Level

### Level 1 — Essentials

#### Fundamentals (L1-M1)
- OGX API surface overview (stable + experimental APIs)
- `OgxClient` — Python client for all API calls
- Distributions: `starter` (general), `remote-vllm` (production)
- Configuration via `run.yaml`

#### Inference API (L1-M2)
- `client.chat.completions.create()` — chat completions
- `client.completions.create()` — text completions
- `client.embeddings.create()` — generate embeddings
- Streaming responses via `stream=True`
- Model: `ollama/gemma4:e4b` via Ollama

#### RAG / Vector Stores API (L1-M3)
- `client.vector_stores.create()` — create a vector store
- `client.vector_stores.list()` — list vector stores
- `client.vector_stores.delete()` — delete a vector store
- Vector IO operations: insert chunks, query for similarity
- Qdrant as vector backend (`inline::qdrant` or `remote::qdrant`)
- Document chunking and embedding pipeline

#### Tool Runtime API (L1-M4)
- Function tools via the Responses API
- Custom tool definitions with JSON Schema parameters
- Tool execution flow: LLM decides → app executes → result returned
- MCP integration: connecting MCP servers as tool providers
- Built-in tools: web search, code interpreter

#### Responses API / Agents (L1-M5)
- `client.responses.create()` — the primary agent orchestration endpoint
- Multi-turn via `previous_response_id`
- Built-in tool types: `web_search`, `file_search`, `code_interpreter`, `mcp`
- Agent helper: `from ogx_client.lib.agents.agent import Agent` with `@client_tool`
- Streaming agent responses with tool call events

#### Safety API (L1-M6)
- Safety shields via `/v1/safety/run-shield` (httpx raw API)
- Input shields: check user messages before processing
- Output shields: check model responses before returning
- Built-in detectors: content classification, toxicity, PII

#### Additional APIs (L1-M7)
- Files API: `client.files.create()`, `client.files.list()`
- Batches API: `/v1/batches` for offline batch processing
- Conversations API: `client.conversations.list()`, `client.conversations.get()`
- Prompts API: `/v1/prompts` for prompt templates

### Level 2 — Practitioner

#### Multi-Provider Configuration (L2-M1.1)
- Multiple inference providers in one OGX instance
- Routing: different models for different tasks
- Fallback chains: primary → secondary provider

#### Custom Providers (L2-M1.2)
- Building custom inference providers
- Provider interface: `InferenceProvider`, `VectorIOProvider`, `SafetyProvider`
- `OpenAIMixin` for OpenAI-compatible provider wrappers
- Custom safety detectors
- Plugin architecture: external (pip) vs internal (in-tree)

#### Telemetry and Observability (L2-M1.3)
- OpenTelemetry (OTel) integration for tracing
- Exporting traces to Jaeger
- Structured logging: request IDs, latency, token counts

#### Evaluation and RAG Benchmarks (L2-M1.4)
- Model evaluation: question-answer pairs, expected outputs
- RAG benchmarking: precision, recall, MRR
- Comparing retrieval configurations

#### Reranking and Advanced Retrieval (L2-M1.5)
- Experimental Rerank API: `/v1alpha/inference/rerank`
- Two-stage retrieval: vector search → rerank
- Comparing RAG quality with and without reranking

#### File Processors (L2-M1.6)
- Experimental File Processors API: `/v1alpha/file_processors`
- Document ingestion pipeline: upload → process → chunk → embed → store
- Supported file types: PDF, DOCX, HTML, Markdown

#### Production Deployment (L2-M1.7)
- Podman Compose: OGX + vLLM + Qdrant + PostgreSQL
- PostgreSQL KVStore for memory (production)
- Qdrant server for vector storage (production)
- Health checks, scaling, restart policies

#### OGX on OpenShift AI (L2-M2)
- OGX Operator via DataScienceCluster (`llamastackoperator` component)
- CRDs: LlamaStackServer, LlamaStackDistribution
- vLLM integration via KServe InferenceService
- Safety on OpenShift: NeMo Guardrails, TrustyAI, Guardrails Orchestrator

## Patterns to Follow

### OGX Client Setup
Always initialize the client at the top of `main.py`:
```python
from ogx_client import OgxClient

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"

client = OgxClient(base_url=OGX_URL)
```

### Chat Completion
```python
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
print(response.choices[0].message.content)
```

### Streaming
```python
stream = client.chat.completions.create(
    model=MODEL,
    messages=[...],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Responses API (Agents)
```python
response = client.responses.create(
    model=MODEL,
    input="What is the weather in Paris?",
    tools=[{
        "type": "function",
        "name": "get_weather",
        "description": "Get weather for a city",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}},
    }],
)
```

### Using OGX with LangChain
OGX exposes an OpenAI-compatible API, so use `langchain-openai`:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8321/v1",
    model="ollama/gemma4:e4b",
    api_key="not-needed",
)
```

### Always Check the OGX Documentation
When implementing OGX features, verify the API exists and its signature by consulting:
- Documentation: https://ogx-ai.github.io/docs
- Python client: https://github.com/ogx-ai/ogx-client-python
- Providers: https://ogx-ai.github.io/docs/providers

Do NOT guess at API names or parameters. Read the docs if unsure.
