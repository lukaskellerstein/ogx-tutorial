"""L2-M2.3 — OGX + Safety on OpenShift.

Demonstrates how to integrate OGX safety shields on OpenShift AI:
NeMo Guardrails, TrustyAI, Llama Guard, and the Guardrails Orchestrator.
This is a conceptual/educational lesson — no live cluster required.
"""

from configs import (
    LLAMA_GUARD_KSERVE_YAML,
    LLAMA_GUARD_PROVIDER_YAML,
    NEMO_DEPLOYMENT_YAML,
    NEMO_PROVIDER_YAML,
    ORCHESTRATOR_PROVIDER_YAML,
    SHIELD_CATEGORIES_YAML,
    TRUSTYAI_PROVIDER_YAML,
)


def safety_architecture() -> None:
    """Step 1: Print the safety pipeline architecture on OpenShift."""
    print("=" * 60)
    print("Step 1: Safety Architecture on OpenShift")
    print("=" * 60)
    print()
    print("On OpenShift AI, safety is a pipeline of shields that")
    print("inspect every request and response:\n")
    lines = [
        "  User Request",
        "       |",
        "       v",
        "  +-----------------------------+",
        "  | Guardrails Orchestrator     |",
        "  +-----------------------------+",
        "       |",
        "       v",
        "  +-----------------------------+",
        "  | Input Shield                |",
        "  | (NeMo / Llama Guard / PII)  |",
        "  +-----------------------------+",
        "       |  (if safe)",
        "       v",
        "  +-----------------------------+",
        "  | OGX Inference (vLLM)       |",
        "  +-----------------------------+",
        "       |",
        "       v",
        "  +-----------------------------+",
        "  | Output Shield               |",
        "  | (NeMo / Llama Guard / PII)  |",
        "  +-----------------------------+",
        "       |  (if safe)",
        "       v",
        "  Response to User",
    ]
    print("\n".join(lines))
    print("\nIf any shield flags the content, a safety violation")
    print("message is returned instead of the model response.\n")


def nemo_guardrails_config() -> None:
    """Step 2: Print NeMo Guardrails deployment configuration."""
    print("=" * 60)
    print("Step 2: NeMo Guardrails Integration")
    print("=" * 60)
    print()
    print("NVIDIA NeMo Guardrails runs as a separate pod on OpenShift.")
    print("It provides programmable safety rails with dialog management,")
    print("topic control, and content filtering.\n")
    print("Deployment configuration (OpenShift):\n")
    print(NEMO_DEPLOYMENT_YAML)
    print("\nOGX provider configuration (run.yaml):\n")
    print(NEMO_PROVIDER_YAML)
    print()
    print("Key features:")
    print("  - Programmable dialog rails (allow/deny topic lists)")
    print("  - Content safety classification")
    print("  - PII detection and redaction")
    print("  - Custom rails via Colang scripting language\n")


def trustyai_config() -> None:
    """Step 3: Print TrustyAI integration configuration."""
    print("=" * 60)
    print("Step 3: TrustyAI Integration")
    print("=" * 60)
    print()
    print("TrustyAI is an OpenShift AI component for bias detection,")
    print("fairness monitoring, and model explainability.\n")
    print("TrustyAI detector configuration (run.yaml):\n")
    print(TRUSTYAI_PROVIDER_YAML)
    print()
    checks = [
        ("Bias Detection", "Flags responses with demographic bias"),
        ("Fairness Check", "Ensures equitable treatment across groups"),
        ("Explainability", "Provides reasoning transparency scores"),
        ("Drift Monitoring", "Detects model behavior changes over time"),
    ]
    for name, desc in checks:
        print(f"  - {name:20s} {desc}")
    print("\nTrustyAI is pre-installed on OpenShift AI and accessible")
    print("via in-cluster service URLs. No extra deployment needed.\n")


def guardrails_orchestrator_config() -> None:
    """Step 4: Print Guardrails Orchestrator configuration."""
    print("=" * 60)
    print("Step 4: Guardrails Orchestrator")
    print("=" * 60)
    print()
    print("The Guardrails Orchestrator routes every request through")
    print("configured safety detectors before forwarding to inference.\n")
    print("OGX provider configuration (run.yaml):\n")
    print(ORCHESTRATOR_PROVIDER_YAML)
    print("\nArchitecture on OpenShift:\n")
    print("  OGX Route (external)")
    print("       |")
    print("       v")
    print("  OGX Service --> Guardrails Orchestrator Service")
    print("                       |           |")
    print("                       v           v")
    print("                  NeMo Rails   Llama Guard")
    print("                       |           |")
    print("                       +-----------+")
    print("                             |")
    print("                             v")
    print("                     Verdict: SAFE / BLOCKED")
    print("\nThe orchestrator aggregates verdicts from all detectors.")
    print("If ANY detector flags the content, the request is blocked.\n")


def llama_guard_config() -> None:
    """Step 5: Print Llama Guard configuration for content moderation."""
    print("=" * 60)
    print("Step 5: Llama Guard via OGX")
    print("=" * 60)
    print()
    print("Llama Guard is a fine-tuned model for content classification.")
    print("It runs as a separate KServe endpoint on OpenShift.\n")
    print("OGX safety provider configuration (run.yaml):\n")
    print(LLAMA_GUARD_PROVIDER_YAML)
    print("\nOpenShift deployment (KServe InferenceService):\n")
    print(LLAMA_GUARD_KSERVE_YAML)
    print("\nLlama Guard runs on a dedicated GPU node and processes")
    print("safety checks in parallel with the main inference model.\n")


def end_to_end_flow() -> None:
    """Step 6: Print the complete end-to-end safety request lifecycle."""
    print("=" * 60)
    print("Step 6: End-to-End Safety Flow")
    print("=" * 60)
    print()
    steps = [
        ("1", "Request arrives", "User sends request to OGX Route"),
        ("2", "Input shield", "Guardrails Orchestrator checks input"),
        ("3", "Content check", "Llama Guard classifies content category"),
        ("4", "PII scan", "NeMo Guardrails scans for PII data"),
        ("5", "Verdict: input", "All detectors return SAFE or BLOCKED"),
        ("6", "Inference", "If SAFE: forward to vLLM via OGX"),
        ("7", "Output shield", "Response checked by output detectors"),
        ("8", "Bias check", "TrustyAI checks for bias/fairness"),
        ("9", "Verdict: output", "All detectors return SAFE or BLOCKED"),
        ("10", "Response", "If SAFE: return to user via Route"),
    ]
    for num, phase, description in steps:
        print(f"  [{num:>2s}] {phase:20s} -> {description}")
    print("\nBlocked request example:\n")
    print("  User: 'How do I hack into a bank account?'")
    print("  [Input Shield] Llama Guard -> Category: S2 (illegal activity)")
    print("  [Verdict] BLOCKED")
    print("  Response: 'I cannot help with that request.'")
    print("\nSafe request example:\n")
    print("  User: 'Explain how encryption protects bank accounts.'")
    print("  [Input Shield] Llama Guard -> Category: SAFE")
    print("  [Inference] vLLM generates response about encryption")
    print("  [Output Shield] Llama Guard -> Category: SAFE")
    print("  Response: 'Encryption protects bank accounts by ...'\n")


def safety_categories() -> None:
    """Step 7: Print safety categories that shields can detect."""
    print("=" * 60)
    print("Step 7: Safety Categories")
    print("=" * 60)
    print()
    print("Llama Guard classifies content using the MLCommons AI")
    print("Safety taxonomy (13 categories):\n")
    categories = [
        ("S1", "Violent Crimes", "Physical violence, weapons, terrorism"),
        ("S2", "Non-Violent Crimes", "Fraud, hacking, illegal activity"),
        ("S3", "Sex-Related Crimes", "Exploitation, trafficking"),
        ("S4", "Child Safety", "Content involving minors"),
        ("S5", "Defamation", "False statements, libel"),
        ("S6", "Specialized Advice", "Unqualified medical/legal/financial"),
        ("S7", "Privacy", "PII exposure, doxxing, surveillance"),
        ("S8", "Intellectual Property", "Copyright violation, plagiarism"),
        ("S9", "Indiscriminate Weapons", "Chemical, biological, nuclear"),
        ("S10", "Hate Speech", "Discrimination, slurs, bias"),
        ("S11", "Self-Harm", "Suicide, eating disorders"),
        ("S12", "Sexual Content", "Explicit material"),
        ("S13", "Elections", "Voter manipulation, misinformation"),
    ]
    print(f"  {'Code':<6s} {'Category':<26s} {'Description'}")
    print(f"  {'----':<6s} {'--------':<26s} {'-----------'}")
    for code, name, desc in categories:
        print(f"  {code:<6s} {name:<26s} {desc}")
    print(f"\nSelective category configuration:\n")
    print(SHIELD_CATEGORIES_YAML)
    print("\nFewer categories means faster checks. Enable only those")
    print("relevant to your application.\n")


def main() -> None:
    """Run all safety-on-OpenShift demonstrations."""
    print()
    print("L2-M2.3 — OGX + Safety on OpenShift")
    print("=" * 60)
    print()
    print("This lesson covers production safety patterns for OGX on")
    print("OpenShift AI. All examples are configuration-based — no")
    print("live cluster is required to follow along.\n")

    safety_architecture()
    nemo_guardrails_config()
    trustyai_config()
    guardrails_orchestrator_config()
    llama_guard_config()
    end_to_end_flow()
    safety_categories()

    print("=" * 60)
    print("Lesson complete!")
    print("=" * 60)
    print()
    print("Congratulations — you have completed the OGX on OpenShift AI")
    print("module and the entire OGX tutorial course!")
    print()


if __name__ == "__main__":
    main()
