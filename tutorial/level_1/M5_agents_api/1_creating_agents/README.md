# L1-M5.1 — Creating Agents

**Level:** Essentials
**Duration:** 1 hour

## Overview

In this lesson you build AI agents with OGX using two complementary approaches: the **Responses API** for direct agentic interactions with tool calling, and the **Agent helper class** for session-based workflows with automatic tool execution. By the end you will understand how to create agents, chain multi-turn conversations, define and invoke custom tools, and choose between OGX agents and LangGraph agents.

## Prerequisites

- Completed: L1-M4.1 Tool Runtime API
- Infrastructure running: OGX (port 8321), Ollama with `gemma4:e4b`
- See `infra/` in the repository root for setup instructions

## Concepts

### The Responses API

The Responses API (`client.responses.create()`) is OGX's primary interface for agentic interactions. Unlike the lower-level Chat Completions API, the Responses API provides:

- **Instructions** — a system-level directive separate from user input
- **Tool definitions** — function schemas the model can decide to invoke
- **Conversation chaining** — link responses together with `previous_response_id` for multi-turn context
- **Response management** — retrieve, list, and delete past responses

Each call returns a `ResponseObject` with an `id` that can be referenced in subsequent calls, enabling stateful conversations without manually managing message history.

### Tool Calling

When you pass `tools` to `client.responses.create()`, the model can decide to call one or more tools instead of (or before) generating a text answer. The flow is:

1. Send a request with tool definitions (JSON Schema format)
2. The model returns `function_call` output items with the tool name and arguments
3. Your code executes the tool and collects results
4. Send the results back with `previous_response_id` so the model can incorporate them
5. The model generates its final text answer

This manual loop gives you full control over tool execution — you decide how and when tools run.

### The Agent Helper Class

The `Agent` class from `ogx_client.lib.agents` wraps the Responses API into a higher-level abstraction:

- **Sessions** — create named conversation sessions that persist across turns
- **Automatic tool execution** — the Agent runs client-side tools for you in a loop
- **Streaming events** — iterate over turn events (step progress, tool calls, completion)
- **`@client_tool` decorator** — turn any Python function into an agent tool with a single decorator

The Agent helper is ideal when you want a "batteries-included" experience without managing the tool-call loop yourself.

### OGX Agents vs LangGraph Agents

Both frameworks connect to OGX via its OpenAI-compatible API, but they serve different needs:

| Aspect | OGX Agents | LangGraph Agents |
|--------|-----------|-----------------|
| API complexity | Simple — few lines of code | Complex — StateGraph, nodes, edges |
| Tool calling | Built-in, automatic loop | Manual or via pre-built nodes |
| Safety | Native shield integration | Requires separate setup |
| Multi-turn memory | Built-in via sessions | Manual state management |
| Control flow | Linear tool-call loop | Conditional routing, cycles, branches |
| Multi-agent | Not built-in | Supervisor, swarm, collaboration patterns |

Use OGX agents for straightforward tool-calling agents. Use LangGraph when you need complex control flow or multi-agent orchestration.

## Step-by-Step

### Step 1: Simple Response with the Responses API

The simplest agentic interaction sends a prompt with optional instructions. The `instructions` parameter acts as a system prompt, separate from the user's `input`.

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")

response = client.responses.create(
    model="ollama/gemma4:e4b",
    input="Explain what OGX is in 2 sentences.",
    instructions="You are a helpful AI assistant that specializes in developer tools.",
)
print(response.output_text)
```

The response object includes an `id` that uniquely identifies this interaction — we use it in the next step.

### Step 2: Multi-Turn Conversation

Chain conversations by passing `previous_response_id`. OGX automatically includes the prior context, so you do not need to resend the full message history.

```python
r1 = client.responses.create(
    model="ollama/gemma4:e4b",
    input="My name is Alice and I am learning about AI runtimes.",
    instructions="You are a friendly AI tutor. Remember the user's name.",
)

r2 = client.responses.create(
    model="ollama/gemma4:e4b",
    input="What is my name and what am I learning about?",
    previous_response_id=r1.id,
)
print(r2.output_text)  # The model recalls "Alice" and "AI runtimes"
```

### Step 3: Agent with Tools (Manual Loop)

Define tools as JSON Schema objects and pass them via the `tools` parameter. The model decides when to call them. Your code executes the tools and sends results back.

```python
tools = [
    {
        "type": "function",
        "name": "get_current_time",
        "description": "Get the current UTC time.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
]

response = client.responses.create(
    model="ollama/gemma4:e4b",
    input="What time is it?",
    tools=tools,
)

# Process tool calls from the response output
for item in response.output:
    if item.type == "function_call":
        result = execute_tool(item.name, item.arguments)
        # Send tool result back to the model
```

The lesson code implements the full loop with two tools (`get_current_time` and `search_knowledge`) and shows the model composing a final answer from tool results.

### Step 4: Agent Helper Class

The `Agent` class automates the tool-call loop. Define tools with the `@client_tool` decorator and the Agent handles execution, streaming, and session management.

```python
from ogx_client.lib.agents.agent import Agent
from ogx_client.lib.agents.client_tool import client_tool

@client_tool
def get_current_time() -> str:
    """Get the current UTC time.

    Returns the current time in ISO 8601 format.
    """
    return datetime.now(timezone.utc).isoformat()

agent = Agent(
    client,
    model="ollama/gemma4:e4b",
    instructions="You are a helpful assistant. Use tools when appropriate.",
    tools=[get_current_time],
)

session_id = agent.create_session("demo-session")
for event in agent.create_turn(
    messages=[{"role": "user", "content": "What time is it?"}],
    session_id=session_id,
):
    if hasattr(event, "final_text"):
        print(event.final_text)
```

The `@client_tool` decorator reads the function's docstring and type hints to generate the tool schema automatically. Use RST-style `:param name:` docstrings to describe parameters.

### Step 5: Comparison Note

The lesson prints a side-by-side comparison of OGX agents versus LangGraph agents, covering API complexity, tool integration, safety, memory, and control flow.

## Running the Lesson

```bash
cd tutorial/level_1/M5_agents_api/1_creating_agents
uv sync
uv run python main.py
```

## Expected Output

```
L1-M5.1 — Creating Agents
============================================================

Checking OGX server connectivity...
  OGX is reachable at http://localhost:8321

============================================================
Step 1: Simple response with the Responses API
============================================================
  Response ID: resp_abc123...
  Output: OGX (Open GenAI Stack) is an open-source unified AI runtime
  that provides standardized APIs for inference, RAG, agents, tool
  calling, and safety. It supports 23 inference providers and lets
  developers build AI applications through a single API surface.

============================================================
Step 2: Multi-turn conversation (previous_response_id)
============================================================
  Turn 1: Introducing ourselves...
  Response: Hi Alice! Welcome to the world of AI runtimes...

  Turn 2: Follow-up linked via previous_response_id...
  Response: Your name is Alice, and you are learning about AI runtimes.

  The model remembered context from turn 1 because we
  chained the conversation with previous_response_id.

============================================================
Step 3: Agent with tools (Responses API)
============================================================
  Tools available: get_current_time, search_knowledge
  Asking: 'What is OGX? Also, what time is it?'

  Tool call: search_knowledge({'query': 'OGX'})
  Result:    OGX (Open GenAI Stack) is an open-source unified AI runtime...
  Tool call: get_current_time({})
  Result:    2026-07-03T14:30:00+00:00

  Final answer: OGX is an open-source unified AI runtime providing
  standardized APIs for inference, RAG, agents, tools, and safety.
  The current UTC time is 2026-07-03T14:30:00.

============================================================
Step 4: Agent helper class (session-based workflow)
============================================================
  Session created: conv_xyz789...
  Turn 1: 'What time is it?'
  Response: The current UTC time is 2026-07-03T14:30:00.

  Turn 2: 'Tell me about Qdrant.'
  Response: Qdrant is an open-source vector database.

============================================================
Step 5: OGX Agents vs LangGraph Agents
============================================================

  OGX Agents (Responses API + Agent helper)
    + Simpler API — fewer lines of code to get started
    + Native integration with OGX tools, safety shields, memory
    ...

  LangGraph Agents
    + Full control via StateGraph with nodes and edges
    + Conditional routing, branching, and cycles
    ...

============================================================
Done!
============================================================

  Next: L1-M5.2 — Agents with RAG
  (Combine agents with Vector IO for retrieval-augmented answers)
```

Note: The exact model responses will vary with each run.

## Key Takeaways

- The **Responses API** (`client.responses.create()`) is OGX's primary agentic interface, supporting instructions, tools, and conversation chaining via `previous_response_id`.
- **Multi-turn conversations** are built by linking responses — no need to manually track message history.
- **Tool calling** follows a request-execute-respond loop: the model decides which tools to call, your code runs them, and results are sent back for the final answer.
- The **Agent helper class** automates the tool-call loop and adds session management, making it the fastest path to a working agent.
- **OGX agents** are best for straightforward tool-calling workflows; **LangGraph agents** are better when you need complex control flow or multi-agent orchestration.

## Next Steps

In the next lesson, **L1-M5.2 — Agents with RAG**, you will combine agents with the Vector IO API so the agent can retrieve relevant context from a document corpus before answering questions. You will also integrate the Memory API for persistent conversation history across sessions.
