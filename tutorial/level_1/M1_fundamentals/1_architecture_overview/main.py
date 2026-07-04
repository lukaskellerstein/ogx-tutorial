"""
L1-M1.1 — What is OGX? Architecture Overview

Explores the OGX API surface using raw HTTP calls.
No inference is performed — this lesson is about understanding
the architecture, available endpoints, and configured providers.
"""

import json
import sys

import httpx

OGX_URL = "http://localhost:8321"


def check_health(client: httpx.Client) -> bool:
    """Check if the OGX server is reachable."""
    print("=" * 60)
    print("Step 1: Checking OGX Server Health")
    print("=" * 60)
    try:
        response = client.get(f"{OGX_URL}/v1/health")
        print(f"  Status code : {response.status_code}")
        print(f"  Response    : {response.json()}")
        print("  OGX server is healthy!\n")
        return True
    except httpx.ConnectError:
        print(f"  ERROR: Cannot connect to OGX server at {OGX_URL}")
        print("  Make sure the infrastructure is running:")
        print("    cd ogx-local && podman compose up -d")
        return False


def list_models(client: httpx.Client) -> None:
    """List all models registered with the OGX server."""
    print("=" * 60)
    print("Step 2: Listing Registered Models (GET /v1/models)")
    print("=" * 60)
    data = client.get(f"{OGX_URL}/v1/models").json()
    models = data.get("data", []) if isinstance(data, dict) else data
    print(f"  Found {len(models)} registered model(s):\n")
    for m in models:
        mid = m.get("id", "unknown") if isinstance(m, dict) else m
        owner = m.get("owned_by", "") if isinstance(m, dict) else ""
        print(f"    - {mid}" + (f"  (owned_by: {owner})" if owner else ""))
    print()


def list_routes(client: httpx.Client) -> None:
    """List all available API routes on the OGX server."""
    print("=" * 60)
    print("Step 3: Listing Available API Routes (GET /v1/routes)")
    print("=" * 60)
    response = client.get(f"{OGX_URL}/v1/routes")
    if response.status_code == 404:
        print("  /v1/routes not available — printing known routes:\n")
        for cat, path, desc in [
            ("Inference", "/v1/chat/completions", "Chat (OpenAI-compatible)"),
            ("Inference", "/v1/embeddings", "Text embeddings"),
            ("Models", "/v1/models", "List registered models"),
            ("Vectors", "/v1/vector_stores", "Vector store operations"),
            ("Agents", "/v1/responses", "Agentic orchestration"),
            ("Safety", "/v1/safety", "Content moderation"),
            ("Health", "/v1/health", "Server health check"),
        ]:
            print(f"    {cat:10s}  {path:28s}  {desc}")
    else:
        print(f"  {json.dumps(response.json(), indent=2)}")
    print()


def list_providers(client: httpx.Client) -> None:
    """List all configured providers on the OGX server."""
    print("=" * 60)
    print("Step 4: Listing Configured Providers (GET /v1/providers)")
    print("=" * 60)
    response = client.get(f"{OGX_URL}/v1/providers")
    if response.status_code == 404:
        print("  /v1/providers not available on this OGX version.")
        print("  Providers are configured in the distribution's run.yaml.\n")
        return
    data = response.json()
    if isinstance(data, dict):
        for api_name, providers in data.items():
            print(f"\n  [{api_name}]")
            for p in (providers if isinstance(providers, list) else [providers]):
                pid = p.get("provider_id", "?") if isinstance(p, dict) else p
                ptype = p.get("provider_type", "") if isinstance(p, dict) else ""
                print(f"    - {pid}" + (f" ({ptype})" if ptype else ""))
    else:
        print(f"  {json.dumps(data, indent=2)}")
    print()


def print_api_overview() -> None:
    """Print a summary table of the OGX API surface."""
    print("=" * 60)
    print("Step 5: OGX API Surface Overview")
    print("=" * 60)
    print("""
  OGX is a unified AI runtime that sits between your application
  and one or more inference backends (vLLM, Ollama, OpenAI, etc.).

  +-------------------------------------------+
  |            Your Application               |
  +-------------------------------------------+
                      |
                 OGX Server (:8321)
                      |
       +--------------+--------------+
       |              |              |
     vLLM          Ollama        OpenAI
  (local GPU)    (Apple Si.)    (cloud)

  Core API Surface:
  +--------------------+--------------------------------------+
  | Endpoint           | Purpose                              |
  +--------------------+--------------------------------------+
  | /v1/chat/          | Chat completions, streaming,         |
  |   completions      | tool calling (OpenAI-compatible)     |
  | /v1/embeddings     | Text embeddings for search & RAG     |
  | /v1/models         | List and manage registered models    |
  | /v1/vector_stores  | Vector DB operations for RAG         |
  | /v1/responses      | Server-side agentic orchestration    |
  | /v1/safety         | Content moderation & guardrails      |
  | /v1/health         | Server health check                  |
  +--------------------+--------------------------------------+

  Key Characteristics:
  - Provider-agnostic: 23+ inference providers supported
  - OpenAI-compatible: use any OpenAI SDK or client
  - Multi-SDK: also supports Anthropic and Google SDKs
  - Distributions: pre-packaged provider configurations
  - Server-based: HTTP API, works from any language
""")


def main() -> None:
    """Explore the OGX API surface using raw HTTP calls."""
    print("\n" + "#" * 60)
    print("#  L1-M1.1 — OGX Architecture Overview")
    print("#  Exploring the OGX API surface")
    print("#" * 60 + "\n")

    with httpx.Client(timeout=10.0) as client:
        if not check_health(client):
            sys.exit(1)
        list_models(client)
        list_routes(client)
        list_providers(client)

    print_api_overview()

    print("=" * 60)
    print("Lesson complete! Next: L1-M1.2 — Installing and Running OGX")
    print("=" * 60)


if __name__ == "__main__":
    main()
