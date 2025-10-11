"""MCP Tool Filtering for ArchQA Agents

Filters MCP Fairmind tools to assign appropriate subsets to each specialized agent.

Following the pattern from docgen but adapted for ArchQA's 3-agent architecture:
- context-mapper: Needs General, Studio, and basic Code tools for discovery
- code-investigator: Needs all Code tools for deep analysis
- solution-synthesizer: No MCP tools (uses only filesystem for synthesis)
"""

def get_context_mapper_tools(mcp_tools):
    """
    Get MCP tools appropriate for the Context Mapper agent.

    Context Mapper needs:
    - General tools: List projects, RAG search for architectural context
    - Studio tools: User stories, requirements, needs for business context
    - Basic Code tools: List repositories, view structure

    Args:
        mcp_tools: Dictionary of MCP tool objects from initialization

    Returns:
        List of filtered tool objects for context mapping phase
    """
    if not mcp_tools:
        return []

    tools_list = list(mcp_tools.values()) if isinstance(mcp_tools, dict) else mcp_tools

    # Tools needed for understanding project scope and architecture
    context_mapper_tool_names = [
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

    filtered_tools = []
    for tool in tools_list:
        tool_name = getattr(tool, 'name', str(tool))
        # Check for both prefixed (mcp__fairmind__) and non-prefixed versions
        if any(expected in tool_name for expected in context_mapper_tool_names):
            filtered_tools.append(tool)

    return filtered_tools


def get_code_investigator_tools(mcp_tools):
    """
    Get MCP tools appropriate for the Code Investigator agent.

    Code Investigator needs:
    - All Code tools: For deep code analysis and exploration
    - Studio tools: To cross-reference code with business requirements

    Args:
        mcp_tools: Dictionary of MCP tool objects from initialization

    Returns:
        List of filtered tool objects for code investigation phase
    """
    if not mcp_tools:
        return []

    tools_list = list(mcp_tools.values()) if isinstance(mcp_tools, dict) else mcp_tools

    # Tools needed for deep code analysis
    investigator_tool_names = [
        # All Code tools - comprehensive code analysis
        'Code_list_repositories',
        'Code_search',
        'Code_cat',
        'Code_tree',
        'Code_grep',
        'Code_find_usages',

        # Studio tools - business context for analysis
        'Studio_list_user_stories_by_project',
        'Studio_get_user_story',
        'Studio_list_requirements_by_project',
        'Studio_get_requirement',
    ]

    filtered_tools = []
    for tool in tools_list:
        tool_name = getattr(tool, 'name', str(tool))
        # Check for both prefixed and non-prefixed versions
        if any(expected in tool_name for expected in investigator_tool_names):
            filtered_tools.append(tool)

    return filtered_tools


def get_solution_synthesizer_tools(mcp_tools):
    """
    Get MCP tools appropriate for the Solution Synthesizer agent.

    Solution Synthesizer doesn't need MCP tools - it synthesizes findings
    from the virtual filesystem (context_map.json, investigation_findings.md)
    and presents the final answer to the user.

    Args:
        mcp_tools: Dictionary of MCP tool objects from initialization

    Returns:
        Empty list (no MCP tools needed for synthesis)
    """
    # Synthesizer only uses built-in filesystem tools (read_file, etc.)
    # No MCP tools needed
    return []


def verify_tool_assignment(mcp_tools):
    """
    Verify that MCP tools are properly categorized and assigned.

    Useful for debugging - call this to check tool distribution.

    Args:
        mcp_tools: Dictionary of MCP tool objects from initialization

    Returns:
        Dictionary with tool counts and names for each agent type
    """
    context_tools = get_context_mapper_tools(mcp_tools)
    investigator_tools = get_code_investigator_tools(mcp_tools)
    synthesizer_tools = get_solution_synthesizer_tools(mcp_tools)

    return {
        'context_mapper': {
            'count': len(context_tools),
            'tools': [getattr(t, 'name', str(t)) for t in context_tools],
        },
        'code_investigator': {
            'count': len(investigator_tools),
            'tools': [getattr(t, 'name', str(t)) for t in investigator_tools],
        },
        'solution_synthesizer': {
            'count': len(synthesizer_tools),
            'tools': [getattr(t, 'name', str(t)) for t in synthesizer_tools],
        },
        'total_mcp_tools': len(mcp_tools) if mcp_tools else 0,
    }
