---
globs: ["tutorial/level_1/M5_agents_api/**", "tutorial/level_2/**"]
---

# Agent Patterns — Focus Area

Agents are a core part of this tutorial. The goal is to show how to build, run, and integrate AI agents using OGX's APIs and external agent frameworks.

## Where Agents Appear in the Curriculum

- **Level 1, M4**: Tool Calling & MCP — OGX tool runtime, custom tools, MCP integration
- **Level 1, M5**: Agents API — OGX native agents, agents with RAG
- **Level 2, M1**: Advanced Patterns — multi-provider, custom providers, production deployment

## Agent Frameworks

### 1. OGX Native Agents (Level 1, M5)
- Use OGX Agents API (`/v1alpha/agents`)
- Built-in tool calling, safety shields, memory
- Simpler API than LangGraph, less flexible but tighter OGX integration
- Multi-turn conversations with session management

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
    model="google/gemma-4-E4B-it",
    api_key="not-needed",
)
```

For OGX native agents, use the OGX client directly:

```python
from ogx_client import OGXClient

client = OGXClient(base_url="http://localhost:8321")
agent = client.agents.create(
    model="google/gemma-4-E4B-it",
    instructions="...",
    tools=[...],
)
```

## MCP Integration

OGX has native MCP tool runtime support. MCP servers can be connected as tool providers for agents.

Reference code: `/Users/lkellers/Projects/github/lukaskellerstein/ai-agents-course/Version_2/2_MCP`
