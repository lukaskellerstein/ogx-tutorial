"""L1-M2.1 — Chat and Completion.

Demonstrates the OGX Inference API for chat completions:
basic calls, system prompts, conversation history, streaming,
and parameter tuning.
"""

import sys

import httpx
from ogx_client import OgxClient


OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"


def check_server() -> bool:
    """Verify that the OGX server is reachable."""
    try:
        resp = httpx.get(f"{OGX_URL}/v1/models", timeout=5)
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"ERROR: OGX server is not reachable at {OGX_URL}")
        print(f"  {exc}")
        print("Start the infrastructure first:")
        print("  Ollama:  ollama serve")
        print("  OGX:     podman compose up -d ogx")
        return False


def basic_chat_completion(client: OgxClient) -> None:
    """Step 1: Send a simple chat completion request."""
    print("=" * 60)
    print("Step 1: Basic Chat Completion")
    print("=" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "What is OGX (Open GenAI Stack) in one sentence?"},
        ],
    )

    print(f"Response: {response.choices[0].message.content}")
    print()


def system_prompt(client: OgxClient) -> None:
    """Step 2: Use a system message to control assistant behavior."""
    print("=" * 60)
    print("Step 2: System Prompts")
    print("=" * 60)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": "You are a pirate. Answer everything in pirate speak.",
            },
            {"role": "user", "content": "What is machine learning?"},
        ],
    )

    print(f"Response: {response.choices[0].message.content}")
    print()


def conversation_history(client: OgxClient) -> None:
    """Step 3: Multi-turn conversation with message history."""
    print("=" * 60)
    print("Step 3: Conversation History (Multi-Turn)")
    print("=" * 60)

    messages: list[dict[str, str]] = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "My name is Alice."},
    ]

    # First turn
    response = client.chat.completions.create(model=MODEL, messages=messages)
    assistant_reply = response.choices[0].message.content
    print(f"User:      My name is Alice.")
    print(f"Assistant: {assistant_reply}")

    # Add assistant reply and ask a follow-up that requires context
    messages.append({"role": "assistant", "content": assistant_reply})
    messages.append({"role": "user", "content": "What is my name?"})

    response = client.chat.completions.create(model=MODEL, messages=messages)
    print(f"User:      What is my name?")
    print(f"Assistant: {response.choices[0].message.content}")
    print()


def streaming_response(client: OgxClient) -> None:
    """Step 4: Stream tokens as they are generated."""
    print("=" * 60)
    print("Step 4: Streaming Response")
    print("=" * 60)
    print("Response: ", end="", flush=True)

    stream = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "Explain what an API is in 2-3 sentences."},
        ],
        stream=True,
    )

    for chunk in stream:
        if chunk.choices and chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)

    print("\n")


def parameter_effects(client: OgxClient) -> None:
    """Step 5: Show how temperature, max_tokens, and top_p affect output."""
    print("=" * 60)
    print("Step 5: Parameters — Temperature, Max Tokens, Top-p")
    print("=" * 60)

    prompt = "Write a one-sentence story about a cat."

    # Low temperature — deterministic, consistent output
    print("Temperature 0.0 (deterministic):")
    for i in range(2):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=60,
        )
        print(f"  Run {i + 1}: {response.choices[0].message.content}")

    # High temperature — creative, varied output
    print("\nTemperature 1.0 (creative):")
    for i in range(2):
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=1.0,
            max_tokens=60,
        )
        print(f"  Run {i + 1}: {response.choices[0].message.content}")

    # Max tokens — truncated output
    print("\nMax tokens = 10 (truncated):")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "Tell me a long story about a dragon."},
        ],
        max_tokens=10,
    )
    print(f"  Response: {response.choices[0].message.content}")

    # Top-p — narrow sampling nucleus
    print("\nTop-p = 0.1 (narrow sampling):")
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        top_p=0.1,
        max_tokens=60,
    )
    print(f"  Response: {response.choices[0].message.content}")
    print()


def vllm_comparison_note() -> None:
    """Step 6: Explain what OGX adds on top of raw inference."""
    print("=" * 60)
    print("Step 6: OGX vs Direct vLLM / Ollama")
    print("=" * 60)
    print(
        "In this lesson we called OGX's /v1/chat/completions endpoint.\n"
        "Under the hood, OGX forwards the request to the configured\n"
        "inference backend (vLLM or Ollama). You could call that backend\n"
        "directly, but OGX adds a unified layer on top:\n"
        "\n"
        "  - RAG:     Vector IO API for retrieval-augmented generation\n"
        "  - Agents:  Agent creation, sessions, and multi-turn execution\n"
        "  - Memory:  Conversation history across sessions\n"
        "  - Safety:  Input/output shields and content moderation\n"
        "  - Tools:   Tool runtime with MCP integration\n"
        "\n"
        "OGX is a unified API surface for the full AI application stack.\n"
        "The remaining lessons in this tutorial explore each of these."
    )
    print()


def main() -> None:
    """Run all chat completion demonstrations."""
    print()
    print("L1-M2.1 — Chat and Completion")
    print("=" * 60)
    print()

    if not check_server():
        sys.exit(1)

    client = OgxClient(base_url=OGX_URL)

    basic_chat_completion(client)
    system_prompt(client)
    conversation_history(client)
    streaming_response(client)
    parameter_effects(client)
    vllm_comparison_note()

    print("=" * 60)
    print("Lesson complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
