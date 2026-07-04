# L2-M1.2 — Custom Providers and Extensions

**Level:** Practitioner
**Duration:** 1 hour

## Overview

OGX's power comes from its provider-agnostic architecture -- you can swap inference backends, vector stores, and safety detectors without changing your application code. In this lesson you will explore the provider interface, understand what a custom provider must implement, and see complete skeleton code for building your own inference and safety providers. While building a fully functional custom provider requires publishing a pip package and modifying the OGX server configuration, this lesson gives you the knowledge to do so.

## Prerequisites

- Completed: L2-M1.1 Multi-Provider Configuration
- Familiarity with OGX API surface from Level 1 (especially inference, vector IO, and safety APIs)
- Infrastructure running: OGX (port 8321) with at least one inference provider

## Concepts

### Provider types

OGX has two categories of providers:

- **Remote providers** (`remote::`) -- adapt an external service by forwarding requests over the network (e.g., `remote::vllm`, `remote::ollama`, `remote::openai`).
- **Inline providers** (`inline::`) -- run processing within the OGX process itself (e.g., `inline::qdrant` for embedded vector search, `inline::sentence-transformers` for local embeddings).

### Provider interfaces

Each OGX API defines a protocol (interface) that providers must implement:

| API | Key methods |
|-----|-------------|
| Inference | `chat_completion()`, `completion()`, `embeddings()` |
| Vector IO | `register_vector_db()`, `insert_chunks()`, `query_chunks()` |
| Safety | `register_shield()`, `run_shield()` |
| Tool Runtime | `register_tool()`, `invoke_tool()` |
| Files | `upload_file()`, `get_file()` |

### Internal vs external providers

| Aspect | Internal (in-tree) | External (out-of-tree) |
|--------|--------------------|------------------------|
| Location | In the OGX source code | Separate pip package |
| Changes to OGX | Required | None |
| Best for | Contributing to OGX | Custom/proprietary APIs |
| Registration | Via provider registry | Via `module` in run.yaml |

### OpenAIMixin

For providers that wrap an OpenAI-compatible API, OGX provides `OpenAIMixin` -- a base class that implements `chat_completion()`, `completion()`, and `embeddings()`. You only need to implement `get_api_key()` and `get_base_url()`.

### External provider package structure

An external provider is a pip package with a specific structure:

```
ogx-provider-myapi/
  pyproject.toml           # Package metadata
  my_ogx_provider/
    __init__.py            # get_adapter_impl() or get_provider_impl()
    provider.py            # get_provider_spec()
    config.py              # Pydantic configuration model
    adapter.py             # Protocol implementation
```

The `get_provider_spec()` function tells OGX what API the provider serves, what packages it needs, and where to find the config class. The `get_adapter_impl()` function (for remote) or `get_provider_impl()` (for inline) creates the actual provider instance.

## Step-by-Step

### Step 1: Inspect existing providers

Query the OGX server to see what providers are currently configured, their types, and which API each one serves.

```python
resp = httpx.get(f"{OGX_URL}/v1/providers", timeout=10)
data = resp.json()
# Prints all providers grouped by API
```

### Step 2: Provider interface overview

Understand the three key interfaces -- InferenceProvider, VectorIOProvider, and SafetyProvider -- and the methods each requires.

### Step 3: Custom inference provider skeleton

See a complete Python skeleton for wrapping an external API as an OGX inference provider. The skeleton includes:
- `provider.py` with `get_provider_spec()`
- `config.py` with a Pydantic config model
- `__init__.py` with `get_adapter_impl()`
- `adapter.py` with `chat_completion()` and `embeddings()`

For OpenAI-compatible APIs, inherit from `OpenAIMixin` to get the implementations for free.

### Step 4: Registration in run.yaml

Register your custom provider in OGX's configuration:

```yaml
providers:
  inference:
    - provider_id: my-custom
      provider_type: remote::my-custom-api
      module: my_ogx_provider
      config:
        api_url: http://my-api:8080
        api_key: ${MY_API_KEY}
```

OGX uses the `module` field to install the package and discover the provider via `get_provider_spec()`.

### Step 5: Custom safety detector

See a skeleton for a safety provider that combines keyword filtering with an external moderation API. Safety providers implement `run_shield()` and return either a violation description or `None` (safe).

### Step 6: Plugin architecture

Understand the three extension levels: external providers (pip packages, no OGX source changes), internal providers (in-tree contributions), and custom distributions (reusable provider bundles).

### Step 7: Test the existing provider

Make a real inference call through the currently configured provider to see the working flow, then understand how a custom provider would handle the same request.

## Running the Lesson

```bash
cd tutorial/level_2/M1_advanced_patterns/2_custom_providers
uv sync
uv run python main.py
```

## Expected Output

```
############################################################
#  L2-M1.2 — Custom Providers and Extensions
#  Understanding the OGX provider interface
############################################################

============================================================
Step 1: Inspect Existing Providers
============================================================

  [inference]
    - ollama (remote::ollama)

  [vector_io]
    - qdrant (inline::qdrant)

  [safety]
    - llama-guard (inline::llama-guard)

  Provider types in OGX:
    remote::  -- adapts an external service (vLLM, Ollama, OpenAI)
    inline::  -- runs processing within the OGX process itself

============================================================
Step 2: Provider Interface Overview
============================================================

  OGX organizes providers by API. Each API has a protocol that
  providers must implement. Here are the key interfaces:

  ---- InferenceProvider ----
  class InferenceProvider:
      async def chat_completion(...) -> ChatCompletionResponse: ...
      async def completion(...) -> CompletionResponse: ...
      async def embeddings(...) -> EmbeddingsResponse: ...

  ---- VectorIOProvider ----
  class VectorIOProvider:
      async def register_vector_db(...) -> None: ...
      async def insert_chunks(...) -> None: ...
      async def query_chunks(...) -> QueryChunksResponse: ...

  ---- SafetyProvider ----
  class SafetyProvider:
      async def register_shield(...) -> None: ...
      async def run_shield(...) -> RunShieldResponse: ...
  ...

============================================================
Step 3: Custom Inference Provider Skeleton
============================================================
  [prints provider package structure and adapter code]

============================================================
Step 4: Registering a Custom Provider
============================================================
  [prints run.yaml configuration example]

============================================================
Step 5: Custom Safety Detector Skeleton
============================================================
  [prints safety provider with keyword + API moderation]

============================================================
Step 6: Plugin Architecture
============================================================
  [prints extension model overview]

============================================================
Step 7: Test the Existing Provider
============================================================
  Making an inference call via the configured provider...
  Model: ollama/gemma4:e4b

  Response: A provider is a pluggable backend that implements
  a specific API interface to handle requests for a service
  like inference, storage, or safety.

  This call was routed through OGX to the configured inference
  provider. A custom provider would handle the same request by
  implementing the same chat_completion interface and forwarding
  the call to a different backend.

============================================================
Lesson complete! Next: L2-M1.3 — Telemetry and Observability
============================================================
```

> Note: The provider list in Step 1 depends on your OGX distribution. The inference response in Step 7 will vary.

## Key Takeaways

- OGX providers come in two types: **remote** (external services) and **inline** (local processing).
- Each API (inference, vector IO, safety) defines a protocol that custom providers must implement.
- **External providers** are pip packages with `get_provider_spec()` and `get_adapter_impl()` -- no changes to OGX source code required.
- For OpenAI-compatible APIs, use `OpenAIMixin` to avoid reimplementing chat_completion and embeddings from scratch.
- Providers are registered in `run.yaml` using the `module` field, which tells OGX how to install and discover them.
- Custom distributions bundle providers into reusable configurations for team-wide standardization.

## Next Steps

Continue to **L2-M1.3 Telemetry and Observability**, where you will enable OpenTelemetry tracing in OGX, export traces to Jaeger, and visualize end-to-end request flows through inference and tool calls.
