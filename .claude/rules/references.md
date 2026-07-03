# Reference Sources

Always consult these sources when building lessons. Do NOT guess at APIs — read the docs and source code first.

## OGX (Open GenAI Stack)
- **GitHub**: https://github.com/ogx-ai/ogx
- **Documentation**: https://ogx-ai.github.io/docs
- **Providers**: https://ogx-ai.github.io/docs/providers
- **Python Client**: https://github.com/ogx-ai/ogx-client-python
- **K8s Operator**: https://github.com/ogx-ai/ogx-k8s-operator
- Check for the latest API signatures before writing code

## vLLM
- **Documentation**: https://docs.vllm.ai/
- **Docker image**: `vllm/vllm-openai` on Docker Hub
- **Gemma 4 support blog**: https://vllm.ai/blog/2026-04-02-gemma4
- Model ID: `google/gemma-4-E4B-it`

## Qdrant
- **Documentation**: https://qdrant.tech/documentation/
- **Docker image**: `qdrant/qdrant` on Docker Hub
- **REST API**: http://localhost:6333
- **Dashboard**: http://localhost:6333/dashboard

## LangChain + LangGraph
- **Code samples**: `/Users/lkellers/Projects/github/lukaskellerstein/ai-agents-course/Version_2/6_langchain-ai`
  - LangChain basics: `.../1_langchain/`
  - LangChain agents: `.../1_langchain/10_agent/`
  - LangChain agents + custom tools: `.../1_langchain/11_agent_custom_tools/`
  - LangChain agents + MCP: `.../1_langchain/12_agent_mcp/`
  - LangGraph basics: `.../2_langgraph/`
  - LangGraph agents: `.../2_langgraph/5_agent/`
  - LangGraph multi-agent: `.../2_langgraph/6_agents/`
- Verify that LangChain APIs used in reference code are still current (v1.0+ only)

## MCP (Model Context Protocol)
- **Code samples**: `/Users/lkellers/Projects/github/lukaskellerstein/ai-agents-course/Version_2/2_MCP`
  - STDIO transport: `.../1_STDIO/`
  - Streamable HTTP: `.../3_STREAMABLE_HTTP/`
  - Code interpreter: `.../10_MY_Code_interpreter/`
- OGX has native MCP tool runtime integration

## How to Use References

1. **Before implementing a lesson**: read the corresponding reference code to understand patterns
2. **Before using an API**: check the OGX docs to verify it exists and get the correct signature
3. **Adapt, don't copy**: reference code is inspiration — tutorial code should be clean, self-contained, and educational
4. **Check for deprecations**: LangChain APIs change frequently. Always verify against current docs
5. **Cross-reference**: when building an agent lesson, check both the agent framework reference AND the OGX agents API docs
