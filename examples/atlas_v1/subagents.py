# Atlas V1 Sub-agents Configuration
# 4 specialized agents for the Atlas methodology with enhanced prompt patterns

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

# =============================================================================
# PROMPT ENHANCEMENT PATTERNS - Reusable Components for Dynamic Prompts
# =============================================================================

# Tool Categories for Dynamic Injection
TOOL_CATEGORIES = {
    "investigation": {
        "name": "Business Analysis Tools",
        "tools": ["Studio_get_user_story", "Studio_list_user_stories_by_project", "Studio_get_need", "General_rag_retrieve_documents"],
        "description": "Tools for business context discovery and requirements analysis"
    },
    "discussion": {
        "name": "Interactive Clarification Tools", 
        "tools": ["human_input"],
        "description": "Tools for user interaction and requirements validation"
    },
    "planning": {
        "name": "Repository Analysis Tools",
        "tools": ["Code_list_repositories", "Code_get_directory_structure", "Code_find_relevant_code_snippets", "Code_get_file"],
        "description": "Tools for technical architecture analysis and solution design"
    },
    "task_generation": {
        "name": "Documentation Creation Tools",
        "tools": ["read_file", "write_file", "ls"],
        "description": "Tools for task documentation and implementation planning"
    }
}

# Success Criteria Templates
SUCCESS_CRITERIA_TEMPLATES = {
    "investigation": [
        "✓ Business context captured from user stories and needs",
        "✓ Target user story analyzed with related stories identified", 
        "✓ Business constraints and requirements documented",
        "✓ Knowledge gaps identified for discussion phase",
        "✓ All findings archived to virtual filesystem"
    ],
    "discussion": [
        "✓ Targeted clarification questions generated (5-7 questions)",
        "✓ User responses collected via human_input tool",
        "✓ Requirements consolidated and presented for approval", 
        "✓ User approval obtained before documentation",
        "✓ Technical requirements specification created"
    ],
    "planning": [
        "✓ All project repositories discovered and analyzed",
        "✓ Repository-specific sub-agents deployed in parallel",
        "✓ Technical solution proposed and approved by user",
        "✓ Comprehensive 8-section implementation plan created",
        "✓ Repository-to-task mapping clearly defined"
    ],
    "task_generation": [
        "✓ Implementation plan parsed into actionable tasks", 
        "✓ Every task mapped to exactly one repository",
        "✓ Task dependencies and priorities established",
        "✓ Repository validation matrix created and verified",
        "✓ Implementation documentation complete and ready"
    ]
}

# Context Variables for Dynamic Prompt Injection
CONTEXT_VARIABLES = {
    "project_context": "{project_id}",
    "phase_context": "{current_phase}", 
    "completion_context": "{completion_percentage}%",
    "tools_context": "{tool_categories}",
    "gaps_context": "{knowledge_gaps}",
    "scope_context": "{scope_summary}"
}

# Output File Templates for Consistency
OUTPUT_FILE_PATTERNS = {
    "investigation": [
        "investigation_findings.md",
        "business_context.md"
    ],
    "discussion": [
        "clarification_questions.md",
        "user_responses.md",
        "requirements_clarified.md"
    ],
    "planning": [
        "implementation_plan.md",
        "repo_analysis_{repository_name}.md"  # Pattern for repository analyses
    ],
    "task_generation": [
        "implementation_tasks.md",
        "focus_chain.md", 
        "success_criteria.md",
        "next_steps.md",
        "repository_task_matrix.md"
    ]
}

# Workflow Pattern Templates for Examples
WORKFLOW_EXAMPLES = {
    "investigation": {
        "autonomous_discovery": [
            "write_todos(['Analyze target user story', 'Identify business need', 'Find related stories'])",
            "story = Studio_get_user_story(story_id)",
            "need = Studio_get_need(need_id)", 
            "related = Studio_list_user_stories_by_need(need_id)",
            "write_file('investigation_findings.md', synthesis)"
        ],
        "project_wide_analysis": [
            "stories = Studio_list_user_stories_by_project(project_id)",
            "docs = General_rag_retrieve_documents('business requirements')", 
            "write_file('business_context.md', analysis)"
        ]
    },
    "discussion": {
        "question_workflow": [
            "read_file('investigation_findings.md')",
            "questions = generate_targeted_questions(findings)",
            "responses = [human_input(q) for q in questions]",
            "summary = consolidate_responses(responses)",
            "approval = human_input('Approve requirements summary?')",
            "write_file('requirements_clarified.md', approved_summary)"
        ]
    },
    "planning": {
        "repository_analysis": [
            "repos = Code_list_repositories(project_id)",
            "for repo in repos: task(description=f'Analyze {repo}', subagent_type=f'repository-analyzer-{repo}')",
            "analyses = [read_file(f'repo_analysis_{repo}.md') for repo in repos]",
            "solution = design_technical_solution(analyses, requirements)",
            "approval = human_input(solution_proposal)",
            "write_file('implementation_plan.md', detailed_plan)"
        ]
    },
    "task_generation": {
        "repository_mapping": [
            "plan = read_file('implementation_plan.md')",
            "repos = extract_repositories(plan)",
            "tasks = [create_repo_specific_tasks(repo, plan) for repo in repos]",
            "validate_1_to_1_mapping(tasks, repos)",
            "write_file('implementation_tasks.md', prioritized_tasks)"
        ]
    }
}

# Quality Standards for Prompt Validation
QUALITY_STANDARDS = {
    "specificity": "Questions and tasks must be specific and actionable, not generic",
    "repository_mapping": "Every task must map to exactly one repository with no exceptions",
    "user_approval": "All user-facing outputs require explicit approval via human_input", 
    "documentation": "All findings must be archived to virtual filesystem for next phases",
    "handover": "Each phase must create structured handover documentation for next phase"
}

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

def validate_phase_completion(phase_name: str, files: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that a phase has completed successfully
    
    Args:
        phase_name: Name of the phase to validate
        files: Virtual filesystem from LangGraph state (previously called virtual_filesystem)
    """
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
            if output_file not in files:
                validation_result["missing_outputs"].append(output_file)
        
        # Check validation criteria
        validation_criteria = agent_config.get("validation_criteria", [])
        for criterion in validation_criteria:
            # For discussion phase, check that files contain evidence of user interaction
            if phase_name == "discussion":
                if "Questions were presented to user" in criterion:
                    if "clarification_questions.md" not in files or not files.get("clarification_questions.md", "").strip():
                        validation_result["missing_criteria"].append(criterion)
                elif "User responses were collected" in criterion:
                    if "user_responses.md" not in files or not files.get("user_responses.md", "").strip():
                        validation_result["missing_criteria"].append(criterion)
                elif "Requirements summary was approved by user" in criterion:
                    if "requirements_clarified.md" not in files or not files.get("requirements_clarified.md", "").strip():
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
    
    # Find all template variables in the prompt
    import re
    template_vars = re.findall(r'\{([^}]+)\}', prompt_template)
    unique_vars = set(template_vars)
    
    # Start with provided context
    format_context = dict(kwargs)
    
    # Add intelligent defaults for any missing variables
    for var_name in unique_vars:
        if var_name not in format_context:
            # Generate intelligent default based on variable name pattern
            default_value = _generate_default_value(var_name, agent_name)
            format_context[var_name] = default_value
    
    try:
        return prompt_template.format(**format_context)
    except KeyError as e:
        # If template variable is missing, return template as-is with error note
        return f"{prompt_template}\n\n[ERROR: Missing template variable: {e}]"

def _generate_default_value(var_name: str, agent_name: str) -> str:
    """Generate intelligent default value for template variable based on naming patterns"""
    var_lower = var_name.lower()
    
    # Project and context defaults
    if var_name == "project_id":
        return "unknown"
    elif var_name == "current_phase":
        return "investigation"
    elif var_name == "completion_percentage":
        return "0"
    elif var_name == "tool_categories":
        return "General, Studio, Code tools available"
    elif var_name == "investigation_focus":
        return "business requirements analysis"
    elif var_name == "knowledge_gaps":
        return "technical specifications"
    elif var_name == "project_type":
        return "software development"
    elif var_name == "scope_summary":
        return "implementation scope to be determined"
    elif var_name == "recommended_agent":
        return agent_name
    elif var_name == "recommended_next_action":
        return f"Deploy {agent_name} for current phase"
    
    # Repository-related defaults
    elif "repository" in var_lower or "repo" in var_lower:
        if "name" in var_lower:
            return "to be determined during planning phase"
        elif "count" in var_lower:
            return "to be determined during code analysis"
        else:
            return "repository details to be determined"
    
    # Task-related defaults
    elif "task" in var_lower:
        if "count" in var_lower or "number" in var_lower:
            return "to be determined during task generation"
        elif "title" in var_lower:
            return "task title to be defined"
        else:
            return "task details to be determined"
    
    # File-related defaults
    elif "file" in var_lower or "path" in var_lower:
        return "file path to be determined during implementation"
    
    # Requirements and business defaults
    elif "requirement" in var_lower or "business" in var_lower:
        return "to be determined during investigation and discussion phases"
    
    # Time and duration defaults
    elif any(word in var_lower for word in ["duration", "time", "hours", "days"]):
        return "to be estimated during planning"
    
    # Count and number defaults  
    elif any(word in var_lower for word in ["count", "number", "percentage"]):
        return "0"
    
    # Name defaults
    elif "name" in var_lower:
        return "to be determined"
    
    # Phase defaults
    elif "phase" in var_lower:
        return "current phase"
    
    # Generic defaults for common patterns
    elif any(word in var_lower for word in ["description", "summary", "details"]):
        return "to be determined during appropriate phase"
    elif any(word in var_lower for word in ["validation", "requirement", "criteria"]):
        return "to be defined based on project requirements"
    elif var_lower in ["yes_or_no", "level"]:
        return "TBD"
    
    # Default fallback
    else:
        return f"[{var_name} placeholder - to be determined]"

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