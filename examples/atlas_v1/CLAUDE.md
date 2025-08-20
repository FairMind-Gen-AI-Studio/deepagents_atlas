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
- **`atlas_agent.py`**: Main AtlasAgentV1 class and orchestrator
- **`subagents.py`**: Agent configurations, phase definitions, and validation logic
- **`prompts.py`**: Detailed prompt templates for each agent type (recently updated with Phase Sequence Awareness)
- **`mcp_tools.py`**: MCP integration wrapper for Fairmind tools
- **`mcp_client.py`**: MCP client initialization and connection management
- **`config.yaml`**: Configuration for models, phases, and MCP settings

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

### Testing Phase Behavior
```bash
python test_phase_sequence.py  # Verify Phase Sequence Awareness
python test_discussion_phase.py  # Test discussion agent specifically
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

# Test phase sequence behavior
python test_phase_sequence.py

# Test discussion phase specifically
python test_discussion_phase.py

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

### Agent Not Following Phase Sequence
1. Check if `Phase Sequence Awareness Protocol` is in orchestrator prompt
2. Verify `read_file` calls are working for phase detection
3. Look for `human_input` permission requests in logs

### MCP Tools Not Available
1. Verify environment variables are set correctly
2. Check MCP server connectivity
3. Agent will work with builtin tools only if MCP unavailable

### Context Window Issues
1. Monitor virtual filesystem size with `ls` tool
2. Large content should auto-archive to virtual files
3. Manual archiving available via `write_file` tool

---

**Remember**: Atlas V1 implements a structured, methodical approach to project planning. The 4-phase sequence is critical for comprehensive analysis and should only be modified with careful consideration of the methodology's integrity.