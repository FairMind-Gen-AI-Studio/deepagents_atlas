"""
MCP Tool Filtering Utilities for Fairmind Agents

Provides reusable filtering functions and preset filters for phase-specific tool assignment.
Handles both standard tool names (e.g., 'General_list_projects') and MCP-prefixed names
(e.g., 'mcp__fairmind__General_list_projects').
"""

from typing import Dict, List, Any, Optional, Callable


def handle_tool_name_variants(tool_name: str, expected_names: List[str]) -> bool:
    """
    Check if tool name matches any expected name, handling naming variants.

    Handles both:
    - Standard: 'General_list_projects'
    - MCP prefixed: 'mcp__fairmind__General_list_projects'

    Args:
        tool_name: Actual tool name from MCP server
        expected_names: List of expected tool names to match against

    Returns:
        True if tool name matches any expected name (with or without prefix)
    """
    # Check direct match
    if tool_name in expected_names:
        return True

    # Check if tool_name is prefixed version of expected name
    for expected in expected_names:
        if f"mcp__fairmind__{expected}" == tool_name:
            return True
        if tool_name.endswith(expected):  # Handles any prefix pattern
            return True

    return False


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
        if any(prefix in name for prefix in prefixes)
    ]


def filter_tools_by_names(
    mcp_tools: Optional[Dict[str, Any]],
    tool_names: List[str]
) -> List[Any]:
    """
    Filter MCP tools by exact names (handles naming variants).

    Args:
        mcp_tools: Dictionary of MCP tools {name: tool_object}
        tool_names: List of exact tool names to include

    Returns:
        List of tool objects matching the names
    """
    if not mcp_tools:
        return []

    filtered = []
    for actual_name, tool in mcp_tools.items():
        if handle_tool_name_variants(actual_name, tool_names):
            filtered.append(tool)

    return filtered


def filter_by_tool_list(
    mcp_tools: Optional[Dict[str, Any]],
    tool_list: List[str]
) -> List[Any]:
    """
    Filter tools by list of expected names (handles variants).

    This is an alias for filter_tools_by_names for consistency.

    Args:
        mcp_tools: Dictionary of MCP tools
        tool_list: List of tool names to include

    Returns:
        List of filtered tool objects
    """
    return filter_tools_by_names(mcp_tools, tool_list)


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
        include_names: Exact tool names to include (handles variants)
        exclude_names: Exact tool names to exclude (handles variants)

    Returns:
        Filter function that takes mcp_tools dict and returns filtered list
    """
    def filter_func(mcp_tools: Optional[Dict[str, Any]]) -> List[Any]:
        if not mcp_tools:
            return []

        # If include_names is specified, use name-based filtering first
        if include_names:
            return filter_tools_by_names(mcp_tools, include_names)

        tools = []
        for name, tool in mcp_tools.items():
            # Apply inclusion rules
            include = True
            if include_prefixes:
                include = any(prefix in name for prefix in include_prefixes)

            # Apply exclusion rules
            if exclude_prefixes and include:
                include = not any(prefix in name for prefix in exclude_prefixes)
            if exclude_names and include:
                include = not handle_tool_name_variants(name, exclude_names)

            if include:
                tools.append(tool)

        return tools

    return filter_func


# =============================================================================
# BASIC PRESET FILTERS
# =============================================================================

GENERAL_TOOLS_FILTER = create_tool_filter(include_prefixes=["General_"])
"""Filter for all General_* tools (project discovery, RAG search, documents)"""

STUDIO_TOOLS_FILTER = create_tool_filter(include_prefixes=["Studio_"])
"""Filter for all Studio_* tools (user stories, requirements, needs, tasks)"""

CODE_TOOLS_FILTER = create_tool_filter(include_prefixes=["Code_"])
"""Filter for all Code_* tools (repository analysis, code search, file reading)"""

GENERAL_AND_CODE_FILTER = create_tool_filter(include_prefixes=["General_", "Code_"])
"""Filter for General_* and Code_* tools combined"""

ALL_TOOLS_FILTER = lambda mcp_tools: list(mcp_tools.values()) if mcp_tools else []
"""Filter that returns all available tools"""


# =============================================================================
# ARCHQA AGENT PRESET FILTERS
# =============================================================================

ARCHQA_CONTEXT_MAPPER_FILTER = create_tool_filter(
    include_names=[
        # General tools - project discovery and knowledge retrieval
        'General_list_projects',
        'General_list_user_attachments_by_project',
        'General_get_document_content',
        'General_rag_retrieve_documents',
        'General_rag_retrieve_specific_documents',
        # Studio tools - business context
        'Studio_list_user_stories_by_project',
        'Studio_list_requirements_by_project',
        'Studio_list_needs_by_project',
        'Studio_get_user_story',
        'Studio_get_requirement',
        'Studio_get_need',
        # Code tools - repository discovery
        'Code_list_repositories',
        'Code_tree',
    ]
)
"""
ArchQA Context Mapper Filter - Phase 1: Question scope analysis and project discovery

Tools: 13 total (5 General + 6 Studio + 2 Code)
- General: Project listing, document access, RAG search
- Studio: User stories, requirements, needs for business context
- Code: Repository listing and structure view

Use case: Analyze architectural question, discover relevant projects/repositories,
create context map with investigation scope.
"""

ARCHQA_CODE_INVESTIGATOR_FILTER = create_tool_filter(
    include_names=[
        # Code tools - comprehensive code analysis
        'Code_list_repositories',
        'Code_search',
        'Code_cat',
        'Code_tree',
        'Code_grep',
        'Code_find_usages',
        # Studio tools - requirements tracing
        'Studio_list_user_stories_by_project',
        'Studio_get_user_story',
        'Studio_list_requirements_by_project',
        'Studio_get_requirement',
    ]
)
"""
ArchQA Code Investigator Filter - Phase 2: Deep code analysis with requirements tracing

Tools: 10 total (6 Code + 4 Studio)
- Code: All operations (search, cat, tree, grep, find usages)
- Studio: User stories and requirements for tracing code to business needs

Use case: Investigate code implementations, find technical debt, perform impact analysis,
cross-reference with business requirements. Combined with Tavily for technology research.
"""

ARCHQA_SOLUTION_SYNTHESIZER_FILTER = lambda mcp_tools: []
"""
ArchQA Solution Synthesizer Filter - Phase 3: Synthesis of findings into answer

Tools: 0 MCP tools (filesystem only)
- Uses only built-in tools: read_file, write_file, ls

Use case: Read context_map.json and investigation_findings.md, synthesize into
comprehensive architectural answer. No MCP access needed - all data from previous phases.
"""


# =============================================================================
# DOCGEN AGENT PRESET FILTERS
# =============================================================================

DOCGEN_DISCOVERY_FILTER = create_tool_filter(
    include_names=[
        # General tools - project discovery
        'General_list_projects',
        'General_list_user_attachments_by_project',
        'General_get_document_content',
        'General_rag_retrieve_documents',
        'General_rag_retrieve_specific_documents',
        # Code tools - repository discovery
        'Code_list_repositories',
        'Code_tree',
    ]
)
"""
DocGen Discovery Filter - Phase 1: Silent project reconnaissance

Tools: 7 total (5 General + 2 Code)
- General: Project listing, document access
- Code: Repository listing, directory structure

Use case: Silent exploration of project to catalog all repositories and code structure
before defining documentation scope with user.
"""

DOCGEN_SCOPING_FILTER = lambda mcp_tools: []
"""
DocGen Scoping Filter - Phase 2: Interactive scope definition

Tools: 0 MCP tools (uses human_input tool instead)
- Uses custom human_input tool for HumanInTheLoopMiddleware

Use case: Interactive phase where agent works with user to define documentation scope.
Reads discovery_catalog.json and discusses with user what to document.
"""

DOCGEN_ANALYSIS_FILTER = create_tool_filter(
    include_names=[
        # Code tools - comprehensive code analysis
        'Code_list_repositories',
        'Code_search',
        'Code_cat',
        'Code_tree',
        'Code_grep',
        'Code_find_usages',
    ]
)
"""
DocGen Analysis Filter - Phase 3: Deep code analysis

Tools: 6 total (6 Code)
- Code: All operations for exploring and analyzing code

Use case: Analyze code repositories according to defined scope. Explore file structures,
search code, understand implementations. Delegates to specialized sub-agents.
"""

DOCGEN_CLARIFICATION_FILTER = lambda mcp_tools: []
"""
DocGen Clarification Filter - Phase 4: Interactive clarification questions

Tools: 0 MCP tools (uses human_input tool instead)
- Uses custom human_input tool for HumanInTheLoopMiddleware

Use case: Review analysis outputs, identify ambiguities, ask user clarifying questions
about unclear code patterns or requirements.
"""

DOCGEN_GENERATION_FILTER = create_tool_filter(
    include_names=[
        # Code tools - fetch code examples
        'Code_list_repositories',
        'Code_search',
        'Code_cat',
        'Code_tree',
        'Code_grep',
        'Code_find_usages',
    ]
)
"""
DocGen Generation Filter - Phase 5: Final documentation creation

Tools: 6 total (6 Code)
- Code: All operations for fetching code examples

Use case: Generate final documentation by synthesizing all previous phases.
Uses Code tools to fetch real code examples to include in documentation.
"""


# =============================================================================
# FILTER METADATA
# =============================================================================

FILTER_REGISTRY = {
    # Basic filters
    "general": GENERAL_TOOLS_FILTER,
    "studio": STUDIO_TOOLS_FILTER,
    "code": CODE_TOOLS_FILTER,
    "general_and_code": GENERAL_AND_CODE_FILTER,
    "all": ALL_TOOLS_FILTER,
    # ArchQA filters
    "archqa_context_mapper": ARCHQA_CONTEXT_MAPPER_FILTER,
    "archqa_code_investigator": ARCHQA_CODE_INVESTIGATOR_FILTER,
    "archqa_solution_synthesizer": ARCHQA_SOLUTION_SYNTHESIZER_FILTER,
    # DocGen filters
    "docgen_discovery": DOCGEN_DISCOVERY_FILTER,
    "docgen_scoping": DOCGEN_SCOPING_FILTER,
    "docgen_analysis": DOCGEN_ANALYSIS_FILTER,
    "docgen_clarification": DOCGEN_CLARIFICATION_FILTER,
    "docgen_generation": DOCGEN_GENERATION_FILTER,
}
"""Registry of all available preset filters"""
