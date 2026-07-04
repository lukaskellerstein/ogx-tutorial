# L1-M7.1 — Files, Batches, Conversations, and Prompts

**Level:** Essentials
**Duration:** 30 min

## Overview

OGX exposes more than just inference and RAG. This lesson explores four additional APIs that round out the platform: uploading and managing files, submitting batch inference jobs, tracking persistent conversations, and storing reusable prompt templates. Together they give you the building blocks for production workflows where you need file handling, bulk processing, conversation history, and standardised prompts.

## Prerequisites

- Completed: L1-M6.1 Content Moderation
- Infrastructure running: OGX (port 8321), Ollama

## Concepts

### Files API (`/v1/files`)

The Files API lets you upload documents to the OGX server so they can be referenced by other APIs (for example, as input to a batch job or as context for an agent). You can upload, list, retrieve metadata, and delete files.

### Batches API (`/v1/batches`)

The Batches API is designed for offline bulk inference. Instead of sending requests one by one, you package many requests into a JSONL file and submit them as a single batch. The server processes them asynchronously and you poll for results. This is useful for workloads like scoring a dataset or generating embeddings for a large corpus.

### Conversations API (`/v1/conversations`)

When you use the Responses API with `store=True`, OGX persists the exchange as a conversation. The Conversations API lets you list and retrieve these stored conversations, providing a server-side record of multi-turn interactions. This is the foundation for persistent agent state.

### Prompts API (`/v1/prompts`)

The Prompts API lets you store parameterised prompt templates on the server. A template can include `{{placeholders}}` that are filled in at call time. This helps standardise prompts across an organisation and keeps prompt engineering separate from application code.

## Step-by-Step

### Step 1: Check server connectivity

Before calling any API, the script verifies the OGX server is reachable at `http://localhost:8321`.

```python
resp = httpx.get(f"{BASE_URL}/v1/health", timeout=5)
```

### Step 2: Files API — upload, list, retrieve, delete

We create a temporary text file, upload it via the OGX client, inspect the server's file list, retrieve the file's metadata, and then clean up by deleting it.

```python
with open(tmp_path, "rb") as f:
    uploaded = client.files.create(file=f, purpose="assistants")

file_list = client.files.list()
info = client.files.retrieve(file_id)
client.files.delete(file_id)
```

### Step 3: Batches API — understand the request format

We show the JSONL format expected by the Batches API and attempt to list existing batches on the server. Not every OGX distribution supports batches, so the code handles errors gracefully.

### Step 4: Conversations API — create and inspect a conversation

We call the Responses API with `store=True` to seed a conversation, then use `httpx` to list and retrieve conversations from the `/v1/conversations` endpoint.

```python
response = client.responses.create(
    model=MODEL,
    input="What is OGX in one sentence?",
    store=True,
)
```

### Step 5: Prompts API — create a prompt template

We POST a parameterised prompt template to `/v1/prompts` and list all templates on the server.

```python
template_payload = {
    "name": "summarizer",
    "description": "Summarises text to a target length",
    "prompt_template": "Summarise the following text in {{num_sentences}} sentences:\n\n{{text}}",
}
```

## Running the Lesson

```bash
cd tutorial/level_1/M7_additional_apis/1_files_batches_conversations_prompts
uv sync
uv run python main.py
```

## Expected Output

```
============================================================
L1-M7.1 — Files, Batches, Conversations, and Prompts
============================================================

OGX server is running at http://localhost:8321

============================================================
1. Files API  (/v1/files)
============================================================

Created temp file: ogx_demo_XXXXXX.txt
Uploaded  -> id=file-abc123, purpose=assistants
Listed    -> 1 file(s) on server
Retrieved -> filename=ogx_demo_XXXXXX.txt, bytes=72
Deleted   -> id=file-abc123, deleted=True

============================================================
2. Batches API  (/v1/batches)
============================================================

The Batches API lets you submit many inference requests at once ...
Batches on server: 0

============================================================
3. Conversations API  (/v1/conversations)
============================================================

Creating a stored response to seed a conversation...
Response created -> id=resp-xyz789
Output: OGX is an open-source unified AI runtime that provides ...
Conversations on server: 1

============================================================
4. Prompts API  (/v1/prompts)
============================================================

The Prompts API lets you store reusable prompt templates ...
Created prompt template: summarizer

============================================================
Done!  You explored four additional OGX APIs.
============================================================
```

Note: Some APIs may return 404 or error responses depending on your OGX distribution. The script handles these gracefully and prints explanatory messages.

## Key Takeaways

- The **Files API** provides server-side file management for documents used by other OGX APIs.
- The **Batches API** enables offline bulk inference using JSONL input files.
- The **Conversations API** gives you persistent, server-side conversation history when using `store=True` with the Responses API.
- The **Prompts API** lets you centrally manage parameterised prompt templates.
- Not every API is available in every OGX distribution — always handle missing endpoints gracefully.

## Next Steps

This concludes Level 1 of the OGX tutorial. You now have hands-on experience with every major OGX API: inference, embeddings, RAG, tool calling, agents, safety, files, batches, conversations, and prompts.

Continue to **Level 2 (L2-M1.1 Multi-Provider Configuration)** to learn how to configure multiple inference providers in a single OGX instance and route requests across them.
