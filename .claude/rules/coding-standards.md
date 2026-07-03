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
from ogx_client import OGXClient

client = OGXClient(base_url="http://localhost:8321")
```

## Inference via OGX

OGX connects to vLLM serving `google/gemma-4-E4B-it`:

```python
response = client.inference.chat_completion(
    model_id="google/gemma-4-E4B-it",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ],
)
print(response.completion_message.content.text)
```

For streaming:
```python
for chunk in client.inference.chat_completion(
    model_id="google/gemma-4-E4B-it",
    messages=[...],
    stream=True,
):
    print(chunk, end="", flush=True)
```

## Agent Frameworks with OGX

For LangChain/LangGraph lessons, use OGX as the OpenAI-compatible inference backend:

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    base_url="http://localhost:8321/v1",
    model="google/gemma-4-E4B-it",
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
