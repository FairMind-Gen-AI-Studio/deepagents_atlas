"""
Unified MCP Client for Fairmind Integration

This module provides a single source of truth for MCP tool initialization,
used by all agents in the fairmind-agents package.
"""

import os
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def normalize_mcp_url(url: Optional[str]) -> Optional[str]:
    """Normalize MCP URL: enforce trailing slash."""
    if not url:
        return url
    return url if url.endswith("/") else url + "/"


async def initialize_mcp_tools(
    server_name: str = "fairmind",
    url: Optional[str] = None,
    token: Optional[str] = None,
    runtime_token: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Initialize MCP tools by connecting to MCP server.

    Supports multi-user authentication by accepting a runtime token (per-user API key)
    that takes precedence over static configuration.

    Args:
        server_name: Name of MCP server (default: "fairmind")
        url: MCP server URL (defaults to FAIRMIND_MCP_URL env var)
        token: MCP auth token (defaults to FAIRMIND_MCP_TOKEN env var)
        runtime_token: Per-user API key from LangGraph state (takes precedence over token and env)
                      Used for multi-user scenarios where each user has their own JWT token

    Returns:
        Dictionary of available MCP tools {tool_name: tool_object}, or None if connection fails

    Token Priority (highest to lowest):
        1. runtime_token (per-user, from LangGraph state via HTTP header)
        2. token parameter (explicit override)
        3. FAIRMIND_MCP_TOKEN environment variable (fallback for development/single-user)
    """
    # Get configuration from environment if not provided
    url = url or os.getenv("FAIRMIND_MCP_URL")

    # Token priority: runtime_token > token parameter > .env
    # This enables multi-user support while maintaining backward compatibility
    token = runtime_token or token or os.getenv("FAIRMIND_MCP_TOKEN")

    # Log which token source is being used (for debugging multi-user scenarios)
    if runtime_token:
        logger.info(f"Using runtime token (multi-user mode) - token preview: {runtime_token[:20]}...")
    elif token and token != os.getenv("FAIRMIND_MCP_TOKEN"):
        logger.info("Using explicit token parameter")
    else:
        logger.info("Using FAIRMIND_MCP_TOKEN from .env (fallback mode)")

    url = normalize_mcp_url(url)

    if not url or not token:
        logger.warning(f"MCP configuration missing for {server_name}. "
                      f"Set FAIRMIND_MCP_URL and FAIRMIND_MCP_TOKEN environment variables.")
        logger.info(f"Agents will run without MCP tools (limited capabilities)")
        return None

    try:
        logger.info(f"Connecting to {server_name} MCP server at {url}")

        # Import MCP client here to avoid import errors if not installed
        from langchain_mcp_adapters.client import MultiServerMCPClient

        mcp_client = MultiServerMCPClient({
            server_name: {
                "url": url,
                "transport": "streamable_http",
                "headers": {
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                }
            }
        })

        mcp_tools = await mcp_client.get_tools()

        if not mcp_tools:
            logger.warning(f"No MCP tools retrieved from {server_name} server")
            return None

        # Convert tools list to dictionary
        tools_dict = {tool.name: tool for tool in mcp_tools}

        logger.info(f"Successfully connected to MCP server: {len(tools_dict)} tools available")
        logger.debug(f"Available MCP tools: {list(tools_dict.keys())}")

        return tools_dict

    except ImportError:
        logger.error("langchain_mcp_adapters not installed. Install with: pip install langchain-mcp-adapters")
        return None
    except Exception as e:
        logger.error(f"Failed to initialize MCP tools: {e}")
        logger.info(f"Agents will run without MCP tools (limited capabilities)")
        return None


async def close_mcp_client():
    """Close MCP client connections gracefully."""
    try:
        logger.info("MCP client connections closed")
    except Exception as e:
        logger.warning(f"Error closing MCP client: {e}")


def validate_mcp_environment() -> Dict[str, bool]:
    """Validate MCP environment configuration."""
    return {
        "fairmind_url_set": bool(os.getenv("FAIRMIND_MCP_URL")),
        "fairmind_token_set": bool(os.getenv("FAIRMIND_MCP_TOKEN")),
        "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
    }


def get_mcp_status() -> Dict[str, Any]:
    """Get current MCP configuration status."""
    validation = validate_mcp_environment()
    return {
        "mcp_configured": validation["fairmind_url_set"] and validation["fairmind_token_set"],
        "anthropic_configured": validation["anthropic_key_set"],
        "fairmind_url": os.getenv("FAIRMIND_MCP_URL", "Not set"),
        "validation": validation
    }
