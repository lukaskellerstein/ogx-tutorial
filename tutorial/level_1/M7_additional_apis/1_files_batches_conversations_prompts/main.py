"""
L1-M7.1 — Files, Batches, Conversations, and Prompts

Demonstrates four additional OGX APIs beyond inference and RAG:
  1. Files API        — upload and manage files
  2. Batches API      — offline batch processing
  3. Conversations API — persistent conversation state
  4. Prompts API      — reusable prompt templates
"""

import json
import tempfile
from pathlib import Path

import httpx
from ogx_client import OGXClient

BASE_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"


def check_server(base_url: str) -> bool:
    """Return True if the OGX server is reachable."""
    try:
        resp = httpx.get(f"{base_url}/v1/health", timeout=5)
        return resp.status_code == 200
    except httpx.ConnectError:
        return False


# ── 1. Files API ─────────────────────────────────────────────

def demo_files_api(client: OGXClient) -> None:
    print("=" * 60)
    print("1. Files API  (/v1/files)")
    print("=" * 60)

    # Create a temporary file with sample content
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="ogx_demo_"
    )
    tmp.write("OGX tutorial sample file.\nThis text is used to test the Files API.\n")
    tmp.close()
    tmp_path = Path(tmp.name)
    print(f"\nCreated temp file: {tmp_path.name}")

    try:
        # Upload
        with open(tmp_path, "rb") as f:
            uploaded = client.files.create(file=f, purpose="assistants")
        file_id = uploaded.id
        print(f"Uploaded  -> id={file_id}, purpose={uploaded.purpose}")

        # List
        file_list = client.files.list()
        print(f"Listed    -> {len(file_list.data)} file(s) on server")

        # Retrieve metadata
        info = client.files.retrieve(file_id)
        print(f"Retrieved -> filename={info.filename}, bytes={info.bytes}")

        # Delete
        delete_result = client.files.delete(file_id)
        print(f"Deleted   -> id={file_id}, deleted={delete_result.deleted}")

    except Exception as exc:
        print(f"Files API not fully available: {exc}")
        print("(Some distributions may not implement /v1/files)")
    finally:
        tmp_path.unlink(missing_ok=True)

    print()


# ── 2. Batches API ───────────────────────────────────────────

def demo_batches_api() -> None:
    print("=" * 60)
    print("2. Batches API  (/v1/batches)")
    print("=" * 60)

    print("""
The Batches API lets you submit many inference requests at once
for offline processing. Requests are packaged as a JSONL file
where each line is a JSON object with a custom_id and a request body.

Example JSONL line:
""")

    example_line = {
        "custom_id": "req-1",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": {
            "model": MODEL,
            "messages": [
                {"role": "user", "content": "Summarize quantum computing in one sentence."}
            ],
        },
    }
    print(json.dumps(example_line, indent=2))

    print("\nAttempting to list existing batches...")
    try:
        resp = httpx.get(f"{BASE_URL}/v1/batches", timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            print(f"Batches on server: {len(data.get('data', []))}")
        else:
            print(f"Server returned {resp.status_code} — batches may not be supported in this distribution.")
    except Exception as exc:
        print(f"Batches API not available: {exc}")

    print()


# ── 3. Conversations API ─────────────────────────────────────

def demo_conversations_api(client: OGXClient) -> None:
    print("=" * 60)
    print("3. Conversations API  (/v1/conversations)")
    print("=" * 60)

    print("\nCreating a stored response to seed a conversation...")

    try:
        # Use the Responses API with store=True to create a conversation
        response = client.responses.create(
            model=MODEL,
            input="What is OGX in one sentence?",
            store=True,
        )
        response_id = response.id
        print(f"Response created -> id={response_id}")
        print(f"Output: {response.output_text[:120]}...")

        # List conversations via httpx (convenience endpoint)
        resp = httpx.get(f"{BASE_URL}/v1/conversations", timeout=10)
        if resp.status_code == 200:
            convos = resp.json()
            print(f"\nConversations on server: {len(convos.get('data', []))}")
            if convos.get("data"):
                convo_id = convos["data"][0].get("id")
                print(f"First conversation id: {convo_id}")

                # Retrieve that conversation
                detail = httpx.get(f"{BASE_URL}/v1/conversations/{convo_id}", timeout=10)
                if detail.status_code == 200:
                    print(f"Conversation detail keys: {list(detail.json().keys())}")
        else:
            print(f"Conversations endpoint returned {resp.status_code}")

    except Exception as exc:
        print(f"Conversations API not fully available: {exc}")
        print("(Requires a distribution that supports the Responses API with store=True)")

    print()


# ── 4. Prompts API ────────────────────────────────────────────

def demo_prompts_api() -> None:
    print("=" * 60)
    print("4. Prompts API  (/v1/prompts)")
    print("=" * 60)

    print("""
The Prompts API lets you store reusable prompt templates on the
server.  Templates can include {{parameters}} that are filled in
at call time — useful for standardising prompts across an org.
""")

    # Try to create a prompt template
    template_payload = {
        "name": "summarizer",
        "description": "Summarises text to a target length",
        "prompt_template": (
            "Summarise the following text in {{num_sentences}} sentences:\n\n{{text}}"
        ),
    }

    try:
        resp = httpx.post(
            f"{BASE_URL}/v1/prompts",
            json=template_payload,
            timeout=10,
        )
        if resp.status_code in (200, 201):
            prompt = resp.json()
            print(f"Created prompt template: {prompt.get('name', prompt.get('id'))}")
        else:
            print(f"Create returned {resp.status_code}: {resp.text[:200]}")

        # List prompts
        resp = httpx.get(f"{BASE_URL}/v1/prompts", timeout=10)
        if resp.status_code == 200:
            prompts = resp.json()
            print(f"Prompts on server: {len(prompts.get('data', prompts) if isinstance(prompts, dict) else prompts)}")
        else:
            print(f"List prompts returned {resp.status_code}")

    except Exception as exc:
        print(f"Prompts API not available: {exc}")
        print("(Not all distributions expose /v1/prompts)")

    print()


# ── Main ──────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("L1-M7.1 — Files, Batches, Conversations, and Prompts")
    print("=" * 60)
    print()

    if not check_server(BASE_URL):
        print(f"ERROR: OGX server not reachable at {BASE_URL}")
        print("Start infrastructure with:  cd ogx-local && podman compose up -d")
        return

    print(f"OGX server is running at {BASE_URL}\n")

    client = OGXClient(base_url=BASE_URL)

    demo_files_api(client)
    demo_batches_api()
    demo_conversations_api(client)
    demo_prompts_api()

    print("=" * 60)
    print("Done! Next: L2-M1.1 — Multi-Provider Configuration")
    print("=" * 60)


if __name__ == "__main__":
    main()
