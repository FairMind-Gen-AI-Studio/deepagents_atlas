# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**deepagents** is a Python package that creates "deep agents" - LLM agents with enhanced capabilities including planning tools, sub-agents, virtual file systems, and detailed prompts. The project is built on LangGraph and inspired by Claude Code's architecture.

### Key Components
- **Core Framework**: Located in `src/deepagents/` - the main library for creating deep agents
- **Atlas V1 Implementation**: Located in `examples/atlas_v1/` - a specialized 4-phase planning agent with MCP Fairmind integration
- **Research Example**: Located in `examples/research/` - demonstrates using Tavily for web search with sub-agents

## Architecture

### Core Framework (`src/deepagents/`)
- **`graph.py`**: Main entry point with `create_deep_agent()` function
- **`tools.py`**: Built-in tools (write_todos, file operations on virtual filesystem)  
- **`sub_agent.py`**: Sub-agent creation and task delegation system
- **`state.py`**: LangGraph state management with `DeepAgentState`
- **`prompts.py`**: Built-in prompt templates and tool descriptions
- **`model.py`**: Model initialization and configuration

### Atlas V1 Architecture (`examples/atlas_v1/`)
The Atlas V1 agent implements a sophisticated 4-phase methodology:

1. **Investigation Phase**: Silent project exploration using MCP tools
2. **Discussion Phase**: Interactive requirements clarification  
3. **Planning Phase**: Repository analysis with parallel sub-agents
4. **Task Generation Phase**: Transform plans into actionable tasks

Key files:
- **`atlas_agent.py`**: Main AtlasAgentV1 class and orchestrator
- **`subagents.py`**: Agent configurations, phase definitions, and validation logic
- **`prompts.py`**: Detailed prompt templates for each agent type
- **`mcp_tools.py`**: MCP integration wrapper for Fairmind tools
- **`config.yaml`**: Configuration for models, phases, and MCP settings

## Common Development Commands

### Installation and Setup
```bash
# Install the package in development mode
pip install -e .

# Install with research example dependencies
pip install deepagents[research]  # Not yet implemented - use requirements

# For Atlas V1 example, install additional dependencies:
pip install langchain-litellm pydantic-settings
```

### Running Examples

#### Basic Research Agent
```bash
cd examples/research
python research_agent.py
# Requires: TAVILY_API_KEY environment variable
```

#### Atlas V1 Agent
```bash
cd examples/atlas_v1
python atlas_agent.py
# Requires: ANTHROPIC_API_KEY, FAIRMIND_MCP_URL, FAIRMIND_MCP_TOKEN
```

### Development and Testing

Currently no formal test suite is configured. Manual testing is done by:
1. Running example scripts
2. Testing with LangGraph Studio/CLI: `langgraph dev`
3. Manual verification of agent outputs and virtual filesystem operations

## Key Patterns and Conventions

### Virtual File System
All deep agents use a mock file system stored in LangGraph state under the `files` key:
- Files are stored as `Dict[str, str]` (filename -> content)
- Built-in tools: `ls`, `read_file`, `write_file`, `edit_file`
- No nested directories - flat structure only
- Content is preserved across agent invocations via LangGraph state

### Sub-Agent Pattern
Sub-agents are defined as dictionaries with required keys:
```python
{
    "name": "agent-name",
    "description": "What this agent does",
    "prompt": "System prompt for the agent",
    "tools": ["tool1", "tool2"]  # Optional, inherits parent tools by default
}
```

### Task Management
All agents have access to `write_todos` tool for planning and progress tracking:
- Use states: `pending`, `in_progress`, `completed`
- Only one task should be `in_progress` at a time
- Mark tasks completed immediately after finishing

### Model Configuration
- Default model: `"claude-sonnet-4-20250514"` (via `get_default_model()`)
- Atlas V1 uses LiteLLM for flexible model selection
- Model can be overridden per sub-agent in Atlas V1

### MCP Integration (Atlas V1)
Uses Fairmind MCP server for project management capabilities:
- **General_\*** tools: Project listing, document access, RAG search
- **Studio_\*** tools: User stories, needs, tasks, requirements
- **Code_\*** tools: Repository analysis, file reading, code search

### MCP Tool Filtering Architecture

The project uses a shared library at `src/fairmind/shared/mcp/` for centralized MCP tool management. This architecture enables precise tool assignment to different agent phases, improving security, efficiency, and maintainability.

#### Core Modules

**`client.py`** - MCP Connection Management
```python
from fairmind.shared.mcp import initialize_mcp_tools

# Initialize MCP connection
mcp_tools = await initialize_mcp_tools(
    server_name="fairmind",
    url=os.getenv("FAIRMIND_MCP_URL"),
    token=os.getenv("FAIRMIND_MCP_TOKEN")
)
```

**`filters.py`** - Tool Filtering and Presets
```python
from fairmind.shared.mcp import (
    filter_tools_by_names,
    create_tool_filter,
    # Preset filters
    ARCHQA_CONTEXT_MAPPER_FILTER,
    DOCGEN_DISCOVERY_FILTER,
)

# Use preset filter
context_tools = ARCHQA_CONTEXT_MAPPER_FILTER(mcp_tools)

# Create custom filter
custom_filter = create_tool_filter(
    include_prefixes=["General_", "Code_"],
    exclude_names=["Code_find_usages"]
)
filtered_tools = custom_filter(mcp_tools)
```

**`verification.py`** - Tool Verification and Logging
```python
from fairmind.shared.mcp import log_agent_startup

# Comprehensive startup logging
log_agent_startup(
    agent_name="MyAgent",
    mcp_tools=mcp_tools,
    phase_assignments={
        "phase1": phase1_tools,
        "phase2": phase2_tools,
    },
    critical_tools_per_phase={
        "phase1": ["General_list_projects"],
        "phase2": ["Code_search"],
    }
)
```

#### Tool Categories

MCP Fairmind tools are organized into three categories:

1. **General Tools** (`General_*`)
   - Project discovery and listing
   - Document access and retrieval
   - RAG-based knowledge search
   - Work session management
   - Examples: `General_list_projects`, `General_rag_retrieve_documents`

2. **Studio Tools** (`Studio_*`)
   - Business requirements (needs, user stories)
   - Task and development task management
   - Functional and technical requirements
   - Test case management
   - Examples: `Studio_list_user_stories_by_project`, `Studio_get_requirement`

3. **Code Tools** (`Code_*`)
   - Repository analysis and exploration
   - Code search (semantic and text-based)
   - File content retrieval
   - Usage analysis
   - Examples: `Code_search`, `Code_cat`, `Code_find_usages`

#### Preset Filters

The shared library provides tested preset filters for common agent phases:

**ArchQA Agent Filters**
```python
from fairmind.shared.mcp import (
    ARCHQA_CONTEXT_MAPPER_FILTER,      # 13 tools: General(5) + Studio(6) + Code(2)
    ARCHQA_CODE_INVESTIGATOR_FILTER,   # 10 tools: Code(6) + Studio(4)
    ARCHQA_SOLUTION_SYNTHESIZER_FILTER # 0 tools (filesystem only)
)

# Context Mapper: Project discovery and scope mapping
context_mapper_tools = ARCHQA_CONTEXT_MAPPER_FILTER(mcp_tools)
# Gets: list_projects, rag_retrieve_documents, list_user_stories,
#       list_repositories, tree, etc.

# Code Investigator: Deep code analysis
investigator_tools = ARCHQA_CODE_INVESTIGATOR_FILTER(mcp_tools)
# Gets: All Code_* tools + requirements/user stories for cross-reference

# Solution Synthesizer: No MCP tools (reads from virtual filesystem)
synthesizer_tools = ARCHQA_SOLUTION_SYNTHESIZER_FILTER(mcp_tools)
# Gets: Empty list - uses only built-in file tools
```

**DocGen Agent Filters**
```python
from fairmind.shared.mcp import (
    DOCGEN_DISCOVERY_FILTER,   # 7 tools: General(5) + Code(2)
    DOCGEN_ANALYSIS_FILTER,    # 6 tools: Code(6)
    DOCGEN_GENERATION_FILTER   # 6 tools: Code(6)
)

# Discovery: Find relevant projects and repositories
discovery_tools = DOCGEN_DISCOVERY_FILTER(mcp_tools)

# Analysis: Deep code exploration
analysis_tools = DOCGEN_ANALYSIS_FILTER(mcp_tools)

# Generation: Fetch code examples for documentation
generation_tools = DOCGEN_GENERATION_FILTER(mcp_tools)
```

**Basic Category Filters**
```python
from fairmind.shared.mcp import (
    GENERAL_TOOLS_FILTER,
    STUDIO_TOOLS_FILTER,
    CODE_TOOLS_FILTER
)

# Get all tools in a category
general_tools = GENERAL_TOOLS_FILTER(mcp_tools)
studio_tools = STUDIO_TOOLS_FILTER(mcp_tools)
code_tools = CODE_TOOLS_FILTER(mcp_tools)
```

#### Custom Filter Creation

Create specialized filters for new agent phases:

```python
from fairmind.shared.mcp import create_tool_filter

# Include only specific tool types
planning_filter = create_tool_filter(
    include_prefixes=["General_", "Studio_"],
    exclude_names=["General_rag_retrieve_specific_documents"]
)

# Exclude specific tools from a category
safe_code_filter = create_tool_filter(
    include_prefixes=["Code_"],
    exclude_names=["Code_find_usages"]  # Expensive operation
)

# Complex filtering
custom_filter = create_tool_filter(
    include_prefixes=["General_", "Code_"],
    exclude_prefixes=["Code_grep"],
    include_names=["Studio_list_user_stories_by_project"],
    exclude_names=["General_list_work_sessions"]
)

# Apply filter
filtered_tools = custom_filter(mcp_tools)
```

#### Tool Verification and Logging

Always verify tool availability at agent startup:

```python
from fairmind.shared.mcp import (
    log_agent_startup,
    verify_tool_availability,
    categorize_tools
)

# Method 1: Comprehensive startup logging (recommended)
log_agent_startup(
    agent_name="ArchQA",
    mcp_tools=mcp_tools,
    phase_assignments={
        "context-mapper": context_mapper_tools,
        "code-investigator": code_investigator_tools,
        "solution-synthesizer": solution_synthesizer_tools,
    },
    critical_tools_per_phase={
        "context-mapper": ["General_list_projects", "Code_list_repositories"],
        "code-investigator": ["Code_search", "Code_cat"],
        "solution-synthesizer": [],
    }
)

# Method 2: Manual verification for specific tools
missing = verify_tool_availability(
    tools_dict=mcp_tools,
    required_tools=["General_list_projects", "Code_search"],
    agent_name="MyAgent"
)
if missing:
    logger.error(f"Missing critical tools: {missing}")

# Method 3: Categorize for inspection
categorized = categorize_tools(mcp_tools)
logger.info(f"Available: {len(categorized['general'])} General, "
           f"{len(categorized['studio'])} Studio, "
           f"{len(categorized['code'])} Code tools")
```

#### Migration from Legacy Patterns

**Old Pattern (agent-local filters)**
```python
# OLD: fairmind-agents/archqa/mcp_tool_filters.py
from mcp_tool_filters import (
    get_context_mapper_tools,
    get_code_investigator_tools,
)

context_tools = get_context_mapper_tools(mcp_tools)
investigator_tools = get_code_investigator_tools(mcp_tools)

# Manual logging
logger.info(f"Context mapper tools: {len(context_tools)}")
```

**New Pattern (shared library)**
```python
# NEW: Use shared library
from fairmind.shared.mcp import (
    ARCHQA_CONTEXT_MAPPER_FILTER,
    ARCHQA_CODE_INVESTIGATOR_FILTER,
    log_agent_startup,
)

context_tools = ARCHQA_CONTEXT_MAPPER_FILTER(mcp_tools)
investigator_tools = ARCHQA_CODE_INVESTIGATOR_FILTER(mcp_tools)

# Automated comprehensive logging
log_agent_startup(
    agent_name="ArchQA",
    mcp_tools=mcp_tools,
    phase_assignments={"context-mapper": context_tools, ...},
    critical_tools_per_phase={"context-mapper": ["General_list_projects"], ...}
)
```

#### Tool Name Variant Handling

The filtering system automatically handles both tool name formats:

```python
# Both formats are matched automatically:
# - Short form: "General_list_projects"
# - Full form: "mcp__fairmind__General_list_projects"

filter_tools_by_names(
    mcp_tools,
    ["General_list_projects", "Code_search"]
)
# Matches both "General_list_projects" and "mcp__fairmind__General_list_projects"
```

#### Best Practices

1. **Use Preset Filters**: Start with tested presets before creating custom filters
2. **Verify at Startup**: Always call `log_agent_startup()` to verify tool availability
3. **Principle of Least Privilege**: Give each agent phase only the tools it needs
4. **Document Critical Tools**: Specify which tools are required vs. optional
5. **Test Filter Changes**: Verify agents work correctly after filter modifications
6. **Handle Missing Tools**: Check for empty tool lists before agent delegation

#### Common Patterns

**Pattern 1: Phase-Based Filtering**
```python
# Different tools for each phase
phase_filters = {
    "discovery": DOCGEN_DISCOVERY_FILTER,
    "analysis": DOCGEN_ANALYSIS_FILTER,
    "generation": DOCGEN_GENERATION_FILTER,
}

for phase_name, filter_func in phase_filters.items():
    phase_tools = filter_func(mcp_tools)
    agent["tools"] = phase_tools
```

**Pattern 2: Hierarchical Filtering**
```python
# Start broad, narrow down
all_code_tools = CODE_TOOLS_FILTER(mcp_tools)

# Then filter further
search_only = filter_tools_by_names(
    all_code_tools,
    ["Code_search", "Code_grep"]
)
```

**Pattern 3: Conditional Filtering**
```python
# Adjust based on agent capabilities
if agent_has_rag_capability:
    agent_filter = create_tool_filter(include_prefixes=["General_rag_"])
else:
    agent_filter = create_tool_filter(include_prefixes=["General_list_"])

agent_tools = agent_filter(mcp_tools)
```

## Important Implementation Details

### Context Management
- Atlas V1 implements smart archiving to preserve context window
- Large content (>3k characters) automatically archived to virtual filesystem
- Context summaries maintained for efficient retrieval

### Phase Validation
Atlas V1 includes automatic phase validation:
- Each phase has completion criteria in `subagents.py`
- Output files are validated before phase advancement
- Manual and automatic phase transitions supported

### Repository Mapping
Atlas V1 enforces 1:1 repository-to-task mapping in final task generation:
- Every task must specify exactly one repository
- Repository-task matrix validation prevents orphaned tasks
- Parallel repository analysis using specialized sub-agents

## Configuration Files

### `examples/atlas_v1/config.yaml`
```yaml
model:
  provider: "litellm"
  name: "claude-3-5-sonnet-20241022"
  temperature: 0.7
  max_tokens: 8192

phases: ["investigation", "discussion", "planning", "task_generation"]

mcp:
  fairmind:
    enabled: true
```

### Environment Variables Required
- `ANTHROPIC_API_KEY`: For Claude models via LiteLLM
- `FAIRMIND_MCP_URL`: MCP server endpoint  
- `FAIRMIND_MCP_TOKEN`: MCP authentication token
- `TAVILY_API_KEY`: For research example (optional)

## Debugging and Troubleshooting

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues
1. **MCP Connection Failures**: Check URL and token configuration
2. **Model API Errors**: Verify API keys and model names
3. **Phase Validation Failures**: Check required output files in virtual filesystem
4. **Context Window Issues**: Use virtual filesystem archiving for large content

### Virtual Filesystem Inspection
```python
# Access virtual filesystem from agent
status = agent.get_status()
files = agent.list_virtual_files()
content = agent.get_virtual_file("filename.md")
```

## Development Guidelines

### Adding New Sub-Agents (Atlas V1)
1. Create prompt template in `prompts.py`
2. Add agent configuration in `subagents.py` to `AGENT_CONFIGS`
3. Define validation criteria and required outputs
4. Add phase definition if creating new phase type

### Extending Core Framework  
- Follow existing tool patterns in `tools.py`
- Use `@tool` decorator for LangChain compatibility
- Implement proper state injection with `InjectedState`
- Return `Command` objects for state updates

### Testing New Features
1. Create minimal test case in examples directory
2. Test with different model configurations
3. Verify virtual filesystem operations work correctly
4. Test sub-agent delegation and response handling
- MOLTO MOLTO IMPORTANTE: non modificare '/Users/alexiocassani/Projects/deepagents_atlas/src/deepagents' che è il progetto core da non toccare MAI!!!
- IMPORTANTISSIMO: in '/Users/alexiocassani/Projects/deepagents_atlas/examples/research' c'è una best practice funzionante da guardare sempre come punto di riferimento!