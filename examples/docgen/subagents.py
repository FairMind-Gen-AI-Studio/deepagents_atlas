# Subagent Configurations for DocGen
# Defines specialized subagents used by the analysis and generation phases

from prompts import (
    REPOSITORY_ANALYZER_PROMPT,
    CODE_ANALYZER_PROMPT,
    API_DOCUMENTER_PROMPT,
    ARCHITECTURE_DOCUMENTER_PROMPT,
    EXAMPLE_GENERATOR_PROMPT,
    CLARIFICATION_ASSISTANT_PROMPT,
)


def create_repository_analyzer(repo_name: str, mcp_tools: dict = None):
    """
    Create a repository analyzer subagent for a specific repository.

    Args:
        repo_name: Name of the repository to analyze
        mcp_tools: Dictionary of MCP tools (will filter for Code tools)

    Returns:
        Dictionary configuration for repository analyzer subagent
    """
    # Filter for Code tools only
    code_tools = []
    if mcp_tools:
        tools_list = list(mcp_tools.values()) if isinstance(mcp_tools, dict) else mcp_tools
        code_tools = [
            tool for tool in tools_list
            if hasattr(tool, 'name') and (
                tool.name.startswith('mcp__fairmind__Code_') or
                tool.name.startswith('Code_')
            )
        ]

    return {
        "name": f"repository-analyzer-{repo_name}",
        "description": f"Analyzes the structure and organization of {repo_name} repository",
        "prompt": REPOSITORY_ANALYZER_PROMPT.replace("{repo_name}", repo_name),
        "tools": code_tools,
    }


def create_code_analyzer(module_name: str, mcp_tools: dict = None):
    """
    Create a code analyzer subagent for a specific module.

    Args:
        module_name: Name of the module/file to analyze
        mcp_tools: Dictionary of MCP tools (will filter for Code tools)

    Returns:
        Dictionary configuration for code analyzer subagent
    """
    # Filter for Code tools only
    code_tools = []
    if mcp_tools:
        tools_list = list(mcp_tools.values()) if isinstance(mcp_tools, dict) else mcp_tools
        code_tools = [
            tool for tool in tools_list
            if hasattr(tool, 'name') and (
                tool.name.startswith('mcp__fairmind__Code_') or
                tool.name.startswith('Code_')
            )
        ]

    return {
        "name": f"code-analyzer-{module_name}",
        "description": f"Performs deep analysis of {module_name} module",
        "prompt": CODE_ANALYZER_PROMPT.replace("{module_name}", module_name),
        "tools": code_tools,
    }


# Static subagent configurations
# These don't need dynamic creation

api_documenter_subagent = {
    "name": "api-documenter",
    "description": "Extracts and documents public APIs and interfaces",
    "prompt": API_DOCUMENTER_PROMPT,
    "tools": [],  # Will be populated with Code tools at runtime
}

architecture_documenter_subagent = {
    "name": "architecture-documenter",
    "description": "Documents system architecture and component interactions",
    "prompt": ARCHITECTURE_DOCUMENTER_PROMPT,
    "tools": [],  # Will be populated with Code tools at runtime
}

example_generator_subagent = {
    "name": "example-generator",
    "description": "Creates practical code examples and usage patterns",
    "prompt": EXAMPLE_GENERATOR_PROMPT,
    "tools": [],  # Will be populated with Code tools at runtime
}

clarification_assistant_subagent = {
    "name": "clarification-assistant",
    "description": "Identifies areas needing user clarification",
    "prompt": CLARIFICATION_ASSISTANT_PROMPT,
    "tools": [],  # No tools needed - analyzes existing content
}


# Phase validation functions
def validate_discovery_complete(files: dict) -> tuple[bool, str]:
    """
    Validate that discovery phase is complete.

    Args:
        files: Dictionary of virtual filesystem files

    Returns:
        Tuple of (is_complete, message)
    """
    required_files = ["discovery_catalog.json"]

    for required_file in required_files:
        if required_file not in files:
            return False, f"Missing required file: {required_file}"

    # Check that catalog is valid JSON
    try:
        import json
        catalog = json.loads(files["discovery_catalog.json"])
        if "project_id" not in catalog:
            return False, "discovery_catalog.json missing project_id field"
        if "repositories" not in catalog:
            return False, "discovery_catalog.json missing repositories field"
    except json.JSONDecodeError:
        return False, "discovery_catalog.json is not valid JSON"

    return True, "Discovery phase complete"


def validate_scoping_complete(files: dict) -> tuple[bool, str]:
    """
    Validate that scoping phase is complete.

    Args:
        files: Dictionary of virtual filesystem files

    Returns:
        Tuple of (is_complete, message)
    """
    required_files = ["documentation_scope.json"]

    for required_file in required_files:
        if required_file not in files:
            return False, f"Missing required file: {required_file}"

    # Check that scope is valid JSON
    try:
        import json
        scope = json.loads(files["documentation_scope.json"])
        if "selected_repositories" not in scope:
            return False, "documentation_scope.json missing selected_repositories field"
        if "documentation_styles" not in scope:
            return False, "documentation_scope.json missing documentation_styles field"
    except json.JSONDecodeError:
        return False, "documentation_scope.json is not valid JSON"

    return True, "Scoping phase complete"


def validate_analysis_complete(files: dict) -> tuple[bool, str]:
    """
    Validate that analysis phase is complete.

    Args:
        files: Dictionary of virtual filesystem files

    Returns:
        Tuple of (is_complete, message)
    """
    required_files = ["analysis_summary.md"]

    for required_file in required_files:
        if required_file not in files:
            return False, f"Missing required file: {required_file}"

    # Check for at least one analysis file
    analysis_files = [f for f in files.keys() if f.startswith("analysis_") and f != "analysis_summary.md"]
    if not analysis_files:
        return False, "No analysis files found (expected analysis_*.md files)"

    return True, "Analysis phase complete"


def validate_clarification_complete(files: dict) -> tuple[bool, str]:
    """
    Validate that clarification phase is complete.

    Args:
        files: Dictionary of virtual filesystem files

    Returns:
        Tuple of (is_complete, message)
    """
    required_files = ["clarifications_answered.json"]

    for required_file in required_files:
        if required_file not in files:
            return False, f"Missing required file: {required_file}"

    # Check that clarifications is valid JSON
    try:
        import json
        clarifications = json.loads(files["clarifications_answered.json"])
        if "clarifications" not in clarifications:
            return False, "clarifications_answered.json missing clarifications field"
    except json.JSONDecodeError:
        return False, "clarifications_answered.json is not valid JSON"

    return True, "Clarification phase complete"


def validate_generation_complete(files: dict) -> tuple[bool, str]:
    """
    Validate that generation phase is complete.

    Args:
        files: Dictionary of virtual filesystem files

    Returns:
        Tuple of (is_complete, message)
    """
    required_files = ["final_documentation.md"]

    for required_file in required_files:
        if required_file not in files:
            return False, f"Missing required file: {required_file}"

    # Check for at least one documentation file besides the final one
    doc_files = [
        f for f in files.keys()
        if f.endswith(".md") and "documentation" in f and f != "final_documentation.md"
    ]

    # It's acceptable if only final_documentation.md exists (everything in one file)
    return True, "Generation phase complete"


# Phase configuration
PHASE_VALIDATORS = {
    "discovery": validate_discovery_complete,
    "scoping": validate_scoping_complete,
    "analysis": validate_analysis_complete,
    "clarification": validate_clarification_complete,
    "generation": validate_generation_complete,
}

# Expected output files for each phase
PHASE_OUTPUTS = {
    "discovery": ["discovery_catalog.json"],
    "scoping": ["documentation_scope.json"],
    "analysis": ["analysis_summary.md", "clarification_questions.json", "analysis_index.json"],
    "clarification": ["clarifications_answered.json"],
    "generation": ["final_documentation.md", "generation_metadata.json"],
}
