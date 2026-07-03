# L1-M4.1 — Tool Runtime API

**Level:** Essentials
**Duration:** 45 min

## Overview

Learn how to give an LLM the ability to call external functions through OGX's Responses API. This lesson covers defining custom tools with JSON Schema, processing the model's tool call requests, executing functions locally, returning results so the model can compose its final answer, and previewing MCP integration for connecting external tool servers.

## Prerequisites

- Completed: L1-M3.2 Building a RAG Application
- Infrastructure running: OGX server (port 8321), Ollama with `gemma4:e4b`

## Concepts

### What is Tool Calling?

LLMs generate text, but they cannot perform actions in the real world — they cannot check the weather, query a database, or run calculations. Tool calling bridges this gap: you describe available functions to the model, and when it needs external information, it requests a function call instead of guessing.

### The Tool Execution Flow

Tool calling is a multi-step loop between your application and the model:

1. **You** send a user query along with tool definitions to the model
2. **The model** analyzes the query and decides whether a tool is needed
3. **The model** returns a `function_call` output item with the function name and arguments
4. **You** execute the function locally and collect the result
5. **You** send the result back as a `function_call_output` item
6. **The model** incorporates the result and produces its final answer

The model never executes tools directly — it only requests calls. Your application is responsible for execution, which keeps you in control.

### Defining Tools with JSON Schema

Each tool is described as a JSON object with a name, description, and parameter schema:

```python
{
    "type": "function",
    "name": "get_weather",
    "description": "Get current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"}
        },
        "required": ["city"],
    },
}
```

Good descriptions help the model decide when and how to use each tool. Be specific about what the tool does and what each parameter means.

### OGX Responses API

OGX's Responses API (`client.responses.create()`) is the modern interface for tool calling. It returns a response object whose `output` list may contain:

| Output Type | Meaning |
|-------------|---------|
| `message` | Standard text response from the model |
| `function_call` | Model wants to call a tool (has `.name`, `.arguments`, `.call_id`) |
| `web_search_call` | Built-in web search was executed |
| `mcp_call` | MCP tool was called |

### Built-in vs Custom Tools

OGX supports several tool types:

- **`function`** — Custom functions you define and execute locally (this lesson)
- **`web_search`** — Built-in web search, executed server-side by OGX
- **`file_search`** — Built-in RAG/vector search
- **`mcp`** — Tools from an MCP server, discovered and executed by OGX

### MCP Integration

OGX can connect to MCP (Model Context Protocol) servers as tool providers. Instead of defining each tool manually, you point OGX at an MCP server URL and it discovers the available tools automatically. This is covered in the preview at the end of this lesson.

## Step-by-Step

### Step 1: Define Custom Tools

We create two tool definitions in JSON Schema format — `get_weather` and `calculate`. These tell the model what functions are available, what parameters they accept, and when to use them:

```python
WEATHER_TOOL = {
    "type": "function",
    "name": "get_weather",
    "description": "Get current weather for a city.",
    "parameters": {
        "type": "object",
        "properties": {
            "city": {
                "type": "string",
                "description": "City name (e.g. Prague, London, Tokyo)",
            },
        },
        "required": ["city"],
        "additionalProperties": False,
    },
}
```

We also implement mock Python functions that return realistic data. In a real application, these would call actual APIs.

### Step 2: Single Tool Call — Weather Query

We send a weather question to the model along with the tool definitions. The model recognizes it needs external data and returns a `function_call` output item instead of guessing:

```python
response = client.responses.create(
    model=MODEL,
    input="What is the current weather in Prague?",
    tools=ALL_TOOLS,
    stream=False,
)

# Check for tool call requests in the output
tool_calls = [item for item in response.output if item.type == "function_call"]
```

When we find a `function_call`, we extract the arguments, run our local function, and send the result back:

```python
args = json.loads(call.arguments)
result = get_weather(args["city"])

# Send the result back to the model
follow_up = client.responses.create(
    model=MODEL,
    input=[
        *response.output,
        {"type": "function_call_output", "call_id": call.call_id, "output": result},
    ],
    tools=ALL_TOOLS,
    stream=False,
)
print(follow_up.output_text)
```

### Step 3: Calculator Tool Call

A math question triggers the `calculate` tool. The model formats the expression as a tool call argument rather than attempting mental math:

```python
response = client.responses.create(
    model=MODEL,
    input="What is 42 multiplied by 17?",
    tools=ALL_TOOLS,
    stream=False,
)
```

### Step 4: Multi-Tool Query

When a query requires multiple tools, the model may issue several `function_call` items in a single response. We process all of them, send all results back, and the model composes a unified answer:

```python
query = "What's the weather in Prague and what is 42 * 17?"
```

The model might return two `function_call` items — one for `get_weather` and one for `calculate`. Our loop handles both.

### Step 5: MCP Integration (Preview)

OGX can also connect MCP servers as tool providers. Instead of defining tools manually, you specify an MCP server URL:

```python
tools = [{
    "type": "mcp",
    "server_url": "http://localhost:3000/mcp",
    "server_label": "my-mcp-server",
}]
```

OGX discovers the available tools from the MCP server automatically and handles execution server-side.

## Running the Lesson

```bash
cd tutorial/level_1/M4_tool_calling_mcp/1_tool_runtime_api
uv sync
uv run python main.py
```

## Expected Output

```
L1-M4.1 — Tool Runtime API
============================================================

============================================================
Step 1: Define Custom Tools
============================================================
We define two tools as JSON Schema objects:

  - get_weather(city): Get current weather for a city.
  - calculate(expression): Evaluate a mathematical expression ...

The model will receive these definitions and can decide
to call them when it needs external information.

============================================================
Step 2: Single Tool Call — Weather Query
============================================================
User: What is the current weather in Prague?

Model requested 1 tool call(s):
  -> Calling get_weather({'city': 'Prague'})
     Result: {"city": "Prague", "temperature_celsius": 18, ...}

Assistant: The current weather in Prague is 18°C and partly cloudy ...

============================================================
Step 3: Calculator Tool Call
============================================================
User: What is 42 multiplied by 17?

Model requested 1 tool call(s):
  -> Calling calculate({'expression': '42 * 17'})
     Result: {"expression": "42 * 17", "result": 714}

Assistant: 42 multiplied by 17 equals 714.

============================================================
Step 4: Multi-Tool Query
============================================================
User: What's the weather in Prague and what is 42 * 17?

Model requested 2 tool call(s):
  -> Calling get_weather({'city': 'Prague'})
     Result: {"city": "Prague", "temperature_celsius": 18, ...}
  -> Calling calculate({'expression': '42 * 17'})
     Result: {"expression": "42 * 17", "result": 714}

Assistant: In Prague it is currently 18°C and partly cloudy. ...

============================================================
Step 5: MCP Integration (Preview)
============================================================
In this lesson we defined tools as local functions and
handled execution ourselves. OGX also supports MCP ...

============================================================
Lesson complete!
============================================================
```

(Exact model responses will vary. The tool calls and results are deterministic.)

## Key Takeaways

- Tool calling lets the model request external function execution instead of guessing at answers.
- Tools are defined with JSON Schema — name, description, and parameter types — so the model knows when and how to use them.
- The execution loop is: model requests a call -> you execute locally -> you send the result back -> model composes its answer.
- OGX's Responses API handles tool calling through the `output` items: check for `function_call` type, process it, and return `function_call_output`.
- MCP integration lets you connect external tool servers without defining each tool manually.

## Next Steps

Next up: **L1-M5.1 — Creating Agents**. You will learn how to create OGX agents that combine inference, tool calling, and memory into autonomous conversational agents.
