# L2-M1.1 — Multi-Provider Configuration

**Level:** Practitioner
**Duration:** 45 min

## Overview

In this lesson you will learn how to configure multiple inference providers within a single OGX instance. You will explore provider routing (sending different models to different backends), fallback chains (resilience through provider chaining), and custom distributions (bundling providers for specific use cases). This is essential for production deployments where you need to balance performance, cost, and reliability.

## Prerequisites

- Completed: All Level 1 lessons (especially L1-M1.2 Installing and Running OGX)
- Infrastructure running: OGX (port 8321), Ollama with `gemma4:e4b`
- Familiarity with OGX's `config.yaml` format (covered in L1-M1.2)

## Concepts

### Why multiple providers?

In Level 1 you used a single inference provider (Ollama or vLLM). In production, you typically need multiple providers for different reasons:

- **Task specialization** -- use a GPU-accelerated vLLM server for chat inference, a lightweight Ollama instance for embeddings, and a dedicated safety model for content moderation.
- **Cost optimization** -- route simple queries to a cheaper/faster provider and complex queries to a more capable one.
- **Resilience** -- if your primary provider goes down, a fallback provider keeps the system running.
- **Migration** -- run old and new providers side-by-side during a transition.

### Provider types

OGX supports 23+ inference providers. Each is identified by a type string:

| Provider Type | Description |
|---------------|-------------|
| `remote::vllm` | External vLLM server (GPU, high throughput) |
| `remote::ollama` | External Ollama server (CPU/GPU, easy setup) |
| `remote::openai` | OpenAI API |
| `remote::anthropic` | Anthropic API |
| `remote::bedrock` | AWS Bedrock |
| `remote::gemini` | Google Gemini |
| `inline::ollama` | Ollama running in-process |
| `inline::sentence-transformers` | Local sentence-transformers for embeddings |

The `remote::` prefix means OGX connects to an external service. The `inline::` prefix means OGX runs the provider in-process.

### Provider routing

Every model registered in OGX is associated with a `provider_id`. When you call `client.inference.chat_completion(model_id="...")`, OGX looks up which provider serves that model and routes the request accordingly. This happens transparently -- your application code does not need to know which backend is serving a given model.

### Fallback chains

A fallback chain is a pattern where you register the same logical model with multiple providers (under different model IDs) and try them in sequence. If the primary provider fails (overloaded, down, timeout), you fall back to the secondary. This is implemented at the application level.

### Custom distributions

A distribution is a pre-configured bundle of providers, APIs, and models packaged together for a specific use case. OGX ships built-in distributions like `starter`, `remote-vllm`, and `ollama`. You can create your own distribution by writing a `config.yaml` that bundles exactly the providers and models your application needs.

### config.yaml structure

The configuration file has four main sections:

```yaml
apis:         # Which APIs to expose (inference, vector_io, agents, etc.)
providers:    # Provider instances with type and config
models:       # Models registered to specific providers
server:       # Port, TLS, authentication
```

## Step-by-Step

### Step 1: List configured providers

Query the OGX server's `/v1/providers` endpoint to see which providers are currently configured. This shows the provider ID, type, and which API each one serves.

```python
response = httpx.get("http://localhost:8321/v1/providers")
providers = response.json()
for p in providers:
    print(f"Provider: {p['provider_id']} ({p['provider_type']})")
```

### Step 2: List registered models

Use the OGX client to list all models and see which provider serves each one. The model's `provider_id` determines where requests are routed.

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")
models = client.models.list()
for m in models:
    print(f"Model: {m.identifier} -> Provider: {m.provider_id}")
```

### Step 3: Provider routing with a multi-provider config

Examine a sample `config.yaml` that configures two inference providers (vLLM and Ollama) and assigns different models to each. The key insight is that each model registration includes a `provider_id` that OGX uses for routing:

```yaml
providers:
  inference:
    - provider_id: vllm
      provider_type: remote::vllm
      config:
        url: http://localhost:8000

    - provider_id: ollama
      provider_type: remote::ollama
      config:
        url: http://localhost:11434

models:
  - model_id: google/gemma-4-E4B-it
    provider_id: vllm         # Chat requests -> vLLM
    model_type: llm

  - model_id: ollama/gemma4:e4b
    provider_id: ollama       # Fallback chat -> Ollama
    model_type: llm

  - model_id: ollama/nomic-embed-text
    provider_id: ollama       # Embeddings -> Ollama
    model_type: embedding
```

With this config, OGX routes each request to the correct provider based on the `model_id` in the API call.

### Step 4: Inference call demonstrating routing

Make an inference call to see routing in action. The model ID determines which provider handles the request:

```python
response = client.inference.chat_completion(
    model_id="ollama/gemma4:e4b",
    messages=[
        {"role": "user", "content": "What is provider routing?"},
    ],
)
```

### Step 5: Fallback chains

Implement an application-level fallback pattern by trying providers in sequence:

```python
PROVIDERS = [
    "google/gemma-4-E4B-it",  # Primary: vLLM
    "ollama/gemma4:e4b",       # Fallback: Ollama
]

def chat_with_fallback(client, messages):
    for model_id in PROVIDERS:
        try:
            return client.inference.chat_completion(
                model_id=model_id, messages=messages,
            )
        except Exception:
            continue
    raise RuntimeError("All providers failed")
```

### Step 6: Custom distributions

Create a `config.yaml` tailored to your use case. For example, a RAG-focused distribution might bundle vLLM for inference and Qdrant for vector storage, exposing only the APIs your application needs.

## Running the Lesson

```bash
cd tutorial/level_2/M1_advanced_patterns/1_multi_provider_config
uv sync
uv run python main.py
```

## Expected Output

```
L2-M1.1 — Multi-Provider Configuration
============================================================

  This lesson explores how OGX supports multiple inference
  providers in a single instance, enabling routing, fallback,
  and custom distributions for production deployments.

============================================================
Step 1: List configured providers
============================================================
  Querying OGX for all registered providers...

  Provider: ollama
    Type: remote::ollama
    API:  inference
  ...

  Total providers: N

============================================================
Step 2: List registered models
============================================================
  Each model is served by a specific provider.
  OGX routes requests to the correct provider based on model ID.

  Model: ollama/gemma4:e4b
    Provider: ollama
    Type:     llm
  ...

  Total models: N

============================================================
Step 3: Provider routing — different models, different backends
============================================================
  [Explains routing concept with a sample multi-provider config.yaml]

============================================================
Step 4: Inference call — provider routing in action
============================================================
  Calling model: ollama/gemma4:e4b
  Response: [Model's response about provider routing]

============================================================
Step 5: Fallback chains — resilience through provider chaining
============================================================
  [Explains fallback pattern with sample code]

============================================================
Step 6: Custom distributions — bundling providers for use cases
============================================================
  [Explains distributions with a sample config]

============================================================
Summary
============================================================
  Multi-provider configuration gives you:
    1. Routing   — send requests to the best backend for each task
    2. Fallback  — resilience when a provider goes down
    3. Flexibility — mix GPU/CPU, cloud/local, fast/cheap
```

> Note: The exact providers and models listed depend on your OGX instance's configuration. The sample configs printed by Steps 3, 5, and 6 are illustrative -- applying them requires restarting OGX with a new config.yaml.

## Key Takeaways

- OGX supports multiple inference providers in a single instance, each identified by a `provider_id` and `provider_type`.
- Provider routing is based on `model_id` -- each registered model is tied to a specific provider, and OGX routes requests automatically.
- Fallback chains give you resilience: if the primary provider fails, the application falls back to a secondary provider.
- Custom distributions let you bundle exactly the providers, APIs, and models your application needs into a reusable configuration.
- All provider configuration happens in `config.yaml` -- your application code stays the same regardless of which backend is serving a model.

## Next Steps

Continue to **L2-M1.2 -- Custom Providers and Extensions**, where you will build a custom inference provider that wraps an external API and register it with OGX.
