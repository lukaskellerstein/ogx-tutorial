# L2-M2.3 — OGX + Safety on OpenShift

**Level:** Practitioner
**Duration:** 45 min

## Overview

Integrate production safety shields with OGX on OpenShift AI. This lesson covers the full safety pipeline: NeMo Guardrails for programmable dialog rails, TrustyAI for bias and fairness checks, Llama Guard for content classification, and the Guardrails Orchestrator that ties them together. You will learn how to configure each component and understand the end-to-end request lifecycle with safety checks.

## Prerequisites

- Completed: L2-M2.2 OGX + vLLM Integration on OpenShift
- Familiarity with L1-M6.1 Content Moderation (OGX safety API basics)

## Concepts

### Safety Pipeline on OpenShift

Production safety is not a single check — it is a pipeline of shields that inspect both input and output. On OpenShift AI, the Guardrails Orchestrator acts as a central gateway, routing requests through multiple safety detectors before allowing inference. This defense-in-depth approach catches different types of harmful content at different stages.

### NeMo Guardrails

NVIDIA NeMo Guardrails provides programmable safety rails with dialog management, topic control, and content filtering. It runs as a separate deployment on OpenShift and connects to OGX as a safety provider. Rails are configured using the Colang scripting language, allowing fine-grained control over what topics the AI can and cannot discuss.

### TrustyAI

TrustyAI is an OpenShift AI component focused on responsible AI: bias detection, fairness monitoring, and model explainability. Unlike content filters that block harmful requests, TrustyAI monitors model outputs for systemic issues like demographic bias or fairness drift over time.

### Llama Guard

Llama Guard is a fine-tuned LLM that classifies content into safety categories based on the MLCommons AI Safety taxonomy. It runs as a separate inference endpoint (via vLLM on KServe) and acts as both input and output shield. Each piece of content receives a category label (S1-S13) or SAFE.

### Guardrails Orchestrator

The Guardrails Orchestrator is the central safety gateway. It sits between OGX and its safety providers, aggregating verdicts from all configured detectors. If any detector flags content as unsafe, the request is blocked. This pattern ensures that no single point of failure can bypass safety checks.

## Step-by-Step

### Step 1: Safety Architecture

Understand the safety pipeline flow on OpenShift. Every request passes through: Guardrails Orchestrator, Input Shield (content classification, PII scan), OGX Inference, Output Shield (toxicity, bias check), and finally back to the user. The lesson prints a visual diagram of this flow.

### Step 2: NeMo Guardrails Integration

Deploy NeMo Guardrails as a separate pod on OpenShift and configure it as an OGX safety provider. The deployment uses a ConfigMap for guardrails configuration and connects to OGX via an in-cluster service URL:

```yaml
providers:
  safety:
    - provider_id: nemo-guardrails
      provider_type: remote::nemo-guardrails
      config:
        url: http://nemo-guardrails.ogx-safety.svc:8090
```

### Step 3: TrustyAI Integration

Connect OGX to TrustyAI detectors for bias and fairness monitoring. TrustyAI is pre-installed on OpenShift AI and accessible via in-cluster service URLs:

```yaml
providers:
  safety:
    - provider_id: trustyai
      provider_type: remote::trustyai
      config:
        url: http://trustyai.redhat-ods-applications.svc:8080
```

### Step 4: Guardrails Orchestrator

Configure the Guardrails Orchestrator as the central safety gateway. It aggregates verdicts from all detectors and blocks requests if any detector flags the content:

```yaml
providers:
  safety:
    - provider_id: guardrails
      provider_type: remote::guardrails-orchestrator
      config:
        url: http://guardrails-orchestrator.safety.svc:8080
```

### Step 5: Llama Guard via OGX

Deploy Llama Guard as a KServe InferenceService and configure it as an OGX safety provider. Llama Guard classifies content into 13 safety categories:

```yaml
providers:
  safety:
    - provider_id: llama-guard
      provider_type: inline::llama-guard
      config:
        model: meta-llama/Llama-Guard-3-8B
```

### Step 6: End-to-End Safety Flow

Walk through the complete request lifecycle: from the user request arriving at the OGX Route, through input shields, inference, output shields, and back to the user. The lesson shows examples of both blocked and safe requests.

### Step 7: Safety Categories

Review the 13 safety categories (S1-S13) based on the MLCommons AI Safety taxonomy. Learn how to configure which categories your shields enforce, balancing coverage with check latency.

## Running the Lesson

```bash
cd tutorial/level_2/M2_ogx_openshift_ai/3_safety_openshift
uv sync
uv run python main.py
```

## Expected Output

```
L2-M2.3 — OGX + Safety on OpenShift
============================================================

This lesson covers production safety patterns for OGX on
OpenShift AI. All examples are configuration-based — no
live cluster is required to follow along.

============================================================
Step 1: Safety Architecture on OpenShift
============================================================

  User Request
       |
       v
  +-----------------------------+
  | Guardrails Orchestrator     |
  +-----------------------------+
       |
       v
  +-----------------------------+
  | Input Shield                |
  ...

============================================================
Step 2: NeMo Guardrails Integration
============================================================
  ...deployment and provider configuration...

============================================================
Step 3: TrustyAI Integration
============================================================
  ...TrustyAI detector configuration...

============================================================
Step 4: Guardrails Orchestrator
============================================================
  ...orchestrator configuration and architecture...

============================================================
Step 5: Llama Guard via OGX
============================================================
  ...Llama Guard provider and KServe deployment...

============================================================
Step 6: End-to-End Safety Flow
============================================================
  [ 1] Request arrives       -> User sends request to OGX Route
  [ 2] Input shield          -> Guardrails Orchestrator checks input
  ...
  [10] Response              -> If SAFE: return to user via Route

============================================================
Step 7: Safety Categories
============================================================
  Code   Category                   Description
  ----   --------                   -----------
  S1     Violent Crimes             Physical violence, weapons, terrorism
  S2     Non-Violent Crimes         Fraud, hacking, illegal activity
  ...

============================================================
Lesson complete!
============================================================

Congratulations — you have completed the OGX on OpenShift AI
module and the entire OGX tutorial course!
```

## Key Takeaways

- Production safety on OpenShift AI uses a pipeline of shields: input shield, inference, output shield — orchestrated by the Guardrails Orchestrator.
- NeMo Guardrails provides programmable dialog rails with topic control and PII detection, deployed as a separate pod.
- TrustyAI monitors for bias, fairness, and explainability — it is pre-installed on OpenShift AI.
- Llama Guard classifies content into 13 safety categories (MLCommons taxonomy) and runs as a KServe InferenceService.
- The Guardrails Orchestrator aggregates verdicts from all detectors — if any detector flags content, the request is blocked.
- Safety categories can be selectively enabled per shield to balance coverage with check latency.

## Next Steps

Congratulations — you have completed the entire OGX tutorial course! Here is what to explore next:

- **OGX documentation**: https://ogx-ai.github.io/docs for the full API reference and provider catalog.
- **OGX Operator**: https://github.com/ogx-ai/ogx-k8s-operator for Kubernetes deployment automation.
- **NeMo Guardrails**: https://docs.nvidia.com/nemo/guardrails/ for advanced programmable rails.
- **TrustyAI**: https://www.trustyai.io/ for bias detection and responsible AI tooling.
- **OpenShift AI docs**: https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/ for the full platform reference.
