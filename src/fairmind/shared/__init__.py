"""
Shared utilities for Fairmind agents.

Provides common functionality for MCP integration, model configuration,
and utility functions used across all Fairmind agents.

Available modules:
- mcp: MCP client initialization, tool filtering, and verification
- agent_factory: Lazy agent creation with MCP tools from state
- interaction: Human-in-the-loop interaction tools

Usage:
    from fairmind.shared import mcp
    from fairmind.shared.agent_factory import create_stateful_agent_factory

    # Initialize MCP tools
    tools = await mcp.initialize_mcp_tools()

    # Use preset filters
    filtered_tools = mcp.ARCHQA_CONTEXT_MAPPER_FILTER(tools)

    # Create agent factory
    agent = create_stateful_agent_factory(
        agent_creator=create_my_agent,
        agent_name="MyAgent"
    )
"""

from . import mcp
from . import interaction
from . import agent_factory

__all__ = ["mcp", "interaction", "agent_factory"]

__version__ = "0.1.0"
