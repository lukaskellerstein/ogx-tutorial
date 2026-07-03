"""Production configuration text constants for L2-M1.3.

Keeps the large YAML/text blocks out of main.py so it stays readable.
"""

COMPOSE_YAML = """\
services:
  ogx:
    image: ogx-ai/ogx:latest
    ports: ["8321:8321"]
    environment:
      - VLLM_URL=http://vllm:8000
      - PGHOST=postgres
      - PGUSER=ogx
      - PGPASSWORD=ogx-secret
      - PGDATABASE=ogx
    depends_on:
      vllm:    { condition: service_healthy }
      postgres: { condition: service_healthy }
      qdrant:  { condition: service_healthy }
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8321/v1/models || exit 1"]
      interval: 10s
      timeout: 5s
      retries: 12
      start_period: 30s
    restart: unless-stopped

  vllm:
    image: vllm/vllm-openai:latest
    command: --model google/gemma-4-E4B-it --max-model-len 4096
    ports: ["8000:8000"]
    devices: [nvidia.com/gpu=all]
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:8000/health || exit 1"]
      interval: 15s
      timeout: 5s
      retries: 20
      start_period: 120s
    restart: unless-stopped

  qdrant:
    image: docker.io/qdrant/qdrant:latest
    ports: ["6333:6333", "6334:6334"]
    volumes: [qdrant_data:/qdrant/storage]
    healthcheck:
      test: ["CMD-SHELL", "curl -sf http://localhost:6333/healthz || exit 1"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

  postgres:
    image: docker.io/postgres:16-alpine
    environment:
      POSTGRES_USER: ogx
      POSTGRES_PASSWORD: ogx-secret
      POSTGRES_DB: ogx
    ports: ["5432:5432"]
    volumes: [pg_data:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ogx"]
      interval: 5s
      timeout: 3s
      retries: 10
    restart: unless-stopped

volumes:
  qdrant_data:
  pg_data:"""

PG_KVSTORE_YAML = """\
providers:
  kvstore:
    - provider_id: postgres
      provider_type: remote::postgres
      config:
        host: postgres
        port: 5432
        user: ogx
        password: ogx-secret
        database: ogx"""

QDRANT_PROD_YAML = """\
providers:
  vector_io:
    - provider_id: qdrant
      provider_type: remote::qdrant
      config:
        url: http://qdrant:6333"""

OPENSHIFT_CRD = """\
apiVersion: ogx.ai/v1alpha1
kind: OGXStack
metadata:
  name: my-ogx-stack
spec:
  distribution: remote-vllm
  model: google/gemma-4-E4B-it
  providers:
    vector_io: remote::qdrant
    kvstore: remote::postgres"""
