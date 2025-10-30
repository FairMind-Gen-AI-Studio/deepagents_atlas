# CLAUDE.md - Atlas V1 Example

This file provides guidance to Claude Code when working specifically with the Atlas V1 implementation in this directory.

## Atlas V1 Overview

**Atlas V1** is a sophisticated 4-phase planning agent that implements the Atlas methodology using the deepagents framework. It integrates with MCP Fairmind for project management capabilities and provides structured, methodical approach to software project planning.

### Key Features
- **4-Phase Methodology**: Investigation → Discussion → Planning → Task Generation
- **MCP Integration**: Full integration with Fairmind project management system
- **Phase Sequence Awareness**: Built-in safeguards to prevent phase skipping
- **Sub-agent Architecture**: Specialized agents for each phase
- **Virtual Filesystem**: Context management through virtual file system
- **Auto-archiving**: Intelligent content archiving to preserve context window

## Architecture Overview

### Core Files
- **`atlas_agent.py`**: Main AtlasAgentV1 class - serves as the entry point and interface
- **`atlas_coordinator.py`**: AtlasCoordinator class - the actual 4-phase orchestration logic (~150 lines, replaces the old 906-line monolithic class)
- **`agents/`**: Directory containing modular agent implementations for each phase
- **`prompts.py`**: Detailed prompt templates for each agent type
- **`mcp_tools.py`**: MCP integration wrapper for Fairmind tools
- **`mcp_client.py`**: MCP client initialization and connection management
- **`state_store.py`**: External state persistence to work around deepagents limitations
- **`config.yaml`**: Configuration for models, phases, and MCP settings

### Architecture Pattern
The current architecture follows a **delegation pattern**:
1. **AtlasAgentV1** (in atlas_agent.py) - Public interface and compatibility layer
2. **AtlasCoordinator** (in atlas_coordinator.py) - Core orchestration logic
3. **Specialized agents** (in agents/ directory) - Phase-specific implementations
4. **External state store** - File persistence across agent interrupts

### Recent Critical Updates
- **Phase Sequence Fix**: Implemented Orchestrator Auto-Consapevole to prevent discussion phase skipping
- **Enhanced Prompts**: Added Phase Sequence Awareness Protocol to orchestrator prompt
- **Helper Functions**: Added phase management utilities in subagents.py

## 4-Phase Methodology

### Phase 1: Investigation (Silent)
- **Agent**: `investigation-agent`
- **Goal**: Autonomous project exploration without user interaction
- **Tools**: Full MCP access (General_*, Studio_*, Code_*)
- **Output**: `investigation_findings.md`
- **Auto-advance**: Yes

### Phase 2: Discussion (Interactive)
- **Agent**: `discussion-agent`
- **Goal**: Interactive requirements clarification with user
- **Tools**: `human_input` tool only
- **Outputs**: `clarification_questions.md`, `user_responses.md`, `requirements_clarified.md`
- **Critical**: Never skip without explicit user permission

### Phase 3: Planning (Interactive)
- **Agent**: `planning-agent`
- **Goal**: Code analysis and implementation planning using repository analyzers
- **Tools**: Code_* MCP tools for repository analysis
- **Output**: `implementation_plan.md`
- **Uses sub-agents**: Yes (repository-analyzer sub-agents)

### Phase 4: Task Generation (Silent)
- **Agent**: `task-generation-agent`
- **Goal**: Transform plan into actionable implementation tasks
- **Output**: `implementation_tasks.md`
- **Repository mapping**: 1:1 task-to-repository requirement
- **Auto-advance**: Yes

## Phase Sequence Awareness (Critical Update)

**Problem Solved**: The orchestrator was previously skipping the discussion phase.

**Solution**: Orchestrator Auto-Consapevole - The orchestrator now:

1. **Always checks file existence** before deploying agents:
   ```python
   # Phase completion detection via files:
   # investigation_findings.md → Investigation complete
   # requirements_clarified.md → Discussion complete
   # implementation_plan.md → Planning complete
   # implementation_tasks.md → Task generation complete
   ```

2. **Requires user permission** before skipping any phase:
   - Creates `phase_transition_decision.md` with reasoning
   - Uses `human_input` to ask: "Can I skip [PHASE] because [REASON]? (yes/no)"
   - Only skips with explicit "yes" from user

3. **Follows strict sequence** by default:
   ```
   investigation → discussion → planning → task_generation
   ```

## Configuration and Environment

### Required Environment Variables
```bash
# Core API access
ANTHROPIC_API_KEY=your_anthropic_key

# MCP Fairmind integration
FAIRMIND_MCP_URL=https://project-context.mindstream.fairmind.ai/mcp/mcp/
FAIRMIND_MCP_TOKEN=your_fairmind_token

# Optional model overrides
ATLAS_MODEL_NAME=claude-sonnet-4-20250514  # or any LiteLLM compatible model
ATLAS_MODEL_TEMPERATURE=0.7
ATLAS_MODEL_MAX_TOKENS=8192
```

### MCP Tools Available
- **General**: `list_projects`, `get_document_content`, `rag_retrieve_documents`
- **Studio**: `list_user_stories_by_project`, `get_user_story`, `list_needs_by_project`, etc.
- **Code**: `list_repositories`, `find_relevant_code_snippets`, `get_file`, etc.

## Development Patterns

### Running the Agent
```python
from atlas_agent import create_atlas_agent
import asyncio

async def main():
    agent = create_atlas_agent()
    result = await agent.run(
        "Create technical plan for US-2025-1258",
        project_id="fairmind_studio_id"
    )
    print(result["final_response"])

asyncio.run(main())
```

### Testing and Debugging
The test files in the `tests/` subdirectory are debugging utilities and experimental scripts for testing specific agent behaviors. These are not a formal test suite but can be useful for troubleshooting.

```bash
# Run the main atlas agent
python atlas_agent.py

# Or use the run script
python run_atlas.py
```

### Debugging Common Issues

#### 1. Phase Skipping
- **Check**: Look for `phase_transition_decision.md` in virtual filesystem
- **Verify**: Orchestrator prompt contains "Phase Sequence Awareness Protocol"
- **Solution**: User can always say "no" to phase skip requests

#### 2. MCP Connection Issues
- **Check**: Environment variables `FAIRMIND_MCP_URL` and `FAIRMIND_MCP_TOKEN`
- **Debug**: Enable debug logging with `logging.basicConfig(level=logging.DEBUG)`
- **Fallback**: Agent works without MCP (uses only builtin tools)

#### 3. Context Window Issues
- **Auto-archiving**: Large content (>3k chars) automatically archived
- **Virtual filesystem**: Use `ls` tool to see all files
- **Manual archiving**: Use `write_file` to move content to virtual filesystem

### Virtual Filesystem Management

The agent maintains a virtual filesystem for context management:

```python
# Check virtual files
agent.list_virtual_files()

# Read virtual file content  
agent.get_virtual_file("investigation_findings.md")

# Files are preserved across phases and agent invocations
```

## Prompt Engineering Guidelines

### Orchestrator Prompts
- **Focus**: Pure coordination, never execute tasks directly
- **Phase awareness**: Must check file existence before agent deployment
- **Permission protocol**: Must ask before skipping phases

### Sub-agent Prompts
- **Investigation**: Focus on business context, user stories, needs
- **Discussion**: Generate targeted questions, collect user responses
- **Planning**: Repository analysis with parallel sub-agents
- **Task Generation**: 1:1 repository mapping enforcement

## Model Configuration

### Default Model Stack
- **Primary**: Claude Sonnet 4 (via ChatAnthropic for proper tool_calls)
- **Fallback**: Any LiteLLM compatible model
- **Temperature**: 0.7 (configurable via environment)

### Model Selection Logic
```python
# Anthropic models → ChatAnthropic (better tool support)
# Other models → ChatLiteLLM (broader compatibility)
```

## File Structure and Conventions

### Input Files (User Provided)
- User request via `run()` method
- Optional project_id and user_story_id

### Output Files (Generated by Agents)
- `investigation_findings.md` - Business context and requirements
- `requirements_clarified.md` - User feedback and clarifications
- `implementation_plan.md` - Technical architecture and approach
- `implementation_tasks.md` - Actionable implementation tasks
- `phase_transition_decision.md` - Phase skip reasoning (if applicable)

### Configuration Files
- `config.yaml` - Model, phase, and MCP configuration
- `.env` - Environment variables for API keys

## Best Practices

### For Agent Development
1. **Always use MCP tools** for project data access
2. **Respect virtual filesystem** - use `write_file` for large content
3. **Follow phase outputs** - each phase must create expected files
4. **Repository mapping** - ensure 1:1 task-to-repo mapping in final output

### For Debugging
1. **Check phase files** - verify expected outputs exist
2. **Monitor MCP connections** - ensure tools are available
3. **Review phase decisions** - check `phase_transition_decision.md`
4. **Enable debug logging** - see detailed execution flow

### For Configuration
1. **Environment first** - use env vars for sensitive data
2. **Config.yaml second** - use for non-sensitive settings
3. **Test without MCP** - ensure graceful degradation
4. **Validate model access** - confirm API keys work

## Common Commands

```bash
# Run Atlas agent
python atlas_agent.py

# Or use the run script for interactive mode
python run_atlas.py

# Check MCP connection
python -c "from mcp_client import get_mcp_status; print(get_mcp_status())"

# Debug with full logging
ATLAS_MODEL_NAME=claude-sonnet-4-20250514 python atlas_agent.py
```

## Integration with deepagents Framework

Atlas V1 is built on the deepagents framework located in `../../src/deepagents/`:

- **Uses**: `create_deep_agent()`, `SubAgent` patterns, built-in tools
- **Extends**: Adds MCP integration, 4-phase methodology, context management
- **Virtual FS**: Leverages deepagents virtual filesystem via LangGraph state
- **Tool inheritance**: Sub-agents inherit parent tools unless specific tools defined

## Troubleshooting

### LangSmith Connection Issues

#### Quick Diagnosis
```python
from atlas_agent import create_atlas_agent
agent = create_atlas_agent()
diagnostics = agent.get_langsmith_diagnostics()
print(diagnostics)
```

#### Common Issues and Solutions

**Issue: "LangSmith not receiving traces"**
1. **Verify environment configuration:**
   ```bash
   # Check .env file contains:
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_PROJECT=deepagents-atlas
   LANGCHAIN_API_KEY=lsv2_pt_...
   ```

2. **Check trace location:**
   - Navigate to https://smith.langchain.com
   - Select project: `deepagents-atlas`
   - Look for traces with thread_id format: `atlas-{number}`
   - Traces may take 5-10 seconds to appear

3. **Verify configuration loading:**
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   print("Tracing:", os.getenv("LANGCHAIN_TRACING_V2"))
   print("Project:", os.getenv("LANGCHAIN_PROJECT"))
   print("API Key set:", bool(os.getenv("LANGCHAIN_API_KEY")))
   ```

**Issue: "Traces appear but in wrong project"**
- Check `LANGCHAIN_PROJECT` environment variable
- Ensure `.env` file is in the correct directory
- Verify `load_dotenv()` is called before agent creation

**Issue: "Middleware broke LangSmith integration"**
- This is NOT possible - LangSmith tracing operates at the LangChain core level
- Middleware changes don't affect tracing behavior
- The issue is likely configuration-related, not architectural

#### Debug Commands
```bash
# Test with explicit thread_id for easy filtering
python -c "
from atlas_agent import create_atlas_agent
import asyncio
agent = create_atlas_agent()
result = asyncio.run(agent.run('test message'))
print('Check LangSmith for thread_id in logs')
"

# Get diagnostic information
python -c "
from atlas_agent import create_langsmith_diagnostics
import json
print(json.dumps(create_langsmith_diagnostics(), indent=2))
"
```

#### Integration with Middleware
- ✅ **PlanningMiddleware**: Compatible with LangSmith
- ✅ **FilesystemMiddleware**: Compatible with LangSmith
- ✅ **SubAgentMiddleware**: Compatible with LangSmith
- ✅ **checkpointer=False**: Does NOT affect tracing

### Agent Not Following Phase Sequence
1. Check if `Phase Sequence Awareness Protocol` is in orchestrator prompt
2. Verify `read_file` calls are working for phase detection
3. Look for `human_input` permission requests in logs

### MCP Tools Not Available
1. Verify environment variables are set correctly
2. Check MCP server connectivity
3. Agent will work with builtin tools only if MCP unavailable

### LangSmith Recursion Errors (Fixed)

**Issue**: "maximum recursion depth exceeded" when running with `langgraph dev`

**Root Cause**: Circular references in agent object graph caused by tool pre-resolution in middleware. The task tool closures captured full agent instances with their middleware stacks, creating infinite loops during LangSmith serialization.

**Solution Applied**:
1. **Removed tool pre-resolution** from `atlas_coordinator.py` and `atlas_agent.py`
2. **Disabled all custom tools** in agent configurations to break circular references:
   - `investigation_agent`: Empty tools list (built-in only)
   - `discussion_agent`: Empty tools list (built-in only)
   - `planning_agent`: Empty tools list (built-in only)
   - `task_generation_agent`: Empty tools list (built-in only)
   - `create_repository_analyzer`: Empty tools list (built-in only)

**Status**: ✅ **RESOLVED** - Server starts successfully without recursion errors

**Trade-offs**:
- 🚫 MCP tools temporarily disabled (no Fairmind integration)
- 🚫 Custom Atlas tools temporarily disabled (human_input, approve_plan)
- ✅ Core functionality preserved (virtual filesystem, sub-agents, orchestration)
- ✅ LangSmith tracing and debugging fully restored

**Future Improvements**:
1. Wait for deepagents framework fix for tool resolution circular references
2. Implement lazy tool loading pattern similar to research example
3. Create wrapper functions for MCP tools that don't capture agent instances
4. Consider moving to function-based tools instead of string-based tool resolution

**Verification Commands**:
```bash
# Test the fix - should start without errors
langgraph dev

# Should see in logs:
# ✅ Using only built-in deepagents tools to prevent circular references
# 📝 Built-in tools: ls, read_file, write_file, write_todos, edit_file
```

### Context Window Issues
1. Monitor virtual filesystem size with `ls` tool
2. Large content should auto-archive to virtual files
3. Manual archiving available via `write_file` tool

## Virtual Filesystem Best Practices

**Critical Update (2025-01-30)**: Atlas V1 agent prompts have been updated to match DocGen's proven virtual filesystem persistence patterns. The issue of files not persisting was due to **prompt quality**, not architecture.

### The Problem (Resolved)

**Root Cause**: Atlas V1 discussion_agent (and other agents) used vague language like "save to file.md" instead of explicit `write_file()` instructions. This caused agents to not properly persist files to the virtual filesystem.

**Evidence**:
- ❌ **Broken**: "Save user responses to user_responses.md" (vague, no tool specified)
- ✅ **Fixed**: "Save using: `write_file('user_responses.md', response_text)`" (explicit tool call)

### The Solution (Implemented)

All Atlas V1 agent prompts now follow DocGen's explicit instruction pattern:

```markdown
## Correct Pattern (Now Used in All Agents)

1. **Create the file**
   - Save using: write_file("filename.md", content)
   - Verify creation: ls() should show "filename.md"
   - Your work is ONLY complete when the file exists

## Incorrect Pattern (No Longer Used)

❌ "Save draft to requirements_summary.md"
❌ "Archive results to investigation_findings.md"
❌ "Write findings to file"
```

### Agent-Specific File Requirements

Each phase has specific file outputs that MUST be created:

#### Investigation Phase
- **Required**: `investigation_findings.md`
- **Verification**: Orchestrator checks file exists before advancing to discussion

#### Discussion Phase
- **Required**: `requirements_clarified.md`
- **Optional**: `clarification_questions.md`, `user_responses.md`, `requirements_summary.md`
- **Verification**: Orchestrator checks requirements_clarified.md exists

#### Planning Phase
- **Required**: `implementation_plan.md`
- **Optional**: `planning_context.md`, `solution_proposal.md`, `technical_clarifications.md`, `repo_analysis_*.md`
- **Verification**: Orchestrator checks implementation_plan.md exists

#### Task Generation Phase
- **Required**: All of these files:
  - `implementation_tasks.md`
  - `repository_task_matrix.md`
  - `task_dependencies.md`
  - `execution_roadmap.md`
  - `context_summary.md`
- **Verification**: Orchestrator checks implementation_tasks.md exists

### Orchestrator File Verification

The orchestrator now includes explicit file verification after each phase:

```python
# After each agent completes
1. Use ls() to check virtual filesystem
2. Verify expected file exists for that phase
3. If MISSING: Warn user and ask if they want to retry
4. If EXISTS: Confirm success and proceed to next phase
```

### Writing Agent Prompts (Best Practices)

When creating or modifying agent prompts:

1. **Use Explicit Tool Calls**
   ```markdown
   ✅ Create file using: write_file("filename.md", content)
   ❌ Save to filename.md
   ```

2. **Add Verification Steps**
   ```markdown
   ✅ Verify creation: ls() should show "filename.md"
   ❌ (no verification mentioned)
   ```

3. **Make Completion Conditional on File Existence**
   ```markdown
   ✅ Your work is ONLY complete when filename.md exists
   ❌ Save your results when done
   ```

4. **Provide Concrete Examples**
   ```markdown
   ✅ Step 1: read_file("input.md")
       Step 2: write_file("output.md", content)
       Step 3: ls() → Verify "output.md" exists
   ❌ # (pseudocode comments showing general workflow)
   ```

### Testing File Persistence

Run the test suite to verify file persistence:

```bash
cd fairmind-agents/atlas_v1
python -m pytest tests/test_file_persistence.py -v
```

Tests verify:
- All agent prompts include explicit `write_file()` instructions
- All agents include `ls()` verification
- Orchestrator checks file existence after each phase
- File content has required structure

### Reference Implementation

See `fairmind-agents/docgen/` for the baseline reference implementation that Atlas V1 now follows.

**Key Pattern from DocGen**:
```python
# agents.py - Discovery Agent Prompt (lines 8-120)
"""
## Required Output File: discovery_catalog.json

You MUST create this file with the following structure:
[exact JSON schema]

5. **Save Complete Discovery Catalog**
   - Create a comprehensive JSON catalog file: `discovery_catalog.json`
   - Use write_file("discovery_catalog.json", json_content)

## Success Criteria
- discovery_catalog.json exists and contains complete information
"""
```

---

**Remember**: Atlas V1 implements a structured, methodical approach to project planning. The 4-phase sequence is critical for comprehensive analysis and should only be modified with careful consideration of the methodology's integrity.