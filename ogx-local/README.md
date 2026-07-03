# Running OGX Locally

This guide sets up OGX (Open GenAI Stack) for local development on macOS.

## Architecture

```
┌──────────────────────────────────────────────────┐
│  Your Python code (tutorial lessons)             │
│  Uses: OpenAI SDK → http://localhost:8321/v1     │
└──────────────┬───────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────┐
│  OGX Server (Podman container)                   │
│  Port: 8321                                      │
│  Image: ogxai/distribution-starter               │
│  APIs: /v1/inference, /v1/vector_io,             │
│        /v1alpha/agents, /v1/safety, etc.         │
└──────┬──────────────────────┬────────────────────┘
       │                      │
┌──────▼──────────┐   ┌──────▼──────────┐
│  Ollama (native)│   │  Qdrant         │
│  Port: 11434    │   │  (Podman)       │
│  Model:         │   │  Port: 6333     │
│  gemma4:e4b     │   │                 │
│  Runs on host   │   │                 │
│  (Apple Silicon │   │                 │
│   GPU access)   │   │                 │
└─────────────────┘   └─────────────────┘
```

**Why Ollama runs natively:** On macOS with Apple Silicon, Ollama must run outside containers to access the GPU. OGX and Qdrant run as Podman containers and connect to Ollama on the host.

## Prerequisites

1. **Podman** — container runtime
   ```bash
   brew install podman
   podman machine init
   podman machine start
   ```

2. **Ollama** — local LLM inference
   ```bash
   brew install ollama
   ```

3. **uv** — Python package manager
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

## Quick Start

### 1. Start Ollama and pull the model

```bash
# Start Ollama (if not already running)
ollama serve &

# Pull gemma4:e4b (~3 GB)
ollama pull gemma4:e4b
```

### 2. Start OGX and Qdrant

```bash
cd ogx-local
podman compose up -d
```

Wait ~30-60 seconds for OGX to fully start. Check logs:
```bash
podman compose logs -f ogx
```

Look for a message indicating the server is ready on port 8321.

### 3. Verify everything works

```bash
uv sync
uv run python main.py
```

You should see all checks pass:
```
  Ollama       : OK
  Qdrant       : OK
  OGX          : OK
  Inference    : OK

All checks passed! OGX is ready for tutorial lessons.
```

## Service URLs

| Service | URL | Purpose |
|---------|-----|---------|
| OGX API | http://localhost:8321 | Unified AI runtime API |
| OGX Models | http://localhost:8321/v1/models | List registered models |
| Qdrant REST | http://localhost:6333 | Vector DB API |
| Qdrant Dashboard | http://localhost:6333/dashboard | Vector DB UI |
| Ollama | http://localhost:11434 | Inference backend (native) |

## Using OGX from Python

OGX is OpenAI-compatible. Use the `openai` Python SDK:

```python
from openai import OpenAI

client = OpenAI(base_url="http://localhost:8321/v1", api_key="not-needed")

response = client.chat.completions.create(
    model="ollama/gemma4:e4b",
    messages=[{"role": "user", "content": "Hello!"}],
)
print(response.choices[0].message.content)
```

## Stopping

```bash
# Stop containers (preserves data)
podman compose down

# Stop and wipe all data
podman compose down -v

# Stop Ollama
pkill ollama
```

## Troubleshooting

### OGX container fails to start
Check logs:
```bash
podman compose logs ogx
```

Common issues:
- Ollama not running → start it first: `ollama serve`
- Port 8321 in use → stop the other process or change the port in `.env`

### "Model not found" error
OGX auto-discovers models from Ollama. Make sure:
```bash
# Model is pulled
ollama list | grep gemma4

# Ollama is reachable from the container
curl http://localhost:11434/api/tags
```

### Connection refused from OGX to Ollama
On Podman, the host is accessible at `host.containers.internal`. The compose file already configures this. If it doesn't work:
```bash
# Check Podman machine is running
podman machine info

# Restart the Podman machine
podman machine stop && podman machine start
```

### Qdrant not accessible
```bash
podman compose logs qdrant
curl http://localhost:6333/healthz
```

## vLLM (Linux / GPU servers)

On Linux with NVIDIA GPU, you can use vLLM instead of Ollama for production-grade inference:

```bash
# Run vLLM serving gemma-4-E4B
podman run -d --gpus all \
  -p 8000:8000 \
  --name vllm \
  vllm/vllm-openai \
  --model google/gemma-4-E4B-it

# Then configure OGX to use vLLM by setting in .env:
# OLLAMA_URL=http://host.containers.internal:8000
```

This is not needed for local macOS development.
