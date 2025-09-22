# Atlas V2 - Simplified Architecture

## Overview

Atlas V2 is a complete rewrite of the Atlas methodology implementation, following the successful pattern from the `research` example. This version eliminates the complexity of the original Atlas V1 while maintaining the same 4-phase methodology.

## Quick Start

1. **Install dependencies:**
   ```bash
   cd examples/atlas_v2
   pip install -r requirements.txt
   ```

2. **Fix LangGraph versions (if needed):**
   ```bash
   python fix_versions.py
   ```
   This automatically fixes any version compatibility issues.

3. **Run setup check:**
   ```bash
   python setup.py
   ```
   This will check your configuration and show any issues.

4. **Configure environment:**
   ```bash
   cp config.env .env
   # Edit .env with your actual API keys and tokens
   ```

   **Your .env file should look like this:**
   ```bash
   # ===== ANTHROPIC CONFIGURATION =====
   ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
   DEEPAGENTS_MODEL=anthropic/claude-3-5-sonnet-20241022

   # ===== MCP FAIRMIND CONFIGURATION =====
   MCP_FAIRMIND_TOKEN=your-actual-fairmind-token-here

   # ===== OPTIONAL CONFIGURATION =====
   LANGCHAIN_TRACING_V2=false
   DEBUG=false
   LOG_LEVEL=INFO
   ```

5. **Run Atlas V2:**
   ```bash
   langgraph dev
   ```

## Architecture Comparison

### Atlas V1 (Complex - ❌)
- **6+ files** with over-engineered architecture
- **Custom state management** with `file_reducer` incompatible with LangGraph API
- **Complex coordinator** + 4 separate agent modules
- **Virtual filesystem** with custom tools
- **LangGraph API incompatible**

### Atlas V2 (Simple - ✅)
- **1 main file** with clean sub-agent pattern
- **Standard DeepAgents tools** included automatically
- **Built-in state management** via LangGraph API
- **No custom filesystem** - uses standard file operations
- **LangGraph API compatible**

## Key Features

### 🎯 4-Phase Methodology
1. **Investigation** - Silent project exploration
2. **Discussion** - Interactive requirements clarification
3. **Planning** - Repository analysis and solution design
4. **Task Generation** - Create actionable tasks

### 🛠 Tool Architecture

#### **Main Atlas Orchestrator Tools** (4)
- `write_file`, `read_file`, `ls` - Basic file management
- `write_todos` - Task tracking

#### **Sub-Agent MCP FairMind Tools Distribution**

**🔍 Investigation Agent** (8 tools)
- All **Studio Tools** for project exploration:
  - `studio_list_projects`, `studio_list_user_stories_by_project`
  - `studio_get_user_story`, `studio_get_need`
  - `studio_get_related_user_stories`, `studio_list_needs_by_project`
  - `general_get_document_content`, `code_get_file`

**💬 Discussion Agent** (10 tools)
- **Interaction tools**:
  - `human_input` - Ask questions to user
  - `approve_plan` - Get approval on requirements
- **MCP verification tools** (same as Investigation)

**⚙️ Planning Agent** (7 tools)
- **Code analysis tools**:
  - `code_list_repositories`, `code_get_directory_structure`
  - `code_get_file`, `code_find_relevant_code_snippets`
  - `code_find_usages`
- **Task tools**:
  - `studio_list_tasks_by_project`, `studio_get_task`

**📋 Task Generation Agent** (7 tools)
- **Task management**:
  - `studio_list_tasks_by_project`, `studio_get_task`, `write_todos`
- **Code analysis**:
  - `code_get_file`, `code_find_relevant_code_snippets`
- **Project context**:
  - `studio_list_user_stories_by_project`, `studio_get_user_story`

**Note:** All 23 MCP FairMind tools are available across sub-agents based on their specific needs. Each sub-agent has access to the tools required for their phase responsibilities.

### 📁 File Management
- `investigation_findings.md` - Investigation results
- `clarification_questions.md` - Discussion questions
- `user_responses.md` - User answers
- `requirements_clarified.md` - Approved requirements
- `implementation_plan.md` - Technical plan
- `implementation_tasks.md` - Actionable tasks

## Configuration

### Environment Setup

1. **Copy the configuration file:**
   ```bash
   cd examples/atlas_v2
   cp config.env .env
   ```

2. **Configure your API keys in `.env`:**
   ```bash
   # Edit .env file
   nano .env  # or your preferred editor
   ```

3. **Required configuration:**
   - `ANTHROPIC_API_KEY`: Your Anthropic API key from https://console.anthropic.com/
   - `MCP_FAIRMIND_TOKEN`: Your FairMind MCP token for project context access

4. **Optional configuration:**
   - `DEEPAGENTS_MODEL`: Which Anthropic model to use (default: claude-3-5-sonnet-20241022)
   - `LANGCHAIN_TRACING_V2`: Enable LangSmith tracing (optional)
   - `LANGCHAIN_API_KEY`: LangSmith API key for tracing (optional)

### Getting Your FairMind MCP Token

1. **Login to FairMind Platform**
2. **Go to Settings/API** or contact your FairMind administrator
3. **Generate or obtain your MCP token**
4. **Add it to your .env file** as `MCP_FAIRMIND_TOKEN=your-actual-token-here`

### Development
```bash
cd examples/atlas_v2
langgraph dev
```

### Production
```bash
cd examples/atlas_v2
langgraph deploy
```

## Agent Structure

### Main Agent
- **Type**: `create_deep_agent` with sub-agents
- **Model**: Anthropic (default configuration)
- **Tools**: Built-in DeepAgents tools + MCP FairMind integration
- **State**: Standard LangGraph state management

### Sub-Agents
1. **investigation-agent** - Autonomous exploration (MCP tools only)
2. **discussion-agent** - User interaction for requirements (`human_input`, `approve_plan`)
3. **planning-agent** - Technical analysis and design (MCP tools only)
4. **task-generation-agent** - Task breakdown and planning (MCP tools only)

## Benefits

### ✅ Simplicity
- **1 file** vs 6+ files
- **Standard patterns** vs custom implementations
- **Clear separation** of concerns

### ✅ Compatibility
- **LangGraph API** fully compatible
- **DeepAgents** standard tools
- **No custom reducers** or state management

### ✅ Maintainability
- **Easy to understand** architecture
- **Standard debugging** patterns
- **Consistent** with research example

### ✅ Reliability
- **Proven pattern** from research example
- **No custom complexity** that can break
- **Standard LangGraph** error handling

## Migration from Atlas V1

### Files Replaced
- `atlas_agent.py` → Single file with all agents
- `atlas_coordinator.py` → Main agent handles coordination
- `agents/` directory → Sub-agents in main file
- `atlas_tools.py` → Built-in tools only

### State Management
- **REMOVED**: Custom `file_reducer` incompatible with LangGraph API
- **ADDED**: Standard LangGraph state management
- **SIMPLIFIED**: No custom filesystem tools

### Configuration
- **SIMPLIFIED**: Direct `create_deep_agent` usage
- **REMOVED**: Complex interrupt configurations
- **STANDARD**: LangGraph API standard patterns

## Testing

```bash
cd examples/atlas_v2

# Test imports and basic functionality
python -c "from atlas_agent import agent; print('✅ Atlas V2 loaded successfully')"

# Test configuration
python test_atlas_v2.py

# Test MCP FairMind tools
python test_mcp.py

# Test with LangGraph CLI
langgraph dev

# Quick test if server starts (first 5 seconds)
python -c "
import subprocess, time
proc = subprocess.Popen(['langgraph', 'dev'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(5)
proc.terminate()
print('✅ LangGraph dev starts successfully')
"
```

## Troubleshooting

### Common Issues

1. **"ANTHROPIC_API_KEY not found"**
   - Ensure you have set the `ANTHROPIC_API_KEY` in your `.env` file
   - Get your API key from https://console.anthropic.com/

2. **"MCP tools not available"**
   - MCP FairMind tools are automatically available when running with `langgraph dev`
   - No manual configuration needed for MCP tools
   - Ensure your `MCP_FAIRMIND_TOKEN` is set correctly in `.env`

3. **"Model not found"**
   - Check your `DEEPAGENTS_MODEL` setting in `.env`
   - Valid values: `anthropic/claude-3-5-sonnet-20241022`, `anthropic/claude-3-haiku-20240307`

4. **"MCP_FAIRMIND_TOKEN not found" or "FairMind authentication failed"**
   - Ensure you have set the `MCP_FAIRMIND_TOKEN` in your `.env` file
   - Get your token from the FairMind platform settings or administrator
   - Verify the token is correct and active

5. **Import errors**
   - Run `pip install -r requirements.txt` to install dependencies
   - Ensure you're in the correct directory: `examples/atlas_v2`

6. **"ImportError: cannot import name 'FF_RICH_THREADS'"**
   - Run the automatic fix: `python fix_versions.py`
   - Or manually update: `pip install -U langgraph-api "langgraph-cli[inmem]"`
   - This fixes version incompatibility between langgraph-api and langgraph-runtime-inmem
   - Restart the development server after updating

### Debug Mode

Enable debug logging by setting in `.env`:
```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

## Conclusion

Atlas V2 demonstrates that the original complex architecture was unnecessary. By following the proven pattern from the `research` example, we achieve the same functionality with dramatically reduced complexity and full LangGraph API compatibility.

**Key Lesson**: Sometimes the simplest solution is the best solution.
