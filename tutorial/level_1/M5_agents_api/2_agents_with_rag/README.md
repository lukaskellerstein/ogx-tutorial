# L1-M5.2 -- Agents with RAG

**Level:** Essentials
**Duration:** 45 min

## Overview

This lesson combines OGX agents with Retrieval-Augmented Generation (RAG) to build a knowledge-grounded HR assistant. You will populate a vector store with company policy documents, use the Responses API with the `file_search` tool for automatic retrieval, chain multi-turn conversations with `previous_response_id`, and combine RAG with a custom function tool in a single agent.

## Prerequisites

- Completed: L1-M5.1 Creating Agents
- Completed: L1-M3.2 Building a RAG Application (vector store and embedding concepts)
- Infrastructure running: OGX (port 8321), Qdrant (port 6333), Ollama with `gemma4:e4b` and `all-minilm`

## Concepts

### RAG-Powered Agents

In L1-M3.2, you built a manual RAG pipeline: embed a question, query the vector store, inject context into the prompt, and call inference. With the `file_search` tool, OGX handles all of this automatically. You simply tell the Responses API which vector store to search, and it retrieves relevant chunks and injects them into the model's context behind the scenes.

### The file_search Tool

`file_search` is one of OGX's built-in tool types (alongside `function`, `web_search`, and `mcp`). When included in a `responses.create()` call, the server automatically:

1. Embeds the user's query
2. Searches the specified vector store(s) for relevant chunks
3. Injects the retrieved context into the model's prompt
4. Generates a grounded answer

No manual retrieval or prompt construction needed.

```python
response = client.responses.create(
    model=MODEL,
    input="What is the vacation policy?",
    tools=[{
        "type": "file_search",
        "vector_store_ids": ["company-policies"],
    }],
    instructions="You are an HR assistant.",
)
```

### Multi-Turn RAG with previous_response_id

For follow-up questions, use `previous_response_id` to chain responses. OGX preserves the conversation context across turns, so the model understands references to earlier answers while still retrieving fresh context for each new question.

```python
response2 = client.responses.create(
    model=MODEL,
    input="How does remote work differ from that?",
    previous_response_id=response1.id,
    tools=[...],
)
```

Note: the initial response must be created with `store=True` for chaining to work.

### Combining RAG + Custom Tools

An agent can use multiple tool types simultaneously. In this lesson, we combine:

- **file_search** -- retrieves policy documents from the vector store (executed server-side)
- **function** -- a custom `calculate_days_remaining` tool (executed locally)

The model decides which tools to use based on the question. A question about vacation policy triggers `file_search`; a question about calculating remaining days triggers both.

## Step-by-Step

### Step 1: Prepare the Knowledge Base

We create a vector store named `company-policies` and populate it with 8 document chunks covering vacation, remote work, expenses, sick leave, and parental leave policies. Each chunk is embedded using the `all-minilm` model and inserted via the Vector IO API.

```python
client.vector_stores.create(name=VECTOR_STORE_NAME)

texts = [doc["text"] for doc in POLICY_DOCUMENTS]
resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
embeddings = [item.embedding for item in resp.data]

client.vector_io.insert(
    vector_store_id=VECTOR_STORE_NAME,
    chunks=[
        {
            "chunk_id": doc["id"],
            "content": doc["text"],
            "embedding": emb,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": len(emb),
            "chunk_metadata": {"document_id": doc["id"]},
        }
        for doc, emb in zip(POLICY_DOCUMENTS, embeddings)
    ],
)
```

This is the same ingestion pattern from L1-M3.2, applied to a new domain.

### Step 2: RAG-Powered Agent (file_search)

We send a question to the Responses API with the `file_search` tool. OGX handles retrieval automatically -- no manual query-then-generate loop.

```python
response = client.responses.create(
    model=MODEL,
    input="What is the vacation policy?",
    tools=[{
        "type": "file_search",
        "vector_store_ids": [VECTOR_STORE_NAME],
    }],
    instructions="You are an HR assistant. Answer based on company policies.",
    store=True,
    stream=False,
)
print(response.output_text)
```

Compare this to L1-M3.2, where you had to manually embed the query, search the vector store, build the prompt, and call inference. With `file_search`, one API call does it all.

### Step 3: Multi-Turn RAG Agent

We chain follow-up questions using `previous_response_id`. Each question triggers a fresh retrieval from the vector store while maintaining conversation context:

```python
# Turn 1 (from Step 2) gives us response.id

# Turn 2: follow-up question
response2 = client.responses.create(
    model=MODEL,
    input="How does remote work differ from that?",
    tools=[file_search_tool],
    instructions=HR_INSTRUCTIONS,
    previous_response_id=response.id,
    stream=False,
)

# Turn 3: another topic
response3 = client.responses.create(
    model=MODEL,
    input="What about expense reimbursement?",
    tools=[file_search_tool],
    instructions=HR_INSTRUCTIONS,
    previous_response_id=response2.id,
    stream=False,
)
```

### Step 4: RAG + Custom Tools Together

We define a custom function tool `calculate_days_remaining` and combine it with `file_search` in a single request. The model can use both tools to answer a compound question:

```python
combined_tools = [
    {"type": "file_search", "vector_store_ids": [VECTOR_STORE_NAME]},
    {
        "type": "function",
        "name": "calculate_days_remaining",
        "description": "Calculate remaining vacation days.",
        "parameters": {
            "type": "object",
            "properties": {
                "total_days": {"type": "integer"},
                "used_days": {"type": "integer"},
            },
            "required": ["total_days", "used_days"],
        },
    },
]

response = client.responses.create(
    model=MODEL,
    input="I have 20 vacation days and used 13. How many left, and what's the policy?",
    tools=combined_tools,
    instructions=HR_INSTRUCTIONS,
    stream=False,
)
```

The `file_search` tool is executed server-side by OGX. The `function` tool returns a `function_call` output item that we execute locally and send back (the same pattern from L1-M4.1).

### Step 5: Cleanup

We delete the vector store to clean up resources.

## Running the Lesson

```bash
cd tutorial/level_1/M5_agents_api/2_agents_with_rag
uv sync
uv run python main.py
```

## Expected Output

```
L1-M5.2 -- Agents with RAG
============================================================

  OGX server is reachable at http://localhost:8321

============================================================
Step 1: Prepare the Knowledge Base
============================================================
  Created vector store 'company-policies'
  Generating embeddings for 8 policy chunks...
  Embedding dimension: 384
  Inserted 8 chunks into vector store.

============================================================
Step 2: RAG-Powered Agent (file_search)
============================================================
  User: What is the vacation policy?

  Assistant: Employees receive 20 vacation days per year. Days reset on
  January 1st and do not carry over. Vacation requests must be submitted
  at least two weeks in advance. Requests longer than 5 consecutive days
  require VP-level approval...

============================================================
Step 3: Multi-Turn RAG Agent
============================================================

  Turn 1:
  User: How does remote work differ from that?
  Assistant: Remote work is separate from vacation policy. Employees may
  work remotely up to 3 days per week with manager arrangement. All remote
  employees must be available during core hours (10 AM to 3 PM)...

  Turn 2:
  User: What about expense reimbursement?
  Assistant: Business travel expenses are reimbursed within 30 days.
  Flights must be economy class for domestic travel. Hotels are capped at
  $200/night and meals at $75/day. General expenses over $100 require
  pre-approval...

============================================================
Step 4: RAG + Custom Tools Together
============================================================
  User: I get 20 vacation days per year and I have used 13 so far. How
  many days do I have left, and what is the policy for requesting time off?

  -> Tool call: calculate_days_remaining({'total_days': 20, 'used_days': 13})
     Result: {"total_days": 20, "used_days": 13, "remaining_days": 7}

  Assistant: You have 7 vacation days remaining this year. To request time
  off, submit your request at least two weeks in advance. Requests up to
  5 consecutive days are approved by your direct manager; longer requests
  require VP-level approval...

============================================================
Step 5: Cleanup
============================================================
  Deleted vector store 'company-policies'.

============================================================
Done!
============================================================

  You have successfully:
  1. Created a knowledge base with company policy documents
  2. Used file_search for automatic RAG retrieval
  3. Built a multi-turn conversation with continuous retrieval
  4. Combined RAG with a custom function tool in one agent

  Next: L1-M6.1 -- Content Moderation
  (safety shields, input/output filtering, and content classification)
```

Note: exact answer text will vary depending on model behavior and retrieval results.

## Key Takeaways

- **file_search automates the RAG pipeline**: one tool declaration replaces the manual embed-query-inject-generate loop from L1-M3.2.
- **previous_response_id enables multi-turn RAG**: the model maintains conversation context while retrieving fresh content for each turn.
- **Agents can combine multiple tool types**: file_search for retrieval and function tools for computation, all in a single request.
- **Server-side vs local execution**: file_search runs on the OGX server, while function tools are executed locally by your code -- the same pattern from L1-M4.1.
- **store=True is required for chaining**: responses must be stored server-side before they can be referenced by `previous_response_id`.

## Next Steps

Continue to **L1-M6.1 -- Content Moderation**, where you will learn how to use OGX's Safety API to add input shields, output shields, and content classification to your agents. In Level 2, we will explore advanced agent patterns including multi-provider routing and production deployment.
