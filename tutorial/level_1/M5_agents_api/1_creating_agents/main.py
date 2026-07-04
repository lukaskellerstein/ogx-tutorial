"""L1-M5.1 — Creating Agents

Demonstrates OGX agent capabilities: the Responses API for agentic
interactions, multi-turn conversations, tool calling, and the Agent
helper class for session-based workflows.
"""

import json
import sys
from datetime import datetime, timezone

import httpx
from ogx_client import OgxClient
from ogx_client.lib.agents.agent import Agent
from ogx_client.lib.agents.client_tool import client_tool

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"

KNOWLEDGE_BASE = {
    "ogx": "OGX is an open-source unified AI runtime for inference, RAG, agents, and safety.",
    "vllm": "vLLM is a high-throughput inference engine for LLMs.",
    "qdrant": "Qdrant is an open-source vector database for similarity search.",
}

FUNCTION_TOOLS = [
    {"type": "function", "name": "get_current_time",
     "description": "Get the current UTC time.",
     "parameters": {"type": "object", "properties": {}, "required": []}},
    {"type": "function", "name": "search_knowledge",
     "description": "Search a knowledge base for information about AI tools.",
     "parameters": {"type": "object", "properties": {
         "query": {"type": "string", "description": "The search term."}},
         "required": ["query"]}},
]


def check_server_reachable(url: str) -> bool:
    try:
        httpx.get(f"{url}/v1/models", timeout=5).raise_for_status()
        return True
    except Exception:
        return False


def mock_get_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def mock_search(query: str) -> str:
    for key, value in KNOWLEDGE_BASE.items():
        if key in query.lower():
            return value
    return f"No results found for: {query}"


TOOL_DISPATCH = {
    "get_current_time": lambda args: mock_get_time(),
    "search_knowledge": lambda args: mock_search(args.get("query", "")),
}


def step_1_simple_response(client: OgxClient) -> None:
    print()
    print("=" * 60)
    print("Step 1: Simple response with the Responses API")
    print("=" * 60)
    response = client.responses.create(
        model=MODEL,
        input="Explain what OGX is in 2 sentences.",
        instructions="You are a helpful AI assistant that specializes in developer tools.",
    )
    print(f"  Response ID: {response.id}")
    print(f"  Output: {response.output_text}")


def step_2_multi_turn(client: OgxClient) -> None:
    print()
    print("=" * 60)
    print("Step 2: Multi-turn conversation (previous_response_id)")
    print("=" * 60)
    print("  Turn 1: Introducing ourselves...")
    r1 = client.responses.create(
        model=MODEL,
        input="My name is Alice and I am learning about AI runtimes.",
        instructions="You are a friendly AI tutor. Remember the user's name.",
    )
    print(f"  Response: {r1.output_text}")
    print()
    print("  Turn 2: Follow-up linked via previous_response_id...")
    r2 = client.responses.create(
        model=MODEL,
        input="What is my name and what am I learning about?",
        previous_response_id=r1.id,
    )
    print(f"  Response: {r2.output_text}")
    print("  (Model remembered context via previous_response_id chaining.)")


def step_3_agent_with_tools(client: OgxClient) -> None:
    print()
    print("=" * 60)
    print("Step 3: Agent with tools (Responses API)")
    print("=" * 60)
    print("  Tools: get_current_time, search_knowledge")
    print("  Asking: 'What is OGX? Also, what time is it?'\n")

    response = client.responses.create(
        model=MODEL,
        input="What is OGX? Also, what time is it right now?",
        tools=FUNCTION_TOOLS,
        instructions="Use the available tools to answer accurately.",
    )

    tool_outputs = []
    for item in response.output:
        if item.type == "function_call":
            args = json.loads(item.arguments) if item.arguments else {}
            result = TOOL_DISPATCH[item.name](args)
            print(f"  Tool call: {item.name}({args})")
            print(f"  Result:    {result}")
            tool_outputs.append({"type": "function_call_output",
                                 "call_id": item.call_id, "output": result})

    if tool_outputs:
        follow_up = client.responses.create(
            model=MODEL, input=tool_outputs,
            previous_response_id=response.id, tools=FUNCTION_TOOLS,
        )
        print(f"\n  Final answer: {follow_up.output_text}")
    else:
        print(f"  Response (no tools called): {response.output_text}")


def run_agent_turn(agent: Agent, message: str, session_id: str) -> str:
    """Run one agent turn and return the final text."""
    final_text = ""
    for event in agent.create_turn(
        messages=[{"role": "user", "content": message}],
        session_id=session_id,
    ):
        if hasattr(event, "final_text"):
            final_text = event.final_text
    return final_text


def step_4_agent_helper(client: OgxClient) -> None:
    print()
    print("=" * 60)
    print("Step 4: Agent helper class (session-based workflow)")
    print("=" * 60)

    @client_tool
    def get_current_time() -> str:
        """Get the current UTC time.

        Returns the current time in ISO 8601 format.
        """
        return datetime.now(timezone.utc).isoformat()

    @client_tool
    def search_knowledge(query: str) -> str:
        """Search a knowledge base for AI-related information.

        :param query: The search term to look up.
        """
        for key, val in KNOWLEDGE_BASE.items():
            if key in query.lower():
                return val
        return f"No results for: {query}"

    agent = Agent(
        client, model=MODEL,
        instructions="You are a helpful AI assistant. Use tools when appropriate.",
        tools=[get_current_time, search_knowledge],
    )
    session_id = agent.create_session("demo-session")
    print(f"  Session created: {session_id}")

    print("  Turn 1: 'What time is it?'")
    print(f"  Response: {run_agent_turn(agent, 'What time is it?', session_id)}")
    print()
    print("  Turn 2: 'Tell me about Qdrant.'")
    print(f"  Response: {run_agent_turn(agent, 'Tell me about Qdrant.', session_id)}")


def step_5_comparison() -> None:
    print()
    print("=" * 60)
    print("Step 5: OGX Agents vs LangGraph Agents")
    print("=" * 60)
    print("""
  OGX Agents:  simpler API, native tool/safety/memory integration,
               built-in multi-turn via previous_response_id.
               Less control over execution flow.

  LangGraph:   full StateGraph control (nodes, edges, cycles),
               multi-agent orchestration (supervisor, swarm).
               More boilerplate; separate tool/safety setup.

  Use OGX for simple tool-calling agents with built-in safety.
  Use LangGraph for complex control flow or multi-agent systems.
""")


def main() -> None:
    print()
    print("L1-M5.1 — Creating Agents")
    print("=" * 60)
    print()
    print("Checking OGX server connectivity...")
    if not check_server_reachable(OGX_URL):
        print(f"  ERROR: OGX server not reachable at {OGX_URL}")
        print("  Start infrastructure:  cd infra && podman compose up -d")
        sys.exit(1)
    print(f"  OGX is reachable at {OGX_URL}")

    client = OgxClient(base_url=OGX_URL)

    step_1_simple_response(client)
    step_2_multi_turn(client)
    step_3_agent_with_tools(client)
    step_4_agent_helper(client)
    step_5_comparison()

    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print()
    print("  Next: L1-M5.2 — Agents with RAG")
    print("  (Combine agents with Vector IO for retrieval-augmented answers)")
    print()


if __name__ == "__main__":
    main()
