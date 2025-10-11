"""
Shared Library for FairMind Agents

This package provides common infrastructure for all agents in the fairmind-agents collection:
- MCP client initialization and tool filtering
- Model configuration with multi-provider support
- Utility functions for async/sync bridging and logging
- Configuration management

All agents should import from this shared library rather than duplicating code.
"""

__version__ = "0.1.0"

from .mcp.client import initialize_mcp_tools, get_mcp_status
from .models.config import initialize_model, get_model_info
from .utils.async_helpers import run_async_in_sync_context, initialize_mcp_tools_sync
from .utils.logging import setup_logging

__all__ = [
    "initialize_mcp_tools",
    "get_mcp_status",
    "initialize_model",
    "get_model_info",
    "run_async_in_sync_context",
    "initialize_mcp_tools_sync",
    "setup_logging",
]
