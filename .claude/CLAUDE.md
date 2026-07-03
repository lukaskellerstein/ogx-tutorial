# OGX (Open GenAI Stack) Tutorial Project

## Purpose

This is a two-level tutorial for OGX (formerly Llama Stack) — the open-source unified AI runtime providing standardized APIs for inference, RAG, agents, tool calling, and MCP. The tutorial covers OGX independently as a foundation before deploying it on OpenShift AI.

The primary focus is building AI applications: **RAG pipelines, AI agents with tool calling, and MCP integration** — all through OGX's unified API surface.

The tutorial is structured in two progressive levels:
- **Level 1 — Essentials**: Learn every major OGX API (~30-60 min lessons). Inference, RAG, agents, tools, safety.
- **Level 2 — Practitioner**: Advanced patterns, multi-provider config, production deployment (~45 min-1 hour lessons).

The full syllabus lives in `syllabus.md` — always consult it for module structure, lesson topics, deliverables, and time estimates before creating or modifying any lesson.

## Technical Stack

- **OGX**: Latest (v1.1.3+), runs as a Podman container
- **Python**: 3.10+
- **Package manager**: `uv` (every lesson is a standalone `uv` project)
- **Inference backend**: vLLM (primary, Podman container) — Ollama as optional fallback
- **Model**: `google/gemma-4-E4B-it` (4B effective params) via vLLM
- **Vector DB**: Qdrant — via OGX `inline::qdrant` (dev) or `remote::qdrant` (production)
- **Memory / KVStore**: SQLite (dev, default) / PostgreSQL (production)
- **Agent frameworks**: LangChain v1.0+, LangGraph (latest), DeepAgents
- **MCP**: OGX Tool Runtime with MCP integration
- **Container runtime**: Podman (not Docker)

## Project Layout

```
infra/                          # All infrastructure (Podman Compose)
  compose.yml                   #   OGX + vLLM + Qdrant + PostgreSQL
syllabus.md                     # Master syllabus — the source of truth
tutorial/
  level_1/                      # Level 1: Essentials
    M1_fundamentals/
      1_architecture_overview/
      2_installing_running/
    M2_inference_api/
      1_chat_completion/
      2_embeddings/
    M3_rag/
      1_vector_io_api/
      2_rag_application/
    M4_tool_calling_mcp/
      1_tool_runtime_api/
    M5_agents_api/
      1_creating_agents/
      2_agents_with_rag/
    M6_safety_api/
      1_content_moderation/
  level_2/                      # Level 2: Practitioner
    M1_advanced_patterns/
      1_multi_provider_config/
      2_custom_providers/
      3_production_deployment/
```

Each lesson is a self-contained directory:
```
N_lesson_name/
  pyproject.toml        # uv project — declares dependencies
  main.py               # Working code (the lesson implementation)
  README.md             # Lesson guide with explanation, steps, expected output
  .gitignore            # Ignore .venv, __pycache__
```

## Starting Infrastructure

```bash
cd infra
podman compose up -d
```

This starts OGX, vLLM (with gemma-4-E4B-it), Qdrant, and PostgreSQL.

| Service | URL |
|---------|-----|
| OGX API | http://localhost:8321 |
| vLLM API | http://localhost:8000 |
| Qdrant | http://localhost:6333/dashboard |

## Running a Lesson

```bash
cd tutorial/<level>/<module>/<lesson>
uv sync
uv run python main.py
```

## Key Commands

- `podman compose up -d` — start all infrastructure (from `infra/`)
- `podman compose down` — stop all services (preserves data)
- `podman compose down -v` — stop and wipe all data
- `uv init` — scaffold a new lesson project
- `uv add <package>` — add a dependency
- `uv run python main.py` — run the lesson code

## Rules

Modular instructions are in `.claude/rules/`. Read them — they cover:
- `tutorial-structure.md` — two-level layout and file conventions
- `coding-standards.md` — Python style for tutorial code
- `ogx-patterns.md` — OGX APIs and patterns to use
- `references.md` — where to find source code, docs, and code samples
- `lesson-content.md` — how to write README.md guides
