"""
MCP Tool Filtering Utilities

Provides reusable filtering functions for phase-specific tool assignment.
"""

from typing import Dict, List, Any, Optional, Callable


def filter_tools_by_prefix(
    mcp_tools: Optional[Dict[str, Any]],
    prefixes: List[str]
) -> List[Any]:
    """
    Filter MCP tools by name prefix.

    Args:
        mcp_tools: Dictionary of MCP tools {name: tool_object}
        prefixes: List of prefixes to match (e.g., ["General_", "Code_"])

    Returns:
        List of tool objects matching the prefixes
    """
    if not mcp_tools:
        return []

    return [
        tool for name, tool in mcp_tools.items()
        if any(name.startswith(prefix) for prefix in prefixes)
    ]


def filter_tools_by_names(
    mcp_tools: Optional[Dict[str, Any]],
    tool_names: List[str]
) -> List[Any]:
    """
    Filter MCP tools by exact names.

    Args:
        mcp_tools: Dictionary of MCP tools {name: tool_object}
        tool_names: List of exact tool names to include

    Returns:
        List of tool objects matching the names
    """
    if not mcp_tools:
        return []

    return [
        mcp_tools[name] for name in tool_names
        if name in mcp_tools
    ]


def create_tool_filter(
    include_prefixes: Optional[List[str]] = None,
    exclude_prefixes: Optional[List[str]] = None,
    include_names: Optional[List[str]] = None,
    exclude_names: Optional[List[str]] = None
) -> Callable:
    """
    Create a custom tool filter function.

    Args:
        include_prefixes: Tool name prefixes to include
        exclude_prefixes: Tool name prefixes to exclude
        include_names: Exact tool names to include
        exclude_names: Exact tool names to exclude

    Returns:
        Filter function that takes mcp_tools dict and returns filtered list
    """
    def filter_func(mcp_tools: Optional[Dict[str, Any]]) -> List[Any]:
        if not mcp_tools:
            return []

        tools = []
        for name, tool in mcp_tools.items():
            # Apply inclusion rules
            include = True
            if include_prefixes:
                include = any(name.startswith(p) for p in include_prefixes)
            if include_names and include:
                include = name in include_names

            # Apply exclusion rules
            if exclude_prefixes and include:
                include = not any(name.startswith(p) for p in exclude_prefixes)
            if exclude_names and include:
                include = name not in exclude_names

            if include:
                tools.append(tool)

        return tools

    return filter_func


# Predefined filters for common use cases
GENERAL_TOOLS_FILTER = create_tool_filter(include_prefixes=["General_"])
STUDIO_TOOLS_FILTER = create_tool_filter(include_prefixes=["Studio_"])
CODE_TOOLS_FILTER = create_tool_filter(include_prefixes=["Code_"])
GENERAL_AND_CODE_FILTER = create_tool_filter(include_prefixes=["General_", "Code_"])
ALL_TOOLS_FILTER = lambda mcp_tools: list(mcp_tools.values()) if mcp_tools else []
