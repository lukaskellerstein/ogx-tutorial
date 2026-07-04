---
globs: ["tutorial/**/*.py"]
---

# Python Coding Standards for Tutorial Code

## Style

- Target Python 3.10+. Use type hints on function signatures.
- Use `if __name__ == "__main__":` guard in every `main.py`.
- Use `asyncio.run(main())` for async lessons (agents, streaming).
- Import order: stdlib, third-party, local — separated by blank lines.
- Use f-strings for string formatting.
- Keep functions short and focused — this is tutorial code, readability is paramount.

## Complexity by Level

- **Level 1**: Simple, single-concept scripts. Minimal abstraction. One main function.
- **Level 2**: Multi-step projects. Helper functions OK. Can import from local modules.

## OGX Client Setup

Always set up the OGX client at the top of `main.py`:

```python
from ogx_client import OgxClient

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"

client = OgxClient(base_url=OGX_URL)
```

## Inference via OGX

OGX connects to Ollama serving `gemma4:e4b`:

```python
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
print(response.choices[0].message.content)
```

For streaming:
```python
stream = client.chat.completions.create(
    model=MODEL,
    messages=[...],
    stream=True,
)
for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

## Agent Frameworks with OGX

For LangChain/LangGraph lessons, use OGX as the OpenAI-compatible inference backend:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8321/v1",
    model="ollama/gemma4:e4b",
    api_key="not-needed",
)
```

## Error Handling

- Check that OGX server is reachable before making API calls.
- Print clear error messages if infrastructure is not running.
- Do not silently swallow exceptions — this is educational code.

## Dependencies

- Use `uv add` to add dependencies, never `pip install`.
- Common dependencies by topic:
  - All lessons: `ogx-client`
  - LangChain lessons: `langchain`, `langchain-openai`, `langchain-core`
  - LangGraph lessons: `langgraph`, `langchain-openai`
  - RAG lessons (LangChain): `langchain-qdrant`
  - Embeddings: handled via OGX API (no separate dependency needed)

## Console Output

Print section headers and results so users can follow along:

```python
print("=" * 60)
print("Step 1: Setting up OGX client")
print("=" * 60)
```

Print key results inline — don't force users to check the OGX server for everything.
