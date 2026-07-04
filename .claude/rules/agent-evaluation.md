---
globs: ["tutorial/level_1/M5_agents_api/**", "tutorial/level_2/**"]
---

# Agent Patterns — Focus Area

Agents are a core part of this tutorial. The goal is to show how to build, run, and integrate AI agents using OGX's APIs and external agent frameworks.

## Where Agents Appear in the Curriculum

- **Level 1, M4**: Tool Calling & MCP — function tools via Responses API, MCP integration
- **Level 1, M5**: Responses API & Agents — OGX Responses API agents, agents with RAG
- **Level 2, M1**: Advanced Patterns — multi-provider, telemetry, evaluation, production deployment
- **Level 2, M2**: OGX on OpenShift AI — operator deployment, vLLM integration, safety

## Agent Frameworks

### 1. OGX Responses API Agents (Level 1, M5)
- Use OGX Responses API (`/v1/responses`) — the primary agent orchestration interface
- Multi-turn via `previous_response_id`
- Built-in tool types: `web_search`, `file_search`, `code_interpreter`, `mcp`
- Agent helper: `from ogx_client.lib.agents.agent import Agent` with `@client_tool`
- Note: old Agents API (`/v1alpha/agents`) is deprecated/legacy

### 2. LangChain Agents
- Use `create_react_agent` from LangChain v1.0+ (NOT deprecated APIs)
- Connect to OGX via OpenAI-compatible endpoint (`langchain-openai`)
- Track: tool calls, reasoning steps, iterations, final answers
- Reference code: `/Users/lkellers/Projects/github/lukaskellerstein/ai-agents-course/Version_2/6_langchain-ai/1_langchain/10_agent`

### 3. LangGraph Agents
- Use `StateGraph`, nodes, edges, conditional edges
- Connect to OGX via OpenAI-compatible endpoint
- Single agents and multi-agent systems
- Patterns: collaboration, supervision, swarm
- Reference code (agents): `.../2_langgraph/5_agent`
- Reference code (multi-agent): `.../2_langgraph/6_agents`

### 4. DeepAgents
- LangChain-AI's multi-agent orchestration framework
- Source code: `~/Projects/github/lanchain-ai/deepagents`

## Integration Pattern

All agent frameworks connect to OGX via its OpenAI-compatible API:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8321/v1",
    model="ollama/gemma4:e4b",
    api_key="not-needed",
)
```

For OGX Responses API agents, use the OGX client directly:

```python
from ogx_client import OgxClient

client = OgxClient(base_url="http://localhost:8321")
response = client.responses.create(
    model="ollama/gemma4:e4b",
    input="Hello!",
    tools=[...],
)
```

## MCP Integration

OGX has native MCP tool runtime support. MCP servers can be connected as tool providers for agents.

Reference code: `/Users/lkellers/Projects/github/lukaskellerstein/ai-agents-course/Version_2/2_MCP`
