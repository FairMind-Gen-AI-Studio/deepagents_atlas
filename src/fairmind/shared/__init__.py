"""
Shared utilities for Fairmind agents.

Provides common functionality for MCP integration, model configuration,
and utility functions used across all Fairmind agents.

Available modules:
- mcp: MCP client initialization, tool filtering, and verification

Usage:
    from fairmind.shared import mcp

    # Initialize MCP tools
    tools = await mcp.initialize_mcp_tools()

    # Use preset filters
    filtered_tools = mcp.ARCHQA_CONTEXT_MAPPER_FILTER(tools)

    # Verify and log
    mcp.log_tool_assignment("agent-name", filtered_tools)
"""

from . import mcp

__all__ = ["mcp"]

__version__ = "0.1.0"
