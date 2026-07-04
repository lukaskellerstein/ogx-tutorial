# L2-M2.1 — OGX Operator Deployment

**Level:** Practitioner
**Duration:** 45 min

## Overview

Learn how to deploy OGX on OpenShift AI using the OGX/Llama Stack Operator. This lesson covers operator installation via the DataScienceCluster component, the OGX custom resource definitions (CRDs), and how to connect OGX to KServe-served vLLM models running in your cluster.

## Prerequisites

- Completed: L2-M1.7 Production Deployment
- Access to an OpenShift AI cluster (or follow along conceptually)
- OpenShift AI (RHOAI) 3.4+ installed
- vLLM model serving configured via KServe with `google/gemma-4-E4B-it`

## Concepts

### The OGX Operator

The OGX/Llama Stack Operator is an OpenShift AI component that automates the deployment and lifecycle management of OGX servers on Kubernetes. Instead of manually managing containers and configuration files, you declare your desired state in a custom resource and the operator handles the rest: creating pods, configuring providers, managing upgrades, and monitoring health.

### DataScienceCluster Integration

OpenShift AI manages its components through the DataScienceCluster custom resource. The OGX operator is enabled by setting the `llamastackoperator` component to `Managed`. This approach means the operator is installed, upgraded, and removed alongside the rest of the OpenShift AI platform.

### Custom Resource Definitions

The operator introduces two CRDs:

- **LlamaStackServer** — the primary resource. Defines an OGX server instance with its distribution, provider configuration (inference, vector store, memory), and scaling parameters.
- **LlamaStackDistribution** — defines a reusable bundle of providers that can be referenced by multiple server instances.

### KServe Integration

On OpenShift AI, models are served via KServe InferenceServices. OGX connects to these models using the `remote::vllm` provider, pointing to the in-cluster service URL. This gives you the full OGX API surface (inference, RAG, agents, tools, safety) on top of KServe-managed model serving.

## Step-by-Step

### Step 1: Verify Prerequisites

Before installing the operator, confirm that your cluster has OpenShift AI installed and that you have a vLLM model serving instance running via KServe.

```bash
oc whoami
oc get datasciencecluster
oc get inferenceservice -A
```

### Step 2: Enable the OGX Operator

Patch the DataScienceCluster to enable the Llama Stack Operator component:

```yaml
apiVersion: datasciencecluster.opendatahub.io/v1
kind: DataScienceCluster
metadata:
  name: default-dsc
spec:
  components:
    llamastackoperator:
      managementState: Managed
```

Apply with `oc apply -f datasciencecluster.yaml` or use `oc patch`.

### Step 3: Verify Operator Installation

Check that the operator pod is running:

```bash
oc get pods -n redhat-ods-operator | grep llamastack
oc get crd | grep llamastack
```

You should see two CRDs: `llamastackservers` and `llamastackdistributions`.

### Step 4: Deploy an OGX Server

Create a LlamaStackServer custom resource that defines your OGX instance:

```yaml
apiVersion: llamastack.opendatahub.io/v1alpha1
kind: LlamaStackServer
metadata:
  name: ogx-server
  namespace: ogx-demo
spec:
  distribution: starter
  replicas: 1
  image: llamastack/distribution-starter:latest
  inference:
    provider: remote::vllm
    config:
      url: http://gemma-4-e4b-it.model-serving.svc.cluster.local/v1
      api_token: ""
  vectorStore:
    provider: remote::qdrant
    config:
      url: http://qdrant:6333
  memory:
    provider: remote::postgres
    config:
      host: postgresql
      port: 5432
      db: ogx
```

### Step 5: Connect to KServe Models

The key integration point is the `inference.config.url` field. It uses the in-cluster DNS name of the KServe InferenceService:

```
http://<inferenceservice-name>.<namespace>.svc.cluster.local/v1
```

This lets OGX reach the vLLM model without leaving the cluster network.

### Step 6: Operator Lifecycle

The operator handles:
- **Health monitoring** — continuously reconciles the desired state
- **Upgrades** — managed by OLM alongside OpenShift AI upgrades
- **Scaling** — patch the `replicas` field to scale OGX horizontally
- **Cleanup** — deleting the LlamaStackServer CR removes all associated resources

## Running the Lesson

```bash
cd tutorial/level_2/M2_ogx_openshift_ai/1_operator_deployment
uv sync
uv run python main.py
```

## Expected Output

The script prints a structured walkthrough of the deployment process:

```
======================================================================
  L2-M2.1 — OGX Operator Deployment
======================================================================

Deploy OGX on OpenShift AI using the OGX/Llama Stack Operator.
This lesson walks through configs and commands — no live cluster required.

======================================================================
  Step 1: Prerequisites Checklist
======================================================================

  [1] OpenShift 4.14+ cluster running
  [2] OpenShift AI (RHOAI) 3.4+ installed via OperatorHub
  [3] DataScienceCluster CR exists (default-dsc)
  ...

======================================================================
  Step 2: Install the OGX Operator via DataScienceCluster
======================================================================

--- DataScienceCluster with Llama Stack Operator enabled ---
apiVersion: datasciencecluster.opendatahub.io/v1
kind: DataScienceCluster
...
```

Each step prints the relevant YAML configurations, `oc` commands, and explanations.

## Key Takeaways

- The OGX operator is enabled as a component of the DataScienceCluster (`llamastackoperator: Managed`)
- Two CRDs control deployment: LlamaStackServer (instance config) and LlamaStackDistribution (provider bundle)
- The `remote::vllm` provider connects to KServe InferenceServices via in-cluster DNS URLs
- The operator manages the full lifecycle: deployment, scaling, upgrades, and cleanup
- No manual container management is needed — declare the desired state and the operator reconciles it

## Next Steps

Continue to **L2-M2.2 — OGX + vLLM Integration on OpenShift**, where you will expose OGX via an OpenShift Route, run agent orchestration on-cluster using the Responses API, and configure autoscaling for production workloads.
