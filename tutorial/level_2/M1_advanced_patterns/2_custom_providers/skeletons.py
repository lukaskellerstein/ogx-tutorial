"""Printed skeleton examples for the custom providers lesson.

These multi-line strings are displayed by main.py to teach
the OGX provider interface. They are not executable code.
"""

INTERFACE_OVERVIEW = """
  OGX organizes providers by API. Each API has a protocol that
  providers must implement. Here are the key interfaces:

  ---- InferenceProvider ----
  class InferenceProvider:
      async def chat_completion(self, model_id, messages, **kw): ...
      async def completion(self, model_id, content, **kw): ...
      async def embeddings(self, model_id, contents, **kw): ...

  ---- VectorIOProvider ----
  class VectorIOProvider:
      async def register_vector_db(self, vector_db): ...
      async def insert_chunks(self, vector_db_id, chunks, **kw): ...
      async def query_chunks(self, vector_db_id, query, **kw): ...

  ---- SafetyProvider ----
  class SafetyProvider:
      async def register_shield(self, shield): ...
      async def run_shield(self, shield_id, messages, **kw): ...

  For OpenAI-compatible APIs, OGX provides OpenAIMixin -- a base
  class that implements these methods. You only need to implement
  get_api_key() and get_base_url().
"""

CUSTOM_PROVIDER = """
  Minimal custom inference provider (ogx-provider-myapi):

  ---- provider.py ----
  def get_provider_spec():
      return RemoteProviderSpec(
          api=Api.inference,
          adapter_type="my-custom-api",
          pip_packages=["httpx"],
          config_class="my_ogx_provider.config.MyConfig",
          module="my_ogx_provider",
      )

  ---- config.py ----
  class MyConfig(BaseModel):
      api_url: str = "http://my-api:8080"
      api_key: str = ""

  ---- __init__.py ----
  async def get_adapter_impl(config, deps):
      return MyInferenceAdapter(config)

  ---- adapter.py ----
  class MyInferenceAdapter:
      def __init__(self, config):
          self.api_url = config.api_url

      async def chat_completion(self, model_id, messages, **kw):
          async with httpx.AsyncClient() as c:
              resp = await c.post(f"{self.api_url}/chat",
                  json={"model": model_id, "messages": messages})
              return resp.json()

  For OpenAI-compatible APIs, inherit from OpenAIMixin instead:

  class MyOpenAIAdapter(OpenAIMixin):
      def get_api_key(self):   return self.config.api_key
      def get_base_url(self):  return self.config.api_url
"""

REGISTRATION = """
  Providers are registered in run.yaml via the 'module' field:

  ---- run.yaml ----
  version: 2
  providers:
    inference:
      - provider_id: my-custom
        provider_type: remote::my-custom-api
        module: my_ogx_provider          # pip package name
        config:
          api_url: http://my-api:8080
          api_key: ${MY_API_KEY}
      - provider_id: vllm-fallback
        provider_type: remote::vllm
        config:
          url: http://localhost:8000

  OGX will:
    1. Install the package from the module field
    2. Call get_provider_spec() to discover the provider
    3. Call get_adapter_impl() to instantiate it
    4. Route requests based on provider_id
"""

SAFETY_DETECTOR = """
  Custom safety provider with keyword filter + external API:

  ---- provider.py ----
  def get_provider_spec():
      return InlineProviderSpec(
          api=Api.safety,
          provider_type="inline::my-safety",
          config_class="my_safety.config.MySafetyConfig",
          module="my_safety",
      )

  ---- adapter.py ----
  class MySafetyAdapter:
      async def run_shield(self, shield_id, messages, **kw):
          text = " ".join(m.get("content", "") for m in messages)
          # Keyword filter
          for word in self.blocked_words:
              if word.lower() in text.lower():
                  return {"violation": {"description": f"Blocked: {word}"}}
          # External moderation API
          resp = await client.post(self.moderation_url, json={"text": text})
          if resp.json().get("flagged"):
              return {"violation": {"description": resp.json()["reason"]}}
          return {"violation": None}  # safe
"""

PLUGIN_ARCHITECTURE = """
  OGX's extension model works at three levels:

  1. EXTERNAL PROVIDERS (out-of-tree)
     - Publish a pip package with get_provider_spec()
     - Reference via 'module' in run.yaml -- no OGX changes needed

  2. INTERNAL PROVIDERS (in-tree)
     - Add code to ogx/providers/remote/ or inline/
     - Best for contributing to the OGX project

  3. CUSTOM DISTRIBUTIONS
     - Bundle providers into a reusable config.yaml template
     - Best for team-wide standardization

  Package structure:
    ogx-provider-myapi/
      pyproject.toml            my_ogx_provider/
                                  __init__.py       # get_adapter_impl()
                                  provider.py       # get_provider_spec()
                                  config.py         # Pydantic config
                                  adapter.py        # Implementation
"""
