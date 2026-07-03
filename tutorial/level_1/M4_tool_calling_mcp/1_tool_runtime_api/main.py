"""L1-M4.1 — Tool Runtime API.

Demonstrates tool calling through OGX using the Responses API:
defining custom tools, processing tool call requests, executing
functions locally, and returning results to the model.
"""

import json
import sys

import httpx
from ogx_client import OgxClient


OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"


# ---------------------------------------------------------------------------
# Mock tool implementations
# ---------------------------------------------------------------------------

def get_weather(city: str) -> str:
    """Return mock weather data for a given city."""
    weather_data: dict[str, dict[str, str | int]] = {
        "Prague": {"temp_c": 18, "condition": "Partly cloudy", "humidity": 62},
        "London": {"temp_c": 14, "condition": "Overcast", "humidity": 78},
        "Tokyo": {"temp_c": 27, "condition": "Sunny", "humidity": 55},
    }
    data = weather_data.get(city, {"temp_c": 20, "condition": "Clear", "humidity": 50})
    return json.dumps({
        "city": city,
        "temperature_celsius": data["temp_c"],
        "condition": data["condition"],
        "humidity_percent": data["humidity"],
    })


def calculate(expression: str) -> str:
    """Evaluate a math expression and return the result."""
    try:
        result = eval(expression, {"__builtins__": {}}, {})  # noqa: S307
        return json.dumps({"expression": expression, "result": result})
    except Exception as exc:
        return json.dumps({"expression": expression, "error": str(exc)})


TOOL_DISPATCH: dict[str, callable] = {
    "get_weather": lambda args: get_weather(args["city"]),
    "calculate": lambda args: calculate(args["expression"]),
}


# ---------------------------------------------------------------------------
# Tool definitions (JSON Schema format)
# ---------------------------------------------------------------------------

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

CALCULATE_TOOL = {
    "type": "function",
    "name": "calculate",
    "description": "Evaluate a mathematical expression and return the result.",
    "parameters": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "A math expression to evaluate (e.g. '42 * 17')",
            },
        },
        "required": ["expression"],
        "additionalProperties": False,
    },
}

ALL_TOOLS = [WEATHER_TOOL, CALCULATE_TOOL]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def check_server() -> bool:
    """Verify that the OGX server is reachable."""
    try:
        resp = httpx.get(f"{OGX_URL}/v1/models", timeout=5)
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"ERROR: OGX server is not reachable at {OGX_URL}")
        print(f"  {exc}")
        print("Start the infrastructure first:")
        print("  Ollama:  ollama serve")
        print("  OGX:     podman compose up -d ogx")
        return False


def run_with_tools(client: OgxClient, query: str) -> None:
    """Send a query with tools, handle any tool calls, and print the result."""
    print(f"User: {query}\n")

    response = client.responses.create(
        model=MODEL, input=query, tools=ALL_TOOLS, stream=False,
    )

    tool_calls = [item for item in response.output if item.type == "function_call"]

    if not tool_calls:
        print(f"Assistant (no tool call): {response.output_text}")
        return

    # Execute each tool call and collect results
    print(f"Model requested {len(tool_calls)} tool call(s):")
    input_items: list = list(response.output)

    for call in tool_calls:
        args = json.loads(call.arguments)
        func = TOOL_DISPATCH.get(call.name)
        result = func(args) if func else json.dumps({"error": f"Unknown: {call.name}"})

        print(f"  -> Calling {call.name}({args})")
        print(f"     Result: {result}")

        input_items.append({
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": result,
        })

    # Send results back so the model can compose its final answer
    final = client.responses.create(
        model=MODEL, input=input_items, tools=ALL_TOOLS, stream=False,
    )
    print(f"\nAssistant: {final.output_text}")


# ---------------------------------------------------------------------------
# Lesson steps
# ---------------------------------------------------------------------------

def step1_define_tools() -> None:
    """Step 1: Show the tool definitions."""
    print("=" * 60)
    print("Step 1: Define Custom Tools")
    print("=" * 60)
    print("We define two tools as JSON Schema objects:\n")
    for tool in ALL_TOOLS:
        params = ", ".join(tool["parameters"]["required"])
        print(f"  - {tool['name']}({params}): {tool['description']}")
    print()
    print("The model will receive these definitions and can decide")
    print("to call them when it needs external information.")
    print()


def step2_single_tool_call(client: OgxClient) -> None:
    """Step 2: A query that triggers a single tool call."""
    print("=" * 60)
    print("Step 2: Single Tool Call — Weather Query")
    print("=" * 60)
    run_with_tools(client, "What is the current weather in Prague?")
    print()


def step3_calculator_tool(client: OgxClient) -> None:
    """Step 3: A query that uses the calculator tool."""
    print("=" * 60)
    print("Step 3: Calculator Tool Call")
    print("=" * 60)
    run_with_tools(client, "What is 42 multiplied by 17?")
    print()


def step4_multi_tool(client: OgxClient) -> None:
    """Step 4: A query that may trigger multiple tool calls."""
    print("=" * 60)
    print("Step 4: Multi-Tool Query")
    print("=" * 60)
    run_with_tools(client, "What's the weather in Prague and what is 42 * 17?")
    print()


def step5_mcp_note() -> None:
    """Step 5: Explain MCP integration with the Responses API."""
    print("=" * 60)
    print("Step 5: MCP Integration (Preview)")
    print("=" * 60)
    print(
        "In this lesson we defined tools as local functions and\n"
        "handled execution ourselves. OGX also supports MCP\n"
        "(Model Context Protocol) servers as tool providers.\n"
        "\n"
        "With MCP, you point the Responses API at an MCP server\n"
        "and OGX handles tool discovery and execution for you:\n"
        "\n"
        '  tools=[{\n'
        '      "type": "mcp",\n'
        '      "server_url": "http://localhost:3000/mcp",\n'
        '      "server_label": "my-mcp-server",\n'
        "  }]\n"
        "\n"
        "MCP servers expose tools via a standard protocol, so you\n"
        "can plug in file systems, databases, APIs, and more —\n"
        "all without writing custom tool definitions.\n"
        "\n"
        "The key advantage of using OGX for tool calling is the\n"
        "unified layer: inference + tools + safety + memory, all\n"
        "through a single API surface."
    )
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    """Run all tool calling demonstrations."""
    print()
    print("L1-M4.1 — Tool Runtime API")
    print("=" * 60)
    print()

    if not check_server():
        sys.exit(1)

    client = OgxClient(base_url=OGX_URL)

    step1_define_tools()
    step2_single_tool_call(client)
    step3_calculator_tool(client)
    step4_multi_tool(client)
    step5_mcp_note()

    print("=" * 60)
    print("Lesson complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
