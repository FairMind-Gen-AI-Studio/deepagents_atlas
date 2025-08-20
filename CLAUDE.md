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