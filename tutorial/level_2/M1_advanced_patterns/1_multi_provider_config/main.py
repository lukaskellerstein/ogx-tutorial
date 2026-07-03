"""L2-M1.1 — Multi-Provider Configuration

Demonstrates how OGX routes requests to different providers based on
model ID, and explains the configuration patterns for multi-provider
setups, fallback chains, and custom distributions.
"""

import httpx
from ogx_client import OgxClient


OGX_URL = "http://localhost:8321"
MODEL = "ollama/gemma4:e4b"


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 60)
    print(title)
    print("=" * 60)


def step1_list_providers() -> None:
    """List all providers currently configured in the OGX instance."""
    print_header("Step 1: List configured providers")

    print("  Querying OGX for all registered providers...")
    print()

    response = httpx.get(f"{OGX_URL}/v1/providers")
    response.raise_for_status()
    providers = response.json()

    if isinstance(providers, dict) and "data" in providers:
        provider_list = providers["data"]
    elif isinstance(providers, list):
        provider_list = providers
    else:
        provider_list = [providers]

    for p in provider_list:
        if isinstance(p, dict):
            pid = p.get("provider_id", "unknown")
            ptype = p.get("provider_type", "unknown")
            api = p.get("api", "unknown")
            print(f"  Provider: {pid}")
            print(f"    Type: {ptype}")
            print(f"    API:  {api}")
            print()
        else:
            print(f"  {p}")

    print(f"  Total providers: {len(provider_list)}")


def step2_list_models(client: OgxClient) -> None:
    """List all registered models and their provider assignments."""
    print_header("Step 2: List registered models")

    print("  Each model is served by a specific provider.")
    print("  OGX routes requests to the correct provider based on model ID.")
    print()

    models = client.models.list()

    if hasattr(models, "data"):
        model_list = models.data
    elif hasattr(models, "__iter__"):
        model_list = list(models)
    else:
        model_list = [models]

    for m in model_list:
        model_id = getattr(m, "identifier", None) or getattr(m, "model_id", str(m))
        provider = getattr(m, "provider_id", "unknown")
        mtype = getattr(m, "model_type", "unknown")
        print(f"  Model: {model_id}")
        print(f"    Provider: {provider}")
        print(f"    Type:     {mtype}")
        print()

    print(f"  Total models: {len(model_list)}")


def step3_provider_routing() -> None:
    """Explain provider routing with a sample multi-provider config."""
    print_header("Step 3: Provider routing — different models, different backends")

    print("""
  OGX routes each request to the correct provider based on the model ID.
  This means you can have multiple inference backends in a single instance:

    - Chat model  -->  vLLM (GPU-accelerated, high throughput)
    - Embedding   -->  Ollama (lightweight, CPU-friendly)
    - Safety      -->  Llama Guard (specialized safety model)

  The routing is defined in the config.yaml (formerly run.yaml).
  Each model is registered with a provider_id that tells OGX where
  to send requests for that model.

  Here is a sample multi-provider configuration:
""")

    sample_config = """\
  # config.yaml — multi-provider example
  # ─────────────────────────────────────
  apis:
    - inference
    - vector_io
    - safety
    - agents
    - tool_runtime

  providers:
    inference:
      # Provider 1: vLLM for chat models (GPU)
      - provider_id: vllm
        provider_type: remote::vllm
        config:
          url: ${env.VLLM_URL:=http://localhost:8000}
          max_tokens: 4096
          api_token: ${env.VLLM_API_KEY:=token-not-needed}

      # Provider 2: Ollama for lightweight models (CPU)
      - provider_id: ollama
        provider_type: remote::ollama
        config:
          url: ${env.OLLAMA_URL:=http://localhost:11434}

    vector_io:
      - provider_id: qdrant
        provider_type: remote::qdrant
        config:
          url: ${env.QDRANT_URL:=http://localhost:6333}

    safety:
      - provider_id: llama-guard
        provider_type: inline::llama-guard
        config: {}

  models:
    # Chat model served by vLLM
    - model_id: google/gemma-4-E4B-it
      provider_id: vllm
      model_type: llm

    # Same model available via Ollama (fallback)
    - model_id: ollama/gemma4:e4b
      provider_id: ollama
      model_type: llm

    # Embedding model via Ollama
    - model_id: ollama/nomic-embed-text
      provider_id: ollama
      model_type: embedding"""

    for line in sample_config.split("\n"):
        print(line)

    print()
    print("  With this config, OGX automatically routes:")
    print('    client.inference.chat_completion(model_id="google/gemma-4-E4B-it") --> vLLM')
    print('    client.inference.chat_completion(model_id="ollama/gemma4:e4b")     --> Ollama')
    print('    client.embeddings.create(model="ollama/nomic-embed-text")          --> Ollama')


def step4_inference_call(client: OgxClient) -> None:
    """Make an inference call to demonstrate provider routing in action."""
    print_header("Step 4: Inference call — provider routing in action")

    print(f"  Calling model: {MODEL}")
    print(f"  OGX routes this to the provider registered for '{MODEL}'.")
    print()

    response = client.inference.chat_completion(
        model_id=MODEL,
        messages=[
            {"role": "system", "content": "You are a concise assistant. Reply in 1-2 sentences."},
            {"role": "user", "content": "What is provider routing in an AI gateway?"},
        ],
    )

    text = response.completion_message.content.text
    print(f"  Response: {text}")
    print()
    print("  The request was routed to the provider serving this model ID.")
    print("  If we had a second provider configured, we could call a different")
    print("  model ID and OGX would route to that provider instead.")


def step5_fallback_chains() -> None:
    """Explain the fallback chain concept with a sample configuration."""
    print_header("Step 5: Fallback chains — resilience through provider chaining")

    print("""
  A fallback chain lets you configure multiple providers for the same
  task, so if the primary provider fails, OGX can fall back to a
  secondary one. This is critical for production reliability.

  Example scenario:
    Primary:   vLLM (GPU server, fastest, but might be overloaded)
    Fallback:  Ollama (CPU, slower, but always available locally)

  Implementation approach:
    Register the same logical model with multiple providers,
    then handle failover in your application code:
""")

    fallback_code = '''\
  # Application-level fallback pattern
  # ───────────────────────────────────
  PROVIDERS = [
      "google/gemma-4-E4B-it",   # Primary: vLLM (GPU)
      "ollama/gemma4:e4b",        # Fallback: Ollama (CPU)
  ]

  def chat_with_fallback(client, messages):
      """Try each provider in order until one succeeds."""
      for model_id in PROVIDERS:
          try:
              response = client.inference.chat_completion(
                  model_id=model_id,
                  messages=messages,
              )
              print(f"  Success with provider: {model_id}")
              return response
          except Exception as e:
              print(f"  Provider {model_id} failed: {e}")
              continue
      raise RuntimeError("All providers failed")'''

    for line in fallback_code.split("\n"):
        print(line)

    print()
    print("  Tip: In production, add health checks, retry logic, and")
    print("  circuit breakers around your fallback chain.")


def step6_custom_distributions() -> None:
    """Explain the concept of custom distributions."""
    print_header("Step 6: Custom distributions — bundling providers for use cases")

    print("""
  A distribution is a pre-configured bundle of providers, APIs,
  and models packaged together for a specific use case.

  OGX ships several built-in distributions:

    Distribution       | Use Case
    ─────────────────────────────────────────────────
    starter            | General-purpose, quick start
    remote-vllm        | Production with external vLLM
    ollama             | Local development on CPU
    together           | Together AI cloud inference
    fireworks          | Fireworks AI cloud inference
    bedrock            | AWS Bedrock
    dell               | Dell Enterprise AI

  You can create a custom distribution by writing a config.yaml
  that bundles exactly the providers and models you need:
""")

    custom_dist = """\
  # custom-distribution/config.yaml
  # ────────────────────────────────
  # A custom distribution for a RAG-focused application
  # with vLLM for inference and Qdrant for vector storage.

  apis:
    - inference
    - vector_io
    - agents
    - tool_runtime

  providers:
    inference:
      - provider_id: vllm-primary
        provider_type: remote::vllm
        config:
          url: ${env.VLLM_URL:=http://vllm:8000}

    vector_io:
      - provider_id: qdrant
        provider_type: remote::qdrant
        config:
          url: ${env.QDRANT_URL:=http://qdrant:6333}

  models:
    - model_id: chat-model
      provider_id: vllm-primary
      provider_model_id: google/gemma-4-E4B-it
      model_type: llm

  server:
    port: 8321"""

    for line in custom_dist.split("\n"):
        print(line)

    print()
    print("  To run with a custom distribution:")
    print("    ogx run config.yaml")
    print()
    print("  Or as a container with a mounted config:")
    print("    podman run -v ./config.yaml:/app/config.yaml \\")
    print("      -p 8321:8321 ogx/ogx-server \\")
    print("      --config /app/config.yaml")


def main() -> None:
    print()
    print("L2-M1.1 — Multi-Provider Configuration")
    print("=" * 60)
    print()
    print("  This lesson explores how OGX supports multiple inference")
    print("  providers in a single instance, enabling routing, fallback,")
    print("  and custom distributions for production deployments.")

    client = OgxClient(base_url=OGX_URL)

    # Step 1: List current providers
    step1_list_providers()

    # Step 2: List registered models
    step2_list_models(client)

    # Step 3: Provider routing concept
    step3_provider_routing()

    # Step 4: Demonstrate a live inference call
    step4_inference_call(client)

    # Step 5: Fallback chain concept
    step5_fallback_chains()

    # Step 6: Custom distributions
    step6_custom_distributions()

    # Wrap up
    print_header("Summary")
    print("""
  Multi-provider configuration gives you:
    1. Routing   — send requests to the best backend for each task
    2. Fallback  — resilience when a provider goes down
    3. Flexibility — mix GPU/CPU, cloud/local, fast/cheap

  All of this is controlled by config.yaml and model registration.
  OGX abstracts the provider differences behind a unified API.

  Next: L2-M1.2 — Custom Providers and Extensions
""")


if __name__ == "__main__":
    main()
