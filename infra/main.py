"""OGX local setup verification script.

Checks that Ollama, OGX, and Qdrant are running and working.
"""

import sys
import httpx
from openai import OpenAI


OGX_URL = "http://localhost:8321"
OLLAMA_URL = "http://localhost:11434"
QDRANT_URL = "http://localhost:6333"
MODEL = "ollama/gemma4:e4b"


def check_ollama() -> bool:
    print("=" * 60)
    print("Step 1: Checking Ollama")
    print("=" * 60)
    try:
        resp = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = resp.json().get("models", [])
        model_names = [m["name"] for m in models]
        print(f"  Ollama is running. Models available: {len(models)}")
        for name in model_names:
            print(f"    - {name}")

        has_gemma = any("gemma4" in n and "e4b" in n for n in model_names)
        if not has_gemma:
            print("\n  WARNING: gemma4:e4b not found!")
            print("  Run: ollama pull gemma4:e4b")
            return False

        print("  gemma4:e4b is available.")
        return True
    except Exception as e:
        print(f"  FAILED: Ollama is not running at {OLLAMA_URL}")
        print(f"  Error: {e}")
        print("  Start Ollama first: ollama serve")
        return False


def check_qdrant() -> bool:
    print()
    print("=" * 60)
    print("Step 2: Checking Qdrant")
    print("=" * 60)
    try:
        resp = httpx.get(f"{QDRANT_URL}/healthz", timeout=5)
        resp.raise_for_status()
        print(f"  Qdrant is healthy at {QDRANT_URL}")
        print(f"  Dashboard: {QDRANT_URL}/dashboard")
        return True
    except Exception as e:
        print(f"  FAILED: Qdrant is not running at {QDRANT_URL}")
        print(f"  Error: {e}")
        print("  Start with: podman compose up -d qdrant")
        return False


def check_ogx() -> bool:
    print()
    print("=" * 60)
    print("Step 3: Checking OGX server")
    print("=" * 60)
    try:
        resp = httpx.get(f"{OGX_URL}/v1/models", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("data", [])
        print(f"  OGX is running at {OGX_URL}")
        print(f"  Models registered: {len(models)}")
        for m in models:
            print(f"    - {m.get('id', 'unknown')}")
        return True
    except Exception as e:
        print(f"  FAILED: OGX is not running at {OGX_URL}")
        print(f"  Error: {e}")
        print("  Start with: podman compose up -d ogx")
        print("  Note: OGX may take 30-60s to start. Check logs:")
        print("    podman compose logs -f ogx")
        return False


def test_inference() -> bool:
    print()
    print("=" * 60)
    print("Step 4: Testing inference via OGX")
    print("=" * 60)
    try:
        client = OpenAI(base_url=f"{OGX_URL}/v1", api_key="not-needed")
        print(f"  Sending chat completion request (model: {MODEL})...")
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "user", "content": "Say hello in one sentence."},
            ],
            max_tokens=50,
        )
        text = response.choices[0].message.content
        print(f"  Response: {text}")
        print("  Inference is working!")
        return True
    except Exception as e:
        print(f"  FAILED: Inference test failed")
        print(f"  Error: {e}")
        return False


def main() -> None:
    print()
    print("OGX Local Setup Verification")
    print("=" * 60)
    print()

    results = {}
    results["Ollama"] = check_ollama()
    results["Qdrant"] = check_qdrant()
    results["OGX"] = check_ogx()

    if results["OGX"] and results["Ollama"]:
        results["Inference"] = test_inference()
    else:
        results["Inference"] = False
        print()
        print("  Skipping inference test (OGX or Ollama not ready)")

    print()
    print("=" * 60)
    print("Summary")
    print("=" * 60)
    all_ok = True
    for name, ok in results.items():
        status = "OK" if ok else "FAILED"
        print(f"  {name:12s} : {status}")
        if not ok:
            all_ok = False

    print()
    if all_ok:
        print("All checks passed! OGX is ready for tutorial lessons.")
    else:
        print("Some checks failed. See above for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
