# L2-M1.7 — Production Deployment

**Level:** Practitioner
**Duration:** 45 min

## Overview

Deploy OGX for production with a containerized, scalable architecture. This lesson covers a complete Podman Compose stack (OGX + vLLM + Qdrant + PostgreSQL), PostgreSQL as the production KVStore backend, production Qdrant configuration, scaling patterns, and a preview of deploying OGX on OpenShift AI via the OGX Operator.

## Prerequisites

- Completed: L2-M1.6 File Processors
- Infrastructure running: OGX server (port 8321), Qdrant (port 6333), Ollama with `gemma4:e4b`

## Concepts

### Containerized Deployment

In development, you might run OGX with SQLite and inline Qdrant — all in a single process. Production requires external, persistent services: a dedicated Qdrant container for vector storage and PostgreSQL for the KVStore (sessions, memory). Podman Compose orchestrates all four services (OGX, vLLM, Qdrant, PostgreSQL) with health checks, restart policies, and dependency ordering.

### PostgreSQL KVStore

SQLite is the default OGX KVStore backend. It works for single-process development but fails under concurrent access — you cannot run multiple OGX replicas against the same SQLite file. PostgreSQL handles concurrent reads and writes, supports standard backup tooling, and is required for horizontal scaling.

### Production Qdrant

The `inline::qdrant` provider runs an embedded Qdrant instance inside the OGX process. This is convenient for development but loses data on restart and cannot be shared across replicas. The `remote::qdrant` provider connects to an external Qdrant server with persistent storage, gRPC access, and a management dashboard.

### Scaling Architecture

OGX is stateless when backed by external PostgreSQL and Qdrant. This means you can run multiple OGX replicas behind a load balancer — each replica connects to the same shared databases. The inference backend (vLLM) is typically the bottleneck and can be scaled with tensor parallelism or multiple replicas.

### OpenShift AI Operator

For Kubernetes-based production, the OGX Operator (`ogx-k8s-operator`) automates deployment on OpenShift AI. You define your stack as a custom resource (OGXStack CRD), and the operator creates all necessary Kubernetes objects automatically.

## Step-by-Step

### Step 1: Health Checks

Before deploying to production, verify that all services are reachable. The lesson checks OGX, Qdrant, and the inference backend:

```python
def check_service(name: str, url: str, timeout: float = 5.0) -> bool:
    try:
        resp = httpx.get(url, timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception:
        return False
```

Each service exposes a health endpoint:

| Service | Health Endpoint |
|---------|----------------|
| OGX | `GET /v1/models` |
| Qdrant | `GET /healthz` |
| vLLM | `GET /health` |
| PostgreSQL | `pg_isready -U ogx` (inside container) |

### Step 2: Production Podman Compose

A production `compose.yml` includes four services with health checks, restart policies, persistent volumes, and dependency ordering. Key points:

- `depends_on` with `condition: service_healthy` ensures services start in the right order.
- vLLM uses `nvidia.com/gpu=all` for GPU pass-through on Linux.
- Named volumes (`qdrant_data`, `pg_data`) persist data across container restarts.
- Every service has `restart: unless-stopped`.

### Step 3: PostgreSQL KVStore

Configure PostgreSQL in your OGX `run.yaml`:

```yaml
providers:
  kvstore:
    - provider_id: postgres
      provider_type: remote::postgres
      config:
        host: postgres
        port: 5432
        user: ogx
        password: ogx-secret
        database: ogx
```

This replaces the default SQLite backend and enables concurrent access from multiple OGX replicas.

### Step 4: Qdrant Production Configuration

Switch from `inline::qdrant` to `remote::qdrant` in `run.yaml`:

```yaml
providers:
  vector_io:
    - provider_id: qdrant
      provider_type: remote::qdrant
      config:
        url: http://qdrant:6333
```

Production best practices:
- Use HNSW index (default) for fast approximate search.
- Set `on_disk: true` for collections larger than available RAM.
- Configure `replication_factor >= 2` for high availability.

### Step 5: Scaling Considerations

OGX scales horizontally because it is stateless:

1. Run N OGX replicas behind a load balancer (round-robin).
2. All replicas share the same PostgreSQL and Qdrant backends.
3. The inference backend (vLLM) is the bottleneck — scale with tensor parallelism or multiple replicas.

Approximate resource requirements:

| Component | CPU | RAM | GPU |
|-----------|-----|-----|-----|
| OGX server | 1 | 512 MB | -- |
| vLLM (4B model) | -- | 8 GB | 1 (16 GB VRAM) |
| Qdrant | 2 | 2-4 GB | -- |
| PostgreSQL | 1 | 512 MB | -- |

### Step 6: OpenShift AI Preview

The OGX Operator deploys the full stack on OpenShift AI via a custom resource:

```yaml
apiVersion: ogx.ai/v1alpha1
kind: OGXStack
metadata:
  name: my-ogx-stack
spec:
  distribution: remote-vllm
  model: google/gemma-4-E4B-it
  providers:
    vector_io: remote::qdrant
    kvstore: remote::postgres
```

The operator handles Deployments, Services, ConfigMaps, PVCs, and GPU scheduling automatically.

### Step 7: Production-Readiness Checklist

The lesson finishes by running health checks against the local infrastructure and printing a pass/fail checklist covering OGX, Qdrant, inference, and PostgreSQL.

## Running the Lesson

```bash
cd tutorial/level_2/M1_advanced_patterns/7_production_deployment
uv sync
uv run python main.py
```

## Expected Output

```
L2-M1.7 — Production Deployment
============================================================

============================================================
Step 1: Infrastructure Health Checks
============================================================
  [+] OGX Server             UP      (http://localhost:8321/v1/models)
  [+] Qdrant                 UP      (http://localhost:6333/healthz)
  [+] Inference Backend      UP      (2 model(s) registered)

============================================================
Step 2: Production Podman Compose
============================================================
  A production deployment runs four services via Podman Compose:
  ...

============================================================
Step 3: PostgreSQL KVStore Configuration
============================================================
  By default, OGX uses SQLite for its KVStore ...
  ...

============================================================
Step 4: Qdrant Production Configuration
============================================================
  Development vs Production Qdrant providers:
  ...

============================================================
Step 5: Scaling Considerations
============================================================
  OGX is designed for horizontal scaling:
  ...

============================================================
Step 6: OpenShift AI — OGX Operator Preview
============================================================
  For Kubernetes-based production, the OGX Operator ...
  ...

============================================================
Step 7: Production-Readiness Checklist
============================================================

  [PASS] OGX server reachable                  (Required)
  [PASS] Qdrant reachable                      (Required)
  [PASS] Inference backend responds             (Required)
  [FAIL] PostgreSQL KVStore                     (Recommended)

  Result: 3/4 checks passed.
  Some services are not running. For production, all
  checks should pass. See compose.yml above for setup.

============================================================
Lesson complete!
============================================================
```

(Exact model counts and check results depend on your running infrastructure.)

## Key Takeaways

- A production OGX deployment requires four services: OGX, vLLM (or Ollama), Qdrant, and PostgreSQL — orchestrated by Podman Compose with health checks and restart policies.
- PostgreSQL replaces SQLite as the KVStore backend to support concurrent access from multiple OGX replicas.
- `remote::qdrant` replaces `inline::qdrant` for persistent, shared vector storage in production.
- OGX is stateless when backed by external databases, enabling horizontal scaling behind a load balancer.
- The OGX Operator automates deployment on OpenShift AI via a custom resource definition (OGXStack CRD).

## Next Steps

Continue to **L2-M2.1 — OGX Operator Deployment**, where you will deploy OGX on OpenShift AI using the OGX Kubernetes Operator and custom resource definitions.
