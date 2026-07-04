# OGX Tutorial

[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![OGX v1.1.3+](https://img.shields.io/badge/OGX-v1.1.3%2B-orange.svg)](https://github.com/ogx-ai/ogx)
[![uv](https://img.shields.io/badge/uv-package%20manager-blueviolet.svg)](https://docs.astral.sh/uv/)

> A hands-on, two-level tutorial for building AI applications with OGX (Open GenAI Stack) -- inference, RAG, agents, tool calling, MCP, and safety through a single unified API.

OGX is an open-source AI runtime that provides standardized, OpenAI-compatible APIs across 23+ inference providers. This tutorial teaches you to build real AI applications -- RAG pipelines, tool-calling agents, and MCP integrations -- progressing from API essentials to production deployment on OpenShift AI.

## Features

- **21 self-contained lessons** -- each is a standalone `uv` project you can run independently
- **Two progressive levels** -- Essentials (11 lessons) and Practitioner (10 lessons)
- **Full RAG pipeline** -- document ingestion, vector search with Qdrant, retrieval-augmented generation
- **Agent development** -- OGX Responses API agents, tool calling, MCP integration
- **Production patterns** -- multi-provider config, telemetry, evaluation, reranking, containerized deployment
- **OpenShift AI deployment** -- OGX Operator, vLLM integration, safety on Kubernetes
- **Infrastructure included** -- Podman Compose brings up OGX + Qdrant in one command

## Architecture

```mermaid
graph TD
    subgraph Tutorial["Tutorial Lessons (Python + uv)"]
        L1["Level 1: Essentials<br/>11 lessons"]
        L2["Level 2: Practitioner<br/>10 lessons"]
    end

    subgraph OGX["OGX Server :8321"]
        CHAT["/v1/chat/completions"]
        EMB["/v1/embeddings"]
        RESP["/v1/responses"]
        VS["/v1/vector_stores"]
        TOOLS["/v1/admin/tools"]
        SAF["/v1/safety"]
    end

    subgraph Infra["Infrastructure"]
        OL["Ollama :11434<br/>gemma4:e4b"]
        QD["Qdrant :6333"]
    end

    L1 --> OGX
    L2 --> OGX
    CHAT --> OL
    EMB --> OL
    RESP --> CHAT
    RESP --> VS
    RESP --> TOOLS
    VS --> QD
```

## Quick Start

### Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) package manager
- [Podman](https://podman.io/) (with Compose)
- [Ollama](https://ollama.ai/) installed on the host
- ~4 GB disk for the Gemma 4 model

### 1. Clone and pull the model

```bash
git clone https://github.com/lukaskellerstein/ogx-tutorial.git
cd ogx-tutorial
ollama pull gemma4:e4b
```

### 2. Start infrastructure

```bash
cd infra
podman compose up -d
```

This starts the OGX server and Qdrant. Ollama runs natively on the host. OGX takes 30-60 seconds to initialize.

### 3. Verify the setup

```bash
cd infra
uv sync
uv run python main.py
```

### 4. Run your first lesson

```bash
cd tutorial/level_1/M1_fundamentals/1_architecture_overview
uv sync
uv run python main.py
```

## Usage

Every lesson follows the same pattern:

```bash
cd tutorial/<level>/<module>/<lesson>
uv sync
uv run python main.py
```

Each lesson's `main.py` connects to the OGX server at `http://localhost:8321` and prints step-by-step output to the console. The accompanying `README.md` in each lesson directory explains the concepts and expected output.

## Configuration

| Service | URL | Purpose |
|---------|-----|---------|
| OGX API | `http://localhost:8321` | Unified AI runtime |
| Ollama | `http://localhost:11434` | Inference backend (host-native) |
| Qdrant | `http://localhost:6333` | Vector database |
| Qdrant Dashboard | `http://localhost:6333/dashboard` | Vector DB UI |

Infrastructure is configured via `infra/.env`:

| Variable | Description | Default |
|----------|-------------|---------|
| `OGX_IMAGE` | OGX container image | `ogxai/distribution-starter` |
| `QDRANT_VERSION` | Qdrant image tag | `latest` |
| `INFERENCE_MODEL` | Model for inference | `gemma4:e4b` |
| `OLLAMA_URL` | Ollama endpoint for OGX | `http://host.containers.internal:11434/v1` |

## Curriculum

### Level 1 -- Essentials (~9-10 hours)

| Module | Lessons | Topics |
|--------|---------|--------|
| **M1: Fundamentals** | Architecture Overview, Installing & Running | OGX API surface, distributions, client setup |
| **M2: Inference API** | Chat Completion, Embeddings | Chat/text completions, streaming, embedding generation |
| **M3: RAG** | Vector IO API, RAG Application | Qdrant vector store, document ingestion, end-to-end RAG |
| **M4: Tool Calling & MCP** | Tool Runtime API | Custom tools, MCP server integration, built-in tools |
| **M5: Agents API** | Creating Agents, Agents with RAG | Responses API agents, multi-turn, RAG-powered agents |
| **M6: Safety API** | Content Moderation | Input/output shields, safety detectors |
| **M7: Additional APIs** | Files, Batches, Conversations, Prompts | File management, batch processing, prompt templates |

### Level 2 -- Practitioner (~7-8 hours)

| Module | Lessons | Topics |
|--------|---------|--------|
| **M1: Advanced Patterns** | Multi-Provider Config, Custom Providers, Telemetry, Evaluation, Reranking, File Processors, Production Deployment | Provider routing, custom extensions, OpenTelemetry, RAG benchmarks, reranking, document ingestion, Podman production stack |
| **M2: OGX on OpenShift AI** | Operator Deployment, vLLM Integration, Safety on OpenShift | OGX Operator via DSC, KServe integration, NeMo Guardrails, TrustyAI |

See [`syllabus.md`](syllabus.md) for full lesson details, deliverables, and time estimates.

## Project Structure

```
ogx-tutorial/
├── infra/                   # Infrastructure: Podman Compose + verification
│   ├── compose.yml               # OGX + Qdrant services
│   ├── .env                      # Container configuration
│   └── main.py                   # Setup verification script
├── syllabus.md                   # Full course syllabus (source of truth)
└── tutorial/
    ├── level_1/                  # Essentials: 11 lessons across 7 modules
    │   ├── M1_fundamentals/
    │   ├── M2_inference_api/
    │   ├── M3_rag/
    │   ├── M4_tool_calling_mcp/
    │   ├── M5_agents_api/
    │   ├── M6_safety_api/
    │   └── M7_additional_apis/
    └── level_2/                  # Practitioner: 10 lessons across 2 modules
        ├── M1_advanced_patterns/
        └── M2_ogx_openshift_ai/
```

Each lesson directory contains:

| File | Purpose |
|------|---------|
| `main.py` | Working lesson code |
| `README.md` | Lesson guide with concepts and expected output |
| `pyproject.toml` | Standalone `uv` project with dependencies |
| `.gitignore` | Ignores `.venv/`, `__pycache__/` |

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/new-lesson`)
3. Each lesson must be self-contained with `pyproject.toml`, `main.py`, `README.md`, and `.gitignore`
4. Test your lesson: `cd <lesson-dir> && uv sync && uv run python main.py`
5. Open a Pull Request
