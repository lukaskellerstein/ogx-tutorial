# L1-M2.1 — Chat and Completion

**Level:** Essentials
**Duration:** 30 min

## Overview

Learn how to use the OGX Inference API for chat completions. This lesson covers basic chat calls, system prompts for controlling assistant behavior, multi-turn conversations with message history, streaming responses for real-time output, and tuning generation parameters like temperature, max_tokens, and top_p.

## Prerequisites

- Completed: L1-M1.2 Installing and Running OGX
- Infrastructure running: OGX server (port 8321), Ollama with `gemma4:e4b`

## Concepts

### Chat Completions API

OGX exposes an OpenAI-compatible `/v1/chat/completions` endpoint. You send a list of messages (system, user, assistant) and receive a model-generated response. This is the primary interface for text generation through OGX.

### Message Roles

Each message in the conversation has a role:

| Role | Purpose |
|------|---------|
| `system` | Sets the assistant's behavior and personality |
| `user` | The human's input |
| `assistant` | The model's previous responses (for multi-turn context) |

### Streaming

By default, the API returns the full response at once. With `stream=True`, you receive tokens as they are generated — useful for real-time UIs and long responses.

### Generation Parameters

| Parameter | Effect |
|-----------|--------|
| `temperature` | Controls randomness. 0.0 = deterministic, 1.0 = creative |
| `max_tokens` | Maximum number of tokens in the response |
| `top_p` | Nucleus sampling — limits token selection to the top cumulative probability |

### OGX vs Direct Inference

You could call vLLM or Ollama directly, but OGX adds RAG, agents, memory, safety, and tool calling on top of raw inference — all through a single unified API.

## Step-by-Step

### Step 1: Basic Chat Completion

The simplest possible call — send a user message, get a response:

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")

response = client.chat.completions.create(
    model="ollama/gemma4:e4b",
    messages=[
        {"role": "user", "content": "What is OGX in one sentence?"},
    ],
)
print(response.choices[0].message.content)
```

### Step 2: System Prompts

A system message controls how the assistant behaves. Here we make it respond like a pirate:

```python
response = client.chat.completions.create(
    model="ollama/gemma4:e4b",
    messages=[
        {"role": "system", "content": "You are a pirate. Answer everything in pirate speak."},
        {"role": "user", "content": "What is machine learning?"},
    ],
)
```

### Step 3: Conversation History

The chat completions API is stateless — it does not remember previous calls. To have a multi-turn conversation, you include the full message history in each request:

```python
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "My name is Alice."},
]

response = client.chat.completions.create(model=MODEL, messages=messages)
assistant_reply = response.choices[0].message.content

# Add the assistant's reply, then ask a follow-up
messages.append({"role": "assistant", "content": assistant_reply})
messages.append({"role": "user", "content": "What is my name?"})

response = client.chat.completions.create(model=MODEL, messages=messages)
# The model remembers: "Your name is Alice."
```

### Step 4: Streaming Responses

With `stream=True`, the API returns chunks as they are generated:

```python
stream = client.chat.completions.create(
    model="ollama/gemma4:e4b",
    messages=[{"role": "user", "content": "Explain what an API is."}],
    stream=True,
)
for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Step 5: Generation Parameters

Temperature controls randomness. At 0.0, the model produces the same output every time. At 1.0, responses vary:

```python
# Deterministic
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Write a one-sentence story about a cat."}],
    temperature=0.0,
    max_tokens=60,
)

# Creative
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Write a one-sentence story about a cat."}],
    temperature=1.0,
    max_tokens=60,
)
```

`max_tokens` caps the response length. `top_p` narrows the sampling nucleus — lower values make the model pick from fewer top candidates.

### Step 6: OGX vs Direct vLLM

OGX forwards inference requests to the configured backend (vLLM or Ollama). Calling OGX instead of the backend directly gives you access to the full OGX stack: RAG via Vector IO, agents, memory, safety shields, and tool calling — all explored in the remaining lessons.

## Running the Lesson

```bash
cd tutorial/level_1/M2_inference_api/1_chat_completion
uv sync
uv run python main.py
```

## Expected Output

```
L1-M2.1 — Chat and Completion
============================================================

============================================================
Step 1: Basic Chat Completion
============================================================
Response: OGX (Open GenAI Stack) is an open-source unified AI runtime ...

============================================================
Step 2: System Prompts
============================================================
Response: Ahoy, matey! Machine learnin' be the art of teachin' ...

============================================================
Step 3: Conversation History (Multi-Turn)
============================================================
User:      My name is Alice.
Assistant: Nice to meet you, Alice! How can I help you today?
User:      What is my name?
Assistant: Your name is Alice!

============================================================
Step 4: Streaming Response
============================================================
Response: An API (Application Programming Interface) is a set of ...

============================================================
Step 5: Parameters — Temperature, Max Tokens, Top-p
============================================================
Temperature 0.0 (deterministic):
  Run 1: A curious tabby cat discovered a hidden garden ...
  Run 2: A curious tabby cat discovered a hidden garden ...

Temperature 1.0 (creative):
  Run 1: Under the silver moonlight, a sleek black cat ...
  Run 2: The old marmalade cat stretched lazily across ...

Max tokens = 10 (truncated):
  Response: Once upon a time, a mighty dragon

Top-p = 0.1 (narrow sampling):
  Response: A curious cat discovered a hidden door ...

============================================================
Step 6: OGX vs Direct vLLM / Ollama
============================================================
In this lesson we called OGX's /v1/chat/completions endpoint.
Under the hood, OGX forwards the request to the configured
inference backend (vLLM or Ollama). You could call that backend
directly, but OGX adds a unified layer on top:

  - RAG:     Vector IO API for retrieval-augmented generation
  - Agents:  Agent creation, sessions, and multi-turn execution
  - Memory:  Conversation history across sessions
  - Safety:  Input/output shields and content moderation
  - Tools:   Tool runtime with MCP integration

OGX is a unified API surface for the full AI application stack.
The remaining lessons in this tutorial explore each of these.

============================================================
Lesson complete!
============================================================
```

(Exact responses will vary depending on the model and parameters.)

## Key Takeaways

- OGX exposes an OpenAI-compatible `/v1/chat/completions` endpoint via the `ogx_client` Python SDK.
- System messages control assistant behavior; conversation history enables multi-turn context.
- Streaming (`stream=True`) delivers tokens in real time, which is essential for interactive applications.
- Temperature, max_tokens, and top_p let you tune the tradeoff between creativity and consistency.
- OGX adds RAG, agents, memory, safety, and tools on top of raw inference — you get the full AI stack through one API.

## Next Steps

Next up: **L1-M2.2 — Embeddings**. You will learn how to generate vector embeddings through OGX for use in similarity search and RAG pipelines.
