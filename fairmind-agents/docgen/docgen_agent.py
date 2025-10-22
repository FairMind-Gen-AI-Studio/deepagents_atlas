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

# Import MCP tools initialization
def _get_mcp_initialize():
    """Get MCP tools initialization function from atlas_v1."""
    try:
        # Temporarily add atlas_v1 to path for this import only
        atlas_path = str(Path(__file__).parent.parent / "atlas_v1")
        if atlas_path not in sys.path:
            sys.path.insert(0, atlas_path)
        from mcp_client import initialize_mcp_tools
        return initialize_mcp_tools
    except ImportError:
        logging.warning("MCP client not available - using builtin tools only")
        return None

initialize_mcp_tools = _get_mcp_initialize()


def _initialize_mcp_tools_sync():
    """Synchronous wrapper for MCP tools initialization."""
    if not initialize_mcp_tools:
        return None

    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        logger.warning("Cannot initialize MCP tools - event loop already running")
        return None
    else:
        try:
            return loop.run_until_complete(initialize_mcp_tools())
        except Exception as e:
            logger.warning(f"Failed to initialize MCP tools: {e}")
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
    # Temporarily remove atlas_v1 from sys.path to avoid module conflicts
    atlas_path = str(Path(__file__).parent.parent / "atlas_v1")
    atlas_in_path = atlas_path in sys.path
    if atlas_in_path:
        sys.path.remove(atlas_path)

    try:
        # Import local agents module
        from agents import (
            discovery_agent,
            scoping_agent,
            analysis_agent,
            clarification_agent,
            generation_agent,
            get_discovery_tools,
            get_scoping_tools,
            get_analysis_tools,
            get_clarification_tools,
            get_generation_tools,
        )
    finally:
        # Restore atlas_v1 to sys.path if it was there before
        if atlas_in_path and atlas_path not in sys.path:
            sys.path.insert(0, atlas_path)

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
    mcp_tool_objects = list(mcp_tools.values()) if mcp_tools and isinstance(mcp_tools, dict) else []

    # Assign phase-specific tools to each agent
    # NOTE: Agents that need human_input interrupts use the "middleware" key with
    # HumanInTheLoopMiddleware. The "graph" key bypasses middleware, so NEVER use it
    # for agents that need interrupts. Framework applies middleware at creation time.

    discovery_agent_with_tools = discovery_agent.copy()
    discovery_agent_with_tools["tools"] = get_discovery_tools(mcp_tools)

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
    analysis_agent_with_tools["tools"] = get_analysis_tools(mcp_tools)

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
    generation_agent_with_tools["tools"] = get_generation_tools(mcp_tools)

    # Runtime verification - check that critical tools are available
    discovery_tools = discovery_agent_with_tools['tools']
    analysis_tools = analysis_agent_with_tools['tools']

    # Critical tool names we expect for core functionality
    critical_tools = {
        'discovery': ['General_list_projects', 'Code_list_repositories', 'Code_tree'],
        'analysis': ['Code_search', 'Code_cat']
    }

    # Check discovery agent has critical tools
    if mcp_tools:
        discovery_tool_names = [getattr(t, 'name', str(t)) for t in discovery_tools]
        missing_discovery = []
        for tool_name in critical_tools['discovery']:
            # Check for both prefixed and non-prefixed versions
            found = any(
                tool_name in name or f"mcp__fairmind__{tool_name}" in name
                for name in discovery_tool_names
            )
            if not found:
                missing_discovery.append(tool_name)

        if missing_discovery:
            logger.warning(f"⚠️  Discovery agent is missing critical tools: {missing_discovery}")
            logger.warning("   Repository discovery may not work correctly")

        # Check analysis agent has critical tools
        analysis_tool_names = [getattr(t, 'name', str(t)) for t in analysis_tools]
        missing_analysis = []
        for tool_name in critical_tools['analysis']:
            found = any(
                tool_name in name or f"mcp__fairmind__{tool_name}" in name
                for name in analysis_tool_names
            )
            if not found:
                missing_analysis.append(tool_name)

        if missing_analysis:
            logger.warning(f"⚠️  Analysis agent is missing critical tools: {missing_analysis}")
            logger.warning("   Code analysis may not work correctly")

        # Verify tool counts are reasonable
        if len(discovery_tools) < 5:
            logger.warning(f"⚠️  Discovery agent has only {len(discovery_tools)} tools")
            logger.warning("   Expected at least 5 tools (General + Code)")
            logger.warning("   Check that MCP Fairmind server is fully initialized")

    # Enhanced logging for tool assignment verification
    logger.info("=" * 70)
    logger.info("MCP TOOLS VERIFICATION")
    logger.info("=" * 70)

    if mcp_tool_objects:
        logger.info(f"✅ MCP tools initialized: {len(mcp_tool_objects)} tools available")
        logger.info(f"   Available MCP tools: {[getattr(t, 'name', str(t)) for t in mcp_tool_objects][:5]}...")
        logger.info("")
        logger.info("MCP tools assigned to agents:")

        # Discovery agent
        discovery_tools = discovery_agent_with_tools['tools']
        discovery_tool_names = [getattr(t, 'name', str(t)) for t in discovery_tools]
        logger.info(f"  - Discovery: {len(discovery_tools)} tools")
        if discovery_tools:
            logger.info(f"      Examples: {discovery_tool_names[:3]}")
            has_code_tools = any('Code_' in name for name in discovery_tool_names)
            has_general_tools = any('General_' in name for name in discovery_tool_names)
            logger.info(f"      Has Code tools: {has_code_tools}, Has General tools: {has_general_tools}")

        # Scoping agent (compiled graph with human_input interrupt)
        logger.info(f"  - Scoping: Compiled subgraph with human_input interrupt support")

        # Analysis agent
        analysis_tools = analysis_agent_with_tools['tools']
        analysis_tool_names = [getattr(t, 'name', str(t)) for t in analysis_tools]
        logger.info(f"  - Analysis: {len(analysis_tools)} tools")
        if analysis_tools:
            logger.info(f"      Examples: {analysis_tool_names[:3]}")

        # Clarification agent (compiled graph with human_input interrupt)
        logger.info(f"  - Clarification: Compiled subgraph with human_input interrupt support")

        # Generation agent
        generation_tools = generation_agent_with_tools['tools']
        generation_tool_names = [getattr(t, 'name', str(t)) for t in generation_tools]
        logger.info(f"  - Generation: {len(generation_tools)} tools")
        if generation_tools:
            logger.info(f"      Examples: {generation_tool_names[:3]}")

        # Verification warnings
        logger.info("")
        if len(discovery_tools) == 0:
            logger.warning("⚠️  WARNING: Discovery agent has NO MCP tools!")
            logger.warning("   This will prevent repository discovery. Check MCP connection.")

        if len(analysis_tools) == 0:
            logger.warning("⚠️  WARNING: Analysis agent has NO MCP tools!")
            logger.warning("   This will prevent code analysis. Check MCP connection.")

    else:
        logger.warning("⚠️  NO MCP tools available - agents will use only built-in tools")
        logger.warning("   This means repository discovery and code analysis will NOT work")
        logger.warning("   Check: FAIRMIND_MCP_URL and FAIRMIND_MCP_TOKEN environment variables")

    logger.info("")
    logger.info("Built-in tools (added by deepagents middleware):")
    logger.info("  - File operations: ls, read_file, write_file, edit_file")
    logger.info("  - Task planning: write_todos")
    logger.info("  - Delegation: task (orchestrator only)")
    logger.info("")
    logger.info("ARCHITECTURE NOTE:")
    logger.info("  - Orchestrator: Delegates via 'task' tool (no MCP tools by design)")
    logger.info("  - Dict-based subagents: Receive MCP tools at creation time")
    logger.info("  - Compiled subagents: Use graph pattern for human_input interrupt support")
    logger.info("  - Human-in-the-loop: Scoping and Clarification use compiled graphs")
    logger.info("  - In LangSmith: Look for 'task' tool invocations to see subagent prompts")
    logger.info("=" * 70)

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

ONLY when `final_documentation.md` exists:
1. Present the final documentation to the user
2. Add the marker `[WORKFLOW_COMPLETE]` at the end of your message
3. This signals the router that DocGen has finished and the user's next message should be re-routed

**Never add [WORKFLOW_COMPLETE] until the entire workflow is done!**

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

    return async_create_deep_agent(
        model=model,
        tools=[],  # Orchestrator uses only built-in task tool for delegation
        instructions=orchestrator_instructions,
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


# For LangGraph compatibility
agent = create_langgraph_agent(_initialize_mcp_tools_sync())


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
