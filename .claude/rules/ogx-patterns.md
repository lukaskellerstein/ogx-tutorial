---
globs: ["tutorial/**/*.py"]
---

# OGX Patterns and APIs

## Core APIs by Level

### Level 1 — Essentials

#### Fundamentals (L1-M1)
- OGX API surface overview
- `OGXClient` — Python client for all API calls
- Distributions: `starter` (general), `remote-vllm` (production)
- Configuration via `run.yaml`

#### Inference API (L1-M2)
- `client.inference.chat_completion()` — chat completions
- `client.inference.completion()` — text completions
- `client.inference.embeddings()` — generate embeddings
- Streaming responses
- Model: `google/gemma-4-E4B-it` via vLLM

#### RAG / Vector IO API (L1-M3)
- `client.vector_io.insert()` — add documents with embeddings
- `client.vector_io.query()` — similarity search
- Qdrant as vector backend (`inline::qdrant` or `remote::qdrant`)
- Document chunking and embedding pipeline

#### Tool Runtime API (L1-M4)
- `client.tool_runtime` — tool calling infrastructure
- Custom tool registration with function signatures
- MCP integration: connecting MCP servers as tool providers
- Built-in tools: web search, code interpreter

#### Agents API (L1-M5)
- `client.agents.create()` — create an agent with model, tools, instructions
- `client.agents.session.create()` — create a conversation session
- `client.agents.turn.create()` — run agent turns (single-turn and multi-turn)
- Streaming agent responses
- Agents with RAG: automatic Vector IO integration
- Memory API for conversation history across sessions

#### Safety API (L1-M6)
- `client.safety` — content moderation
- Input shields: check user messages before processing
- Output shields: check model responses before returning
- Built-in detectors: content classification, toxicity, PII

### Level 2 — Practitioner

#### Multi-Provider Configuration (L2-M1.1)
- Multiple inference providers in one OGX instance
- Routing: different models for different tasks
- Fallback chains: primary → secondary provider

#### Custom Providers (L2-M1.2)
- Building custom inference providers
- Custom safety detectors
- Plugin architecture

#### Production Deployment (L2-M1.3)
- Podman Compose: OGX + vLLM + Qdrant + PostgreSQL
- PostgreSQL KVStore for memory (production)
- Qdrant server for vector storage (production)
- Health checks, logging, metrics

## Patterns to Follow

### OGX Client Setup
Always initialize the client at the top of `main.py`:
```python
from ogx_client import OGXClient

client = OGXClient(base_url="http://localhost:8321")
```

### Using OGX with LangChain
OGX exposes an OpenAI-compatible API, so use `langchain-openai`:
```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8321/v1",
    model="google/gemma-4-E4B-it",
    api_key="not-needed",
)
```

### RAG Pattern with Qdrant
```python
# 1. Create a vector store
client.vector_stores.create(name="my-docs", embedding_model="...",
                            provider_id="qdrant")

# 2. Insert documents
client.vector_io.insert(vector_db_id="my-docs", chunks=[...])

# 3. Query
results = client.vector_io.query(vector_db_id="my-docs", query="search text")

# 4. Pass context to inference
response = client.inference.chat_completion(
    model_id="google/gemma-4-E4B-it",
    messages=[
        {"role": "system", "content": f"Context: {results}"},
        {"role": "user", "content": question},
    ],
)
```

### Agent Pattern
```python
# 1. Create agent
agent = client.agents.create(
    model="google/gemma-4-E4B-it",
    instructions="You are a helpful assistant.",
    tools=[...],
)

# 2. Create session
session = client.agents.session.create(agent_id=agent.agent_id)

# 3. Run turns
response = client.agents.turn.create(
    agent_id=agent.agent_id,
    session_id=session.session_id,
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Always Check the OGX Documentation
When implementing OGX features, verify the API exists and its signature by consulting:
- Documentation: https://ogx-ai.github.io/docs
- Python client: https://github.com/ogx-ai/ogx-client-python
- Providers: https://ogx-ai.github.io/docs/providers

Do NOT guess at API names or parameters. Read the docs if unsure.
