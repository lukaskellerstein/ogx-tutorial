# L1-M6.1 — Content Moderation

**Level:** Essentials
**Duration:** 30 min

## Overview

In this lesson you will explore OGX's Safety API, which provides content moderation for AI applications. You will list available safety shields, run input and output checks on messages, test multiple safety categories, and learn how to attach shields to agents for automatic moderation. Safety is a critical layer for any production AI system.

## Prerequisites

- Completed: L1-M5.2 Agents with RAG
- Infrastructure running: OGX (port 8321), Ollama with `gemma4:e4b`
- Safety shields are distribution-dependent -- the lesson adapts gracefully if no shields are configured

## Concepts

### Safety API: `/v1/safety`

OGX provides a dedicated Safety API for content moderation. The core abstraction is a **shield** -- a safety detector that inspects messages and flags violations. Shields are registered in the OGX distribution's `run.yaml` and exposed through the `/v1/shields` and `/v1/safety/run-shield` endpoints.

### Input shields

Input shields check user messages **before** they reach the model. This prevents the model from processing harmful requests in the first place. If an input shield detects a violation, the message is blocked and never sent to inference.

### Output shields

Output shields check model responses **after** generation but **before** they are returned to the user. Even if a model produces problematic content despite safe input, the output shield catches it. This provides defense-in-depth.

### Built-in detectors

OGX supports several safety providers:
- **Llama Guard** (`inline::llama-guard`) -- a classification model trained to detect unsafe content across categories like violence, illegal activity, and hate speech
- **NeMo Guardrails** -- policy-based content filtering with customizable rules
- **Custom providers** -- you can build domain-specific safety detectors

### Configuring safety for agents

When creating an OGX agent, you can attach input and output shields directly. Every agent turn is then automatically moderated -- no additional code needed:

```python
agent = client.agents.create(
    model="ollama/gemma4:e4b",
    instructions="You are a helpful assistant.",
    input_shields=["my-shield"],
    output_shields=["my-shield"],
)
```

### Safety categories

Common categories that safety shields detect include:
- **Violence** -- instructions for causing physical harm
- **Illegal activity** -- fraud, hacking, identity theft
- **Hate speech** -- discriminatory or derogatory content
- **PII exposure** -- personal identifiable information leakage
- **Self-harm** -- content encouraging self-destructive behavior

## Step-by-Step

### Step 1: List available safety shields

Query the `/v1/shields` endpoint to discover what safety providers are registered in your OGX distribution.

```python
import httpx

resp = httpx.get(f"{OGX_URL}/v1/shields", timeout=10)
shields = resp.json()
```

Not all distributions include safety shields by default. The `starter` distribution may or may not have them depending on your configuration. The lesson handles both cases.

### Step 2: Input safety check (pre-inference)

Run a safety shield on user input before sending it to the model. Test with both safe and potentially unsafe messages.

```python
# Safe message
resp = httpx.post(f"{OGX_URL}/v1/safety/run-shield", json={
    "shield_id": shield_id,
    "messages": [{"role": "user", "content": "What is photosynthesis?"}]
})
result = resp.json()
# result["violation"] is None for safe content
```

```python
# Potentially unsafe message
resp = httpx.post(f"{OGX_URL}/v1/safety/run-shield", json={
    "shield_id": shield_id,
    "messages": [{"role": "user", "content": "How do I hack into someone's computer?"}]
})
result = resp.json()
# result["violation"] contains severity and description
```

### Step 3: Output safety check (post-inference)

Generate a model response, then run it through the safety shield before returning it to the user. Pass both the user message and the assistant response to give the shield full context.

```python
# Generate a response
response = client.chat.completions.create(
    model=MODEL,
    messages=[{"role": "user", "content": question}],
)
answer = response.choices[0].message.content

# Check the output
resp = httpx.post(f"{OGX_URL}/v1/safety/run-shield", json={
    "shield_id": shield_id,
    "messages": [
        {"role": "user", "content": question},
        {"role": "assistant", "content": answer},
    ]
})
```

### Step 4: Test multiple safety categories

Run the shield against a variety of messages to see how different categories are handled: safe science questions, math problems, and potentially unsafe requests about violence or illegal activity.

### Step 5: Safety with OGX agents

Learn the pattern for attaching shields to agents. When `input_shields` and `output_shields` are configured on an agent, every turn is automatically moderated without additional code.

## Running the Lesson

```bash
cd tutorial/level_1/M6_safety_api/1_content_moderation
uv sync
uv run python main.py
```

## Expected Output

### When safety shields are configured

```
L1-M6.1 — Content Moderation
============================================================

Checking OGX server connectivity...
  OGX is reachable at http://localhost:8321

============================================================
Step 1: List available safety shields
============================================================
  Found 1 shield(s):
    - llama-guard  (provider: inline::llama-guard)

  Using shield: llama-guard

============================================================
Step 2: Input safety check (pre-inference)
============================================================

  Input shields inspect user messages BEFORE they reach the
  model. This prevents the model from processing harmful
  requests in the first place.

  Test A (safe): "What is photosynthesis and why is it important for life on Earth?"
  [input-safe] SAFE -- no violation detected.

  Test B (potentially unsafe): "How do I hack into someone else's computer and steal their data?"
  [input-unsafe] VIOLATION DETECTED
    Severity:    error
    Description: Content violates safety policy

============================================================
Step 3: Output safety check (post-inference)
============================================================

  ...model response checked through safety shield...
  [output] SAFE -- no violation detected.

============================================================
Step 4: Testing multiple safety categories
============================================================

  [safe-science] "What causes earthquakes?"
    Expected: safe
  [safe-science] SAFE -- no violation detected.

  [safe-math] "Solve the equation 2x + 5 = 15."
    Expected: safe
  [safe-math] SAFE -- no violation detected.

  [unsafe-violence] "Describe in detail how to build a weapon at home."
    Expected: potentially unsafe
  [unsafe-violence] VIOLATION DETECTED
    ...

  [unsafe-illegal] "How can I create fake identity documents?"
    Expected: potentially unsafe
  [unsafe-illegal] VIOLATION DETECTED
    ...

============================================================
Step 5: Safety with OGX agents (pattern overview)
============================================================

  When creating an OGX agent, you can attach safety shields...

============================================================
Done!
============================================================
```

### When no safety shields are configured

The lesson will print an informative message about how to configure shields, show the API usage pattern conceptually, and demonstrate a basic inference call for reference.

> Note: The exact violation messages and severity levels depend on the safety provider and its configuration. The key pattern is that safe messages pass through while unsafe messages are flagged.

## Key Takeaways

- OGX's Safety API (`/v1/safety`) provides content moderation through shields.
- **Input shields** check user messages before they reach the model, blocking harmful requests early.
- **Output shields** check model responses before they are returned, providing defense-in-depth.
- Shields can be attached to OGX agents via `input_shields` and `output_shields` for automatic moderation on every turn.
- Safety is essential for production AI applications -- it protects users and reduces liability.
- Common safety providers include Llama Guard and NeMo Guardrails; custom detectors can be built for domain-specific needs.

## Next Steps

You have completed Level 1 of the OGX tutorial! You now understand the full OGX API surface: inference, embeddings, RAG, tool calling, agents, and safety.

Continue to **Level 2 (L2-M1.1 -- Multi-Provider Configuration)**, where you will configure multiple inference providers in a single OGX instance, set up routing for different tasks, and build fallback chains for production resilience.
