"""
Discovery agent — find candidate resources for a given (methodology × type).

Model: Flash-Lite (deterministic-and-API-first).
Tools: direct API calls (OpenAlex, PubMed) for local dev;
       MCPToolset when MCP_SERVER_URL is configured (production).

Output shape per candidate:
  { title, url, source, type_hint, raw_metadata, skip_reason }
"""
from __future__ import annotations

import logging
import os

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from agents.discovery.tools import search_openalex as _openalex_impl
from agents.discovery.tools import search_pubmed as _pubmed_impl

logger = logging.getLogger(__name__)

MODEL = os.environ.get("MODEL_FLASH_LITE", "gemini-3.1-flash-lite")
MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "")
# Treat placeholder values as unset
if MCP_SERVER_URL in ("", "your_public_mcp_hostname_here"):
    MCP_SERVER_URL = ""

_PROMPT_PATH = "agents/prompts/discovery.md"
try:
    with open(_PROMPT_PATH) as f:
        _prompt_text = f.read()
except FileNotFoundError:
    _prompt_text = "Discovery agent — see agents/prompts/discovery.md"

# ---------------------------------------------------------------------------
# Build tool list: MCP (production) or direct APIs (local dev)
# ---------------------------------------------------------------------------

def search_openalex(methodology_code: str, resource_type: str, max_results: int = 10) -> list[dict]:
    """Search OpenAlex for resources matching methodology + resource type."""
    return _openalex_impl(methodology_code, resource_type, max_results)


def search_pubmed(methodology_code: str, max_results: int = 10) -> list[dict]:
    """Search PubMed for methodology-relevant articles."""
    return _pubmed_impl(methodology_code, max_results)


_tools = [
    FunctionTool(func=search_openalex),
    FunctionTool(func=search_pubmed),
]

if MCP_SERVER_URL:
    # Production: add MCPToolset (SSE) — expands the tool set to all 17 APIs
    try:
        from google.adk.tools import MCPToolset
        from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

        _mcp_toolset = MCPToolset(
            connection_params=SseConnectionParams(
                url=MCP_SERVER_URL,
                headers={"Authorization": f"Bearer {os.environ.get('MCP_SERVER_KEY', '')}"},
            )
        )
        _tools.append(_mcp_toolset)
        logger.info("MCPToolset added: %s", MCP_SERVER_URL)
    except Exception as exc:
        logger.warning("MCPToolset setup failed, falling back to direct APIs: %s", exc)


discovery_agent = LlmAgent(
    model=MODEL,
    name="discovery_agent",
    description=(
        "Finds candidate research resources for a given methodology code "
        "(SYN-01, SYN-02, OBS-01, EVAL-01) and resource type. "
        "Returns raw candidate metadata for the Appraisal agent."
    ),
    instruction=_prompt_text,
    tools=_tools,
)
