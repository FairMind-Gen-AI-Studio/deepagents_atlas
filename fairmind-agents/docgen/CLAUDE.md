# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**DocGen** is an intelligent code documentation generation agent built on the deepagents framework. It uses MCP FairMind tools to analyze codebases and generates comprehensive documentation through a structured 5-phase methodology. This is an example implementation showcasing deepagents patterns similar to the research and atlas_v1 examples.

### Key Architecture Concepts

**Orchestrator-Subagent Delegation Pattern**
- **Orchestrator**: Coordinates phases, has NO MCP tools, only delegates via `task` tool
- **Subagents**: 5 specialized phase agents that receive MCP tools as needed
- Virtual filesystem used for state persistence between phases

**5-Phase Methodology**
1. **Discovery** (autonomous) → `discovery_catalog.json`
2. **Scoping** (interactive) → `documentation_scope.json`
3. **Analysis** (autonomous + parallel subagents) → `analysis_summary.md`, `analysis_*.md`
4. **Clarification** (interactive) → `clarifications_answered.json`
5. **Generation** (interactive) → `final_documentation.md`

## Common Development Commands

### Installation & Setup
```bash
# From docgen directory
pip install -r requirements.txt

# Ensure parent deepagents is installed
cd ../../
pip install -e .
```

### Running the Agent

**Basic execution:**
```bash
cd examples/docgen
python docgen_agent.py
```

**Interactive examples:**
```bash
python example_usage.py
```

**With LangGraph Studio:**
```bash
langgraph dev
# Then open LangGraph Studio UI
```

### Environment Configuration

Create `.env` file in `examples/docgen/`:
```bash
# Required
ANTHROPIC_API_KEY=sk-...
FAIRMIND_MCP_URL=https://your-server.com/mcp/
FAIRMIND_MCP_TOKEN=your-token

# Optional
DOCGEN_MODEL_NAME=claude-3-5-sonnet-20241022
DOCGEN_MODEL_TEMPERATURE=0.7
DOCGEN_MODEL_MAX_TOKENS=8192
```

### Testing MCP Connection
```bash
python test_mcp_tools.py
```

## Architecture Deep Dive

### Critical Design Pattern: Tool Delegation

**The orchestrator does NOT have MCP tools by design**. This is correct behavior, not a bug:

```python
# docgen_agent.py:449-454
return create_deep_agent(
    model=model,
    tools=[],  # Orchestrator has no tools - delegates to subagents
    instructions=orchestrator_instructions,
    subagents=subagents,
).with_config({"recursion_limit": 1000})
```

The orchestrator only:
1. Calls `ls` to check virtual filesystem state (built-in tool)
2. Calls `write_todos` to track progress (built-in tool)
3. Calls `task` to delegate to phase agents (built-in tool)

**Subagents receive phase-specific MCP tools**:
- Discovery: `General_*` + `Code_tree`, `Code_list_repositories`
- Analysis: `Code_search`, `Code_cat`, `Code_grep`, `Code_find_usages`
- Generation: `Code_*` tools for fetching examples

### Phase Agent Definitions

Phase agents are defined in `agents.py` (NOT in `agents/` directory - that's a collection of standalone agent definitions). Key structure:

```python
# agents.py defines:
discovery_agent = {
    "name": "discovery-agent",
    "description": "...",
    "prompt": DISCOVERY_PROMPT,
    "tools": []  # Populated at runtime via get_discovery_tools()
}
```

Tool assignment happens in `docgen_agent.py:190-204` via phase-specific tool filtering functions.

### Virtual Filesystem Phase Markers

Phases are determined by checking for specific files:
- No files → Phase 1 (Discovery)
- `discovery_catalog.json` exists → Phase 2 (Scoping)
- `documentation_scope.json` exists → Phase 3 (Analysis)
- `analysis_summary.md` exists → Phase 4 (Clarification)
- `clarifications_answered.json` exists → Phase 5 (Generation)
- `final_documentation.md` exists → Complete

### Parallel Subagent Analysis

Phase 3 (Analysis) can spawn multiple parallel subagents for repository/module analysis:

```python
# subagents.py:14-42
def create_repository_analyzer(repo_name: str, mcp_tools: dict = None):
    """Dynamically creates repo-specific analyzer subagent"""
    return {
        "name": f"repository-analyzer-{repo_name}",
        "description": f"Analyzes {repo_name} repository",
        "prompt": REPOSITORY_ANALYZER_PROMPT.replace("{repo_name}", repo_name),
        "tools": code_tools,  # Filtered Code_* tools only
    }
```

The analysis agent spawns these via the `task` tool with repository-specific prompts.

### MCP Tool Filtering

Each phase gets filtered MCP tools based on needs:

```python
# agents.py tool filter functions
def get_discovery_tools(mcp_tools):
    # Returns: General_list_projects, General_rag_*, Code_list_repositories, Code_tree

def get_analysis_tools(mcp_tools):
    # Returns: Code_search, Code_cat, Code_grep, Code_find_usages

def get_generation_tools(mcp_tools):
    # Returns: Same as analysis (Code_* tools for fetching examples)
```

This prevents tool pollution and keeps token usage efficient.

## Important Implementation Details

### Model Configuration Override Pattern

The model can be overridden via environment variable:

```python
# docgen_agent.py:172-185
model_name = os.getenv("DOCGEN_MODEL_NAME", "claude-3-5-sonnet-20241022")
model_name = model_name.replace("anthropic/", "").replace("openai/", "")

if model_name != "claude-sonnet-4-20250514":
    model = ChatAnthropic(model_name=model_name, max_tokens=64000)
else:
    model = get_default_model()
```

### MCP Client Import from Atlas V1

DocGen reuses the MCP client initialization from atlas_v1:

```python
# docgen_agent.py:25-38
def _get_mcp_initialize():
    """Get MCP tools initialization function from atlas_v1."""
    try:
        atlas_path = str(Path(__file__).parent.parent / "atlas_v1")
        sys.path.insert(0, atlas_path)
        from mcp_client import initialize_mcp_tools
        return initialize_mcp_tools
    except ImportError:
        return None
```

This is a temporary pattern - production implementations should have their own MCP client.

### Context Management Strategy

DocGen implements aggressive context management:

1. **Large content archived to virtual filesystem** (threshold: 3000 chars)
2. **Code snippets limited to 500 lines max** via `Code_cat(max_lines=500)`
3. **Phase outputs compressed after completion** - only summaries retained
4. **Parallel subagents isolate context** - each has independent state

### Phase Validation

Phase completion is validated in `subagents.py:109-245`:

```python
PHASE_VALIDATORS = {
    "discovery": validate_discovery_complete,
    "scoping": validate_scoping_complete,
    "analysis": validate_analysis_complete,
    "clarification": validate_clarification_complete,
    "generation": validate_generation_complete,
}
```

Each validator checks:
- Required files exist in virtual filesystem
- Files contain valid JSON/markdown
- Required fields present in JSON files

## Debugging and Troubleshooting

### Common Issues

**"Discovery agent has NO MCP tools"**
- Check `FAIRMIND_MCP_URL` and `FAIRMIND_MCP_TOKEN` in `.env`
- Run `test_mcp_tools.py` to verify connection
- Check that MCP server is accessible from your network

**"Orchestrator not delegating to subagents"**
- This is expected! Check LangSmith traces for `task` tool invocations
- The orchestrator should ONLY call `ls`, `write_todos`, and `task`
- Look for subagent execution in nested trace nodes

**"Phase not advancing"**
- Call `ls` in the agent to see what files exist
- Check phase validation in `subagents.py` for required files
- Verify JSON files are valid (not malformed)

**"Context window exceeded"**
- Lower `max_file_size_lines` in `config.yaml` (default: 500)
- Increase `archive_threshold_chars` for more aggressive archiving (default: 3000)
- Focus on fewer repositories during scoping phase

### Debug Logging

Enable debug logging to see tool assignment:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

The agent logs extensive MCP tool verification at startup (see `docgen_agent.py:254-322`).

### LangGraph Studio Debugging

Use LangGraph Studio to visualize agent execution:

1. Start dev server: `langgraph dev`
2. Open LangGraph Studio UI
3. Look for:
   - Orchestrator node → only has `task` tool
   - Subagent nodes → have MCP tools
   - `task` tool invocations → show delegation with full subagent prompts

## Development Guidelines

### Adding New Subagents

1. **Create prompt in `prompts.py`:**
```python
MY_ANALYZER_PROMPT = """You are a MyAnalyzer subagent..."""
```

2. **Add factory function to `subagents.py`:**
```python
def create_my_analyzer(target_name: str, mcp_tools: dict = None):
    return {
        "name": f"my-analyzer-{target_name}",
        "description": "Analyzes...",
        "prompt": MY_ANALYZER_PROMPT.replace("{target}", target_name),
        "tools": filter_code_tools(mcp_tools),
    }
```

3. **Use in analysis phase** via `task` tool with dynamic subagent creation

### Extending Phase Functionality

**Add new phase:**
1. Create phase agent in `agents.py`
2. Add tool filter function `get_phase_tools()`
3. Add phase validation in `subagents.py`
4. Update orchestrator instructions in `docgen_agent.py:325-437`
5. Add to `PHASE_VALIDATORS` and `PHASE_OUTPUTS`

**Modify existing phase:**
1. Update phase prompt in `agents.py`
2. Modify tool filter if needed
3. Update phase validation if output format changes

### Testing New Features

No formal test suite exists. Manual testing approach:

1. **Test with LangGraph Studio** - visualize execution
2. **Check virtual filesystem** - verify expected files created
3. **Validate JSON outputs** - ensure proper structure
4. **Test MCP tool calls** - use `test_mcp_tools.py` as reference

## Integration with deepagents Framework

DocGen follows deepagents best practices:

✅ **Uses `create_deep_agent()`** from core framework
✅ **Virtual filesystem** for state persistence
✅ **SubAgent pattern** with `task` tool delegation
✅ **Built-in tools** automatically available (`ls`, `write_file`, etc.)
✅ **No core modifications** - all code in `examples/docgen/`

**Reference implementation:** Check `examples/research/` for simpler subagent pattern.

## Configuration Reference

### config.yaml Structure

```yaml
model:
  name: "claude-3-5-sonnet-20241022"
  temperature: 0.7
  max_tokens: 8192

phases:
  - discovery
  - scoping
  - analysis
  - clarification
  - generation

documentation:
  max_file_size_lines: 500

context_management:
  archive_threshold_chars: 3000
  max_code_snippet_lines: 50
```

### Phase Configuration Options

```yaml
phase_config:
  discovery:
    timeout_minutes: 20
    auto_advance: true

  analysis:
    parallel_subagents: true
    max_parallel: 3
```

## File Organization

```
docgen/
├── docgen_agent.py          # Main entry point, orchestrator setup
├── agents.py                # Phase agent definitions and tool filters
├── agents/                  # Standalone agent definitions (alternative structure)
├── subagents.py            # Subagent factories and phase validators
├── prompts.py              # Detailed subagent prompts
├── mcp_tools.py            # MCP integration wrapper (legacy)
├── config.yaml             # Configuration settings
├── example_usage.py        # Usage examples
├── test_mcp_tools.py       # MCP connection testing
├── langgraph.json          # LangGraph Studio configuration
└── requirements.txt        # Dependencies
```

**Note:** Both `agents.py` and `agents/` exist - `agents.py` is the active implementation.

## Comparison with Atlas V1

| Feature | Atlas V1 | DocGen |
|---------|----------|--------|
| Phases | 4 | 5 |
| Focus | Task planning | Documentation generation |
| MCP Tools | Studio + Code | Primarily Code + General |
| User Interaction | Discussion phase | Scoping + Clarification + Generation |
| Parallel Execution | Repository analyzers | Repository + module analyzers |
| Output Format | Task JSON | Markdown documentation |

Both share the orchestrator-subagent delegation pattern and virtual filesystem usage.

## Known Limitations

1. **No incremental updates** - must regenerate full documentation
2. **Single project at a time** - no multi-project documentation
3. **Markdown only** - no HTML/PDF export
4. **No diagram generation** - architecture diagrams are described, not rendered
5. **Manual phase advancement** - orchestrator decides, but no automatic rollback

## Important Notes

- **NEVER modify core framework** (`src/deepagents/`) when working on this example
- **Reference research example** (`examples/research/`) for simpler patterns
- **Reuse atlas_v1 MCP client** temporarily - should have own client in production
- **Orchestrator has no MCP tools** - this is correct design, not a bug!
