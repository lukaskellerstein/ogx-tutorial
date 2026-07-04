"""L2-M1.3 — Telemetry and Observability.

Explores OGX's OpenTelemetry integration for tracing and observability:
configuring OTel in run.yaml, exporting traces to Jaeger, structured
logging patterns, and correlating traces across OGX and downstream
providers.
"""

import sys
import time

import httpx
from ogx_client import OgxClient

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


def check_telemetry_config() -> None:
    """Step 1: Query the OGX server for telemetry status."""
    print("=" * 60)
    print("Step 1: Check Current Telemetry Configuration")
    print("=" * 60)

    # Try the providers endpoint to see if a telemetry provider is configured
    resp = httpx.get(f"{OGX_URL}/v1/providers", timeout=10)

    if resp.status_code == 200:
        data = resp.json()
        telemetry_found = False

        if isinstance(data, dict):
            for api_name, providers in data.items():
                if "telemetry" in api_name.lower():
                    telemetry_found = True
                    print(f"\n  Telemetry providers found under [{api_name}]:")
                    if isinstance(providers, list):
                        for p in providers:
                            if isinstance(p, dict):
                                pid = p.get("provider_id", "unknown")
                                ptype = p.get("provider_type", "unknown")
                                print(f"    - {pid} ({ptype})")
                            else:
                                print(f"    - {p}")
        elif isinstance(data, list):
            for p in data:
                if isinstance(p, dict):
                    api = p.get("api", "")
                    if "telemetry" in api.lower():
                        telemetry_found = True
                        pid = p.get("provider_id", "unknown")
                        ptype = p.get("provider_type", "unknown")
                        print(f"\n  Telemetry provider: {pid} ({ptype})")

        if not telemetry_found:
            print("\n  No dedicated telemetry provider found in the current")
            print("  OGX configuration. This is normal for the default")
            print("  distribution -- telemetry is opt-in via run.yaml.")
    else:
        print(f"\n  Could not query providers (HTTP {resp.status_code}).")
        print("  Telemetry configuration is managed in run.yaml.")

    print()
    print("  OGX supports OpenTelemetry (OTel) tracing out of the box.")
    print("  When enabled, every API call is traced with spans for")
    print("  inference, tool execution, and provider routing.")
    print()


def otel_configuration() -> None:
    """Step 2: Show how to enable OpenTelemetry tracing in run.yaml."""
    print("=" * 60)
    print("Step 2: OTel Configuration in run.yaml")
    print("=" * 60)

    print("""
  To enable OpenTelemetry tracing, add a telemetry section to your
  OGX run.yaml configuration file:

  ┌─────────────────────────────────────────────────────────┐
  │  # run.yaml (telemetry section)                         │
  │                                                         │
  │  telemetry:                                             │
  │    - provider_id: otel                                  │
  │      provider_type: inline::otel                        │
  │      config:                                            │
  │        service_name: ogx-tutorial                       │
  │        exporter:                                        │
  │          type: otlp                                     │
  │          endpoint: http://jaeger:4318                   │
  │        otel_trace_exporter: otlp_http                   │
  │        otel_exporter_otlp_endpoint: http://jaeger:4318  │
  └─────────────────────────────────────────────────────────┘

  Key configuration fields:

    service_name        Identifies this OGX instance in traces.
                        Use a meaningful name per environment
                        (e.g., ogx-dev, ogx-staging, ogx-prod).

    exporter.type       The OTel exporter protocol. Common values:
                          otlp      -- OpenTelemetry Protocol (default)
                          console   -- print spans to stdout (debugging)

    exporter.endpoint   The collector/backend URL. Jaeger, Zipkin, and
                        Grafana Tempo all accept OTLP on port 4318.

  After changing run.yaml, restart the OGX server for the new
  telemetry configuration to take effect.
""")


def jaeger_setup() -> None:
    """Step 3: Show how to run Jaeger for trace visualization."""
    print("=" * 60)
    print("Step 3: Jaeger Setup for Trace Visualization")
    print("=" * 60)

    print("""
  Jaeger is an open-source distributed tracing platform. It collects,
  stores, and visualizes traces from OTel-instrumented services.

  Run Jaeger with Podman (all-in-one image):

    podman run -d --name jaeger \\
      -p 16686:16686 \\
      -p 4318:4318 \\
      jaegertracing/jaeger:latest

  Port mapping:
    16686   Jaeger UI (open http://localhost:16686 in your browser)
    4318    OTLP HTTP receiver (where OGX sends traces)

  For a Podman Compose setup alongside OGX, add this service to
  your compose.yml:

  ┌─────────────────────────────────────────────────────────┐
  │  services:                                              │
  │    jaeger:                                              │
  │      image: jaegertracing/jaeger:latest                 │
  │      ports:                                             │
  │        - "16686:16686"   # Jaeger UI                    │
  │        - "4318:4318"     # OTLP HTTP                    │
  │      restart: unless-stopped                            │
  └─────────────────────────────────────────────────────────┘

  Once Jaeger is running and OGX has telemetry enabled, traces
  appear in the Jaeger UI within seconds of making API calls.
""")


def traced_inference_call(client: OgxClient) -> None:
    """Step 4: Make an inference call and explain what gets traced."""
    print("=" * 60)
    print("Step 4: Traced Inference Call")
    print("=" * 60)

    print(f"\n  Making an inference call to demonstrate tracing...")
    print(f"  Model: {MODEL}\n")

    start = time.perf_counter()

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "user", "content": "Explain observability in one sentence."},
        ],
        max_tokens=100,
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    content = response.choices[0].message.content
    usage = response.usage

    print(f"  Response: {content}\n")
    print(f"  --- Trace data (what OTel captures) ---")
    print(f"  Request ID:     {response.id}")
    print(f"  Model:          {response.model}")
    print(f"  Latency:        {elapsed_ms:.0f} ms")

    if usage:
        print(f"  Prompt tokens:  {usage.prompt_tokens}")
        print(f"  Output tokens:  {usage.completion_tokens}")
        print(f"  Total tokens:   {usage.total_tokens}")

    print()
    print("  When OTel tracing is enabled, OGX creates spans for:")
    print("    1. The incoming HTTP request (method, path, status)")
    print("    2. Provider routing (which provider handled the call)")
    print("    3. Inference execution (model, token counts, latency)")
    print("    4. Tool calls (if any -- tool name, arguments, result)")
    print("    5. Safety checks (if shields are configured)")
    print()
    print("  Each span includes attributes like model ID, provider ID,")
    print("  token counts, and timing -- giving you full visibility")
    print("  into every API call.")
    print()


def structured_logging() -> None:
    """Step 5: Show structured logging patterns."""
    print("=" * 60)
    print("Step 5: Structured Logging Patterns")
    print("=" * 60)

    print("""
  Structured logging complements tracing by providing searchable,
  machine-readable log entries. Use JSON-formatted logs with
  consistent fields for easy querying.

  Sample structured log entry:

  ┌─────────────────────────────────────────────────────────┐
  │  {                                                      │
  │    "timestamp": "2026-07-04T10:30:00Z",                 │
  │    "level": "INFO",                                     │
  │    "service": "ogx-tutorial",                           │
  │    "trace_id": "abc123def456",                          │
  │    "span_id": "789xyz",                                 │
  │    "event": "inference.chat_completion",                 │
  │    "model": "ollama/gemma4:e4b",                        │
  │    "provider": "remote::ollama",                        │
  │    "latency_ms": 342,                                   │
  │    "prompt_tokens": 28,                                 │
  │    "completion_tokens": 45,                             │
  │    "status": "success"                                  │
  │  }                                                      │
  └─────────────────────────────────────────────────────────┘

  Key fields to include in every log entry:

    trace_id / span_id   Correlate logs with OTel traces. These come
                         from the OTel context propagated by OGX.

    event                The operation name (e.g., inference.chat_completion,
                         tool.invoke, safety.run_shield).

    latency_ms           End-to-end time for the operation. Essential
                         for performance monitoring and alerting.

    token counts         prompt_tokens + completion_tokens. Track usage
                         for cost estimation and quota management.

    status               success / error. Include error details in a
                         separate "error" field when status is error.

  Python logging setup for structured output:

    import logging, json

    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_data = {
                "timestamp": self.formatTime(record),
                "level": record.levelname,
                "message": record.getMessage(),
            }
            return json.dumps(log_data)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("ogx-app")
    logger.addHandler(handler)
""")


def correlating_traces() -> None:
    """Step 6: Explain trace correlation between OGX and providers."""
    print("=" * 60)
    print("Step 6: Correlating Traces Across Services")
    print("=" * 60)

    print("""
  In a production OGX deployment, a single user request flows
  through multiple services:

    Client -> OGX -> vLLM (or Ollama) -> GPU inference
                 -> Qdrant (vector search)
                 -> MCP server (tool execution)

  OpenTelemetry context propagation ensures that ALL spans across
  these services share the same trace ID. This gives you a single,
  end-to-end view of the request.

  How it works:

    1. OGX receives a request and creates a root span.
    2. When OGX calls vLLM, it propagates the trace context via
       HTTP headers (traceparent, tracestate).
    3. If vLLM is OTel-instrumented, it creates child spans under
       the same trace ID.
    4. The same applies to Qdrant, MCP servers, and any other
       downstream service.

  Example trace hierarchy (as seen in Jaeger):

    [ogx] POST /v1/chat/completions          (450 ms)
     +-- [ogx] route_to_provider             ( 2 ms)
     +-- [ogx] inference.chat_completion     (440 ms)
          +-- [vllm] generate                (420 ms)
               +-- [vllm] model_forward      (380 ms)

  To enable correlation:
    - OGX: enable OTel in run.yaml (Step 2)
    - vLLM: set VLLM_CONFIGURE_LOGGING=1 and the OTel env vars
    - Qdrant: enable OTel via its configuration
    - All services export to the same Jaeger/collector endpoint
""")


def dashboard_concepts() -> None:
    """Step 7: Summarize monitoring dashboard requirements."""
    print("=" * 60)
    print("Step 7: Monitoring Dashboard Concepts")
    print("=" * 60)

    print("""
  A production OGX monitoring dashboard should display these
  key metrics, grouped by category:

  --- Request Metrics ---
    Request rate          Requests per second, by endpoint
    Error rate            Percentage of 4xx/5xx responses
    Active requests       Current in-flight requests

  --- Latency Metrics ---
    P50 latency           Median response time
    P95 latency           95th percentile (tail latency)
    P99 latency           99th percentile (worst case)
    Time to first token   For streaming responses

  --- Token Metrics ---
    Token throughput       Tokens per second (input + output)
    Prompt token avg       Average prompt size
    Completion token avg   Average response size
    Cost estimation        Based on token counts and model pricing

  --- Provider Metrics ---
    Provider health        Up/down status per provider
    Provider latency       Latency breakdown by provider
    Routing decisions      Which provider handled each request
    Fallback rate          How often the fallback provider is used

  --- Resource Metrics ---
    GPU utilization        (from vLLM / inference backend)
    Memory usage           OGX process and provider memory
    Queue depth            Pending requests in the inference queue

  Tools for building dashboards:
    - Grafana + Prometheus   (metrics)
    - Grafana + Tempo        (traces, alternative to Jaeger)
    - Jaeger UI              (trace visualization)
    - Datadog / New Relic    (commercial, full-stack)

  All of these can consume OTel data exported by OGX.
""")


def main() -> None:
    """Explore OGX telemetry and observability."""
    print()
    print("#" * 60)
    print("#  L2-M1.3 — Telemetry and Observability")
    print("#  OpenTelemetry tracing and monitoring for OGX")
    print("#" * 60)
    print()

    if not check_server():
        sys.exit(1)

    client = OgxClient(base_url=OGX_URL)

    check_telemetry_config()
    otel_configuration()
    jaeger_setup()
    traced_inference_call(client)
    structured_logging()
    correlating_traces()
    dashboard_concepts()

    print("=" * 60)
    print("Lesson complete!")
    print("Next: L2-M1.4 — Evaluation and RAG Benchmarks")
    print("=" * 60)


if __name__ == "__main__":
    main()
