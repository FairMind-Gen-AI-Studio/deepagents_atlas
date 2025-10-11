"""
MCP Integration Module

Provides unified MCP client initialization and tool filtering for FairMind integration.
"""

from .client import initialize_mcp_tools, get_mcp_status, validate_mcp_environment
from .filters import (
    filter_tools_by_prefix,
    filter_tools_by_names,
    create_tool_filter,
    GENERAL_TOOLS_FILTER,
    STUDIO_TOOLS_FILTER,
    CODE_TOOLS_FILTER,
    GENERAL_AND_CODE_FILTER,
    ALL_TOOLS_FILTER,
)

__all__ = [
    "initialize_mcp_tools",
    "get_mcp_status",
    "validate_mcp_environment",
    "filter_tools_by_prefix",
    "filter_tools_by_names",
    "create_tool_filter",
    "GENERAL_TOOLS_FILTER",
    "STUDIO_TOOLS_FILTER",
    "CODE_TOOLS_FILTER",
    "GENERAL_AND_CODE_FILTER",
    "ALL_TOOLS_FILTER",
]
