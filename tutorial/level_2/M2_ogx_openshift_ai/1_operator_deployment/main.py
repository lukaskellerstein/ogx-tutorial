"""
L2-M2.1 — OGX Operator Deployment

Deploy OGX on OpenShift AI using the OGX/Llama Stack Operator.

This lesson is conceptual — it prints configuration examples and explains
the deployment workflow. No live OpenShift cluster is required.
"""

import textwrap


def print_header(title: str) -> None:
    """Print a formatted section header."""
    print()
    print("=" * 70)
    print(f"  {title}")
    print("=" * 70)
    print()


def print_yaml(label: str, yaml_text: str) -> None:
    """Print a labeled YAML block."""
    print(f"--- {label} ---")
    print(textwrap.dedent(yaml_text).strip())
    print()


def step_prerequisites() -> None:
    """Step 1: Prerequisites checklist."""
    print_header("Step 1: Prerequisites Checklist")

    checklist = [
        "OpenShift 4.14+ cluster running",
        "OpenShift AI (RHOAI) 3.4+ installed via OperatorHub",
        "DataScienceCluster CR exists (default-dsc)",
        "vLLM model serving configured via KServe (ServingRuntime + InferenceService)",
        "Model google/gemma-4-E4B-it deployed and reachable in-cluster",
        "oc CLI authenticated to the cluster (oc login)",
        "Qdrant deployed in-cluster (optional, for vector store)",
        "PostgreSQL deployed in-cluster (optional, for KVStore memory)",
    ]

    for i, item in enumerate(checklist, 1):
        print(f"  [{i}] {item}")

    print()
    print("Verify your cluster access:")
    print("  $ oc whoami")
    print("  $ oc get datasciencecluster")
    print()


def step_operator_installation() -> None:
    """Step 2: Install the OGX Operator via DataScienceCluster."""
    print_header("Step 2: Install the OGX Operator via DataScienceCluster")

    print("The OGX/Llama Stack Operator is a component of OpenShift AI.")
    print("Enable it by patching the DataScienceCluster custom resource.")
    print()

    print_yaml(
        "DataScienceCluster with Llama Stack Operator enabled",
        """
        apiVersion: datasciencecluster.opendatahub.io/v1
        kind: DataScienceCluster
        metadata:
          name: default-dsc
        spec:
          components:
            llamastackoperator:
              managementState: Managed
        """,
    )

    print("Apply this configuration:")
    print("  $ oc apply -f datasciencecluster.yaml")
    print()
    print("Or patch the existing DSC:")
    print(
        "  $ oc patch datasciencecluster default-dsc --type merge "
        "-p '{\"spec\":{\"components\":{\"llamastackoperator\":"
        "{\"managementState\":\"Managed\"}}}}'"
    )
    print()
    print("Verify the operator pod is running:")
    print("  $ oc get pods -n redhat-ods-operator | grep llamastack")
    print()


def step_crds() -> None:
    """Step 3: OGX Custom Resource Definitions."""
    print_header("Step 3: OGX Custom Resource Definitions (CRDs)")

    print("The operator installs two CRDs:")
    print()
    print("  1. LlamaStackServer  — defines the OGX server instance")
    print("     - Which distribution to run (starter, remote-vllm, etc.)")
    print("     - Replica count and resource limits")
    print("     - Inference, vector store, and safety provider config")
    print()
    print("  2. LlamaStackDistribution — defines a provider bundle")
    print("     - Groups providers for inference, memory, safety, tools")
    print("     - Reusable across multiple LlamaStackServer instances")
    print()

    print("List installed CRDs:")
    print("  $ oc get crd | grep llamastack")
    print()
    print("Expected output:")
    print("  llamastackdistributions.llamastack.opendatahub.io")
    print("  llamastackservers.llamastack.opendatahub.io")
    print()


def step_server_crd() -> None:
    """Step 4: Deploy an OGX server via LlamaStackServer CRD."""
    print_header("Step 4: Deploy OGX Server via LlamaStackServer CRD")

    print_yaml(
        "LlamaStackServer custom resource",
        """
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
              url: http://vllm-service:8000/v1
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
        """,
    )

    print("Apply the server CRD:")
    print("  $ oc apply -f llamastackserver.yaml")
    print()
    print("Check the OGX server pod status:")
    print("  $ oc get pods -n ogx-demo -l app=ogx-server")
    print()
    print("Check the OGX server logs:")
    print("  $ oc logs -n ogx-demo -l app=ogx-server --tail=50")
    print()


def step_kserve_integration() -> None:
    """Step 5: Connecting to KServe-served vLLM models."""
    print_header("Step 5: Connecting to KServe-Served vLLM Models")

    print("On OpenShift AI, vLLM models are served via KServe.")
    print("The OGX remote::vllm provider points to the in-cluster")
    print("KServe InferenceService URL.")
    print()

    print_yaml(
        "KServe InferenceService for vLLM (reference)",
        """
        apiVersion: serving.kserve.io/v1beta1
        kind: InferenceService
        metadata:
          name: gemma-4-e4b-it
          namespace: model-serving
        spec:
          predictor:
            model:
              modelFormat:
                name: vLLM
              runtime: vllm-runtime
              storageUri: s3://models/google/gemma-4-E4B-it
              resources:
                limits:
                  nvidia.com/gpu: 1
                requests:
                  memory: 8Gi
        """,
    )

    print("The in-cluster URL for this InferenceService is:")
    print(
        "  http://gemma-4-e4b-it.model-serving.svc.cluster.local/v1"
    )
    print()
    print("Use this URL in the LlamaStackServer spec:")
    print()

    print_yaml(
        "inference provider pointing to KServe",
        """
        spec:
          inference:
            provider: remote::vllm
            config:
              url: http://gemma-4-e4b-it.model-serving.svc.cluster.local/v1
              api_token: ""
        """,
    )

    print("Verify OGX can reach the model:")
    print(
        "  $ oc exec -n ogx-demo deploy/ogx-server -- "
        "curl -s http://gemma-4-e4b-it.model-serving.svc.cluster.local/v1/models"
    )
    print()


def step_operator_lifecycle() -> None:
    """Step 6: Operator lifecycle management."""
    print_header("Step 6: Operator Lifecycle Management")

    print("Health monitoring:")
    print("  $ oc get llamastackserver ogx-server -n ogx-demo")
    print("  $ oc describe llamastackserver ogx-server -n ogx-demo")
    print()

    print("Check operator status and conditions:")
    print("  $ oc get pods -n redhat-ods-operator | grep llamastack")
    print("  $ oc logs -n redhat-ods-operator -l app=llamastack-operator --tail=20")
    print()

    print("Upgrades:")
    print("  - The operator is managed by OLM (Operator Lifecycle Manager)")
    print("  - Upgrading OpenShift AI upgrades the OGX operator automatically")
    print("  - CRD changes are handled by the operator during upgrades")
    print("  - Existing LlamaStackServer instances are reconciled after upgrade")
    print()

    print("Scaling the OGX server:")
    print("  $ oc patch llamastackserver ogx-server -n ogx-demo \\")
    print("      --type merge -p '{\"spec\":{\"replicas\":3}}'")
    print()

    print("Deleting the OGX server:")
    print("  $ oc delete llamastackserver ogx-server -n ogx-demo")
    print()

    print("Disabling the operator component:")
    print(
        "  $ oc patch datasciencecluster default-dsc --type merge "
        "-p '{\"spec\":{\"components\":{\"llamastackoperator\":"
        "{\"managementState\":\"Removed\"}}}}'"
    )
    print()


def step_summary() -> None:
    """Print a summary of the deployment workflow."""
    print_header("Deployment Workflow Summary")

    steps = [
        "Ensure prerequisites: OpenShift AI, KServe, vLLM model serving",
        "Enable llamastackoperator in DataScienceCluster (Managed)",
        "Verify operator pod is running in redhat-ods-operator namespace",
        "Create a LlamaStackServer CR with distribution and provider config",
        "Point remote::vllm to the KServe InferenceService in-cluster URL",
        "Optionally configure remote::qdrant and remote::postgres backends",
        "Verify OGX server pod is running and healthy",
        "Test: call OGX APIs from within the cluster or via an OpenShift Route",
    ]

    for i, step in enumerate(steps, 1):
        print(f"  {i}. {step}")

    print()
    print("Next lesson: L2-M2.2 — OGX + vLLM Integration on OpenShift")
    print("  You will expose the OGX server via an OpenShift Route,")
    print("  run agent orchestration on-cluster, and configure autoscaling.")
    print()


def main() -> None:
    """Run the OGX Operator Deployment lesson."""
    print_header("L2-M2.1 — OGX Operator Deployment")
    print("Deploy OGX on OpenShift AI using the OGX/Llama Stack Operator.")
    print("This lesson walks through configs and commands — no live cluster required.")

    step_prerequisites()
    step_operator_installation()
    step_crds()
    step_server_crd()
    step_kserve_integration()
    step_operator_lifecycle()
    step_summary()


if __name__ == "__main__":
    main()
