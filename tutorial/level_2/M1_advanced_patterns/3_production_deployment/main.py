"""L2-M1.3 — Production Deployment.

Demonstrates production deployment patterns for OGX:
health checks, containerized architecture, PostgreSQL KVStore,
Qdrant production config, scaling, and OpenShift AI preview.
"""

import httpx
from ogx_client import OgxClient

from configs import COMPOSE_YAML, PG_KVSTORE_YAML, QDRANT_PROD_YAML, OPENSHIFT_CRD


OGX_URL = "http://localhost:8321"
QDRANT_URL = "http://localhost:6333"
MODEL = "ollama/gemma4:e4b"


def check_service(name: str, url: str, timeout: float = 5.0) -> bool:
    """Check whether a service is reachable."""
    try:
        resp = httpx.get(url, timeout=timeout)
        resp.raise_for_status()
        return True
    except Exception:
        return False


def health_checks() -> bool:
    """Step 1: Run health checks against all services."""
    print("=" * 60)
    print("Step 1: Infrastructure Health Checks")
    print("=" * 60)

    services = [
        ("OGX Server", f"{OGX_URL}/v1/models"),
        ("Qdrant", f"{QDRANT_URL}/healthz"),
    ]
    all_ok = True
    for name, url in services:
        ok = check_service(name, url)
        marker = "[+]" if ok else "[-]"
        print(f"  {marker} {name:20s} {'UP' if ok else 'DOWN':6s}  ({url})")
        if not ok:
            all_ok = False

    try:
        resp = httpx.get(f"{OGX_URL}/v1/models", timeout=5)
        data = resp.json()
        n = len(data.get("data", data)) if isinstance(data, dict) else 0
        print(f"  [+] {'Inference Backend':20s} {'UP':6s}  ({n} model(s))")
    except Exception:
        print(f"  [-] {'Inference Backend':20s} {'DOWN':6s}")
        all_ok = False

    print()
    return all_ok


def production_compose() -> None:
    """Step 2: Print a production-grade Podman Compose config."""
    print("=" * 60)
    print("Step 2: Production Podman Compose")
    print("=" * 60)
    print("A production stack runs four services: OGX, vLLM, Qdrant, PostgreSQL.\n")
    print(COMPOSE_YAML)
    print()
    print("Key points:")
    print("  - Every service has a healthcheck and restart policy.")
    print("  - depends_on + service_healthy ensures correct start order.")
    print("  - vLLM uses nvidia.com/gpu=all for GPU pass-through (Linux).")
    print("  - Named volumes persist Qdrant and PostgreSQL data.\n")


def postgresql_kvstore() -> None:
    """Step 3: Explain PostgreSQL as the production KVStore backend."""
    print("=" * 60)
    print("Step 3: PostgreSQL KVStore Configuration")
    print("=" * 60)
    print("SQLite (default) is single-writer and cannot handle concurrent")
    print("access from multiple OGX replicas. PostgreSQL is required for")
    print("production. Configure it in run.yaml:\n")
    print(PG_KVSTORE_YAML)
    print()
    print("Benefits: concurrent access, standard backup tooling (pg_dump),")
    print("streaming replication, horizontal OGX scaling.\n")


def qdrant_production() -> None:
    """Step 4: Show production Qdrant configuration."""
    print("=" * 60)
    print("Step 4: Qdrant Production Configuration")
    print("=" * 60)
    print("inline::qdrant (dev)   -> embedded, temp storage, single process")
    print("remote::qdrant (prod)  -> separate container, persistent volume, gRPC\n")
    print("Production run.yaml:\n")
    print(QDRANT_PROD_YAML)
    print()
    print("Best practices:")
    print("  - HNSW index (default) for fast approximate search.")
    print("  - on_disk: true for collections exceeding available RAM.")
    print("  - replication_factor >= 2 for high availability.")
    print("  - WAL enabled (default) for crash recovery.\n")


def scaling_considerations() -> None:
    """Step 5: Print production scaling guidance."""
    print("=" * 60)
    print("Step 5: Scaling Considerations")
    print("=" * 60)
    print("OGX is stateless (with external PG + Qdrant) and scales horizontally.\n")
    rows = [
        ("Component", "CPU", "RAM", "GPU"),
        ("OGX server", "1", "512 MB", "--"),
        ("vLLM (4B)", "--", "8 GB", "1 x 16 GB"),
        ("Qdrant", "2", "2-4 GB", "--"),
        ("PostgreSQL", "1", "512 MB", "--"),
    ]
    for comp, cpu, ram, gpu in rows:
        print(f"  {comp:16s} {cpu:5s} {ram:10s} {gpu}")
    print()
    print("Scaling pattern:")
    print("  1. Run N OGX replicas behind a load balancer (round-robin).")
    print("  2. All replicas share the same PostgreSQL + Qdrant.")
    print("  3. vLLM is the bottleneck — scale with tensor parallelism")
    print("     or multiple vLLM replicas.\n")


def openshift_preview() -> None:
    """Step 6: Preview OGX deployment on OpenShift AI."""
    print("=" * 60)
    print("Step 6: OpenShift AI — OGX Operator Preview")
    print("=" * 60)
    print("The OGX Operator (ogx-k8s-operator) automates deployment on")
    print("OpenShift AI. Define your stack as a custom resource:\n")
    print(OPENSHIFT_CRD)
    print()
    print("The operator creates Deployments, Services, ConfigMaps, and PVCs.")
    print("It integrates with the NVIDIA GPU Operator for inference scheduling.")
    print("Covered in depth in the OpenShift AI tutorial (L2-M1, L2-M3).\n")


def readiness_checklist() -> None:
    """Step 7: Run health checks and print a readiness checklist."""
    print("=" * 60)
    print("Step 7: Production-Readiness Checklist")
    print("=" * 60)

    checks: list[tuple[str, str, bool]] = []

    checks.append(("OGX server reachable", "Required",
                    check_service("OGX", f"{OGX_URL}/v1/models")))
    checks.append(("Qdrant reachable", "Required",
                    check_service("Qdrant", f"{QDRANT_URL}/healthz")))

    # Quick inference test
    inference_ok = False
    try:
        client = OgxClient(base_url=OGX_URL)
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": "Say OK"}],
            max_tokens=5,
        )
        inference_ok = bool(resp.choices and resp.choices[0].message.content)
    except Exception:
        pass
    checks.append(("Inference backend responds", "Required", inference_ok))
    checks.append(("PostgreSQL KVStore", "Recommended",
                    check_service("PostgreSQL", "http://localhost:5432")))

    print()
    for label, importance, ok in checks:
        marker = "[PASS]" if ok else "[FAIL]"
        print(f"  {marker} {label:35s} ({importance})")

    passed = sum(1 for _, _, ok in checks if ok)
    print(f"\n  Result: {passed}/{len(checks)} checks passed.")
    if passed == len(checks):
        print("  Your local setup mirrors a production topology.")
    else:
        print("  Some services are not running. For production, all")
        print("  checks should pass. See compose.yml above for setup.")
    print()


def main() -> None:
    """Run all production deployment demonstrations."""
    print()
    print("L2-M1.3 — Production Deployment")
    print("=" * 60)
    print()

    if not health_checks():
        print("WARNING: Some services are down. Continuing with")
        print("informational steps (configs and guidance).\n")

    production_compose()
    postgresql_kvstore()
    qdrant_production()
    scaling_considerations()
    openshift_preview()
    readiness_checklist()

    print("=" * 60)
    print("Lesson complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
