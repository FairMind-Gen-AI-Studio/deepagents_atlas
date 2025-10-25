"""
MCP Tool Wrappers for Project Context Injection

This module provides utilities to wrap MCP tools with automatic project_id injection,
ensuring agents always query the correct project without manual parameter passing.

The wrapping mechanism uses functools.partial to pre-fill project parameters, making
project context transparent to agents while maintaining type safety.
"""

from functools import partial
from typing import Dict, Any, Callable
import logging

logger = logging.getLogger(__name__)


# Mapping of tool names to their project parameter name
# Some tools use 'project_id', others use 'project'
# This mapping ensures correct parameter binding for each tool
PROJECT_SCOPED_TOOLS = {
    # Studio tools - use 'project_id' parameter
    "Studio_list_needs_by_project": "project_id",
    "Studio_list_user_stories_by_project": "project_id",
    "Studio_list_tasks_by_project": "project_id",
    "Studio_list_requirements_by_project": "project_id",
    "Studio_list_tests_by_project": "project_id",
    "Studio_list_needs_by_session": "project_id",
    "Studio_list_user_stories_by_session": "project_id",
    "Studio_list_tasks_by_session": "project_id",
    "Studio_list_development_tasks_by_session": "project_id",
    "Studio_list_functional_requirements_by_session": "project_id",
    "Studio_list_technical_requirements_by_session": "project_id",

    # Code tools - use 'project' parameter (not 'project_id')
    "Code_list_repositories": "project",
    "Code_search": "project",
    "Code_cat": "project",
    "Code_tree": "project",
    "Code_grep": "project",
    "Code_find_usages": "project",

    # General tools - use 'project_id' parameter
    "General_list_user_attachments_by_project": "project_id",
    "General_rag_retrieve_documents": "project_id",
    "General_rag_retrieve_specific_documents": "project_id",
    "General_list_input_sources_by_session": "project_id",
    "General_rag_retrieve_documents_for_session": "project_id",
    "General_rag_retrieve_specific_documents_for_session": "project_id",
}


def create_project_scoped_tools(
    mcp_tools: Dict[str, Callable],
    project_id: str,
    log_wrapping: bool = True
) -> Dict[str, Callable]:
    """
    Wrap MCP tools to automatically inject project_id parameter.

    This creates a new dict of tools where project-scoped tools have their
    project parameter pre-filled using functools.partial. Tools that don't
    need project context are passed through unchanged.

    The wrapping is selective based on PROJECT_SCOPED_TOOLS mapping, ensuring
    only tools that actually require project context are modified.

    Args:
        mcp_tools: Dictionary of MCP tools from initialize_mcp_tools()
        project_id: Project ID to inject into all project-scoped tools
        log_wrapping: Whether to log which tools were wrapped (default True)

    Returns:
        New dictionary of tools with project-scoped tools wrapped

    Example:
        >>> mcp_tools = await initialize_mcp_tools(...)
        >>> project_id = state.get("project_id")
        >>> scoped_tools = create_project_scoped_tools(mcp_tools, project_id)
        >>> # Now agents can call tools without passing project_id!
        >>> scoped_tools["Studio_list_user_stories_by_project"]()  # project_id auto-injected

    Notes:
        - Tools not in PROJECT_SCOPED_TOOLS are returned unchanged
        - Handles both short names ("Code_search") and full names ("mcp__fairmind__Code_search")
        - Uses functools.partial for efficient parameter binding
        - Returns a new dict (original mcp_tools unchanged)
    """
    if not project_id:
        logger.warning("⚠️  No project_id provided to create_project_scoped_tools - "
                      "tools will NOT be wrapped (may cause errors)")
        return mcp_tools

    wrapped_tools = {}
    wrapped_count = 0

    for tool_name, tool in mcp_tools.items():
        # Extract short name (handle both "Code_search" and "mcp__fairmind__Code_search")
        short_name = tool_name.split("__")[-1] if "__" in tool_name else tool_name

        if short_name in PROJECT_SCOPED_TOOLS:
            param_name = PROJECT_SCOPED_TOOLS[short_name]

            # Use partial to pre-fill project parameter
            # This creates a new callable with project_id bound
            wrapped_tools[tool_name] = partial(tool, **{param_name: project_id})
            wrapped_count += 1

            if log_wrapping:
                logger.debug(f"   🔗 Wrapped {short_name} with {param_name}={project_id}")
        else:
            # Keep tool as-is (doesn't need project context)
            wrapped_tools[tool_name] = tool

    if log_wrapping:
        logger.info(f"✅ Project-scoped tools: wrapped {wrapped_count}/{len(mcp_tools)} "
                   f"tools with project_id={project_id}")

    return wrapped_tools


def get_project_scoped_tool_names() -> list[str]:
    """
    Get list of all tool names that require project context.

    Useful for validation and testing to verify that all expected
    project-scoped tools are being wrapped correctly.

    Returns:
        List of tool names (short names without mcp__fairmind__ prefix)

    Example:
        >>> tool_names = get_project_scoped_tool_names()
        >>> print(f"Found {len(tool_names)} project-scoped tools")
        >>> assert "Studio_list_user_stories_by_project" in tool_names
    """
    return list(PROJECT_SCOPED_TOOLS.keys())
