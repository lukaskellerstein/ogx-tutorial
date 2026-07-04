# L2-M1.3 — Telemetry and Observability

**Level:** Practitioner
**Duration:** 45 min

## Overview

Observability is essential for understanding how your OGX deployment behaves in production -- how long requests take, where bottlenecks occur, and how tokens are consumed. In this lesson you will learn how to enable OpenTelemetry (OTel) tracing in OGX, export traces to Jaeger for visualization, apply structured logging patterns, and understand how traces correlate across OGX and its downstream providers (vLLM, Qdrant, MCP servers).

## Prerequisites

- Completed: L2-M1.2 Custom Providers and Extensions
- Familiarity with OGX API surface from Level 1 (inference, agents, tools)
- Infrastructure running: OGX (port 8321) with Ollama

## Concepts

### OpenTelemetry in OGX

OGX has built-in support for OpenTelemetry, the industry-standard observability framework. When enabled, OGX automatically instruments every API call with distributed traces, capturing:

- **Spans** for each operation (inference, tool calls, safety checks)
- **Attributes** on each span (model ID, provider, token counts, latency)
- **Context propagation** to downstream services (vLLM, Qdrant, MCP)

### Traces, Spans, and Attributes

| Concept | Description |
|---------|-------------|
| **Trace** | End-to-end record of a single request across all services |
| **Span** | A single unit of work within a trace (e.g., one inference call) |
| **Attribute** | Key-value metadata on a span (e.g., `model=gemma4:e4b`) |
| **Context propagation** | Passing trace IDs across service boundaries via HTTP headers |

### Enabling Telemetry

Telemetry is configured in OGX's `run.yaml` file. It is opt-in -- the default configuration does not export traces. To enable it, add a telemetry provider section that specifies:

- A **service name** to identify this OGX instance
- An **exporter type** (OTLP is the standard)
- An **endpoint** where traces are sent (Jaeger, Grafana Tempo, etc.)

### Jaeger

Jaeger is an open-source distributed tracing platform that collects, indexes, and visualizes OTel traces. It provides a web UI where you can search for traces by service, operation, tags, and time range, then drill into individual spans to see timing and attributes.

### Structured Logging

Structured logging produces machine-readable JSON log entries instead of free-form text. Each entry includes consistent fields (trace ID, operation, latency, token counts) that enable log aggregation, searching, and alerting. When log entries include the OTel trace ID, you can jump from a log entry directly to its trace in Jaeger.

### Trace Correlation

In a production deployment, a single user request flows through OGX, then to an inference provider (vLLM/Ollama), possibly to a vector store (Qdrant), and to MCP servers for tool execution. OTel context propagation ensures all services share the same trace ID, giving you a unified view of the entire request path.

## Step-by-Step

### Step 1: Check current telemetry configuration

Query the OGX server's provider list to see whether a telemetry provider is configured. In the default distribution, telemetry is not enabled -- this step confirms the baseline.

```python
resp = httpx.get(f"{OGX_URL}/v1/providers", timeout=10)
data = resp.json()
# Look for telemetry-related providers in the response
```

### Step 2: OTel configuration in run.yaml

Review the `run.yaml` snippet that enables OpenTelemetry tracing. The key fields are `service_name` (identifies the OGX instance), `exporter.type` (OTLP protocol), and `exporter.endpoint` (where traces go).

```yaml
telemetry:
  - provider_id: otel
    provider_type: inline::otel
    config:
      service_name: ogx-tutorial
      exporter:
        type: otlp
        endpoint: http://jaeger:4318
```

After modifying `run.yaml`, the OGX server must be restarted for changes to take effect.

### Step 3: Jaeger setup

See how to run Jaeger as a Podman container for local trace visualization, and how to add it to a Podman Compose file for integration with the OGX infrastructure stack.

```bash
podman run -d --name jaeger \
  -p 16686:16686 \
  -p 4318:4318 \
  jaegertracing/jaeger:latest
```

Port 16686 serves the Jaeger UI; port 4318 accepts OTLP HTTP traces from OGX.

### Step 4: Traced inference call

Make a real inference call and examine the data that OTel would capture: request ID, model, latency, and token counts. This shows what information appears in each trace span.

```python
start = time.perf_counter()
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": "Explain observability in one sentence."}],
    max_tokens=100,
)
elapsed_ms = (time.perf_counter() - start) * 1000
```

The response object contains the request ID, model name, and token usage -- all of which become span attributes when tracing is enabled.

### Step 5: Structured logging patterns

Review a structured (JSON) log entry format with consistent fields: timestamp, trace ID, event name, model, latency, token counts, and status. See a minimal Python `JsonFormatter` for producing structured logs.

### Step 6: Correlating traces across services

Understand how OTel context propagation creates a unified trace across OGX, vLLM, Qdrant, and MCP servers. See an example trace hierarchy as it appears in Jaeger, showing parent-child span relationships.

### Step 7: Monitoring dashboard concepts

Review the key metrics categories for a production dashboard: request metrics (rate, errors), latency percentiles (P50, P95, P99), token throughput, provider health, and resource utilization. See which tools (Grafana, Prometheus, Jaeger) consume OTel data.

## Running the Lesson

```bash
cd tutorial/level_2/M1_advanced_patterns/3_telemetry_observability
uv sync
uv run python main.py
```

## Expected Output

```
############################################################
#  L2-M1.3 — Telemetry and Observability
#  OpenTelemetry tracing and monitoring for OGX
############################################################

============================================================
Step 1: Check Current Telemetry Configuration
============================================================

  No dedicated telemetry provider found in the current
  OGX configuration. This is normal for the default
  distribution -- telemetry is opt-in via run.yaml.

  OGX supports OpenTelemetry (OTel) tracing out of the box.
  When enabled, every API call is traced with spans for
  inference, tool execution, and provider routing.

============================================================
Step 2: OTel Configuration in run.yaml
============================================================

  To enable OpenTelemetry tracing, add a telemetry section to your
  OGX run.yaml configuration file:
  [prints run.yaml snippet with service_name, exporter, endpoint]

============================================================
Step 3: Jaeger Setup for Trace Visualization
============================================================

  [prints Podman run command and Compose snippet for Jaeger]

============================================================
Step 4: Traced Inference Call
============================================================

  Making an inference call to demonstrate tracing...
  Model: ollama/gemma4:e4b

  Response: Observability is the ability to understand a system's
  internal state by examining its external outputs like logs,
  metrics, and traces.

  --- Trace data (what OTel captures) ---
  Request ID:     chatcmpl-abc123
  Model:          ollama/gemma4:e4b
  Latency:        342 ms
  Prompt tokens:  12
  Output tokens:  28
  Total tokens:   40

  When OTel tracing is enabled, OGX creates spans for:
    1. The incoming HTTP request (method, path, status)
    2. Provider routing (which provider handled the call)
    3. Inference execution (model, token counts, latency)
    4. Tool calls (if any -- tool name, arguments, result)
    5. Safety checks (if shields are configured)

============================================================
Step 5: Structured Logging Patterns
============================================================

  [prints JSON log entry format and Python JsonFormatter example]

============================================================
Step 6: Correlating Traces Across Services
============================================================

  [prints trace flow diagram and Jaeger trace hierarchy example]

============================================================
Step 7: Monitoring Dashboard Concepts
============================================================

  [prints metric categories: request, latency, token, provider, resource]

============================================================
Lesson complete!
Next: L2-M1.4 — Evaluation and RAG Benchmarks
============================================================
```

> Note: The inference response in Step 4 will vary. Token counts and latency depend on the model and hardware. The telemetry provider check in Step 1 depends on your OGX distribution.

## Key Takeaways

- OGX has **built-in OpenTelemetry support** that traces every API call with spans, attributes, and context propagation.
- Telemetry is **opt-in** -- enable it by adding a `telemetry` section to `run.yaml` with a service name and OTLP exporter endpoint.
- **Jaeger** provides trace visualization out of the box and runs as a single Podman container accepting OTLP on port 4318.
- Each OGX trace captures **request ID, model, provider, latency, and token counts** -- essential data for debugging and cost tracking.
- **Structured logging** with JSON format and trace IDs bridges the gap between logs and traces, enabling end-to-end debugging.
- **Context propagation** links OGX spans with downstream provider spans (vLLM, Qdrant, MCP), giving you a unified view of the full request path.

## Next Steps

Continue to **L2-M1.4 -- Evaluation and RAG Benchmarks**, where you will define evaluation tasks, run them against OGX-served models, and benchmark RAG retrieval quality with different configurations.
