# L2-M2.2 — OGX + vLLM Integration on OpenShift

**Level:** Practitioner
**Duration:** 45 min

## Overview

This lesson covers how OGX integrates with vLLM when both are running on OpenShift AI. You will learn how to expose OGX via Routes, connect it to KServe-deployed vLLM models, configure streaming for long-running agents, set up persistent vector stores, and autoscale OGX pods.

## Prerequisites

- Completed: L2-M2.1 OGX Operator Deployment
- Access to OpenShift AI cluster (or follow along conceptually)
- Infrastructure running: OGX (port 8321), vLLM, Qdrant (for local testing)

## Concepts

### OpenShift Routes and Services

OGX runs as a Deployment behind a Service inside OpenShift. To make it accessible from outside the cluster, you create a Route — OpenShift's equivalent of an Ingress. The Route provides a public HTTPS URL that proxies traffic to the OGX Service on port 8321.

### Connecting to KServe-Deployed vLLM

On OpenShift AI, vLLM is typically deployed as a KServe InferenceService. OGX connects to it using Kubernetes internal DNS (`svc.cluster.local`), so no external route or API key is needed for the inference backend. This is configured in OGX's `run.yaml` under the `providers.inference` section.

### Responses API on the Cluster

The Responses API works identically on OpenShift — the only difference is the endpoint URL. From outside the cluster, requests go through the Route. From inside (e.g., another pod), requests use the internal Service DNS directly.

### Streamable HTTP Transport

For long-running agent interactions, streaming prevents timeouts and provides real-time feedback. OpenShift Routes default to a 30-second timeout, which must be increased via an annotation for streaming agent turns.

### Persistent Vector Stores

In production, Qdrant needs persistent storage so vector data survives pod restarts. On OpenShift, this is handled via PersistentVolumeClaims (PVCs) mounted into the Qdrant Deployment.

### Autoscaling OGX Pods

OGX is stateless — all persistent state lives in Qdrant and PostgreSQL. This makes it an excellent candidate for horizontal pod autoscaling (HPA) based on CPU utilization.

## Step-by-Step

### Step 1: OpenShift Route Configuration

Create a Route to expose OGX externally with TLS termination at the edge:

```yaml
apiVersion: route.openshift.io/v1
kind: Route
metadata:
  name: ogx-api
spec:
  to:
    kind: Service
    name: ogx-server
  port:
    targetPort: 8321
  tls:
    termination: edge
```

This gives you a URL like `https://ogx-api-<namespace>.apps.<cluster-domain>`.

### Step 2: Connecting to KServe vLLM

Configure OGX's `run.yaml` to point at the in-cluster vLLM service:

```yaml
providers:
  inference:
    - provider_id: vllm
      provider_type: remote::vllm
      config:
        url: http://vllm-predictor.model-serving.svc.cluster.local:8000
        model: google/gemma-4-E4B-it
```

The URL uses Kubernetes service DNS — no external route needed.

### Step 3: Responses API at Scale

Use the Route URL from outside the cluster:

```bash
ROUTE_URL="https://ogx-api-myproject.apps.cluster.example.com"

curl -s $ROUTE_URL/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-E4B-it",
    "input": "Explain Kubernetes in one sentence."
  }'
```

### Step 4: Streamable HTTP Transport

For streaming, increase the Route timeout and use `"stream": true`:

```yaml
metadata:
  annotations:
    haproxy.router.openshift.io/timeout: 300s
```

```bash
curl -N $ROUTE_URL/v1/responses \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemma-4-E4B-it",
    "input": "Write a detailed analysis.",
    "stream": true
  }'
```

### Step 5: Vector Stores on OpenShift

Create a PVC for Qdrant and mount it:

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: qdrant-storage
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: gp3-csi
```

Configure OGX to use the in-cluster Qdrant:

```yaml
providers:
  vector_io:
    - provider_id: qdrant
      provider_type: remote::qdrant
      config:
        url: http://qdrant.myproject.svc.cluster.local:6333
```

### Step 6: Autoscaling OGX Pods

Apply an HPA to scale OGX based on CPU:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ogx-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ogx-server
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

### Step 7: Testing External Access

Get the Route URL and test:

```bash
oc get route ogx-api -o jsonpath='{.spec.host}'

curl -s https://<route-url>/v1/health
curl -s https://<route-url>/v1/models | python -m json.tool
```

## Running the Lesson

```bash
cd tutorial/level_2/M2_ogx_openshift_ai/2_vllm_integration
uv sync
uv run python main.py
```

## Expected Output

The script prints seven configuration sections covering:
- OpenShift Route YAML for exposing OGX
- OGX `run.yaml` provider configuration for in-cluster vLLM
- Curl examples for the Responses API (inside and outside the cluster)
- Streaming configuration with Route timeout annotations
- PVC and Qdrant Deployment YAML for persistent vector stores
- HPA YAML for autoscaling OGX pods
- External access testing commands and Python client example

## Key Takeaways

- OGX is exposed externally via OpenShift Routes with TLS termination.
- In-cluster vLLM is accessed via Kubernetes service DNS — no API keys or external routes needed.
- The Responses API works the same on-cluster; only the URL changes.
- Streaming requires increasing the Route timeout beyond the default 30 seconds.
- Qdrant needs PVC-backed persistent storage for production use on OpenShift.
- OGX is stateless and scales horizontally with HPA.

## Next Steps

Continue to **L2-M2.3 -- OGX + Safety on OpenShift** to learn how to configure safety shields and content moderation for production OGX deployments on OpenShift AI.
