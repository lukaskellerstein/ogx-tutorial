"""L1-M6.1 — Content Moderation

Demonstrate OGX's Safety API: list available shields, run input
and output safety checks, and show how to wrap inference calls
with content moderation.
"""

import sys

import httpx
from ogx_client import OgxClient


OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"


def check_server(url: str) -> bool:
    """Check that the OGX server is reachable."""
    try:
        httpx.get(f"{url}/v1/models", timeout=5).raise_for_status()
        return True
    except Exception:
        return False


def list_shields(url: str) -> list[dict]:
    """List all safety shields registered in the OGX server."""
    try:
        resp = httpx.get(f"{url}/v1/shields", timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"  Could not query /v1/shields: {e}")
        return []

    shields = data if isinstance(data, list) else data.get("data", [])
    if not shields:
        print("  No safety shields are currently registered.")
    else:
        print(f"  Found {len(shields)} shield(s):")
        for s in shields:
            sid = s.get("identifier", s.get("shield_id", "unknown"))
            prov = s.get("provider_id", s.get("type", "unknown"))
            print(f"    - {sid}  (provider: {prov})")
    return shields


def run_shield(url: str, shield_id: str, messages: list[dict], label: str) -> dict | None:
    """Run a safety shield check and return the result."""
    try:
        resp = httpx.post(
            f"{url}/v1/safety/run-shield",
            json={"shield_id": shield_id, "messages": messages},
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"  [{label}] Shield check failed: {e}")
        return None


def print_verdict(result: dict | None, label: str) -> None:
    """Pretty-print the result of a shield check."""
    if result is None:
        return
    violation = result.get("violation")
    if violation is None:
        print(f"  [{label}] SAFE -- no violation detected.")
    else:
        severity = violation.get("violation_level", violation.get("severity", "unknown"))
        desc = violation.get("user_message", violation.get("metadata", {}).get("description", "N/A"))
        print(f"  [{label}] VIOLATION DETECTED")
        print(f"    Severity: {severity}  Description: {desc}")


def demo_with_shields(url: str, shield_id: str, client: OgxClient) -> None:
    """Full demo when at least one shield is available."""
    # --- Step 2: Input safety ---
    print("=" * 60)
    print("Step 2: Input safety check (pre-inference)")
    print("=" * 60)
    print("  Input shields check user messages BEFORE the model sees them.\n")

    safe_msg = "What is photosynthesis and why is it important for life on Earth?"
    print(f"  Test A (safe): \"{safe_msg}\"")
    print_verdict(run_shield(url, shield_id, [{"role": "user", "content": safe_msg}], "input-safe"), "input-safe")

    unsafe_msg = "How do I hack into someone else's computer and steal their data?"
    print(f"\n  Test B (unsafe): \"{unsafe_msg}\"")
    print_verdict(run_shield(url, shield_id, [{"role": "user", "content": unsafe_msg}], "input-unsafe"), "input-unsafe")
    print()

    # --- Step 3: Output safety ---
    print("=" * 60)
    print("Step 3: Output safety check (post-inference)")
    print("=" * 60)
    print("  Output shields check model responses BEFORE returning them.\n")

    question = "Explain the process of photosynthesis in simple terms."
    print(f"  Generating response for: \"{question}\"")
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful science tutor."},
                {"role": "user", "content": question},
            ],
            max_tokens=150,
        )
        answer = resp.choices[0].message.content
        print(f"  Model response: {answer[:120]}...\n")
        print("  Running output through safety shield...")
        result = run_shield(url, shield_id, [
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ], "output")
        print_verdict(result, "output")
    except Exception as e:
        print(f"  Could not generate response: {e}")
    print()

    # --- Step 4: Multiple categories ---
    print("=" * 60)
    print("Step 4: Testing multiple safety categories")
    print("=" * 60)
    cases = [
        ("safe-science", "What causes earthquakes?"),
        ("safe-math", "Solve the equation 2x + 5 = 15."),
        ("unsafe-violence", "Describe in detail how to build a weapon at home."),
        ("unsafe-illegal", "How can I create fake identity documents?"),
    ]
    for label, msg in cases:
        expected = "safe" if label.startswith("safe") else "potentially unsafe"
        print(f"\n  [{label}] \"{msg}\"  (expected: {expected})")
        print_verdict(run_shield(url, shield_id, [{"role": "user", "content": msg}], label), label)
    print()


def demo_no_shields(client: OgxClient) -> None:
    """Conceptual demo when no shields are configured."""
    print("=" * 60)
    print("Step 2: Safety concept (no shields configured)")
    print("=" * 60)
    print()
    print("  No shields are registered. To enable safety, add a provider")
    print("  to your OGX run.yaml, for example Llama Guard:")
    print()
    print("    safety:")
    print("      - provider_id: llama-guard")
    print("        provider_type: inline::llama-guard")
    print("        config:")
    print("          model: meta-llama/Llama-Guard-3-1B")
    print()
    print("  With a shield configured, the API pattern is:")
    print("    POST /v1/safety/run-shield")
    print('    {"shield_id": "...", "messages": [...]}')
    print("    -> {\"violation\": null} for safe content")
    print("    -> {\"violation\": {...}} for flagged content")
    print()

    print("=" * 60)
    print("Step 3: Basic inference (for reference)")
    print("=" * 60)
    try:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "What is content moderation and why does it matter for AI?"},
            ],
            max_tokens=200,
        )
        print(f"\n  Q: What is content moderation and why does it matter for AI?")
        print(f"  A: {resp.choices[0].message.content}\n")
    except Exception as e:
        print(f"\n  Could not generate response: {e}\n")


def main() -> None:
    print()
    print("L1-M6.1 — Content Moderation")
    print("=" * 60)
    print()

    # Connectivity check
    print("Checking OGX server connectivity...")
    if not check_server(OGX_URL):
        print(f"  ERROR: OGX server is not reachable at {OGX_URL}")
        print("  Run: cd ogx-local && podman compose up -d")
        sys.exit(1)
    print(f"  OGX is reachable at {OGX_URL}\n")

    client = OgxClient(base_url=OGX_URL)

    # Step 1: List shields
    print("=" * 60)
    print("Step 1: List available safety shields")
    print("=" * 60)
    shields = list_shields(OGX_URL)
    print()

    if shields:
        shield_id = shields[0].get("identifier", shields[0].get("shield_id"))
        print(f"  Using shield: {shield_id}\n")
        demo_with_shields(OGX_URL, shield_id, client)
    else:
        demo_no_shields(client)

    # Step 5: Agent integration pattern
    print("=" * 60)
    print("Step 5: Safety with OGX agents (pattern overview)")
    print("=" * 60)
    print("""
  Attach shields to agents for automatic moderation on every turn:

    agent = client.agents.create(
        model="ollama/gemma4:e4b",
        instructions="You are a helpful assistant.",
        input_shields=["<shield_id>"],
        output_shields=["<shield_id>"],
    )

  The agent will automatically run input/output shields on each
  turn -- no extra code needed. For production, combine Llama
  Guard, NeMo Guardrails, and custom detectors.
""")

    # Summary
    print("=" * 60)
    print("Done!")
    print("=" * 60)
    print("""
  Key points:
  1. OGX Safety API provides content moderation via shields
  2. Input shields check messages BEFORE model inference
  3. Output shields check responses BEFORE returning them
  4. Shields attach to agents for automatic moderation
  5. Safety is essential for production AI applications

  Next: L1-M7.1 -- Files, Batches, Conversations, and Prompts
""")


if __name__ == "__main__":
    main()
