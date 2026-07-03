"""L2-M1.2 — Custom Providers and Extensions.

Explores the OGX provider architecture: inspects existing providers,
explains the provider interface, shows skeleton code for custom
inference and safety providers, and demonstrates provider registration.
"""

import sys

import httpx
from ogx_client import OgxClient

from skeletons import (
    CUSTOM_PROVIDER,
    INTERFACE_OVERVIEW,
    PLUGIN_ARCHITECTURE,
    REGISTRATION,
    SAFETY_DETECTOR,
)

OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"


def check_server() -> bool:
    """Verify that the OGX server is reachable."""
    try:
        resp = httpx.get(f"{OGX_URL}/v1/health", timeout=5)
        resp.raise_for_status()
        return True
    except Exception as exc:
        print(f"ERROR: OGX server is not reachable at {OGX_URL}")
        print(f"  {exc}")
        print("Start the infrastructure first:")
        print("  cd ogx-local && podman compose up -d")
        return False


def inspect_providers() -> None:
    """Step 1: Query the OGX server for its configured providers."""
    print("=" * 60)
    print("Step 1: Inspect Existing Providers")
    print("=" * 60)

    resp = httpx.get(f"{OGX_URL}/v1/providers", timeout=10)

    if resp.status_code == 404:
        print("  /v1/providers not available on this OGX version.\n")
        return

    data = resp.json()

    if isinstance(data, dict):
        for api_name, providers in data.items():
            print(f"\n  [{api_name}]")
            if isinstance(providers, list):
                for p in providers:
                    if isinstance(p, dict):
                        pid = p.get("provider_id", "unknown")
                        ptype = p.get("provider_type", "unknown")
                        print(f"    - {pid} ({ptype})")
                    else:
                        print(f"    - {p}")
    elif isinstance(data, list):
        print(f"  Found {len(data)} provider(s):\n")
        for p in data:
            if isinstance(p, dict):
                pid = p.get("provider_id", "unknown")
                ptype = p.get("provider_type", "unknown")
                api = p.get("api", "unknown")
                print(f"    - {pid} ({ptype}) -> API: {api}")
            else:
                print(f"    - {p}")
    else:
        print(f"  Response: {data}")

    print()
    print("  Provider types in OGX:")
    print("    remote::  -- adapts an external service (vLLM, Ollama, OpenAI)")
    print("    inline::  -- runs processing within the OGX process itself")
    print()


def provider_interface_overview() -> None:
    """Step 2: Explain the provider interfaces."""
    print("=" * 60)
    print("Step 2: Provider Interface Overview")
    print("=" * 60)
    print(INTERFACE_OVERVIEW)


def custom_provider_skeleton() -> None:
    """Step 3: Show a custom inference provider skeleton."""
    print("=" * 60)
    print("Step 3: Custom Inference Provider Skeleton")
    print("=" * 60)
    print(CUSTOM_PROVIDER)


def registration_pattern() -> None:
    """Step 4: Show how to register a custom provider in run.yaml."""
    print("=" * 60)
    print("Step 4: Registering a Custom Provider")
    print("=" * 60)
    print(REGISTRATION)


def custom_safety_detector() -> None:
    """Step 5: Show a skeleton for a custom safety detector."""
    print("=" * 60)
    print("Step 5: Custom Safety Detector Skeleton")
    print("=" * 60)
    print(SAFETY_DETECTOR)


def plugin_architecture() -> None:
    """Step 6: Explain OGX's plugin and extension system."""
    print("=" * 60)
    print("Step 6: Plugin Architecture")
    print("=" * 60)
    print(PLUGIN_ARCHITECTURE)


def test_existing_provider(client: OgxClient) -> None:
    """Step 7: Make a real call to show how the current provider works."""
    print("=" * 60)
    print("Step 7: Test the Existing Provider")
    print("=" * 60)

    print(f"  Making an inference call via the configured provider...")
    print(f"  Model: {MODEL}\n")

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "What is a provider in one sentence?"},
        ],
        max_tokens=100,
    )

    print(f"  Response: {response.choices[0].message.content}")
    print()
    print("  This call was routed through OGX to the configured inference")
    print("  provider. A custom provider would handle the same request by")
    print("  implementing the same chat_completion interface and forwarding")
    print("  the call to a different backend.")
    print()


def main() -> None:
    """Explore OGX custom provider architecture."""
    print()
    print("#" * 60)
    print("#  L2-M1.2 — Custom Providers and Extensions")
    print("#  Understanding the OGX provider interface")
    print("#" * 60)
    print()

    if not check_server():
        sys.exit(1)

    client = OgxClient(base_url=OGX_URL)

    inspect_providers()
    provider_interface_overview()
    custom_provider_skeleton()
    registration_pattern()
    custom_safety_detector()
    plugin_architecture()
    test_existing_provider(client)

    print("=" * 60)
    print("Lesson complete! Next: L2-M1.3 — Production Deployment")
    print("=" * 60)


if __name__ == "__main__":
    main()
