"""
MCP Integration Module for Fairmind Agents

Provides unified MCP client initialization, tool filtering, and verification
for all agents in the fairmind-agents package.

Usage:
    from fairmind.shared.mcp import (
        initialize_mcp_tools,
        ARCHQA_CONTEXT_MAPPER_FILTER,
        log_tool_assignment,
    )

    # Initialize MCP tools
    mcp_tools = await initialize_mcp_tools()

    # Filter tools for specific phase
    context_tools = ARCHQA_CONTEXT_MAPPER_FILTER(mcp_tools)

    # Verify and log
    log_tool_assignment("context-mapper", context_tools,
                       critical_tools=["General_list_projects"])
"""

from .client import (
    initialize_mcp_tools,
    get_mcp_status,
    validate_mcp_environment,
    close_mcp_client,
    normalize_mcp_url,
)

from .filters import (
    # Filtering functions
    filter_tools_by_prefix,
    filter_tools_by_names,
    filter_by_tool_list,
    create_tool_filter,
    handle_tool_name_variants,
    # Basic filters
    GENERAL_TOOLS_FILTER,
    STUDIO_TOOLS_FILTER,
    CODE_TOOLS_FILTER,
    GENERAL_AND_CODE_FILTER,
    ALL_TOOLS_FILTER,
    # ArchQA filters
    ARCHQA_CONTEXT_MAPPER_FILTER,
    ARCHQA_CODE_INVESTIGATOR_FILTER,
    ARCHQA_SOLUTION_SYNTHESIZER_FILTER,
    # DocGen filters
    DOCGEN_DISCOVERY_FILTER,
    DOCGEN_SCOPING_FILTER,
    DOCGEN_ANALYSIS_FILTER,
    DOCGEN_CLARIFICATION_FILTER,
    DOCGEN_GENERATION_FILTER,
    # Filter registry
    FILTER_REGISTRY,
)

from .verification import (
    verify_tool_availability,
    log_tool_assignment,
    create_tool_report,
    check_tool_name_consistency,
    verify_phase_tools,
    categorize_tools,
    log_agent_startup,
)

__all__ = [
    # Client functions
    "initialize_mcp_tools",
    "get_mcp_status",
    "validate_mcp_environment",
    "close_mcp_client",
    "normalize_mcp_url",
    # Filtering functions
    "filter_tools_by_prefix",
    "filter_tools_by_names",
    "filter_by_tool_list",
    "create_tool_filter",
    "handle_tool_name_variants",
    # Basic preset filters
    "GENERAL_TOOLS_FILTER",
    "STUDIO_TOOLS_FILTER",
    "CODE_TOOLS_FILTER",
    "GENERAL_AND_CODE_FILTER",
    "ALL_TOOLS_FILTER",
    # ArchQA preset filters
    "ARCHQA_CONTEXT_MAPPER_FILTER",
    "ARCHQA_CODE_INVESTIGATOR_FILTER",
    "ARCHQA_SOLUTION_SYNTHESIZER_FILTER",
    # DocGen preset filters
    "DOCGEN_DISCOVERY_FILTER",
    "DOCGEN_SCOPING_FILTER",
    "DOCGEN_ANALYSIS_FILTER",
    "DOCGEN_CLARIFICATION_FILTER",
    "DOCGEN_GENERATION_FILTER",
    # Filter registry
    "FILTER_REGISTRY",
    # Verification functions
    "verify_tool_availability",
    "log_tool_assignment",
    "create_tool_report",
    "check_tool_name_consistency",
    "verify_phase_tools",
    "categorize_tools",
    "log_agent_startup",
]

__version__ = "0.1.0"
