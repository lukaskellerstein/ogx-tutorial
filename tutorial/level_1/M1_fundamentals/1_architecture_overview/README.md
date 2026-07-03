# L1-M1.1 — What is OGX? Architecture Overview

**Level:** Essentials
**Duration:** 30 min

## Overview

This lesson introduces OGX (Open GenAI Stack) — the open-source unified AI runtime that provides standardized APIs for inference, RAG, agents, tool calling, and safety. You will explore the OGX API surface using raw HTTP calls to understand what OGX offers before writing application code on top of it.

## Prerequisites

- Infrastructure running: OGX server on port 8321
- See `infra/` for setup instructions (`podman compose up -d`)

## Concepts

### What is OGX?

OGX is an HTTP server that sits between your application and one or more AI inference backends. Instead of talking directly to vLLM, Ollama, or a cloud provider, your application talks to OGX — and OGX handles the routing, translation, and orchestration.

```
+---------------------------------------------+
|              Your Application                |
+---------------------------------------------+
                    |
               OGX Server (:8321)
                    |
     +--------------+--------------+
     |              |              |
   vLLM          Ollama        OpenAI
(local GPU)    (Apple Si.)    (cloud)
```

This design gives you three key advantages:

1. **Provider-agnostic code** — swap from vLLM to Ollama to OpenAI without changing your application.
2. **Unified API surface** — inference, embeddings, vector storage, agents, safety, and tools through a single server.
3. **Language-agnostic** — OGX is an HTTP server, so you can write clients in Python, Go, TypeScript, or any language.

### The OGX API Surface

OGX exposes OpenAI-compatible endpoints, so any OpenAI SDK or client works out of the box. The core endpoints are:

| Endpoint | Purpose |
|----------|---------|
| `/v1/chat/completions` | Chat completions with streaming and tool calling |
| `/v1/completions` | Text completions |
| `/v1/embeddings` | Text embeddings for search and RAG |
| `/v1/models` | List and manage registered models |
| `/v1/vector_stores` | Vector database operations (insert, query) |
| `/v1/files` | File upload and management |
| `/v1/responses` | Server-side agentic orchestration with MCP |
| `/v1/safety` | Content moderation and guardrails |
| `/v1/health` | Server health check |

In addition, OGX natively supports the Anthropic Messages API (`/v1/messages`) and Google Interactions API (`/v1alpha/interactions`), so teams using different SDKs can all point at the same server.

### Providers: The Pluggable Backend

A **provider** is an implementation of a specific API capability. OGX supports 23+ inference providers including:

- **vLLM** — high-performance local inference (our primary backend)
- **Ollama** — easy local inference, great for Apple Silicon
- **OpenAI, Anthropic, Google** — cloud-hosted models
- **AWS Bedrock, Azure OpenAI** — enterprise cloud
- **NVIDIA NIM, Together AI, Fireworks** — specialized hosting

Providers are not limited to inference. OGX also has providers for:
- **Vector stores** — Qdrant, ChromaDB, FAISS, pgvector, Milvus, Weaviate, Elasticsearch (15+ providers)
- **Tool runtimes** — MCP servers, web search, code interpreter (7+ providers)
- **Safety** — content classifiers, guardrails

### Distributions: Pre-Packaged Configurations

A **distribution** is a pre-configured bundle of providers for a specific use case:

- **`starter`** — general-purpose, good for getting started
- **`remote-vllm`** — points to a separate vLLM server (production)

When you start OGX, you choose a distribution. The distribution's `run.yaml` file specifies which providers to load and how to configure them.

### Why OGX Over Direct vLLM?

vLLM is an excellent inference server, but it only does inference. OGX adds:

| Capability | vLLM | OGX |
|-----------|------|-----|
| Chat completions | Yes | Yes (via vLLM) |
| Embeddings | Yes | Yes (via vLLM) |
| Vector storage (RAG) | No | Yes |
| Agent orchestration | No | Yes |
| Tool calling / MCP | No | Yes |
| Safety / guardrails | No | Yes |
| Memory management | No | Yes |
| Multi-provider routing | No | Yes |

OGX uses vLLM as its inference engine but wraps it in a much richer API surface for building complete AI applications.

## Step-by-Step

### Step 1: Check Server Health

We start by verifying the OGX server is reachable. The lesson uses `httpx` for raw HTTP calls so you can see exactly what the API looks like.

```python
response = client.get(f"{OGX_URL}/v1/health")
print(f"Status code: {response.status_code}")
print(f"Response:    {response.json()}")
```

### Step 2: List Registered Models

The `/v1/models` endpoint returns all models the server knows about. In our setup, this should show `google/gemma-4-E4B-it` served by vLLM.

```python
response = client.get(f"{OGX_URL}/v1/models")
data = response.json()
for model in data.get("data", data):
    print(f"  - {model.get('id')}")
```

### Step 3: List API Routes

The `/v1/routes` endpoint shows all available API routes on the server, giving you a map of what this OGX instance can do.

```python
response = client.get(f"{OGX_URL}/v1/routes")
for route in response.json():
    print(f"  {route['method']:6s} {route['route']}")
```

### Step 4: List Configured Providers

The `/v1/providers` endpoint shows which providers are loaded — this tells you what backends are powering each API.

```python
response = client.get(f"{OGX_URL}/v1/providers")
for api_name, providers in response.json().items():
    print(f"  [{api_name}]")
    for p in providers:
        print(f"    - {p['provider_id']} ({p['provider_type']})")
```

### Step 5: API Overview Table

Finally, the lesson prints an ASCII architecture diagram and API summary table — a visual reference for the rest of the tutorial.

## Running the Lesson

```bash
cd tutorial/level_1/M1_fundamentals/1_architecture_overview
uv sync
uv run python main.py
```

## Expected Output

```
############################################################
#  L1-M1.1 — OGX Architecture Overview
#  Exploring the OGX API surface
############################################################

============================================================
Step 1: Checking OGX Server Health
============================================================
  Status code : 200
  Response    : {"status": "OK"}
  OGX server is healthy!

============================================================
Step 2: Listing Registered Models (GET /v1/models)
============================================================
  Found 1 registered model(s):

    - google/gemma-4-E4B-it
      Provider: vllm

============================================================
Step 3: Listing Available API Routes (GET /v1/routes)
============================================================
  Found N API route(s):

    GET    /v1/models
    POST   /v1/chat/completions
    POST   /v1/embeddings
    ...

============================================================
Step 4: Listing Configured Providers (GET /v1/providers)
============================================================
  [inference]
    - vllm (remote::vllm)
  [vector_io]
    - qdrant (remote::qdrant)
  ...

============================================================
Step 5: OGX API Surface Overview
============================================================

    OGX is a unified AI runtime that sits between your application
    and one or more inference backends ...

    Core API Surface:
    +-----------------+-----------------------------------+
    | API             | Purpose                           |
    +-----------------+-----------------------------------+
    | /v1/chat/       | Chat completions, streaming,      |
    |   completions   | tool calling (OpenAI-compatible)   |
    | /v1/embeddings  | Text embeddings for search & RAG  |
    | ...             | ...                               |
    +-----------------+-----------------------------------+

============================================================
Lesson complete! Next: L1-M1.2 — Installing and Running OGX
============================================================
```

Note: The exact output depends on your OGX distribution and configuration. The model list, routes, and providers will vary.

## Key Takeaways

- **OGX is an HTTP server**, not a library. Your application talks to it over the network, in any language.
- **Provider-agnostic**: OGX supports 23+ inference providers. Swap vLLM for Ollama or OpenAI without changing your code.
- **Unified API**: inference, RAG, agents, tools, and safety through a single server at `localhost:8321`.
- **OpenAI-compatible**: any OpenAI SDK or client works with OGX out of the box.
- **Distributions** are pre-packaged provider configurations for specific use cases.

## Next Steps

In the next lesson, **L1-M1.2 — Installing and Running OGX**, you will set up OGX as a Podman container with vLLM as the inference backend, configure a distribution, and make your first inference call using the Python client.
