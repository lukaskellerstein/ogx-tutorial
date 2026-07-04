"""L1-M1.2 — Installing and Running OGX.

Connects to a running OGX server, lists available models,
and makes the first chat completion call using the ogx-client SDK.
"""

import sys

import httpx
from ogx_client import OgxClient

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"


def check_server_reachable(url: str) -> bool:
    """Check that the OGX server is reachable before making API calls."""
    try:
        resp = httpx.get(f"{url}/v1/health", timeout=5)
        resp.raise_for_status()
        return True
    except Exception:
        try:
            resp = httpx.get(f"{url}/v1/models", timeout=5)
            resp.raise_for_status()
            return True
        except Exception:
            return False


def list_models(client: OgxClient) -> bool:
    """List all models registered in the OGX server."""
    print("=" * 60)
    print("Step 1: Listing available models")
    print("=" * 60)
    try:
        models = client.models.list()
        print(f"  Models registered in OGX: {len(models.data)}")
        for model in models.data:
            print(f"    - {model.id}")
        print()
        return True
    except Exception as e:
        print(f"  FAILED: Could not list models — {e}")
        return False


def first_chat_completion(client: OgxClient) -> bool:
    """Make the first chat completion call through OGX."""
    print("=" * 60)
    print("Step 2: First chat completion via OGX")
    print("=" * 60)
    try:
        print(f"  Sending request to model: {MODEL}")
        print("  Prompt: 'What is OGX (Open GenAI Stack) in one sentence?'\n")

        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Answer concisely."},
                {"role": "user", "content": "What is OGX (Open GenAI Stack) in one sentence?"},
            ],
            max_tokens=100,
        )

        text = response.choices[0].message.content
        print(f"  Response: {text}\n")
        print(f"  Model used: {response.model}")
        print(f"  Tokens — prompt: {response.usage.prompt_tokens}, "
              f"completion: {response.usage.completion_tokens}\n")
        return True
    except Exception as e:
        print(f"  FAILED: Chat completion failed — {e}")
        return False


def second_chat_completion(client: OgxClient) -> bool:
    """Make a second call to show conversation-style usage."""
    print("=" * 60)
    print("Step 3: Multi-message conversation")
    print("=" * 60)
    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Name three key APIs that OGX provides."},
            ],
            max_tokens=150,
        )
        print(f"  Response: {response.choices[0].message.content}\n")
        return True
    except Exception as e:
        print(f"  FAILED: Second chat completion failed — {e}")
        return False


def show_openai_compatibility() -> None:
    """Show that OGX is OpenAI-compatible (informational only)."""
    print("=" * 60)
    print("Step 4: OpenAI compatibility (informational)")
    print("=" * 60)
    print(f"""
  OGX exposes an OpenAI-compatible API at /v1.
  This means you can also use the standard openai SDK:

    from openai import OpenAI

    client = OpenAI(base_url="{OGX_URL}/v1", api_key="not-needed")

    response = client.chat.completions.create(
        model="{MODEL}",
        messages=[{{"role": "user", "content": "Hello!"}}],
    )
    print(response.choices[0].message.content)

  Any library that works with the OpenAI API (LangChain,
  LlamaIndex, etc.) can connect to OGX by pointing its
  base_url to {OGX_URL}/v1.
""")


def main() -> None:
    print()
    print("L1-M1.2 — Installing and Running OGX")
    print("=" * 60)
    print()

    # Check server is reachable
    print("Checking OGX server connectivity...")
    if not check_server_reachable(OGX_URL):
        print(f"  ERROR: OGX server is not reachable at {OGX_URL}\n")
        print("  Make sure the infrastructure is running:")
        print("    cd ogx-local && podman compose up -d\n")
        print("  Then wait ~30-60 seconds for OGX to start and retry.")
        sys.exit(1)
    print(f"  OGX is reachable at {OGX_URL}\n")

    # Create the OGX client and run lesson steps
    client = OgxClient(base_url=OGX_URL)

    list_models(client)
    first_chat_completion(client)
    second_chat_completion(client)
    show_openai_compatibility()

    # Summary
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print("""
  You have successfully:
  1. Connected to a running OGX server
  2. Listed the available models
  3. Made chat completion calls through OGX
  4. Learned about OpenAI SDK compatibility

  Next: L1-M2.1 — Chat and Completion (deep dive into
  inference parameters, streaming, and system prompts)
""")


if __name__ == "__main__":
    main()
