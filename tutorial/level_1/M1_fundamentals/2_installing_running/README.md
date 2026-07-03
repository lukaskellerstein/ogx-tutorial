# L1-M1.2 — Installing and Running OGX

**Level:** Essentials
**Duration:** 45 min

## Overview

In this lesson you install the OGX Python client, connect to a running OGX server, and make your first API calls. By the end you will have listed the models registered in OGX and run a chat completion — confirming that your local development environment is fully operational.

## Prerequisites

- Completed: L1-M1.1 Architecture Overview
- Infrastructure running: OGX (port 8321), Ollama with `gemma4:e4b`
- See `ogx-local/` in the repository root for setup instructions

## Concepts

### Installation Options

There are two ways to get OGX running:

1. **pip install** — Install the OGX distribution as a Python package:
   ```bash
   uv pip install ogx[starter]
   ogx run starter
   ```
   This runs OGX directly on your machine. Good for quick experiments but harder to reproduce.

2. **Container (recommended for this tutorial)** — Run OGX as a Podman container:
   ```bash
   podman run -it -p 8321:8321 ogxai/distribution-starter
   ```
   Reproducible, isolated, and closer to how you would deploy in production.

This tutorial uses the container approach via `ogx-local/compose.yml`.

### Distributions

OGX ships as *distributions* — pre-configured bundles of providers:

| Distribution | Use case | Inference provider |
|---|---|---|
| `starter` | General-purpose development | Ollama (inline) |
| `remote-vllm` | Production with external vLLM | vLLM (remote) |

The `starter` distribution is what `ogx-local/` uses. It bundles Ollama for inference, SQLite for key-value storage, and can connect to Qdrant for vector search.

### Inference Backends

OGX does not run models itself — it delegates to an inference backend:

- **Ollama** — Best for macOS / Apple Silicon development. Runs natively on the host so it can access the GPU. OGX connects via `inline::ollama`.
- **vLLM** — Best for Linux with NVIDIA GPUs in production. Runs as a container. OGX connects via `remote::vllm`.

For local development on macOS, Ollama is the recommended backend. The `ogx-local/` setup configures this automatically.

### Configuration: run.yaml

Every OGX distribution is configured by a `run.yaml` file that declares which providers are active, which models are registered, and connection details. The `starter` distribution generates a default configuration when it starts. You do not need to edit it for this lesson.

### Python Client: ogx-client

The `ogx-client` package is the official Python SDK for OGX. It provides a typed client with methods for every OGX API: inference, models, vector IO, agents, safety, and more.

```bash
uv add ogx-client
```

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")
```

### OpenAI Compatibility

OGX exposes an OpenAI-compatible REST API at `/v1`. This means any tool or library that supports the OpenAI API — including the `openai` Python SDK, LangChain, and LlamaIndex — can connect to OGX simply by changing the `base_url`:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="not-needed")
```

This is useful when integrating OGX with existing code that already uses the OpenAI SDK.

## Step-by-Step

### Step 1: List Available Models

The first thing to do after connecting is verify which models OGX knows about. The `client.models.list()` call returns every model registered in the running OGX instance.

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")

models = client.models.list()
for model in models.data:
    print(f"  - {model.id}")
```

You should see `ollama/gemma4:e4b` (and possibly others, depending on what Ollama has pulled).

### Step 2: First Chat Completion

With the model confirmed, make a chat completion call. This sends a user message through OGX to the Ollama backend, which runs inference with Gemma 4 and returns the response.

```python
response = client.chat.completions.create(
    model="ollama/gemma4:e4b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant. Answer concisely."},
        {"role": "user", "content": "What is OGX (Open GenAI Stack) in one sentence?"},
    ],
    max_tokens=100,
)
print(response.choices[0].message.content)
```

The response object includes the generated text, the model name, and token usage statistics.

### Step 3: Multi-Message Conversation

A second call demonstrates that you can send multiple messages in the `messages` list to provide conversation context. OGX forwards the full message history to the model.

```python
response = client.chat.completions.create(
    model="ollama/gemma4:e4b",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Name three key APIs that OGX provides."},
    ],
    max_tokens=150,
)
print(response.choices[0].message.content)
```

### Step 4: OpenAI Compatibility (Informational)

The lesson prints the equivalent code using the standard `openai` SDK. This shows that any OpenAI-compatible library can talk to OGX by pointing its `base_url` to `http://localhost:8321/v1`. No code changes are needed beyond the URL.

## Running the Lesson

```bash
cd tutorial/level_1/M1_fundamentals/2_installing_running
uv sync
uv run python main.py
```

## Expected Output

```
L1-M1.2 — Installing and Running OGX
============================================================

Checking OGX server connectivity...
  OGX is reachable at http://localhost:8321

============================================================
Step 1: Listing available models
============================================================
  Models registered in OGX: 1
    - ollama/gemma4:e4b

============================================================
Step 2: First chat completion via OGX
============================================================
  Sending request to model: ollama/gemma4:e4b
  Prompt: 'What is OGX (Open GenAI Stack) in one sentence?'

  Response: OGX is an open-source unified AI runtime that provides
  standardized APIs for inference, RAG, agents, tool calling, and safety.

  Model used: ollama/gemma4:e4b
  Tokens — prompt: 32, completion: 28

============================================================
Step 3: Multi-message conversation
============================================================
  Response: Three key APIs provided by OGX are: (1) Inference API for
  chat completions and embeddings, (2) Vector IO API for document
  storage and similarity search, and (3) Agents API for creating
  AI agents with tool calling.

============================================================
Step 4: OpenAI compatibility (informational)
============================================================

  OGX exposes an OpenAI-compatible API at /v1.
  This means you can also use the standard openai SDK:

    from openai import OpenAI

    client = OpenAI(base_url="http://localhost:8321/v1",
                    api_key="not-needed")

    response = client.chat.completions.create(
        model="ollama/gemma4:e4b",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response.choices[0].message.content)

  Any library that works with the OpenAI API (LangChain,
  LlamaIndex, etc.) can connect to OGX by pointing its
  base_url to http://localhost:8321/v1.

============================================================
Done!
============================================================

  You have successfully:
  1. Connected to a running OGX server
  2. Listed the available models
  3. Made chat completion calls through OGX
  4. Learned about OpenAI SDK compatibility

  Next: L1-M2.1 — Chat and Completion (deep dive into
  inference parameters, streaming, and system prompts)
```

Note: The exact model responses will vary with each run.

## Key Takeaways

- OGX can be installed via pip or run as a container. The container approach is recommended for reproducibility.
- The `starter` distribution bundles Ollama for inference and is the quickest way to get started.
- On macOS, Ollama runs natively (for GPU access) while OGX and Qdrant run as Podman containers.
- The `ogx-client` Python SDK provides typed access to every OGX API.
- OGX is OpenAI-compatible — any tool that works with the OpenAI API can connect to OGX by changing the `base_url`.

## Next Steps

In the next lesson, **L1-M2.1 — Chat and Completion**, you will explore the Inference API in depth: streaming responses, system prompts, temperature and sampling parameters, and how OGX compares to calling vLLM directly.
