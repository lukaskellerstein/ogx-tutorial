"""L1-M5.2 — Agents with RAG.

Combines OGX agents with RAG for knowledge-grounded conversations:
  1. Populate a vector store with company policy documents
  2. Use the Responses API with file_search for automatic retrieval
  3. Multi-turn RAG conversations with previous_response_id
  4. Combine RAG (file_search) with a custom function tool
"""

import json
import sys

import httpx
from ogx_client import OgxClient


OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"
EMBEDDING_MODEL = "ollama/all-minilm"
VECTOR_STORE_NAME = "company-policies"

HR_INSTRUCTIONS = (
    "You are an HR assistant. Answer questions based on company policies. "
    "Be specific and cite the relevant policy when possible."
)

POLICY_DOCUMENTS: list[dict[str, str]] = [
    {"id": "vacation-basic",
     "text": "Employees receive 20 vacation days per year. Days reset on "
             "January 1st and do not carry over. Requests must be submitted "
             "at least two weeks in advance."},
    {"id": "vacation-approval",
     "text": "Vacation requests are approved by the direct manager. Requests "
             "longer than 5 consecutive days require VP-level approval."},
    {"id": "remote-work",
     "text": "Employees may work remotely up to 3 days per week. Fully remote "
             "positions require HR approval. Remote employees must be available "
             "during core hours (10 AM - 3 PM local time)."},
    {"id": "remote-equipment",
     "text": "The company provides a laptop and monitor for remote work. "
             "Standing desk reimbursement up to $500 and ergonomic chair up to "
             "$400 are available for home offices."},
    {"id": "expense-travel",
     "text": "Business travel expenses are reimbursed within 30 days. Economy "
             "class for domestic flights. Hotels up to $200/night. Meals capped "
             "at $75/day."},
    {"id": "expense-general",
     "text": "General expenses over $100 must be pre-approved. Receipts required "
             "for all expenses over $25. Reports due within 60 days of purchase."},
    {"id": "sick-leave",
     "text": "Employees receive 10 paid sick days per year. A doctor's note is "
             "required for absences longer than 3 consecutive days."},
    {"id": "parental-leave",
     "text": "New parents receive 16 weeks of paid parental leave for both birth "
             "and adoption. Leave can be split into two blocks with manager "
             "approval."},
]


DAYS_REMAINING_TOOL = {
    "type": "function",
    "name": "calculate_days_remaining",
    "description": "Calculate remaining vacation days given total and used days.",
    "parameters": {
        "type": "object",
        "properties": {
            "total_days": {"type": "integer", "description": "Total vacation days per year"},
            "used_days": {"type": "integer", "description": "Days already used this year"},
        },
        "required": ["total_days", "used_days"],
        "additionalProperties": False,
    },
}


def calculate_days_remaining(total_days: int, used_days: int) -> str:
    """Return remaining vacation days as a JSON string."""
    remaining = max(0, total_days - used_days)
    return json.dumps({
        "total_days": total_days,
        "used_days": used_days,
        "remaining_days": remaining,
    })


TOOL_DISPATCH: dict[str, callable] = {
    "calculate_days_remaining": lambda args: calculate_days_remaining(
        args["total_days"], args["used_days"],
    ),
}


def check_server(url: str) -> bool:
    """Return True if the OGX server is reachable."""
    for path in ("/v1/health", "/v1/models"):
        try:
            httpx.get(f"{url}{path}", timeout=5).raise_for_status()
            return True
        except Exception:
            continue
    return False


def create_and_populate_store(client: OgxClient) -> None:
    """Create the vector store and ingest policy documents."""
    # Check if the store already exists
    for store in client.vector_stores.list().data:
        if store.name == VECTOR_STORE_NAME:
            print(f"  Vector store '{VECTOR_STORE_NAME}' already exists")
            return
    client.vector_stores.create(name=VECTOR_STORE_NAME)
    print(f"  Created vector store '{VECTOR_STORE_NAME}'")

    # Generate embeddings for all documents
    texts = [doc["text"] for doc in POLICY_DOCUMENTS]
    print(f"  Generating embeddings for {len(texts)} policy chunks...")
    resp = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    embeddings = [item.embedding for item in resp.data]
    dim = len(embeddings[0])
    print(f"  Embedding dimension: {dim}")

    # Insert into vector store
    chunks = [
        {
            "chunk_id": doc["id"],
            "content": doc["text"],
            "embedding": emb,
            "embedding_model": EMBEDDING_MODEL,
            "embedding_dimension": dim,
            "chunk_metadata": {"document_id": doc["id"]},
        }
        for doc, emb in zip(POLICY_DOCUMENTS, embeddings)
    ]
    client.vector_io.insert(vector_store_id=VECTOR_STORE_NAME, chunks=chunks)
    print(f"  Inserted {len(chunks)} chunks into vector store.\n")


def execute_tool_calls(client: OgxClient, response: object, tools: list) -> object:
    """Process function_call items, run tools, return follow-up response."""
    tool_calls = [item for item in response.output if item.type == "function_call"]
    if not tool_calls:
        return response

    input_items: list = list(response.output)

    for call in tool_calls:
        args = json.loads(call.arguments)
        func = TOOL_DISPATCH.get(call.name)
        if func is None:
            result = json.dumps({"error": f"Unknown tool: {call.name}"})
        else:
            result = func(args)

        print(f"  -> Tool call: {call.name}({args})")
        print(f"     Result: {result}")

        input_items.append({
            "type": "function_call_output",
            "call_id": call.call_id,
            "output": result,
        })

    follow_up = client.responses.create(
        model=MODEL,
        input=input_items,
        tools=tools,
        instructions=HR_INSTRUCTIONS,
        stream=False,
    )
    return follow_up


def step1_prepare_knowledge_base(client: OgxClient) -> None:
    """Step 1: Create and populate the vector store."""
    print("=" * 60)
    print("Step 1: Prepare the Knowledge Base")
    print("=" * 60)
    create_and_populate_store(client)


def step2_rag_agent(client: OgxClient) -> str:
    """Step 2: RAG-powered agent using file_search."""
    print("=" * 60)
    print("Step 2: RAG-Powered Agent (file_search)")
    print("=" * 60)

    question = "What is the vacation policy?"
    print(f"  User: {question}\n")

    response = client.responses.create(
        model=MODEL,
        input=question,
        tools=[{
            "type": "file_search",
            "vector_store_ids": [VECTOR_STORE_NAME],
        }],
        instructions=HR_INSTRUCTIONS,
        store=True,  # Required for previous_response_id chaining
        stream=False,
    )

    print(f"  Assistant: {response.output_text}\n")
    return response.id


def step3_multi_turn_rag(client: OgxClient, previous_id: str) -> None:
    """Step 3: Multi-turn RAG with previous_response_id."""
    print("=" * 60)
    print("Step 3: Multi-Turn RAG Agent")
    print("=" * 60)

    file_search_tool = {
        "type": "file_search",
        "vector_store_ids": [VECTOR_STORE_NAME],
    }

    questions = [
        "How does remote work differ from that?",
        "What about expense reimbursement?",
    ]

    current_id = previous_id
    for i, question in enumerate(questions, start=1):
        print(f"\n  Turn {i}:")
        print(f"  User: {question}")

        response = client.responses.create(
            model=MODEL,
            input=question,
            tools=[file_search_tool],
            instructions=HR_INSTRUCTIONS,
            previous_response_id=current_id,
            stream=False,
        )

        print(f"  Assistant: {response.output_text}")
        current_id = response.id

    print()


def step4_rag_plus_tools(client: OgxClient) -> None:
    """Step 4: Combine file_search with a custom function tool."""
    print("=" * 60)
    print("Step 4: RAG + Custom Tools Together")
    print("=" * 60)

    combined_tools = [
        {
            "type": "file_search",
            "vector_store_ids": [VECTOR_STORE_NAME],
        },
        DAYS_REMAINING_TOOL,
    ]

    question = (
        "I get 20 vacation days per year and I have used 13 so far. "
        "How many days do I have left, and what is the policy for "
        "requesting time off?"
    )
    print(f"  User: {question}\n")

    response = client.responses.create(
        model=MODEL,
        input=question,
        tools=combined_tools,
        instructions=HR_INSTRUCTIONS,
        stream=False,
    )

    # Handle any function tool calls (file_search is handled server-side)
    has_function_calls = any(
        item.type == "function_call" for item in response.output
    )
    if has_function_calls:
        response = execute_tool_calls(client, response, combined_tools)

    print(f"\n  Assistant: {response.output_text}\n")


def main() -> None:
    """Run the Agents with RAG demonstration."""
    print()
    print("L1-M5.2 — Agents with RAG")
    print("=" * 60)
    print()

    if not check_server(OGX_URL):
        print(f"  ERROR: OGX server not reachable at {OGX_URL}")
        print("  Start infrastructure:  cd ogx-local && podman compose up -d")
        sys.exit(1)
    print(f"  OGX server is reachable at {OGX_URL}\n")

    client = OgxClient(base_url=OGX_URL)

    step1_prepare_knowledge_base(client)
    response_id = step2_rag_agent(client)
    step3_multi_turn_rag(client, response_id)
    step4_rag_plus_tools(client)

    # Step 5: Cleanup
    print("=" * 60)
    print("Step 5: Cleanup")
    print("=" * 60)
    try:
        client.vector_stores.delete(VECTOR_STORE_NAME)
        print(f"  Deleted vector store '{VECTOR_STORE_NAME}'.\n")
    except Exception:
        print(f"  Vector store '{VECTOR_STORE_NAME}' already removed.\n")

    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print()
    print("  You have successfully:")
    print("  1. Created a knowledge base with company policy documents")
    print("  2. Used file_search for automatic RAG retrieval")
    print("  3. Built a multi-turn conversation with continuous retrieval")
    print("  4. Combined RAG with a custom function tool in one agent")
    print()
    print("  Next: L1-M6.1 — Content Moderation")
    print("  (safety shields, input/output filtering, and content classification)")
    print()


if __name__ == "__main__":
    main()
