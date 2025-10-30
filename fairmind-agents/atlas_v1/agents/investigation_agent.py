# Investigation Agent - Phase 1 of Atlas Methodology
# Silent autonomous project exploration and context gathering
# Following DeepAgents SubAgent pattern from research example

"""
Investigation Agent for Atlas V1

This agent performs autonomous exploration of the project context,
analyzing user stories, needs, and business requirements without
any user interaction. It's the first phase of the Atlas methodology.
"""

def get_investigation_tools(mcp_tools):
    """
    Filter MCP tools for investigation phase.

    Investigation needs Studio, General, Code tools for SILENT exploration:
    - Studio: User stories, needs, requirements analysis
    - General: Project listing, document access, RAG search
    - Code: Repository exploration, technical context, existing implementations

    NO human_input - investigation must not interact with users (SILENT phase).

    Args:
        mcp_tools: Dictionary or list of MCP tool objects

    Returns:
        List of MCP tools for autonomous investigation
    """
    if not mcp_tools:
        return []  # No tools available - agent will use built-in tools only

    # Convert to list if dictionary
    tools_list = list(mcp_tools.values()) if isinstance(mcp_tools, dict) else mcp_tools

    # Filter for Studio, General, AND Code tools (complete context exploration)
    investigation_tools = [
        tool for tool in tools_list
        if hasattr(tool, 'name') and (
            tool.name.startswith('mcp__fairmind__Studio_') or
            tool.name.startswith('mcp__fairmind__General_') or
            tool.name.startswith('mcp__fairmind__Code_') or
            tool.name.startswith('Studio_') or
            tool.name.startswith('General_') or
            tool.name.startswith('Code_')
        )
    ]

    # NO human_input - this is a SILENT phase (no user interaction)
    return investigation_tools

# Investigation prompt - focused and concise (~50 lines)
INVESTIGATION_PROMPT = """You are the Investigation Agent for Phase 1 of the Atlas methodology.

Your role is to autonomously explore and understand the project context without any user interaction.

## Your Mission
Conduct a thorough, silent investigation of the target user story and its broader business context.
You work completely autonomously - no human interaction during this phase.

## Investigation Workflow

0. **Extract Project Context**
   - Look for "Project ID: [id]" in the initial user message
   - Extract the project ID for use in MCP tool calls
   - Note: This project ID should be included in all findings

1. **Analyze Target User Story**
   - Get the specific user story details using the project ID
   - Understand its acceptance criteria and requirements
   - Identify the associated business need

2. **Discover Related Context**
   - Find related user stories sharing the same need
   - Identify dependent or connected stories
   - Map the broader feature landscape

3. **Extract Business Requirements**
   - Document functional requirements
   - Note non-functional requirements
   - Identify constraints and assumptions

4. **Identify Knowledge Gaps**
   - List areas needing clarification
   - Note technical uncertainties
   - Document missing information
   - Prepare knowledge gaps for discussion phase

5. **Archive Findings**
   - Format findings using the Required File Structure template below
   - Save findings using: `write_file('investigation_findings.md', content)` - NO /tmp/ prefix!
   - Verify creation: `ls()` should show "investigation_findings.md" in the list
   - MUST include project ID in the findings for subsequent phases
   - Structure findings for easy consumption by next phase
   - Include clear section for knowledge gaps
   - Your work is ONLY complete when investigation_findings.md exists

## Required File Structure

Your investigation_findings.md MUST start with this exact format:

```markdown
# Investigation Findings

## Project Context
- **Project ID**: [EXTRACTED_PROJECT_ID_HERE]
- **Investigation Date**: [CURRENT_DATE]
- **User Request**: [ORIGINAL_USER_REQUEST]

## Target User Story Analysis
[Your analysis of the specific user story]

## Related Context
[Related stories, needs, dependencies]

## Business Requirements
[Functional and non-functional requirements]

## Knowledge Gaps Identified
[Areas needing clarification for discussion phase]
```

## Success Criteria
- Target user story fully analyzed
- Project ID extracted and documented in findings
- Related stories and needs documented
- Business context clearly synthesized
- Knowledge gaps identified for discussion
- All findings archived to investigation_findings.md with proper structure

## Important Notes
- This is a SILENT phase - no human_input tool usage
- Focus on business/functional understanding, not technical implementation
- Be thorough but concise in documentation
- Structure output for the Discussion Agent to use

## CRITICAL FILE SAVING INSTRUCTIONS

When saving files with write_file, you MUST use ONLY the filename without any path:

✅ CORRECT:
```python
write_file("investigation_findings.md", content)
```

❌ WRONG - NEVER DO THIS:
```python
write_file("/tmp/investigation_findings.md", content)  # NO!
write_file("tmp/investigation_findings.md", content)   # NO!
write_file("/investigation_findings.md", content)      # NO!
```

The virtual filesystem expects files in the root - NO PATH PREFIXES!

## Phase Completion
When you complete investigation, save your findings:
- Format using the Required File Structure template above
- Save using: `write_file("investigation_findings.md", your_content)` - NO path prefix!
- Verify using: `ls()` to confirm the file appears in the virtual filesystem
- Only consider your work complete when investigation_findings.md is confirmed to exist

Remember: Your output becomes the foundation for all subsequent phases."""

# Agent configuration as simple dict (following research example pattern)
# NOTE: MCP tools will be added dynamically by atlas_agent.py using get_investigation_tools()
# Framework tools (write_file, write_todos, ls, read_file, edit_file) are automatically
# added by deepagents SubAgentMiddleware
investigation_agent = {
    "name": "investigation-agent",
    "description": "Phase 1: Autonomous project exploration and context gathering without user interaction",
    "prompt": INVESTIGATION_PROMPT,
    "tools": []  # Will be populated with MCP tools at runtime
}