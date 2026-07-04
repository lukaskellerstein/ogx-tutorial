"""
L2-M2.2 — OGX + vLLM Integration on OpenShift

This lesson covers how OGX integrates with vLLM on OpenShift AI:
- Exposing OGX via OpenShift Routes
- Connecting to KServe-deployed vLLM models
- Using the Responses API on-cluster
- Streamable HTTP transport for long-running agents
- Persistent vector stores with Qdrant on OpenShift
- Autoscaling OGX pods with HPA

Since this lesson targets an OpenShift cluster, it focuses on
configuration examples and concepts rather than live API calls.
"""


def step_1_openshift_route() -> None:
    """Show how OGX is exposed via an OpenShift Route."""
    print("=" * 60)
    print("Step 1: OpenShift Route Configuration")
    print("=" * 60)
    print()
    print("OGX runs as a Deployment + Service inside OpenShift.")
    print("To expose it externally, create a Route:")
    print()
    route_yaml = """\
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
    termination: edge"""
    print(route_yaml)
    print()
    print("This gives you a public URL like:")
    print("  https://ogx-api-<namespace>.apps.<cluster-domain>")
    print()
    print("TLS termination: 'edge' means the Route handles TLS,")
    print("and traffic inside the cluster is plain HTTP to port 8321.")
    print()


def step_2_kserve_vllm() -> None:
    """Show the run.yaml provider config for in-cluster vLLM."""
    print("=" * 60)
    print("Step 2: Connecting to KServe vLLM")
    print("=" * 60)
    print()
    print("On OpenShift AI, vLLM is deployed via KServe as an")
    print("InferenceService. OGX connects to it using the in-cluster")
    print("DNS name — no external route needed.")
    print()
    print("Add this to your OGX run.yaml:")
    print()
    provider_yaml = """\
providers:
  inference:
    - provider_id: vllm
      provider_type: remote::vllm
      config:
        url: http://vllm-predictor.model-serving.svc.cluster.local:8000
        model: google/gemma-4-E4B-it"""
    print(provider_yaml)
    print()
    print("Key points:")
    print("  - The URL uses Kubernetes service DNS (in-cluster)")
    print("  - No API key needed for in-cluster communication")
    print("  - The model must match what KServe is serving")
    print("  - provider_type 'remote::vllm' uses the vLLM-optimized path")
    print()


def step_3_responses_api() -> None:
    """Explain the Responses API on-cluster."""
    print("=" * 60)
    print("Step 3: Responses API at Scale")
    print("=" * 60)
    print()
    print("The Responses API works the same on OpenShift as locally.")
    print("The only difference is the endpoint URL — it goes through")
    print("the Route instead of localhost.")
    print()
    print("From outside the cluster:")
    print()
    print('  ROUTE_URL="https://ogx-api-myproject.apps.cluster.example.com"')
    print()
    print("  # Chat completion via Responses API")
    print("  curl -s $ROUTE_URL/v1/responses \\")
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{")
    print('      "model": "google/gemma-4-E4B-it",')
    print('      "input": "Explain Kubernetes in one sentence."')
    print("    }'")
    print()
    print("  # List available models")
    print("  curl -s $ROUTE_URL/v1/models | python -m json.tool")
    print()
    print("From inside the cluster (e.g., another pod):")
    print()
    print("  curl -s http://ogx-server.myproject.svc.cluster.local:8321"
          "/v1/responses \\")
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{...}'")
    print()


def step_4_streaming() -> None:
    """Explain streaming for long-running agent interactions."""
    print("=" * 60)
    print("Step 4: Streamable HTTP Transport")
    print("=" * 60)
    print()
    print("For long-running agent interactions, streaming avoids")
    print("timeouts and gives real-time feedback to the client.")
    print()
    print("OpenShift Route timeout defaults to 30 seconds. For")
    print("streaming agent turns that run longer, configure:")
    print()
    route_annotation = """\
metadata:
  annotations:
    haproxy.router.openshift.io/timeout: 300s"""
    print(route_annotation)
    print()
    print("Streaming request example:")
    print()
    print("  curl -N $ROUTE_URL/v1/responses \\")
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{")
    print('      "model": "google/gemma-4-E4B-it",')
    print('      "input": "Write a detailed analysis of cloud-native AI.",')
    print('      "stream": true')
    print("    }'")
    print()
    print("Python client with streaming:")
    print()
    python_example = """\
  import httpx

  route_url = "https://ogx-api-myproject.apps.cluster.example.com"

  with httpx.stream(
      "POST",
      f"{route_url}/v1/responses",
      json={
          "model": "google/gemma-4-E4B-it",
          "input": "Explain streaming in distributed systems.",
          "stream": True,
      },
      timeout=300.0,
  ) as response:
      for line in response.iter_lines():
          if line:
              print(line)"""
    print(python_example)
    print()


def step_5_vector_stores() -> None:
    """Show persistent storage configuration for Qdrant on OpenShift."""
    print("=" * 60)
    print("Step 5: Vector Stores on OpenShift")
    print("=" * 60)
    print()
    print("In production, Qdrant needs persistent storage so vector")
    print("data survives pod restarts. Use a PersistentVolumeClaim:")
    print()
    pvc_yaml = """\
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
  storageClassName: gp3-csi"""
    print(pvc_yaml)
    print()
    print("Mount it in the Qdrant Deployment:")
    print()
    volume_mount = """\
spec:
  containers:
    - name: qdrant
      image: qdrant/qdrant:latest
      volumeMounts:
        - name: qdrant-data
          mountPath: /qdrant/storage
  volumes:
    - name: qdrant-data
      persistentVolumeClaim:
        claimName: qdrant-storage"""
    print(volume_mount)
    print()
    print("OGX run.yaml for remote Qdrant:")
    print()
    qdrant_config = """\
providers:
  vector_io:
    - provider_id: qdrant
      provider_type: remote::qdrant
      config:
        url: http://qdrant.myproject.svc.cluster.local:6333"""
    print(qdrant_config)
    print()


def step_6_autoscaling() -> None:
    """Show HPA configuration for OGX pods."""
    print("=" * 60)
    print("Step 6: Autoscaling OGX Pods")
    print("=" * 60)
    print()
    print("Use a HorizontalPodAutoscaler to scale OGX based on CPU:")
    print()
    hpa_yaml = """\
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
          averageUtilization: 70"""
    print(hpa_yaml)
    print()
    print("Key considerations:")
    print("  - OGX is stateless (state lives in Qdrant/PostgreSQL),")
    print("    so horizontal scaling works well.")
    print("  - vLLM scaling is separate — managed by KServe autoscaler.")
    print("  - Set resource requests/limits on the OGX Deployment so")
    print("    HPA has metrics to work with.")
    print()
    print("Resource configuration for OGX pods:")
    print()
    resources_yaml = """\
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 2000m
    memory: 2Gi"""
    print(resources_yaml)
    print()


def step_7_external_access() -> None:
    """Show how to test from outside the cluster."""
    print("=" * 60)
    print("Step 7: Testing External Access")
    print("=" * 60)
    print()
    print("Once the Route is created, get the URL:")
    print()
    print("  oc get route ogx-api -o jsonpath='{.spec.host}'")
    print()
    print("Test connectivity:")
    print()
    print("  # Health check")
    print("  curl -s https://<route-url>/v1/health")
    print()
    print("  # List models")
    print("  curl -s https://<route-url>/v1/models | python -m json.tool")
    print()
    print("  # Chat completion")
    print("  curl -s https://<route-url>/v1/responses \\")
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{")
    print('      "model": "google/gemma-4-E4B-it",')
    print('      "input": "Hello from outside the cluster!"')
    print("    }' | python -m json.tool")
    print()
    print("Python client from outside:")
    print()
    python_example = """\
  from ogx_client import OGXClient

  client = OGXClient(
      base_url="https://ogx-api-myproject.apps.cluster.example.com"
  )

  response = client.inference.chat_completion(
      model_id="google/gemma-4-E4B-it",
      messages=[
          {"role": "user", "content": "Hello from outside the cluster!"},
      ],
  )
  print(response.completion_message.content.text)"""
    print(python_example)
    print()


def main() -> None:
    """Run all steps of the OGX + vLLM Integration lesson."""
    print()
    print("L2-M2.2 -- OGX + vLLM Integration on OpenShift")
    print("=" * 60)
    print()
    print("This lesson walks through integrating OGX with vLLM on")
    print("OpenShift AI. Since it requires a cluster, we focus on")
    print("configuration examples and concepts.")
    print()

    step_1_openshift_route()
    step_2_kserve_vllm()
    step_3_responses_api()
    step_4_streaming()
    step_5_vector_stores()
    step_6_autoscaling()
    step_7_external_access()

    print("=" * 60)
    print("Summary")
    print("=" * 60)
    print()
    print("In this lesson you learned how to:")
    print("  1. Expose OGX via an OpenShift Route with TLS")
    print("  2. Connect OGX to KServe-deployed vLLM models")
    print("  3. Use the Responses API from inside and outside the cluster")
    print("  4. Configure streaming for long-running agent interactions")
    print("  5. Set up persistent vector stores with Qdrant on OpenShift")
    print("  6. Autoscale OGX pods with HPA")
    print("  7. Test external access to OGX through the Route")
    print()
    print("Next: L2-M2.3 -- OGX + Safety on OpenShift")
    print()


if __name__ == "__main__":
    main()
