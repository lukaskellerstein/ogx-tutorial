"""Configuration text constants for L2-M2.3.

Keeps the large YAML/text blocks out of main.py so it stays readable.
"""

NEMO_DEPLOYMENT_YAML = """\
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nemo-guardrails
  namespace: ogx-safety
spec:
  replicas: 2
  selector:
    matchLabels:
      app: nemo-guardrails
  template:
    metadata:
      labels:
        app: nemo-guardrails
    spec:
      containers:
        - name: guardrails
          image: nvcr.io/nvidia/nemo-guardrails:latest
          ports:
            - containerPort: 8090
          env:
            - name: GUARDRAILS_CONFIG_DIR
              value: /config
          volumeMounts:
            - name: config
              mountPath: /config
      volumes:
        - name: config
          configMap:
            name: guardrails-config"""

NEMO_PROVIDER_YAML = """\
providers:
  safety:
    - provider_id: nemo-guardrails
      provider_type: remote::nemo-guardrails
      config:
        url: http://nemo-guardrails.ogx-safety.svc:8090
        rails:
          - content-safety
          - topic-control
          - pii-detection"""

TRUSTYAI_PROVIDER_YAML = """\
providers:
  safety:
    - provider_id: trustyai
      provider_type: remote::trustyai
      config:
        url: http://trustyai.redhat-ods-applications.svc:8080
        detectors:
          - bias-detection
          - fairness-check
          - explainability"""

ORCHESTRATOR_PROVIDER_YAML = """\
providers:
  safety:
    - provider_id: guardrails
      provider_type: remote::guardrails-orchestrator
      config:
        url: http://guardrails-orchestrator.safety.svc:8080
        detectors:
          - content-safety
          - pii-detection
          - toxicity
        input_shields:
          - content-safety
          - pii-detection
        output_shields:
          - toxicity
          - content-safety"""

LLAMA_GUARD_PROVIDER_YAML = """\
providers:
  safety:
    - provider_id: llama-guard
      provider_type: inline::llama-guard
      config:
        model: meta-llama/Llama-Guard-3-8B

  inference:
    - provider_id: llama-guard-inference
      provider_type: remote::vllm
      config:
        url: http://llama-guard-vllm.models.svc:8000/v1
        model: meta-llama/Llama-Guard-3-8B"""

LLAMA_GUARD_KSERVE_YAML = """\
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: llama-guard
  namespace: models
spec:
  predictor:
    model:
      modelFormat:
        name: vllm
      runtime: vllm-runtime
      storageUri: s3://models/Llama-Guard-3-8B
      resources:
        limits:
          nvidia.com/gpu: 1"""

SHIELD_CATEGORIES_YAML = """\
shields:
  - shield_id: content-filter
    provider_id: llama-guard
    categories:
      - S1   # Violent Crimes
      - S2   # Non-Violent Crimes
      - S7   # Privacy / PII
      - S10  # Hate Speech
      - S11  # Self-Harm"""
