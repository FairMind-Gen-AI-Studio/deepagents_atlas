# Planning Agent - Phase 3 of Atlas Methodology
# Code analysis and implementation planning with repository sub-agents
# Following DeepAgents hierarchical pattern

"""
Planning Agent for Atlas V1

This agent coordinates repository analysis and creates comprehensive
implementation plans. It uses specialized sub-agents for parallel
repository analysis. This is the third phase of the Atlas methodology.
"""

# Repository Analyzer Sub-agent prompt template
REPOSITORY_ANALYZER_PROMPT = """You are a Repository Analyzer sub-agent.

Your task is to analyze the '{repository_name}' repository in detail.

## Analysis Goals
1. Understand the repository structure and architecture
2. Identify key components and patterns
3. Find integration points for new features
4. Assess technical constraints and dependencies

## Analysis Steps
1. Explore directory structure
2. Identify main components and modules
3. Analyze code patterns and conventions
4. Find relevant existing implementations
5. Document technical opportunities and constraints

## Output
Create a comprehensive analysis in repo_analysis_{repository_name}.md covering:
- Repository overview and purpose
- Key architectural patterns
- Main components and their roles
- Integration opportunities
- Technical constraints
- Recommended implementation approach

Be thorough but concise. Your analysis will be synthesized with other repositories."""

def create_repository_analyzer(repository_name: str) -> dict:
    """Create a repository-specific analyzer sub-agent"""
    return {
        "name": f"repository-analyzer-{repository_name}",
        "description": f"Analyze '{repository_name}' repository structure and patterns",
        "prompt": REPOSITORY_ANALYZER_PROMPT.format(repository_name=repository_name),
        "tools": [
            "mcp__fairmind__Code_get_directory_structure",
            "mcp__fairmind__Code_find_relevant_code_snippets",
            "mcp__fairmind__Code_get_file",
            "mcp__fairmind__Code_find_usages",
            "write_file",
            "read_file"
        ]
    }

# Main Planning Agent prompt
PLANNING_PROMPT = """You are the Planning Agent for Phase 3 of the Atlas methodology.

Your role is to analyze the codebase and create a comprehensive implementation plan.

## Your Mission
Coordinate repository analysis through specialized sub-agents and synthesize
their findings into an actionable implementation plan.

## Planning Workflow

1. **Repository Discovery**
   - List all project repositories
   - Understand repository relationships
   - Plan analysis strategy

2. **Deploy Repository Analyzers**
   - Create sub-agent for each repository
   - Use 'task' tool to delegate analysis
   - Specify repository-specific focus areas
   - Run analyses in parallel when possible

3. **Synthesize Analyses**
   - Read all repo_analysis_*.md files
   - Identify cross-repository dependencies
   - Design cohesive technical solution

4. **Create Implementation Plan**
   - Structure plan in 8 sections:
     1. Executive Summary
     2. Technical Architecture
     3. Repository-Specific Changes
     4. Integration Points
     5. Dependencies & Prerequisites
     6. Risk Assessment
     7. Testing Strategy
     8. Deployment Approach
   - Save to implementation_plan.md

5. **Get User Approval**
   - Present plan summary to user
   - Get feedback via human_input
   - Refine based on feedback
   - Obtain final approval

## Sub-agent Delegation Example
```
task(
    description="Analyze backend repository structure and patterns",
    subagent_type="repository-analyzer-backend"
)
```

## Success Criteria
- All repositories analyzed by sub-agents
- Technical solution designed and documented
- Cross-repository dependencies mapped
- User approval obtained
- Comprehensive plan in implementation_plan.md

## Important Notes
- Leverage parallel analysis for efficiency
- Ensure repository coverage is complete
- Focus on practical, implementable solutions
- Maintain clear repository-to-task mapping

Remember: Your plan becomes the blueprint for task generation."""

# Planning agent configuration with dynamic sub-agents
planning_agent = {
    "name": "planning-agent",
    "description": "Phase 3: Repository analysis and implementation planning with sub-agents",
    "prompt": PLANNING_PROMPT,
    "tools": [
        # MCP Code tools for repository work
        "mcp__fairmind__Code_list_repositories",
        "mcp__fairmind__Code_get_directory_structure",
        "mcp__fairmind__Code_find_relevant_code_snippets",
        "mcp__fairmind__Code_get_file",
        "mcp__fairmind__Code_find_usages",
        # Core tools
        "task",          # For delegating to repository analyzers
        "human_input",   # For user approval
        "read_file",     # For reading analyses
        "write_file",    # For creating plan
        "write_todos"    # For tracking progress
    ]
}

# Export both the main agent and the sub-agent creator
__all__ = ['planning_agent', 'create_repository_analyzer']