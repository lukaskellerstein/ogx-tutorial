---
globs: ["tutorial/**"]
---

# Tutorial Structure Rules

## Two-Level Architecture

The tutorial is organized in two progressive levels:

- **`tutorial/level_1/`** — Essentials: every major OGX API, short-to-medium lessons (~30-60 min)
- **`tutorial/level_2/`** — Practitioner: advanced patterns, production deployment (~45 min-1 hour)

Always consult `syllabus.md` for the full module/lesson breakdown.

## Lesson Directory Convention

Every lesson lives in `tutorial/<level>/<module>/<lesson>/` and contains exactly:

1. **`pyproject.toml`** — standalone `uv` project. Use `[project]` with `name`, `version`, `description`, `requires-python`, and `dependencies`.
2. **`main.py`** — the working lesson code. This is the primary deliverable.
3. **`README.md`** — lesson guide (see `lesson-content.md` rule for format).
4. **`.gitignore`** — always ignore: `.venv/`, `__pycache__/`, `*.pyc`, `.python-version`.

## Directory Structure

```
syllabus.md                         # Master syllabus — source of truth
ogx-local/
  compose.yml                       # Podman Compose: OGX + Qdrant
  .env                              # Environment config (Ollama URL, model, etc.)
tutorial/
  level_1/                          # 11 lessons
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
    M7_additional_apis/
      1_files_batches_conversations_prompts/
  level_2/                          # 10 lessons
    M1_advanced_patterns/
      1_multi_provider_config/
      2_custom_providers/
      3_telemetry_observability/
      4_evaluation_rag_benchmarks/
      5_reranking_advanced_retrieval/
      6_file_processors/
      7_production_deployment/
    M2_ogx_openshift_ai/
      1_operator_deployment/
      2_vllm_integration/
      3_safety_openshift/
```

## pyproject.toml Template

```toml
[project]
name = "ogx-tutorial-L<level>-M<module>-<lesson>"
version = "0.1.0"
description = "<Lesson title from syllabus>"
requires-python = ">=3.10"

[project.dependencies]
ogx-client = ">=1.0"
# Add lesson-specific deps here
```

## .gitignore Template

```
.venv/
__pycache__/
*.pyc
.python-version
```

## Principles

- Each lesson must be fully self-contained — a user should be able to `cd` into it, run `uv sync && uv run python main.py`, and see results.
- All lessons connect to the OGX server at `http://localhost:8321`.
- Print meaningful output to the console so the user sees what's happening.
- Keep `main.py` under ~200 lines. If a lesson needs helper code, put it in a separate module within the same directory.
- Level 1 lessons should be concise and focused on a single OGX API.
- Level 2 lessons can be longer and build multi-step production scenarios.
