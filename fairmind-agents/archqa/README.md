# ArchQA - Architectural Q&A Agent

An intelligent agent that answers complex architectural questions about codebases using MCP FairMind for code access and Tavily for technology research.

## Features

- ✅ **Technical Debt Assessment**: Identifies and prioritizes technical debt across projects
- ✅ **Change Impact Analysis**: Analyzes the impact of proposed changes across all affected components
- ✅ **Solution Architecture Proposals**: Suggests multiple solution options with trade-off analysis
- ✅ **Cross-Project Dependency Mapping**: Discovers and maps relationships between projects
- ✅ **Technology Research**: Researches frameworks and best practices using web search
- ✅ **Code-Based Evidence**: Provides specific file paths, line numbers, and code snippets

## Architecture

ArchQA uses a 3-agent sequential workflow:

1. **context-mapper**: Analyzes question scope and discovers relevant projects/repositories
2. **code-investigator**: Performs deep code analysis with web research capability
3. **solution-synthesizer**: Synthesizes findings into comprehensive architectural answers

## Installation

### Prerequisites

- Python 3.9+
- Node.js (for MCP server)
- Access to MCP FairMind server
- (Optional) Tavily API key for web research

### Setup

1. **Install dependencies**:

```bash
cd examples/archqa
pip install -e ../../  # Install deepagents from root
pip install tavily-python  # Optional, for web research
```

2. **Configure environment variables**:

```bash
cp .env.example .env
# Edit .env and fill in your API keys:
# - ANTHROPIC_API_KEY (required)
# - FAIRMIND_MCP_URL (required)
# - FAIRMIND_MCP_TOKEN (required)
# - TAVILY_API_KEY (optional, for web research)
```

3. **Verify MCP connection**:

The MCP FairMind server is configured in `langgraph.json`. Make sure your credentials are correct.

## Usage

### Via LangGraph CLI (Recommended)

```bash
cd examples/archqa
langgraph dev
```

Then open the LangGraph UI and ask your architectural questions.

### Via Python Script

```bash
python archqa_agent.py
```

You'll be prompted to enter an architectural question.

## Example Questions

### Technical Debt Assessment

```
What are the areas of greatest technical debt in the authentication service?
```

**Expected Output**:
- List of technical debt items prioritized by severity
- Specific file locations with line numbers
- Code snippets showing the issues
- Remediation recommendations with effort estimates
- Phased roadmap for addressing debt

### Change Impact Analysis

```
What happens if I add a birth_date field to the user registration form?
```

**Expected Output**:
- Component impact matrix (database, API, UI, tests)
- Implementation checklist for each layer
- Specific file changes required with line numbers
- Risk analysis (privacy compliance, data migration, etc.)
- Estimated implementation effort

### Solution Architecture Proposals

```
If I wanted to introduce user management in project Z, what solutions do you propose?
```

**Expected Output**:
- Analysis of current implementation
- 2-3 solution options with pros/cons
- Technology research from web (best practices, comparisons)
- Recommended approach with rationale
- High-level implementation roadmap

## How It Works

### Workflow

1. **User asks a question** about architecture, technical debt, or implementation

2. **context-mapper** analyzes the question:
   - Uses `General_list_projects` to find relevant projects
   - Uses `General_rag_retrieve_documents` to search project knowledge
   - Uses `Code_list_repositories` to identify code repositories
   - Creates `context_map.json` with investigation scope

3. **code-investigator** performs deep analysis:
   - Uses `Code_tree`, `Code_search`, `Code_cat`, `Code_grep`, `Code_find_usages` for code analysis
   - Uses `tavily_search` for technology research (if enabled)
   - Creates `investigation_findings.md` with detailed findings

4. **solution-synthesizer** creates the answer:
   - Reads `context_map.json` and `investigation_findings.md`
   - Synthesizes comprehensive architectural answer
   - Presents directly to user with code examples and references

### Virtual Filesystem

All intermediate outputs are stored in a virtual filesystem:

- `context_map.json`: Project scope and investigation boundaries
- `investigation_findings.md`: Detailed code analysis results

These files persist during the conversation and can be referenced for follow-up questions.

## Configuration

### Model Settings

The agent uses Claude Sonnet 4 by default. You can override in `.env`:

```bash
ARCHQA_MODEL_NAME=claude-sonnet-4-20250514
ARCHQA_MODEL_TEMPERATURE=0.7
ARCHQA_MODEL_MAX_TOKENS=8192
```

### MCP Configuration

MCP FairMind is configured in `langgraph.json`. The configuration:

```json
{
  "mcp_servers": {
    "fairmind": {
      "command": "npx",
      "args": ["-y", "@fairmind/mcp-server"],
      "env": {
        "FAIRMIND_MCP_URL": "${FAIRMIND_MCP_URL}",
        "FAIRMIND_MCP_TOKEN": "${FAIRMIND_MCP_TOKEN}"
      }
    }
  }
}
```

### Web Search (Optional)

Web search is optional but recommended for solution proposals. Without Tavily:

- ✅ All code analysis works normally
- ✅ Technical debt assessment works normally
- ✅ Impact analysis works normally
- ⚠️ Solution proposals won't include technology research

## Architecture Details

### Agent Responsibilities

**context-mapper**:
- Tools: `General_*`, `Studio_*`, `Code_list_repositories`, `Code_tree`
- Output: `context_map.json`
- Purpose: Define investigation scope

**code-investigator**:
- Tools: `Code_*` (all), `Studio_*`, `tavily_search`
- Output: `investigation_findings.md`
- Purpose: Analyze code and research technologies

**solution-synthesizer**:
- Tools: `read_file`, `ls` (virtual filesystem only)
- Output: Direct answer to user
- Purpose: Synthesize findings into actionable answer

### Tool Inheritance

All agents inherit tools from the orchestrator:
- MCP tools provided automatically by LangGraph framework
- Tavily added to orchestrator, inherited by all agents
- Agents use `"tools": []` to inherit everything

This follows the validated deepagents pattern (no manual tool filtering).

## Troubleshooting

### "MCP tools not available"

Check your `.env` file:
- Ensure `FAIRMIND_MCP_URL` and `FAIRMIND_MCP_TOKEN` are set
- Verify the MCP server is accessible
- Check `langgraph.json` configuration

### "Tavily not available"

Web search is optional. To enable:
- Install: `pip install tavily-python`
- Add `TAVILY_API_KEY` to `.env`
- Restart the agent

### Agent not finding repositories

Make sure:
- Project exists in MCP FairMind
- Project has linked repositories in the Code tool
- User has access permissions to the project

### Answers are too brief

The agent aims for comprehensive answers. If answers seem brief:
- Check `investigation_findings.md` in virtual filesystem (via orchestrator)
- Ensure MCP Code tools are returning results
- Try more specific questions

## Development

### File Structure

```
archqa/
├── archqa_agent.py              # Main orchestrator
├── langgraph.json               # LangGraph + MCP configuration
├── agents/
│   ├── __init__.py              # Agent exports
│   ├── context_mapper_agent.py  # Scope analysis agent
│   ├── code_investigator_agent.py # Code analysis agent
│   └── solution_synthesizer_agent.py # Answer synthesis agent
├── .env.example                 # Environment template
└── README.md                    # This file
```

### Adding Custom Agents

To add a new specialized agent:

1. Create `agents/new_agent.py` with agent definition
2. Export in `agents/__init__.py`
3. Add to `subagents` list in `archqa_agent.py`
4. Update orchestrator instructions to use new agent

### Debugging

Enable LangSmith tracing in `.env`:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=archqa
LANGCHAIN_API_KEY=your_key
```

View traces at https://smith.langchain.com

## Comparison with Other Agents

| Feature | ArchQA | atlas_v1 | research |
|---------|--------|----------|----------|
| Purpose | Architectural Q&A | Task generation | Web research |
| MCP Integration | ✅ Yes (via framework) | ✅ Yes (manual) | ❌ No |
| Web Search | ✅ Tavily | ❌ No | ✅ Tavily |
| Workflow | Sequential (3 agents) | Phased (4 phases) | Iterative (2 agents) |
| Complexity | Low (~590 lines) | High (~2000+ lines) | Low (~166 lines) |
| State Management | Virtual filesystem | External state store | Virtual filesystem |

## License

Same as parent deepagents project.

## Contributing

This agent follows deepagents best practices:
- Simplified pattern (no mcp_client.py)
- Tool inheritance (no manual filtering)
- Virtual filesystem for state
- Sequential delegation workflow

When contributing, maintain these patterns for consistency.
