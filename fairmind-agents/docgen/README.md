# DocGen Agent - Automated Code Documentation Generator

DocGen is an intelligent documentation generation agent built on the deepagents framework. It analyzes your codebase using MCP FairMind tools and generates comprehensive, high-quality documentation through a structured 5-phase methodology.

## Overview

DocGen automates the documentation process while maintaining accuracy and usefulness by:
- **Discovering** code structure autonomously
- **Scoping** documentation with user input
- **Analyzing** code deeply with parallel subagents
- **Clarifying** ambiguities through targeted questions
- **Generating** polished documentation iteratively

## Features

✅ **MCP FairMind Integration** - Direct access to code repositories via Code_ tools
✅ **Context Engineering** - Efficient token usage through virtual filesystem and compression
✅ **Parallel Analysis** - Multiple subagents analyze different modules simultaneously
✅ **User Interaction** - Strategic questions at key decision points
✅ **Multiple Documentation Styles** - API reference, developer guides, architecture docs, examples
✅ **Iterative Refinement** - User feedback incorporated throughout the process

## Architecture

### 5-Phase Methodology

```
Discovery → Scoping → Analysis → Clarification → Generation
  (Auto)    (User)     (Auto)      (User)        (User)
```

#### Phase 1: Discovery (Autonomous)
- Lists available projects and repositories
- Explores repository structure with Code_tree
- Catalogs files, directories, and organization patterns
- **Output**: `discovery_catalog.json`

#### Phase 2: Scoping (Interactive)
- Presents discovered repositories to user
- Gathers documentation preferences and priorities
- Defines target audience and documentation styles
- **Output**: `documentation_scope.json`

#### Phase 3: Analysis (Autonomous + Subagents)
- Launches specialized subagents for parallel analysis:
  - **repository-analyzer**: High-level structure
  - **code-analyzer**: Detailed module analysis
  - **api-documenter**: Public API extraction
  - **architecture-documenter**: System design
  - **example-generator**: Usage patterns
- **Outputs**: `analysis_summary.md`, `analysis_*.md` files

#### Phase 4: Clarification (Interactive)
- Reviews analysis outputs for ambiguities
- Formulates targeted questions with code context
- Gathers user input on design decisions and business logic
- **Output**: `clarifications_answered.json`

#### Phase 5: Generation (Interactive)
- Creates documentation based on analysis and clarifications
- Generates API reference, guides, architecture docs, examples
- Iteratively refines with user feedback
- **Outputs**: `final_documentation.md`, style-specific docs

## Installation

### Prerequisites

- Python 3.9+
- Access to MCP FairMind server
- Environment variables configured:
  - `ANTHROPIC_API_KEY`: For Claude models
  - `FAIRMIND_MCP_URL`: MCP server endpoint
  - `FAIRMIND_MCP_TOKEN`: MCP authentication token

### Setup

```bash
# From the deepagents_atlas root directory
cd examples/docgen

# Install dependencies
pip install -r requirements.txt

# Or install parent project with all dependencies
cd ../..
pip install -e .
```

### Configuration

Create a `.env` file in the `examples/docgen/` directory:

```bash
# Required
ANTHROPIC_API_KEY=your_anthropic_key_here
FAIRMIND_MCP_URL=https://your-mcp-server.com/mcp/
FAIRMIND_MCP_TOKEN=your_mcp_token_here

# Optional - Model configuration
DOCGEN_MODEL_NAME=claude-3-5-sonnet-20241022
DOCGEN_MODEL_TEMPERATURE=0.7
DOCGEN_MODEL_MAX_TOKENS=8192
```

## Usage

### Basic Usage

```python
import asyncio
from docgen_agent import create_docgen_agent

async def main():
    # Create the agent
    agent = create_docgen_agent()

    # Run documentation generation
    result = await agent.run(
        user_request="Generate developer documentation for the authentication module",
        project_id="your_project_id"
    )

    # Access results
    print(result['final_response'])
    print(f"Created {len(result['files'])} files")

asyncio.run(main())
```

### Running Examples

```bash
# Interactive examples
python example_usage.py

# Direct execution
python docgen_agent.py
```

### Example Requests

**Complete Documentation:**
```python
result = await agent.run(
    "Generate complete developer documentation including API reference, "
    "architecture overview, and usage examples",
    project_id="my_project"
)
```

**API Reference Only:**
```python
result = await agent.run(
    "Create API reference documentation for the user management and "
    "authentication modules. Target audience: external developers.",
    project_id="my_project"
)
```

**Architecture Documentation:**
```python
result = await agent.run(
    "Document the system architecture with component diagrams, "
    "data flow, and design decisions",
    project_id="my_project"
)
```

## Directory Structure

```
docgen/
├── agents/
│   ├── __init__.py
│   ├── discovery_agent.py       # Phase 1: Repository discovery
│   ├── scoping_agent.py         # Phase 2: Scope definition
│   ├── analysis_agent.py        # Phase 3: Code analysis coordinator
│   ├── clarification_agent.py   # Phase 4: Question gathering
│   └── generation_agent.py      # Phase 5: Documentation creation
├── subagents.py                 # Specialized subagent configurations
├── prompts.py                   # Detailed prompts for subagents
├── mcp_tools.py                 # MCP integration wrapper
├── docgen_agent.py              # Main agent interface
├── config.yaml                  # Configuration settings
├── example_usage.py             # Usage examples
├── requirements.txt             # Dependencies
└── README.md                    # This file
```

## Context Management

DocGen uses several strategies to manage context efficiently:

### Virtual Filesystem Offloading
Large content is stored in virtual filesystem:
```
discovery_catalog.json       # Repository catalog
documentation_scope.json     # User preferences
analysis_*.md               # Code analysis outputs
clarifications_answered.json # User Q&A
final_documentation.md      # Generated docs
```

### Intelligent Code Fetching
- Uses `Code_cat` with line range limits (max 500 lines)
- Archives code snippets to virtual FS
- References code by file:line instead of repeating

### Parallel Subagents
- Isolates context per subagent
- Runs multiple analyses in parallel
- Each subagent outputs to virtual FS

### Compression
- Archives phase outputs after completion
- Maintains summaries instead of full content
- Automatic archiving for content >3k chars

## Configuration

Edit `config.yaml` to customize:

```yaml
# Model settings
model:
  name: "claude-3-5-sonnet-20241022"
  temperature: 0.7
  max_tokens: 8192

# Documentation preferences
documentation:
  default_format: "markdown"
  include_examples: true
  include_architecture_diagrams: true

# Context management
context_management:
  archive_threshold_chars: 3000
  max_code_snippet_lines: 50
```

## Best Practices

### For Users

1. **Be Specific in Scoping** - Clearly define which modules to document
2. **Provide Context in Clarifications** - Explain business rules and design decisions
3. **Review Iteratively** - Give feedback during generation phase
4. **Start Small** - Document one module thoroughly before expanding

### For Developers

1. **Respect Virtual Filesystem** - Always use root-level filenames
2. **Use Tool Filters** - Each phase gets only necessary MCP tools
3. **Archive Large Content** - Don't keep code in main context
4. **Parallel When Possible** - Use subagents for independent work

## Troubleshooting

### MCP Connection Issues
```bash
# Verify environment variables
echo $FAIRMIND_MCP_URL
echo $FAIRMIND_MCP_TOKEN

# Check MCP server status
# (refer to FairMind documentation)
```

### Context Window Errors
- Reduce `max_file_size_lines` in config.yaml
- Lower `archive_threshold_chars` for more aggressive archiving
- Focus on fewer modules in scoping phase

### Phase Not Advancing
- Check that required output files exist (use `ls` in agent)
- Verify JSON files are valid
- Review phase validation in `subagents.py`

## Extending DocGen

### Adding New Subagents

1. Create prompt in `prompts.py`:
```python
MY_SUBAGENT_PROMPT = """You are a MySubagent..."""
```

2. Add configuration in `subagents.py`:
```python
my_subagent = {
    "name": "my-subagent",
    "description": "Does something specific",
    "prompt": MY_SUBAGENT_PROMPT,
    "tools": [],
}
```

3. Use in analysis or generation phase via `task` tool

### Customizing Documentation Styles

Edit phase agent prompts to support new formats:
- Modify `generation_agent.py` prompt
- Add style templates in `prompts.py`
- Update config.yaml with new style options

## Integration with deepagents Framework

DocGen is built on deepagents and follows its patterns:

- **Uses `async_create_deep_agent()`** - Core framework function
- **Virtual Filesystem** - Leverages LangGraph state for files
- **SubAgent Pattern** - Follows research example structure
- **Tool Inheritance** - Built-in tools automatically available
- **No Core Modifications** - All code in examples/docgen/

## Comparison with Atlas V1

| Feature | Atlas V1 | DocGen |
|---------|----------|--------|
| Phases | 4 | 5 |
| Focus | Task planning | Documentation |
| MCP Tools | Studio + Code | Primarily Code |
| User Interaction | Discussion phase | Scoping + Clarification + Generation |
| Subagents | Repository analyzers | 6 specialized types |
| Output | Implementation tasks | Documentation files |

## Roadmap

- [ ] Support for multiple output formats (HTML, PDF, Docusaurus)
- [ ] Integration with documentation hosting platforms
- [ ] Automatic API spec generation (OpenAPI, GraphQL schema)
- [ ] Documentation quality metrics
- [ ] Incremental updates (document only changed code)
- [ ] Multi-language support

## Contributing

This is an example implementation. To contribute:
1. Follow deepagents best practices
2. Don't modify core framework (`src/deepagents/`)
3. Add tests for new features
4. Update documentation

## License

Follows the parent project's license.

## Support

For issues or questions:
- Review deepagents documentation
- Check atlas_v1 example for patterns
- Refer to MCP FairMind documentation for tool usage

---

**Remember**: Great documentation comes from understanding both the code and its purpose. DocGen helps automate the process, but your domain knowledge makes it valuable.
