# Atlas V1 Sub-agents Configuration
# 4 specialized agents for the Atlas methodology

from typing import Dict, Any, List
try:
    from .prompts import (
        INVESTIGATION_AGENT_PROMPT_TEMPLATE,
        DISCUSSION_AGENT_PROMPT_TEMPLATE, 
        PLANNING_AGENT_PROMPT_TEMPLATE,
        TASK_GENERATION_AGENT_PROMPT_TEMPLATE,
        REPOSITORY_ANALYZER_PROMPT_TEMPLATE
    )
except ImportError:
    # Fallback for direct execution
    from prompts import (
        INVESTIGATION_AGENT_PROMPT_TEMPLATE,
        DISCUSSION_AGENT_PROMPT_TEMPLATE, 
        PLANNING_AGENT_PROMPT_TEMPLATE,
        TASK_GENERATION_AGENT_PROMPT_TEMPLATE,
        REPOSITORY_ANALYZER_PROMPT_TEMPLATE
    )

def get_investigation_agent_config() -> Dict[str, Any]:
    """Investigation Agent - Phase 1: Silent project exploration"""
    return {
        "name": "investigation-agent",
        "description": "Phase 1: Autonomous project exploration and context gathering without user interaction",
        "prompt": INVESTIGATION_AGENT_PROMPT_TEMPLATE,
        "tools": [
            # General tools for project and document management
            "mcp__fairmind__General_list_projects",
            "mcp__fairmind__General_get_document_content", 
            "mcp__fairmind__General_rag_retrieve_documents",
            "mcp__fairmind__General_rag_retrieve_specific_documents",
            
            # Studio tools for business requirements
            "mcp__fairmind__Studio_list_needs_by_project",
            "mcp__fairmind__Studio_get_need",
            "mcp__fairmind__Studio_list_user_stories_by_project",
            "mcp__fairmind__Studio_list_user_stories_by_need",
            "mcp__fairmind__Studio_get_user_story",
            "mcp__fairmind__Studio_get_related_user_stories",
            "mcp__fairmind__Studio_list_tasks_by_project",
            "mcp__fairmind__Studio_get_task",
            "mcp__fairmind__Studio_list_requirements_by_project",
            "mcp__fairmind__Studio_get_requirement",
            "mcp__fairmind__Studio_list_tests_by_project",
            "mcp__fairmind__Studio_list_tests_by_userstory",
            
            # Code tools for initial repository discovery
            "mcp__fairmind__Code_list_repositories",
            "mcp__fairmind__Code_get_directory_structure",
            "mcp__fairmind__Code_find_relevant_code_snippets"
        ],
        "outputs": [
            "investigation_findings.md"
        ],
        "validation_criteria": [
            "User story analyzed",
            "Associated need identified",
            "Related user stories catalogued",
            "Business context synthesized"
        ]
    }

def get_discussion_agent_config() -> Dict[str, Any]:
    """Discussion Agent - Phase 2: Interactive requirements clarification"""
    return {
        "name": "discussion-agent", 
        "description": "Phase 2: Generate targeted clarification questions and process user responses",
        "prompt": DISCUSSION_AGENT_PROMPT_TEMPLATE,
        "tools": ["human_input"],
        "outputs": [
            "clarification_questions.md",
            "user_responses.md", 
            "requirements_clarified.md"
        ],
        "validation_criteria": [
            "Questions were presented to user",
            "User responses were collected",
            "Requirements summary was approved by user"
        ]
    }

def get_planning_agent_config() -> Dict[str, Any]:
    """Planning Agent - Phase 3: Code analysis and implementation planning"""
    return {
        "name": "planning-agent",
        "description": "Phase 3: Analyze repositories with sub-agents and create interactive implementation plan", 
        "prompt": PLANNING_AGENT_PROMPT_TEMPLATE,
        "tools": [
            # Full access to Code_* MCP tools for repository analysis
            "mcp__fairmind__Code_list_repositories",
            "mcp__fairmind__Code_get_directory_structure", 
            "mcp__fairmind__Code_find_relevant_code_snippets",
            "mcp__fairmind__Code_get_file",
            "mcp__fairmind__Code_find_usages"
        ]
    }

def get_task_generation_agent_config() -> Dict[str, Any]:
    """Task Generation Agent - Phase 4: Transform plan into executable tasks"""
    return {
        "name": "task-generation-agent",
        "description": "Phase 4: Transform approved plan into actionable tasks with 1:1 repository mapping",
        "prompt": TASK_GENERATION_AGENT_PROMPT_TEMPLATE
    }

def get_repository_analyzer_subagent_config(repository_name: str) -> Dict[str, Any]:
    """Repository Analyzer Sub-agent - For detailed repository analysis"""
    return {
        "name": f"repository-analyzer-{repository_name}",
        "description": f"Analyze repository '{repository_name}' structure, code patterns, and implementation opportunities",
        "prompt": REPOSITORY_ANALYZER_PROMPT_TEMPLATE.format(repository_name=repository_name),
        "tools": [
            # Full Code_* MCP tools access for deep repository analysis
            "mcp__fairmind__Code_get_directory_structure",
            "mcp__fairmind__Code_find_relevant_code_snippets", 
            "mcp__fairmind__Code_get_file",
            "mcp__fairmind__Code_find_usages"
        ]
    }

# Agent configurations registry
AGENT_CONFIGS = {
    "investigation-agent": get_investigation_agent_config(),
    "discussion-agent": get_discussion_agent_config(),
    "planning-agent": get_planning_agent_config(),
    "task-generation-agent": get_task_generation_agent_config()
}

# Phase definitions for orchestrator
PHASE_DEFINITIONS = {
    "investigation": {
        "name": "Silent Investigation",
        "emoji": "🔍", 
        "goal": "Understand project and codebase without user interaction",
        "agent": "investigation-agent",
        "duration_estimate": "15-30 minutes",
        "completion_weight": 25,
        "auto_advance": True
    },
    
    "discussion": {
        "name": "Targeted Discussion",
        "emoji": "💬",
        "goal": "Clarify requirements through focused questions", 
        "agent": "discussion-agent",
        "duration_estimate": "10-20 minutes",
        "completion_weight": 50,
        "requires_user_input": True
    },
    
    "planning": {
        "name": "Structured Planning",
        "emoji": "📋",
        "goal": "Create comprehensive implementation plan with repository analysis",
        "agent": "planning-agent", 
        "duration_estimate": "20-40 minutes",
        "completion_weight": 75,
        "requires_user_input": True,
        "uses_subagents": True
    },
    
    "task_generation": {
        "name": "Task Generation", 
        "emoji": "⚡",
        "goal": "Transform plan into actionable implementation tasks",
        "agent": "task-generation-agent",
        "duration_estimate": "10-15 minutes", 
        "completion_weight": 90,
        "auto_advance": True
    }
}

def get_agent_config(agent_name: str) -> Dict[str, Any]:
    """Get configuration for a specific agent"""
    if agent_name.startswith("repository-analyzer-"):
        repository_name = agent_name.replace("repository-analyzer-", "")
        return get_repository_analyzer_subagent_config(repository_name)
    
    return AGENT_CONFIGS.get(agent_name, {})

def get_phase_definition(phase_name: str) -> Dict[str, Any]:
    """Get phase definition for orchestrator"""
    return PHASE_DEFINITIONS.get(phase_name, {})

def get_tools_for_agent(agent_name: str) -> List[str]:
    """Get list of tools required for a specific agent"""
    config = get_agent_config(agent_name)
    return config.get("tools", [])

def validate_phase_completion(phase_name: str, virtual_filesystem: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that a phase has completed successfully"""
    phase_def = get_phase_definition(phase_name)
    agent_config = get_agent_config(phase_def.get("agent", ""))
    
    validation_result = {
        "phase": phase_name,
        "completed": False,
        "missing_outputs": [],
        "missing_criteria": [],
        "errors": []
    }
    
    try:
        # Check required outputs exist
        required_outputs = agent_config.get("outputs", [])
        for output_file in required_outputs:
            if output_file not in virtual_filesystem:
                validation_result["missing_outputs"].append(output_file)
        
        # Check validation criteria
        validation_criteria = agent_config.get("validation_criteria", [])
        for criterion in validation_criteria:
            # For discussion phase, check that files contain evidence of user interaction
            if phase_name == "discussion":
                if "Questions were presented to user" in criterion:
                    if "clarification_questions.md" not in virtual_filesystem or not virtual_filesystem.get("clarification_questions.md", "").strip():
                        validation_result["missing_criteria"].append(criterion)
                elif "User responses were collected" in criterion:
                    if "user_responses.md" not in virtual_filesystem or not virtual_filesystem.get("user_responses.md", "").strip():
                        validation_result["missing_criteria"].append(criterion)
                elif "Requirements summary was approved by user" in criterion:
                    if "requirements_clarified.md" not in virtual_filesystem or not virtual_filesystem.get("requirements_clarified.md", "").strip():
                        validation_result["missing_criteria"].append(criterion)
            else:
                # Simplified validation for other phases
                if not required_outputs or validation_result["missing_outputs"]:
                    validation_result["missing_criteria"].append(criterion)
        
        # Phase is complete if no missing outputs and no missing criteria
        validation_result["completed"] = (
            len(validation_result["missing_outputs"]) == 0 and 
            len(validation_result["missing_criteria"]) == 0
        )
        
    except Exception as e:
        validation_result["errors"].append(str(e))
    
    return validation_result

def get_next_phase(current_phase: str) -> str:
    """Get the next phase in the sequence"""
    phases = ["investigation", "discussion", "planning", "task_generation"]
    try:
        current_index = phases.index(current_phase)
        if current_index < len(phases) - 1:
            return phases[current_index + 1]
        else:
            return "completed"
    except ValueError:
        return "investigation"  # Default to first phase if current phase not found

def format_agent_prompt(agent_name: str, **kwargs) -> str:
    """Format agent prompt with provided context variables"""
    config = get_agent_config(agent_name)
    prompt_template = config.get("prompt", "")
    
    # Add default values for common template variables
    default_context = {
        "project_id": kwargs.get("project_id", "unknown"),
        "current_phase": kwargs.get("current_phase", "unknown"),
        "completion_percentage": kwargs.get("completion_percentage", 0),
        "investigation_focus": kwargs.get("investigation_focus", "business requirements analysis"),
        "knowledge_gaps": kwargs.get("knowledge_gaps", "technical specifications"),
        "project_type": kwargs.get("project_type", "software development"),
        "tool_categories": kwargs.get("tool_categories", "General, Studio, Code tools available"),
        "scope_summary": kwargs.get("scope_summary", "implementation scope to be determined"),
        "recommended_agent": kwargs.get("recommended_agent", agent_name),
        "recommended_next_action": kwargs.get("recommended_next_action", f"Deploy {agent_name} for current phase"),
        "repository_name": kwargs.get("repository_name", "unknown")
    }
    
    # Merge provided context with defaults
    format_context = {**default_context, **kwargs}
    
    try:
        return prompt_template.format(**format_context)
    except KeyError as e:
        # If template variable is missing, return template as-is with error note
        return f"{prompt_template}\n\n[ERROR: Missing template variable: {e}]"

def get_phase_status_prompt() -> str:
    """
    Generate a prompt section to help orchestrator understand phase status
    This provides clear guidance on how to determine the current phase based on existing files
    """
    return """
## Phase Status Determination Guide

### How to Check Phase Completion:
Use the read_file tool to check for these specific output files:

1. **Investigation Phase Complete**: 
   - File: investigation_findings.md
   - Contains: Project analysis, user story details, business context

2. **Discussion Phase Complete**:
   - File: requirements_clarified.md  
   - Contains: User responses, clarified requirements, confirmed scope

3. **Planning Phase Complete**:
   - File: implementation_plan.md
   - Contains: Technical architecture, component design, implementation approach

4. **Task Generation Phase Complete**:
   - File: implementation_tasks.md
   - Contains: Actionable tasks, implementation steps, repository assignments

### Decision Logic:
- **No files exist** → Start with investigation-agent
- **Only investigation_findings.md exists** → Deploy discussion-agent
- **investigation_findings.md + requirements_clarified.md exist** → Deploy planning-agent  
- **All above + implementation_plan.md exist** → Deploy task-generation-agent
- **All four files exist** → All phases complete

### Important Reminders:
- Always use read_file to check file existence before making phase decisions
- Never assume a phase is complete without verifying the output file exists
- If you want to skip a phase, you MUST ask user permission first
- Document all phase transition decisions in phase_transition_decision.md
"""

def should_request_phase_skip_permission(current_phase: str, reason: str) -> bool:
    """
    Determine if orchestrator should request permission to skip a phase
    
    Args:
        current_phase: The phase that might be skipped
        reason: The reason for wanting to skip
    
    Returns:
        True if permission should be requested, False if phase is mandatory
    """
    # All phases are important in Atlas V1 methodology, so always request permission
    return True

def get_phase_skip_request_template(phase_to_skip: str, reason: str, next_phase: str) -> str:
    """
    Generate a template for requesting permission to skip a phase
    
    Args:
        phase_to_skip: The phase that would be skipped
        reason: The reason for skipping
        next_phase: The next phase that would be executed
    
    Returns:
        Template message for human_input tool
    """
    return f"""Based on my analysis, I believe we can skip the {phase_to_skip} phase because {reason}.

The next phase would be {next_phase}.

Do you agree with skipping the {phase_to_skip} phase? Please respond:
- 'yes' to skip and proceed to {next_phase}
- 'no' to execute the {phase_to_skip} phase as planned

Your decision: """