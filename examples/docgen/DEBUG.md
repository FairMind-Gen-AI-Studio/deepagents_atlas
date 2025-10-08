# DocGen Agent Debugging Guide

This guide explains the DocGen agent architecture and how to debug MCP tool issues.

## Understanding the Architecture

### Orchestrator vs Subagent Pattern

DocGen uses a **delegation architecture** with two distinct types of agents:

#### 1. Orchestrator Agent
- **Role**: Coordinator only - makes no direct tool calls
- **Tools**: Only has `task` tool for delegation, plus filesystem tools (`ls`)
- **MCP Tools**: ❌ **NONE** - this is intentional!
- **System Prompt**: Short, focused on delegation logic

**Why no MCP tools?**
The orchestrator doesn't need MCP tools because it doesn't do any actual work. It just:
1. Checks virtual filesystem state with `ls`
2. Decides which phase to execute next
3. Delegates to appropriate subagent via `task` tool

#### 2. Subagent Agents (5 phases)
- **discovery-agent**: Explores repositories and builds catalog
  - **MCP Tools**: ✅ 11 tools (General_* and Code_*)
  - **Tools**: `list_projects`, `list_repositories`, `tree`, `cat`, etc.

- **scoping-agent**: Interactive scope definition with user
  - **MCP Tools**: ✅ 0 tools (user interaction only)

- **analysis-agent**: Deep code analysis
  - **MCP Tools**: ✅ 6 tools (Code_* tools)
  - **Tools**: `search`, `cat`, `grep`, `find_usages`

- **clarification-agent**: Asks user about ambiguous code
  - **MCP Tools**: ✅ 0 tools (user interaction only)

- **generation-agent**: Creates final documentation
  - **MCP Tools**: ✅ 6 tools (Code_* tools for examples)

### Execution Flow

```
User Request
     ↓
Orchestrator (checks files with `ls`)
     ↓
Decides phase → Calls `task(subagent_type="discovery-agent")`
     ↓
Discovery Subagent Spawns
     ↓
Discovery uses MCP tools (General_list_projects, Code_tree, etc.)
     ↓
Discovery writes discovery_catalog.json
     ↓
Discovery exits, returns to Orchestrator
     ↓
Orchestrator checks files again with `ls`
     ↓
Sees discovery_catalog.json → Calls `task(subagent_type="scoping-agent")`
     ↓
... (continues through phases)
```

## Common Debugging Scenarios

### Scenario 1: "I don't see MCP tools in the system prompt!"

**Symptom**: Looking at LangSmith traces, the system prompt shows no MCP Fairmind tools.

**Diagnosis**:
1. Which prompt are you viewing?
   - **Orchestrator prompt**: Will NOT have MCP tools (this is correct!)
   - **Subagent prompt**: SHOULD have MCP tools

**Solution**: Find the subagent prompt by:
1. Open your run in LangSmith
2. Look for a node called **"task"** or **"invoke_subagent"**
3. Expand that node - it contains a nested execution
4. Inside the nested execution, look for the **model request**
5. The system prompt HERE should show MCP tools

**Visual Guide**:
```
Run Timeline:
  → model_request (orchestrator) ← You're probably looking here
      System Prompt: No MCP tools ✅ CORRECT
  → task_tool_call
      → [Nested Execution: discovery-agent]
          → model_request ← Look HERE for MCP tools
              System Prompt: 11 MCP tools ✅ SHOULD BE HERE
```

### Scenario 2: "MCP tools initialization failed"

**Symptom**: Logs show "Cannot initialize MCP tools - event loop already running"

**Diagnosis**: This happens when `langgraph dev` starts an event loop before importing the module.

**Solution**: The code now uses `nest-asyncio` to handle this. If you still see this error:
```bash
pip install nest-asyncio
```

Then verify in logs:
```
info: Successfully connected to MCP server: 24 tools available
```

### Scenario 3: "Discovery agent has NO MCP tools"

**Symptom**: Logs show "Discovery: 0 tools"

**Diagnosis**: MCP tools didn't initialize or filtering failed.

**Solution**:
1. Check environment variables:
   ```bash
   echo $FAIRMIND_MCP_URL
   echo $FAIRMIND_MCP_TOKEN
   ```

2. Check logs for MCP connection:
   ```
   info: Connecting to Fairmind MCP server...
   info: Successfully connected to MCP server: 24 tools available
   ```

3. If tools are available but filtering fails, check tool names match the filter:
   ```python
   # In agents/discovery_agent.py:get_discovery_tools()
   # Looking for tools with names starting with:
   # - 'mcp__fairmind__General_'
   # - 'mcp__fairmind__Code_'
   # - 'General_'
   # - 'Code_'
   ```

### Scenario 4: "Agent isn't using MCP tools"

**Symptom**: Agent runs but never calls MCP tools, only uses built-in tools.

**Diagnosis**: Agent may not understand which tools are available or when to use them.

**Solution**:
1. Check agent prompt includes tool usage instructions
2. Verify tool names in agent's system prompt match actual tool names
3. Check if agent instructions mention specific MCP tools by name
4. Try explicitly telling the agent to use MCP tools in user request:
   ```
   "Use Code_list_repositories to find all repositories in the project"
   ```

## Verification Checklist

Use this checklist to verify MCP tools are configured correctly:

### Startup Logs

When `langgraph dev` starts, you should see:

```
✅ info: Connecting to Fairmind MCP server at https://...
✅ info: Successfully connected to MCP server: 24 tools available
✅ info: Available MCP tools: ['General_list_projects', 'General_...", ...]
✅ info: MCP tools assigned to agents:
✅ info:   - Discovery: 11 tools
✅ info:   - Analysis: 6 tools
✅ info:   - Generation: 6 tools
```

**Missing?** Check environment variables.

### Runtime Behavior

When you send a request:

```
1. ✅ Orchestrator receives message
2. ✅ Orchestrator calls `ls` to check virtual filesystem
3. ✅ Orchestrator calls `task(subagent_type="discovery-agent")`
4. ✅ Discovery agent spawns with 11 MCP tools
5. ✅ Discovery agent calls General_list_projects
6. ✅ Discovery agent calls Code_list_repositories
7. ✅ Discovery agent writes discovery_catalog.json
```

**Not happening?** Check:
- Agent instructions mention using MCP tools
- Tool names in prompt match actual tool names
- No errors in LangSmith traces

### LangSmith Trace

In your LangSmith trace:

```
✅ Top level: "orchestrator" agent execution
  ✅ model_request: System prompt mentions `task` tool
  ✅ tool_calls: Contains `task` call with subagent_type
  ✅ Nested execution: "discovery-agent" subagent
    ✅ model_request: System prompt lists 11 MCP tools
    ✅ tool_calls: Contains MCP tool calls (General_*, Code_*)
```

## Manual Testing

### Test 1: Verify MCP Connection

```bash
cd /Users/alexiocassani/Projects/deepagents_atlas/examples/docgen

python3 -c "
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path('.').parent / 'atlas_v1'))

async def test():
    from mcp_client import initialize_mcp_tools
    tools = await initialize_mcp_tools()
    print(f'✅ Connected! {len(tools)} tools available')
    print(f'Tool names: {list(tools.keys())[:5]}...')

asyncio.run(test())
"
```

**Expected**: `✅ Connected! 24 tools available`

### Test 2: Verify Tool Filtering

```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path('.').parent.parent / 'src'))

# Mock MCP tools
mock_tools = {
    'mcp__fairmind__General_list_projects': type('Tool', (), {'name': 'mcp__fairmind__General_list_projects'})(),
    'mcp__fairmind__Code_tree': type('Tool', (), {'name': 'mcp__fairmind__Code_tree'})(),
    'mcp__fairmind__Studio_get_need': type('Tool', (), {'name': 'mcp__fairmind__Studio_get_need'})(),
}

from agents.discovery_agent import get_discovery_tools
filtered = get_discovery_tools(mock_tools)

print(f'Input: {len(mock_tools)} tools')
print(f'Filtered: {len(filtered)} tools')
print(f'Tool names: {[t.name for t in filtered]}')
```

**Expected**: 2 tools (General_* and Code_* only, not Studio_*)

### Test 3: Full Agent Run

```bash
cd /Users/alexiocassani/Projects/deepagents_atlas/examples/docgen

# Watch logs in real-time
langgraph dev --watch

# In LangSmith Studio or API:
# Send request: "List all available projects"
#
# Verify in logs:
# - Orchestrator delegates to discovery-agent
# - Discovery agent calls General_list_projects
# - Results returned and written to virtual filesystem
```

## Understanding Log Output

### Enhanced Logging Format

With the new enhanced logging, you'll see:

```
======================================================================
MCP TOOLS VERIFICATION
======================================================================
✅ MCP tools initialized: 24 tools available
   Available MCP tools: ['General_list_projects', 'General_list_user_attachments_by_project', ...]

MCP tools assigned to agents:
  - Discovery: 11 tools
      Examples: ['General_list_projects', 'General_get_document_content', 'Code_list_repositories']
      Has Code tools: True, Has General tools: True
  - Scoping: 0 tools
  - Analysis: 6 tools
      Examples: ['Code_search', 'Code_cat', 'Code_tree']
  - Clarification: 0 tools
  - Generation: 6 tools
      Examples: ['Code_search', 'Code_cat', 'Code_tree']

Built-in tools (added by deepagents middleware):
  - File operations: ls, read_file, write_file, edit_file
  - Task planning: write_todos
  - Delegation: task (orchestrator only)

ARCHITECTURE NOTE:
  - Orchestrator: Delegates via 'task' tool (no MCP tools by design)
  - Subagents: Receive MCP tools based on their phase requirements
  - In LangSmith: Look for 'task' tool invocations to see subagent prompts
======================================================================
```

**What to check**:
- ✅ Shows "MCP tools initialized" with count
- ✅ Each subagent shows expected tool count
- ✅ Discovery has "Has Code tools: True, Has General tools: True"
- ⚠️ Any WARNING messages about missing tools

## Advanced Debugging

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now run your agent
# You'll see detailed MCP client communication
```

### Inspect Agent Configuration at Runtime

```python
from docgen_agent import create_langgraph_agent
from pathlib import Path
import sys

# Initialize MCP tools
sys.path.insert(0, str(Path('.').parent / 'atlas_v1'))
from mcp_client import initialize_mcp_tools
import asyncio

mcp_tools = asyncio.run(initialize_mcp_tools())

# Create agent
agent = create_langgraph_agent(mcp_tools)

# Inspect state schema
print("Agent state schema:")
print(agent.config_schema())

# Try to access subagent configs (if exposed)
# Note: This depends on deepagents internal structure
```

### Trace Execution Manually

```python
import logging
from langgraph.pregel import StreamMode

# Enable all logging
logging.basicConfig(level=logging.DEBUG)

# Run with streaming to see each step
config = {"configurable": {"thread_id": "test-123"}}
for chunk in agent.stream(
    {"messages": [{"role": "user", "content": "List projects"}]},
    config=config,
    stream_mode=StreamMode.DEBUG
):
    print(f"Step: {chunk}")
```

## Common Fixes

### Fix 1: Restart langgraph dev

Sometimes the dev server caches old module state:

```bash
# Kill existing dev server
pkill -f "langgraph dev"

# Start fresh
langgraph dev
```

### Fix 2: Clear Checkpoint State

If agent seems stuck in old state:

```python
# Delete checkpointer state
# (DocGen uses in-memory checkpointer, so just restart)
# If using persistent checkpointer:
# checkpointer.delete(thread_id)
```

### Fix 3: Verify Environment

```bash
# Check all required env vars are set
env | grep -E '(FAIRMIND|ANTHROPIC|LITELLM)'

# Should see:
# FAIRMIND_MCP_URL=...
# FAIRMIND_MCP_TOKEN=...
# ANTHROPIC_API_KEY=...
```

## Getting Help

If you're still stuck:

1. **Check logs** for:
   - MCP connection errors
   - Tool initialization warnings
   - Agent execution errors

2. **Check LangSmith trace** for:
   - Which agent actually executed (orchestrator or subagent?)
   - Which tools were available in system prompt
   - Which tools were actually called

3. **Verify configuration**:
   - Environment variables set correctly
   - langgraph.json points to correct module
   - config.yaml has MCP enabled

4. **Compare with Atlas V1**:
   - Does Atlas V1 work with same environment?
   - Same MCP tools available in both?
   - What's different in your setup?

## Summary

**Key Takeaway**: The orchestrator having no MCP tools is **correct behavior**. The subagents spawned via the `task` tool are where MCP tools live. Always check the nested execution traces in LangSmith to see subagent tool usage.

**Quick Diagnostic**:
1. Check startup logs: "Successfully connected to MCP server: 24 tools"
2. Check tool assignment: "Discovery: 11 tools"
3. In LangSmith: Look INSIDE `task` tool execution for subagent prompts
4. Verify subagent system prompt lists MCP tools
5. Verify subagent makes MCP tool calls

If all of the above check out, your agent is working correctly!
