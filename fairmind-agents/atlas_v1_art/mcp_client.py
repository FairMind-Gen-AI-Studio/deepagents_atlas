# MCP Client Integration for Fairmind Tools
# Connects to Fairmind MCP server using langchain-mcp-adapters

import os
import logging
from typing import Dict, Any, Optional, List
from langchain_mcp_adapters.client import MultiServerMCPClient

logger = logging.getLogger(__name__)

def _normalize_mcp_url(url: Optional[str]) -> Optional[str]:
    """Normalize MCP URL minimally: enforce a trailing slash only.

    This preserves paths like "/mcp/mcp/" exactly as provided.
    """
    if not url:
        return url
    normalized = url
    if not normalized.endswith("/"):
        normalized = normalized + "/"
    return normalized

async def initialize_mcp_tools() -> Optional[Dict[str, Any]]:
    """
    Initialize MCP tools by connecting to Fairmind MCP server.
    
    Returns:
        Dictionary of available MCP tools, or None if connection fails
    """
    
    # Get MCP configuration from environment
    fairmind_url_raw = os.getenv("FAIRMIND_MCP_URL")
    fairmind_token = os.getenv("FAIRMIND_MCP_TOKEN")
    fairmind_url = _normalize_mcp_url(fairmind_url_raw)
    
    if not fairmind_url or not fairmind_token:
        logger.warning("MCP configuration missing. Set FAIRMIND_MCP_URL and FAIRMIND_MCP_TOKEN environment variables.")
        logger.info("Atlas V1 will run without MCP tools (investigation agent will have limited capabilities)")
        return None
    if fairmind_url_raw != fairmind_url:
        logger.info(f"Normalized MCP URL from '{fairmind_url_raw}' to '{fairmind_url}'")
    
    try:
        logger.info(f"Connecting to Fairmind MCP server at {fairmind_url}")
        
        # Configure MCP client for Fairmind server using streamable_http
        mcp_client = MultiServerMCPClient({
            "fairmind": {
                "url": fairmind_url,
                "transport": "streamable_http",
                "headers": {
                    "Authorization": f"Bearer {fairmind_token}",
                    "Content-Type": "application/json"
                }
            }
        })
        
        # Get available tools from MCP server
        mcp_tools = await mcp_client.get_tools()
        
        if not mcp_tools:
            logger.warning("No MCP tools retrieved from Fairmind server")
            return None
        
        # Convert tools to dictionary for AtlasAgentV1
        tools_dict = {}
        for tool in mcp_tools:
            tools_dict[tool.name] = tool
            # Debug logging for tool structure
            logger.debug(f"MCP Tool '{tool.name}': type={type(tool).__name__}, methods={[m for m in dir(tool) if not m.startswith('_')]}")
        
        logger.info(f"Successfully connected to MCP server: {len(tools_dict)} tools available")
        logger.info(f"Available MCP tools: {list(tools_dict.keys())}")
        
        return tools_dict
        
    except Exception as e:
        logger.error(f"Failed to initialize MCP tools: {e}")
        # Provide more diagnostics if this is an ExceptionGroup (Python 3.11+)
        inner = getattr(e, "exceptions", None)
        if inner:
            for idx, sub in enumerate(inner):
                resp = getattr(sub, "response", None)
                status = getattr(resp, "status_code", None)
                body = None
                if resp is not None:
                    try:
                        body = resp.text
                    except Exception:
                        body = None
                logger.error(f"Inner[{idx}] {type(sub).__name__} status={status} body={body}")
        logger.info("Atlas V1 will run without MCP tools (investigation agent will have limited capabilities)")
        return None

async def close_mcp_client():
    """Close MCP client connections gracefully"""
    try:
        # The MultiServerMCPClient should handle cleanup automatically
        # but we can add explicit cleanup here if needed
        logger.info("MCP client connections closed")
    except Exception as e:
        logger.warning(f"Error closing MCP client: {e}")

def validate_mcp_environment() -> Dict[str, bool]:
    """
    Validate MCP environment configuration.
    
    Returns:
        Dictionary with validation results
    """
    return {
        "fairmind_url_set": bool(os.getenv("FAIRMIND_MCP_URL")),
        "fairmind_token_set": bool(os.getenv("FAIRMIND_MCP_TOKEN")),
        "anthropic_key_set": bool(os.getenv("ANTHROPIC_API_KEY")),
    }

def get_mcp_status() -> Dict[str, Any]:
    """
    Get current MCP configuration status.
    
    Returns:
        Dictionary with MCP status information
    """
    validation = validate_mcp_environment()
    
    return {
        "mcp_configured": validation["fairmind_url_set"] and validation["fairmind_token_set"],
        "anthropic_configured": validation["anthropic_key_set"],
        "fairmind_url": os.getenv("FAIRMIND_MCP_URL", "Not set"),
        "validation": validation
    }