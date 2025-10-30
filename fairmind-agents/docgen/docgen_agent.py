# DocGen Agent - Documentation Generation using DeepAgents Framework
# 5-phase methodology implementation for code documentation
#
# Phases:
# 1. Discovery - Silent project and repository exploration
# 2. Scoping - Interactive scope definition with user
# 3. Analysis - Deep code analysis with parallel subagents
# 4. Clarification - Interactive questions about ambiguous code
# 5. Generation - Final documentation creation with user feedback

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# CRITICAL: Load .env BEFORE any LangChain imports
# This ensures LANGCHAIN_* variables are available when deepagents imports LangChain
_project_root = Path(__file__).parent
load_dotenv(_project_root.parent.parent / ".env")

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _check_langsmith_status():
    """Check and log LangSmith tracing status for DocGen agent."""
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2") == "true"
    project_name = os.getenv("LANGCHAIN_PROJECT")
    api_key = os.getenv("LANGCHAIN_API_KEY")

    if tracing_enabled and project_name and api_key:
        logger.info(f"🔍 [DocGen] LangSmith tracing enabled for project: {project_name}")
        return {"enabled": True, "project": project_name}
    elif tracing_enabled:
        logger.warning("⚠️ [DocGen] LangSmith tracing enabled but missing configuration")
        return {"enabled": False, "issue": "missing_config"}
    else:
        logger.info("📝 [DocGen] LangSmith tracing disabled")
        return {"enabled": False, "disabled": True}


# Check LangSmith status after loading environment
_langsmith_status = _check_langsmith_status()

# Add src to path for deepagents
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from deepagents import async_create_deep_agent
from fairmind.middleware import SafeSummarizationMiddleware

# Import centralized MCP client from shared library
# This provides multi-user support via runtime_token parameter
from fairmind.shared.mcp import initialize_mcp_tools


def _get_mcp_tools_for_state(state: dict) -> Optional[Dict[str, Any]]:
    """
    Get MCP tools using cache from state, or initialize if cache miss.

    This function implements lazy initialization with caching:
    1. Check if mcp_tools_cache exists in state (populated by router wrapper)
    2. If cache hit → return cached tools (fast path)
    3. If cache miss → return None (router wrapper will initialize in thread pool)

    The router wrapper handles ALL initialization to avoid blocking I/O in ASGI context.
    This function ONLY retrieves from cache, never initializes directly.

    Args:
        state: LangGraph state dictionary containing mcp_tools_cache and user_api_key fields

    Returns:
        Dictionary of MCP tools, or None if initialization fails

    Multi-user flow:
        1. Router wrapper initializes MCP tools with user's API key on first request
        2. Tools are cached in state.mcp_tools_cache for reuse
        3. This function retrieves from cache (or initializes as fallback)
    """
    # CACHE CHECK: Try to use cached tools first (populated by router wrapper)
    mcp_tools_cache = state.get("mcp_tools_cache")

    if mcp_tools_cache:
        # Cache hit - return cached tools
        tool_count = len(mcp_tools_cache) if isinstance(mcp_tools_cache, dict) else 0
        logger.info(f"♻️  [DocGen] Using cached MCP tools from state ({tool_count} tools)")
        return mcp_tools_cache

    # CACHE MISS: Return None - router wrapper will handle initialization
    # DO NOT attempt to initialize here - it causes blocking I/O in ASGI context
    logger.debug("ℹ️  [DocGen] MCP cache miss in _get_mcp_tools_for_state - router will initialize")
    return None


class DocGenAgent:
    """
    DocGen Agent for automated code documentation generation.

    This agent implements a 5-phase methodology:
    1. Discovery: Find and catalog repositories/files
    2. Scoping: Define documentation scope with user
    3. Analysis: Deep code analysis with subagents
    4. Clarification: Ask user about ambiguous code
    5. Generation: Create final documentation

    Follows deepagents best practices with context management via
    virtual filesystem and intelligent use of MCP FairMind tools.
    """

    def __init__(self, mcp_tools: Optional[Dict[str, Any]] = None):
        """
        Initialize DocGen Agent.

        Args:
            mcp_tools: Optional MCP tools dictionary. If None, will attempt to initialize.
        """
        # Load environment variables
        load_dotenv()

        # Initialize MCP tools if not provided
        if mcp_tools is None:
            logger.info("Initializing MCP tools...")
            mcp_tools = _initialize_mcp_tools_sync()
            if mcp_tools:
                logger.info(f"Initialized {len(mcp_tools)} MCP tools")
            else:
                logger.info("No MCP tools available, using builtin tools only")

        self.mcp_tools = mcp_tools

    async def run(self, user_request: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the DocGen methodology.

        Args:
            user_request: The user's documentation request
            project_id: Optional project ID to include in request

        Returns:
            Execution results with final response, files, and todos
        """
        # Enhance request with project ID if provided
        if project_id:
            user_request = f"{user_request}\n\nProject ID: {project_id}"

        # Create the agent graph and run
        agent = create_langgraph_agent(self.mcp_tools)

        # Generate consistent thread_id for state persistence
        thread_id = f"docgen-{hash(user_request) % 1000000}"
        config = {"configurable": {"thread_id": thread_id}}

        # Run the agent
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": user_request}]},
            config=config
        )

        return {
            "final_response": result.get("messages", [])[-1].get("content", "") if result.get("messages") else "",
            "files": result.get("files", {}),
            "todos": result.get("todos", []),
        }


def create_langgraph_agent(mcp_tools: Optional[Dict[str, Any]] = None):
    """
    Create the LangGraph-compatible agent (compiled graph).

    Args:
        mcp_tools: Optional MCP tools dictionary

    Returns:
        Compiled LangGraph agent
    """
    # CRITICAL: Force import from local docgen/agents/ module
    # We must insert docgen directory at the FRONT of sys.path to ensure Python
    # resolves 'agents' module to docgen/agents/ instead of archqa/agents/
    docgen_path = str(Path(__file__).parent)

    # Save original sys.path state
    original_sys_path = sys.path.copy()

    try:
        # Clear 'agents' from module cache if it exists (prevents stale imports)
        if 'agents' in sys.modules:
            del sys.modules['agents']

        # Insert docgen path at the front so 'from agents import' resolves correctly
        if docgen_path not in sys.path:
            sys.path.insert(0, docgen_path)
        elif sys.path.index(docgen_path) != 0:
            sys.path.remove(docgen_path)
            sys.path.insert(0, docgen_path)

        # Import local agents module (from docgen/agents/)
        # Now Python will find docgen/agents/ first
        from agents import (
            discovery_agent,
            scoping_agent,
            analysis_agent,
            clarification_agent,
            generation_agent,
            get_scoping_tools,  # Keep - handles human_input tool
            get_clarification_tools,  # Keep - handles human_input tool
        )

        # Import MCP filters from shared library
        from fairmind.shared.mcp import (
            DOCGEN_DISCOVERY_FILTER,
            DOCGEN_ANALYSIS_FILTER,
            DOCGEN_GENERATION_FILTER,
            log_agent_startup,
        )
    finally:
        # Restore original sys.path
        sys.path[:] = original_sys_path

    # Get model configuration
    model_name = os.getenv("DOCGEN_MODEL_NAME", "claude-3-5-sonnet-20241022")

    # Strip provider prefix if present (similar to atlas_v1/model_config.py:46)
    model_name = model_name.replace("anthropic/", "").replace("openai/", "")

    # Import model initialization from deepagents
    from deepagents.model import get_default_model
    from langchain_anthropic import ChatAnthropic

    # Use custom model if specified, otherwise use default
    if model_name != "claude-sonnet-4-20250514":
        model = ChatAnthropic(model_name=model_name, max_tokens=64000)
    else:
        model = get_default_model()

    # Prepare MCP tools for each phase
    # With lazy initialization, mcp_tools will be None at agent creation time.
    # Tools will be fetched from state cache at runtime via _get_mcp_tools_for_state(state).
    # DO NOT attempt to initialize MCP tools here - it would fail without user credentials!
    if mcp_tools is None:
        logger.info("ℹ️  Agent created without MCP tools - will lazy-initialize from state cache at runtime")
        logger.info("   The router wrapper populates mcp_tools_cache with user-specific credentials")

    mcp_tool_objects = list(mcp_tools.values()) if mcp_tools and isinstance(mcp_tools, dict) else []

    # Assign phase-specific tools to each agent
    # NOTE: Agents that need human_input interrupts use the "middleware" key with
    # HumanInTheLoopMiddleware. The "graph" key bypasses middleware, so NEVER use it
    # for agents that need interrupts. Framework applies middleware at creation time.

    discovery_agent_with_tools = discovery_agent.copy()
    discovery_agent_with_tools["tools"] = DOCGEN_DISCOVERY_FILTER(mcp_tools)

    # SCOPING AGENT: Use middleware key for human_input interrupt support
    # The framework will apply HumanInTheLoopMiddleware to create proper LangGraph interrupts
    # DO NOT use "graph" key - that bypasses middleware!
    from agents import SCOPING_PROMPT
    from langchain.agents.middleware import HumanInTheLoopMiddleware

    scoping_agent_with_tools = {
        "name": "scoping-agent",
        "description": "Works with the user to define the documentation scope based on discovery results. Interactive phase that determines what to document.",
        "prompt": SCOPING_PROMPT,
        "tools": get_scoping_tools(mcp_tools),
        "middleware": [HumanInTheLoopMiddleware(interrupt_on={"human_input": True})],
    }

    analysis_agent_with_tools = analysis_agent.copy()
    analysis_agent_with_tools["tools"] = DOCGEN_ANALYSIS_FILTER(mcp_tools)

    # CLARIFICATION AGENT: Use middleware key for human_input interrupt support
    # The framework will apply HumanInTheLoopMiddleware to create proper LangGraph interrupts
    # DO NOT use "graph" key - that bypasses middleware!
    from agents import CLARIFICATION_PROMPT

    clarification_agent_with_tools = {
        "name": "clarification-agent",
        "description": "Reviews analysis outputs and asks the user clarifying questions about ambiguous code patterns or unclear requirements.",
        "prompt": CLARIFICATION_PROMPT,
        "tools": get_clarification_tools(mcp_tools),
        "middleware": [HumanInTheLoopMiddleware(interrupt_on={"human_input": True})],
    }

    generation_agent_with_tools = generation_agent.copy()
    generation_agent_with_tools["tools"] = DOCGEN_GENERATION_FILTER(mcp_tools)

    # Use shared library for comprehensive MCP tools verification
    log_agent_startup(
        agent_name="DocGen",
        mcp_tools=mcp_tools,
        phase_assignments={
            "discovery-agent": discovery_agent_with_tools['tools'],
            "analysis-agent": analysis_agent_with_tools['tools'],
            "generation-agent": generation_agent_with_tools['tools'],
        },
        critical_tools_per_phase={
            "discovery-agent": ["General_list_projects", "Code_list_repositories", "Code_tree"],
            "analysis-agent": ["Code_search", "Code_cat"],
            "generation-agent": ["Code_cat"],
        }
    )

    # Note about interactive phases
    logger.info("Interactive phases:")
    logger.info("  - Scoping: Uses human_input tool with HumanInTheLoopMiddleware")
    logger.info("  - Clarification: Uses human_input tool with HumanInTheLoopMiddleware")
    logger.info("")
    logger.info("Built-in tools (added by deepagents middleware):")
    logger.info("  - File operations: ls, read_file, write_file, edit_file")
    logger.info("  - Task planning: write_todos")
    logger.info("  - Delegation: task (orchestrator only)")
    logger.info("")

    # Orchestrator instructions
    orchestrator_instructions = """You are the DocGen Orchestrator. You guide a 5-phase process to generate code documentation.

## Your Job
1. Check the current state using `ls`
2. Determine which phase comes next
3. Delegate that phase to the appropriate specialist agent using the `task` tool
4. Verify the agent's output with `ls`
5. Move to the next phase

## Before You Start

When you receive the initial request, create a plan using `write_todos`:

write_todos([
    {"content": "Phase 1: Discovery", "status": "pending", "activeForm": "Discovering repositories"},
    {"content": "Phase 2: Scoping", "status": "pending", "activeForm": "Defining scope"},
    {"content": "Phase 3: Analysis", "status": "pending", "activeForm": "Analyzing code"},
    {"content": "Phase 4: Clarification", "status": "pending", "activeForm": "Gathering clarifications"},
    {"content": "Phase 5: Generation", "status": "pending", "activeForm": "Generating documentation"},
])

Mark phases completed as you progress using `write_todos`. This helps you track where you are.

### Step 0.5: Universal Context Discovery 🆕

**Before starting Phase 1, scan for reusable context from ANY agent:**

1. **Scan filesystem**: Use `ls()` to list ALL files

2. **Categorize by semantic type**:
   For each file, read first 50 lines to extract metadata:

   ```
   all_files = ls()
   project_catalogs = []  # semantic_type="project_catalog"
   code_analyses = []     # semantic_type="code_analysis"

   For each file in all_files:
     content_preview = read_file(file, limit=50)

     # Parse metadata (JSON root "metadata" or YAML frontmatter ---)
     if has_metadata(content_preview):
       metadata = extract_metadata(content_preview)

       # Categorize by semantic_type (agent-agnostic!)
       if metadata.semantic_type == "project_catalog":
         project_catalogs.append({
           "file": file,
           "metadata": metadata,
           "agent": metadata.agent,  # Could be "docgen/discovery" OR "archqa/context-mapper"
           "timestamp": metadata.timestamp,
           "scope": {"projects": metadata.projects, "repositories": metadata.repositories}
         })

       elif metadata.semantic_type == "code_analysis":
         code_analyses.append({
           "file": file,
           "metadata": metadata,
           "agent": metadata.agent,  # Could be "docgen/analysis" OR "archqa/code-investigator"
           "timestamp": metadata.timestamp,
           "concerns": metadata.architectural_concerns or []
         })
   ```

3. **Match semantic types to phase needs**:

   **For Discovery phase (Phase 1):**
   - Need: semantic_type="project_catalog"
   - Found: project_catalogs list (could include discovery_catalog.json, context_map.json, etc.)
   - Pick: Most recent with matching scope

   **For Analysis phase (Phase 3):**
   - Need: semantic_type="code_analysis"
   - Found: code_analyses list (could include analysis_summary.md, investigation_findings.md, etc.)
   - Pick: Most recent with overlapping concerns

4. **Delegate with context reuse instructions**:
   ```
   # Example for Phase 1 (Discovery):
   if project_catalogs:
     best_match = pick_most_recent_matching_scope(project_catalogs, user_request)
     if best_match and is_fresh(best_match, hours=24):
       task(
         description=f"[REUSE MODE] Read {best_match.file} (semantic_type=project_catalog) and validate scope matches current documentation request. If scope matches, save as discovery_catalog.json with metadata.reused_from={best_match.file}. If new repos needed, AUGMENT with additional MCP tool calls.",
         subagent_type="discovery-agent"
       )
     else:
       # Normal delegation (fresh discovery needed)
       task(description="Discover all repositories...", subagent_type="discovery-agent")

   # Example for Phase 3 (Analysis):
   if code_analyses:
     best_match = pick_most_recent_with_concern_overlap(code_analyses, documentation_scope)
     if best_match and overlap_percentage > 70%:
       task(
         description=f"[AUGMENT MODE] Read {best_match.file} (semantic_type=code_analysis) and build upon it. Focus on NEW aspects needed for documentation that aren't already covered. Use MCP Code tools for new areas only.",
         subagent_type="analysis-agent"
       )
   ```

**Cache decision matrix:**
- **SKIP**: Same scope, <24h fresh, 100% coverage → Use existing file directly (no agent delegation)
- **AUGMENT**: Partial overlap (30-90%) → Reuse base analysis, add missing pieces with MCP tools
- **REFRESH**: >24h old OR different scope OR <30% overlap → Fresh discovery/analysis

**Cross-Agent Reuse Examples**:
- ArchQA created context_map.json (semantic_type="project_catalog") for backend-api
- User asks DocGen to document backend-api
- Step 0.5 finds context_map.json via semantic_type scan
- Delegate to discovery-agent: "[REUSE MODE] Read context_map.json..."
- Discovery agent validates ArchQA's catalog, saves as discovery_catalog.json with metadata.reused_from="context_map.json"

**Freshness Check**:
```python
from datetime import datetime
def is_fresh(metadata, hours=24):
    timestamp = datetime.fromisoformat(metadata.timestamp.replace('Z', '+00:00'))
    age_hours = (datetime.now() - timestamp).total_seconds() / 3600
    return age_hours < hours
```

## Continuous Workflow Pattern

**IMPORTANT**: Phases flow automatically without confirmations. The workflow proceeds continuously through all 5 phases until completion.

### Phase Transitions

After EACH phase completes:
1. Verify the output file was created using `ls`
2. Inform the user about the completed phase
3. Immediately proceed to the next phase (no confirmation needed)

Example message after Phase 1:
"Phase 1 (Discovery) completed successfully. I cataloged the repository with all information about structure, technologies and components. Proceeding to Phase 2 (Scoping)..."

### Workflow Complete Marker

╔══════════════════════════════════════════════════════════════════════╗
║                    CRITICAL: WORKFLOW COMPLETION                     ║
╚══════════════════════════════════════════════════════════════════════╝

**ONLY when `final_documentation.md` exists - YOU MUST COMPLETE THESE STEPS:**

1. Verify all 5 phases completed using `ls`:
   - ✓ discovery_catalog.json
   - ✓ documentation_scope.json
   - ✓ code_analysis.json
   - ✓ documentation_structure.json
   - ✓ final_documentation.md

2. Present the final documentation to the user:
   "Documentation generation complete! Here's your comprehensive developer documentation:"
   [Present key sections or summary from final_documentation.md]

3. **MANDATORY - END YOUR MESSAGE WITH THIS EXACT MARKER:**

   [WORKFLOW_COMPLETE]

⚠️  **THIS MARKER IS NON-NEGOTIABLE** ⚠️

Without this marker, the router will NOT detect workflow completion and will
incorrectly resume the DocGen session when the user asks their next question
(which may be intended for a different agent like ArchQA).

**Example of correct final message format:**
```
Documentation generation complete! I've created comprehensive developer
documentation covering architecture, API endpoints, and deployment guides.

The documentation includes:
- System Architecture Overview
- API Reference Documentation
- Development Setup Guide
- Deployment Instructions

All documentation is saved in final_documentation.md.

[WORKFLOW_COMPLETE]
```

**CRITICAL RULE:** Never add [WORKFLOW_COMPLETE] until ALL 5 phases are done
and final_documentation.md exists. The marker MUST be on its own line at the
very end of your message.

## Phase Workflow

### Always Start Here
Call `ls` to see what files exist in the virtual filesystem.

### Phase 1: Discovery
**When**: No files exist (empty filesystem)
**Action**: YOU MUST delegate to discovery-agent by calling:

task(
    description="Discover all repositories and code structure. Extract project ID from the user request. List all available repositories. Save complete results to discovery_catalog.json",
    subagent_type="discovery-agent"
)

DO NOT attempt discovery yourself - the discovery-agent has the required MCP tools to access Fairmind project data.

### Phase 2: Scoping
**When**: discovery_catalog.json exists, but NOT documentation_scope.json
**Action**: YOU MUST delegate to scoping-agent by calling:

task(
    description="Review the discovery catalog and work with the user to define documentation scope. Determine which repositories and components to document. Save scope to documentation_scope.json",
    subagent_type="scoping-agent"
)

DO NOT create the scope yourself - the scoping-agent will interact with the user.

### Phase 3: Analysis
**When**: documentation_scope.json exists, but NOT analysis_summary.md
**Action**: YOU MUST delegate to analysis-agent by calling:

task(
    description="Analyze code repositories according to the defined scope. Use MCP Code tools to explore file structures, search code, and understand implementations. Save analysis results to analysis_summary.md",
    subagent_type="analysis-agent"
)

DO NOT analyze code yourself - the analysis-agent has the required MCP Code tools.

### Phase 4: Clarification
**When**: analysis_summary.md exists, but NOT clarifications_answered.json
**Action**: YOU MUST delegate to clarification-agent by calling:

task(
    description="Review the analysis summary and prepare questions for the user about ambiguous code patterns, unclear requirements, or needed clarifications. Collect user responses. Save answered clarifications to clarifications_answered.json",
    subagent_type="clarification-agent"
)

DO NOT skip this phase - user input is critical for accurate documentation.

### Phase 5: Generation
**When**: clarifications_answered.json exists, but NOT final_documentation.md
**Action**: YOU MUST delegate to generation-agent by calling:

task(
    description="Generate final documentation from the analysis and clarifications. Use MCP Code tools to fetch relevant code examples. Create comprehensive documentation. Save to final_documentation.md",
    subagent_type="generation-agent"
)

DO NOT write documentation yourself - the generation-agent will create it properly.

### Completion
**When**: final_documentation.md exists
**Action**:
1. Read the final documentation using `read_file("final_documentation.md")`
2. Present it to the user with a completion summary
3. Update todos to mark all phases completed
4. **CRITICAL**: End your final message with the marker: `[WORKFLOW_COMPLETE]`

The `[WORKFLOW_COMPLETE]` marker signals to the router that DocGen has finished its work and the user's next message should be re-routed based on intent. This is essential for proper session management.

## Critical Rules - READ CAREFULLY

1. **ALWAYS call `ls` FIRST** to determine the current phase
2. **ALWAYS use the `task` tool to delegate** to specialist agents - this is NON-NEGOTIABLE
3. **NEVER do the specialized work yourself** - you don't have MCP tools for discovery, analysis, or code access
4. **After each delegation**, call `ls` again to verify the expected output file was created
5. **If a file is missing**, call the same agent again with more specific instructions about what went wrong

## What You Should NEVER Do

- DO NOT call MCP tools directly (you don't have General_*, Studio_*, or Code_* tools)
- DO NOT try to discover repositories yourself (use discovery-agent)
- DO NOT try to analyze code yourself (use analysis-agent)
- DO NOT create documentation content yourself (use generation-agent)
- DO NOT skip phases - each phase builds on the previous one

## What You SHOULD Do

- DO call `ls` to check filesystem state
- DO call `write_todos` to track progress
- DO call `read_file` to verify output files
- DO call `task` to delegate all specialized work
- DO provide clear, specific descriptions when delegating

You are a coordinator and progress tracker. Your job is to ensure each specialist agent is called at the right time with the right instructions. The specialist agents have the tools and expertise to do the actual work."""

    # Create agent with phases
    subagents = [
        discovery_agent_with_tools,
        scoping_agent_with_tools,     # Compiled graph with human_input interrupt
        analysis_agent_with_tools,
        clarification_agent_with_tools,  # Compiled graph with human_input interrupt
        generation_agent_with_tools,
    ]

    # Create the deep agent
    # Use async_create_deep_agent to support MCP tools that require async invocation
    # NOTE: Scoping and Clarification agents use the "middleware" key with HumanInTheLoopMiddleware
    # to ensure proper interrupt propagation. The framework applies middleware during agent creation.
    # Using "graph" key bypasses middleware, so dict-based definitions with middleware key is correct.
    #
    # ORCHESTRATOR: No additional tools needed - just delegates to subagents via task tool
    # Phases flow automatically without confirmation prompts.

    # Create SafeSummarizationMiddleware for context management
    safe_summarization = SafeSummarizationMiddleware(
        model=model,
        max_tokens_before_summary=50000,  # Lower threshold for earlier intervention
        messages_to_keep=20,
        hard_limit_tokens=180000,  # Emergency protection at 90% of 200k
    )

    return async_create_deep_agent(
        model=model,
        tools=[],  # Orchestrator uses only built-in task tool for delegation
        instructions=orchestrator_instructions,
        middleware=[safe_summarization],  # Add safe context management
        subagents=subagents,
    ).with_config({"recursion_limit": 1000})


# Convenience function
def create_docgen_agent(mcp_tools: Optional[Dict[str, Any]] = None) -> DocGenAgent:
    """
    Create a DocGen agent instance.

    Args:
        mcp_tools: Optional MCP tools dictionary

    Returns:
        Configured DocGenAgent instance
    """
    return DocGenAgent(mcp_tools=mcp_tools)


# For LangGraph compatibility - Multi-user support with lazy agent creation
# Export factory instead of pre-compiled agent. The factory creates agents on-demand
# with MCP tools from state.mcp_tools_cache, enabling proper multi-user support.
#
# Flow:
# 1. Router loads this module: agent = create_stateful_agent_factory(...)
# 2. Router receives first request from user with API key
# 3. Router initializes MCP tools into state.mcp_tools_cache
# 4. Router wrapper detects factory: hasattr(agent, 'is_agent_factory')
# 5. Router calls: agent_instance = agent(state)  # Creates agent with tools
# 6. Router invokes: result = await agent_instance.ainvoke(state)
#
# The factory caches the compiled agent to avoid recompilation overhead on subsequent calls.
from fairmind.shared.agent_factory import create_stateful_agent_factory

agent = create_stateful_agent_factory(
    agent_creator=create_langgraph_agent,
    agent_name="DocGen",
    cache_compiled=True  # Cache to avoid recompilation overhead
)


# For command-line testing
if __name__ == "__main__":
    async def main():
        docgen = create_docgen_agent()
        result = await docgen.run(
            "Document the authentication module",
            project_id="my_project_id"
        )
        print("Documentation Generation Complete!")
        print(f"\nFinal response:\n{result['final_response']}")
        print(f"\nFiles created: {list(result['files'].keys())}")

    asyncio.run(main())
