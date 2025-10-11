# Atlas V1 Agent 🧭

**Deep Planning Agent** implementing the 4-phase Atlas methodology with MCP Fairmind integration.

## Overview

Atlas V1 is a specialized deep agent that transforms user stories into implementation-ready plans through a systematic 4-phase approach:

1. **🔍 Investigation** - Silent project exploration and context gathering
2. **💬 Discussion** - Interactive requirements clarification with targeted questions
3. **📋 Planning** - Repository analysis and technical solution design
4. **⚡ Task Generation** - Convert approved plan into actionable implementation tasks

## Key Features

- **MCP Integration**: Full integration with Fairmind MCP tools for project analysis
- **LiteLLM Support**: Flexible model selection (Claude, GPT, etc.) via LiteLLM
- **Repository Analysis**: Deep code analysis with specialized sub-agents
- **Virtual Filesystem**: Efficient context management and archiving
- **Interactive Approval**: User validation at critical decision points
- **1:1 Task Mapping**: Every generated task maps to exactly one repository

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Setup

```bash
cp .env.example .env
# Edit .env with your API keys and MCP configuration
```

### 3. Run with LangGraph CLI

```bash
# Start the agent in development mode
langgraph dev

# Or run directly
python atlas_agent.py
```

### 4. Use the Agent

```python
from atlas_agent import create_atlas_agent

# Initialize agent
agent = create_atlas_agent()

# Run on a user story
result = await agent.run(
    user_request="I need to implement user authentication for the mobile app",
    project_id="your-project-id",
    user_story_id="US-123"  # optional
)

print(f"Status: {result['status']}")
print(f"Completion: {result['completion_percentage']}%")
```

## Configuration

### Model Configuration (config.yaml)

```yaml
model:
  provider: "litellm"
  name: "claude-3-5-sonnet-20241022"  # or gpt-4, etc.
  temperature: 0.7
  max_tokens: 8192

mcp:
  fairmind:
    enabled: true
```

### Environment Variables (.env)

```bash
# Required for LiteLLM
ANTHROPIC_API_KEY=your_key_here

# Required for MCP Fairmind
FAIRMIND_MCP_URL=https://your-fairmind-endpoint
FAIRMIND_MCP_TOKEN=your_token_here
```

## Architecture

### Orchestrator
The main agent coordinates the 4-phase workflow and delegates work to specialized sub-agents.

### Sub-agents
- **Investigation Agent**: Uses General_*, Studio_*, Code_* MCP tools
- **Discussion Agent**: Interactive user communication (no MCP tools)
- **Planning Agent**: Uses Code_* MCP tools + deploys repository analyzers
- **Task Generation Agent**: Transforms plans into tasks (no MCP tools)

### Repository Analyzers
Specialized sub-agents created by the Planning Agent to analyze individual repositories in parallel.

## 4-Phase Workflow

### Phase 1: Investigation 🔍
- **Duration**: 15-30 minutes
- **Mode**: Silent (no user interaction)
- **Tools**: General_*, Studio_*, Code_* MCP tools
- **Outputs**: 
  - `investigation_findings.md`
  - `business_context.md`
  - `technical_analysis.md`

**What happens**: Agent autonomously explores the project, reads user stories, analyzes business needs, and discovers technical patterns.

### Phase 2: Discussion 💬
- **Duration**: 10-20 minutes  
- **Mode**: Interactive
- **Tools**: Virtual filesystem only
- **Outputs**:
  - `clarification_questions.md`
  - `user_responses.md`
  - `requirements_clarified.md`

**What happens**: Agent generates 5-7 targeted questions, collects user responses, consolidates requirements, and gets explicit approval.

### Phase 3: Planning 📋
- **Duration**: 20-40 minutes
- **Mode**: Interactive with approval points
- **Tools**: Code_* MCP tools + repository analyzers
- **Outputs**:
  - `technical_solution_proposal.md`
  - `implementation_plan.md`
  - `repo_analysis_*.md` (per repository)

**What happens**: Agent analyzes all repositories with sub-agents, proposes technical solution interactively, gets user approval, then creates detailed 8-section implementation plan.

### Phase 4: Task Generation ⚡
- **Duration**: 10-15 minutes
- **Mode**: Silent
- **Tools**: Virtual filesystem only
- **Outputs**:
  - `implementation_tasks.md`
  - `focus_chain.md`
  - `success_criteria.md`
  - `next_steps.md`
  - `repository_task_matrix.md`

**What happens**: Agent transforms approved plan into actionable tasks with mandatory 1:1 repository mapping.

## Virtual Filesystem

The agent uses a virtual filesystem to manage context efficiently:

```python
# Access files from the agent
status = agent.get_status()
files = agent.list_virtual_files()
content = agent.get_virtual_file("implementation_plan.md")
```

Files are automatically archived when they exceed 3,000 characters to preserve context window.

## MCP Tools Integration

### Investigation Agent Tools
- `General_list_projects`, `General_rag_retrieve_documents`
- `Studio_list_user_stories_by_project`, `Studio_get_user_story`
- `Code_list_repositories`, `Code_find_relevant_code_snippets`

### Planning Agent Tools (Critical)
- `Code_list_repositories` - Discover all project repositories
- `Code_get_directory_structure` - Analyze repository structure
- `Code_find_relevant_code_snippets` - Find relevant existing code
- `Code_get_file` - Read specific files
- `Code_find_usages` - Analyze code dependencies

## Advanced Usage

### Custom Configuration

```python
# Load with custom config
agent = create_atlas_agent(config_path="./custom_config.yaml")

# Add custom MCP tools
custom_tools = {
    "mcp__fairmind__Custom_tool": custom_tool_function
}
agent = create_atlas_agent(available_tools=custom_tools)
```

### Monitoring Progress

```python
# Get current status
status = agent.get_status()
print(f"Phase: {status['current_phase']}")
print(f"Progress: {status['completion_percentage']}%")
print(f"Files: {status['virtual_filesystem_files']}")
```

### Validation

```python
# Check phase validation
validation = agent.state['validation_status']
for phase, result in validation.items():
    print(f"{phase}: {'✅' if result['completed'] else '❌'}")
    if result['missing_outputs']:
        print(f"  Missing: {result['missing_outputs']}")
```

## Troubleshooting

### Common Issues

1. **MCP Connection Failed**
   - Check `FAIRMIND_MCP_URL` and `FAIRMIND_MCP_TOKEN`
   - Verify MCP server is accessible

2. **Model API Errors**
   - Verify API keys in `.env`
   - Check model name in `config.yaml`

3. **Phase Not Advancing**
   - Check validation criteria in agent status
   - Ensure required output files are generated

### Debug Mode

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Enable debug mode in config
config = {
    "debug": True,
    "trace_enabled": True
}
```

## Development

### Running Tests

```bash
pytest tests/
```

### Adding New Sub-agents

1. Add prompt template in `prompts.py`
2. Add agent config in `subagents.py` 
3. Update `AGENT_CONFIGS` registry
4. Test with specific use case

### Contributing

1. Follow existing code patterns
2. Add comprehensive documentation
3. Include validation criteria for new phases
4. Test with real MCP endpoints

## License

Part of the deepagents_atlas project. See main repository for license information.

---

**Need Help?** Check the main repository documentation or create an issue for support.