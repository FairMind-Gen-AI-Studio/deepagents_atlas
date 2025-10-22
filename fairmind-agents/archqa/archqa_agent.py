"""ArchQA Agent - Architectural Q&A System

Answers complex architectural questions about codebases using MCP FairMind
integration for codebase access and Tavily for technology research.

Architecture:
- context-mapper: Analyzes question scope and discovers relevant projects
- code-investigator: Performs deep code analysis with web research
- solution-synthesizer: Synthesizes findings into comprehensive answers

Usage:
    # Via LangGraph CLI
    langgraph dev

    # Via Python
    python archqa_agent.py
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# CRITICAL: Load .env BEFORE any LangChain imports
# This ensures LANGCHAIN_* variables are available when deepagents imports LangChain
_project_root = Path(__file__).parent
load_dotenv(_project_root.parent.parent / ".env")

# Setup logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _check_langsmith_status():
    """Check and log LangSmith tracing status for ArchQA agent."""
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2") == "true"
    project_name = os.getenv("LANGCHAIN_PROJECT")
    api_key = os.getenv("LANGCHAIN_API_KEY")

    if tracing_enabled and project_name and api_key:
        logger.info(f"🔍 [ArchQA] LangSmith tracing enabled for project: {project_name}")
        return {"enabled": True, "project": project_name}
    elif tracing_enabled:
        logger.warning("⚠️ [ArchQA] LangSmith tracing enabled but missing configuration")
        return {"enabled": False, "issue": "missing_config"}
    else:
        logger.info("📝 [ArchQA] LangSmith tracing disabled")
        return {"enabled": False, "disabled": True}


# Check LangSmith status after loading environment
_langsmith_status = _check_langsmith_status()

# Add src to path for deepagents and fairmind middleware
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from deepagents import async_create_deep_agent
from fairmind.middleware import SafeSummarizationMiddleware

# Import agent definitions
from agents import (
    context_mapper_agent,
    code_investigator_agent,
    solution_synthesizer_agent
)

# Import from shared library (no more cross-agent imports!)
from shared.mcp import initialize_mcp_tools
from shared.models import initialize_model, get_model_info
from shared.utils import run_async_in_sync_context, setup_logging

# Import MCP tool filtering functions (agent-specific logic stays local)
from mcp_tool_filters import (
    get_context_mapper_tools,
    get_code_investigator_tools,
    get_solution_synthesizer_tools,
    verify_tool_assignment,
)


# MCP Tools Initialization using shared library
def _initialize_mcp_tools_sync():
    """
    Synchronous wrapper for MCP tools initialization using shared library.

    Returns:
        Dictionary of MCP tool objects, or None if initialization fails
    """
    return run_async_in_sync_context(initialize_mcp_tools)


def _init_tavily_tools():
    """
    Initialize Tavily search tool if available.

    Returns:
        list: List containing tavily_search function if available, empty list otherwise
    """
    try:
        from tavily import TavilyClient

        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            logger.warning("⚠️  TAVILY_API_KEY not set - web search disabled")
            logger.warning("   Set TAVILY_API_KEY in .env to enable technology research")
            return []

        tavily_client = TavilyClient(api_key=api_key)

        def tavily_search(query: str, max_results: int = 5):
            """
            Search the web for information about technologies, frameworks, and best practices.

            Args:
                query: Search query (e.g., "Django authentication best practices 2025")
                max_results: Maximum number of results to return

            Returns:
                Search results with titles, URLs, and content snippets
            """
            return tavily_client.search(query, max_results=max_results)

        logger.info("✅ Tavily web search enabled")
        return [tavily_search]

    except ImportError:
        logger.warning("⚠️  Tavily not installed - web search disabled")
        logger.warning("   Install with: pip install tavily-python")
        return []
    except Exception as e:
        logger.warning(f"⚠️  Tavily initialization failed: {e}")
        return []


# Orchestrator Instructions
ORCHESTRATOR_INSTRUCTIONS = """You are the ArchQA Orchestrator - an expert at answering architectural questions about codebases.

## Your Mission

Answer complex architectural questions by coordinating specialized agents. You are the conductor, not the performer - delegate ALL work to specialist agents.

## Your Workflow

When you receive an architectural question, follow these steps:

### Step 1: Context Mapping
Use the `task` tool to delegate to context-mapper:

```
task(
    description="Analyze question scope, find relevant projects and repositories using MCP General and Studio tools. Question: [USER_QUESTION]",
    subagent_type="context-mapper"
)
```

Wait for completion. The agent will create `/tmp/context_map.json` with investigation scope.

### Step 2: Code Investigation
Use the `task` tool to delegate to code-investigator:

```
task(
    description="Investigate code implementations using MCP Code tools and research technologies with web search. Use findings from /tmp/context_map.json to guide investigation. Question: [USER_QUESTION]",
    subagent_type="code-investigator"
)
```

Wait for completion. The agent will create `/investigation_findings.md` with detailed analysis.

### Step 3: Synthesize Answer
Use the `task` tool to delegate to solution-synthesizer:

```
task(
    description="Synthesize findings into comprehensive architectural answer. Read /tmp/context_map.json and /investigation_findings.md. Save answer to /architectural_answer.md and present to user. Question: [USER_QUESTION]",
    subagent_type="solution-synthesizer"
)
```

Wait for completion. The agent will create `/architectural_answer.md` and present the final answer to the user.

### Step 4: Verification (Optional)
After synthesis, you can optionally:
- Use `ls` to verify all expected files were created:
  - `/tmp/context_map.json` (working file)
  - `/investigation_findings.md` (deliverable)
  - `/architectural_answer.md` (deliverable)
- Use `read_file` to check intermediate outputs
- Present summary or offer to elaborate on specific sections

## Critical Rules

- **ALWAYS delegate** - Use `task` tool for ALL actual work
- **DO NOT access MCP tools directly** - You don't have them, specialist agents do
- **Run agents SEQUENTIALLY** - Each depends on previous outputs
- **Use virtual filesystem** - Use `ls`, `read_file` to check agent outputs
- **Track progress** - Use `write_todos` to show user what you're doing

## Tools Available

**Delegation:**
- `task(description, subagent_type)`: Delegate to specialist agents

**Virtual Filesystem:**
- `ls()`: List files in virtual filesystem
- `read_file(filename)`: Read files created by agents
- `write_file(filename, content)`: Create files (rarely needed by orchestrator)

**Progress Tracking:**
- `write_todos(todos)`: Track task progress for user visibility

**NOT Available to You:**
- MCP tools (General_*, Studio_*, Code_*) - only specialist agents have these
- Tavily search - only code-investigator has this

## Example Interaction

**User**: "What are the technical debt areas in the authentication service?"

**Your Response**:
1. Create todo list:
   - Map project context
   - Investigate code for technical debt
   - Synthesize findings into answer

2. Call context-mapper:
   "Let me start by mapping the project context..."
   → Use `task` tool

3. After context-mapper completes:
   "Context mapped. Now investigating authentication service code..."
   → Use `task` tool for code-investigator

4. After code-investigator completes:
   "Investigation complete. Synthesizing findings..."
   → Use `task` tool for solution-synthesizer

5. After solution-synthesizer completes:
   "Analysis complete! Here's what I found:"
   → Present final answer or summary
   → **CRITICAL**: End your final message with the marker: `[WORKFLOW_COMPLETE]`

The `[WORKFLOW_COMPLETE]` marker signals to the router that ArchQA has finished its work and the user's next message should be re-routed based on intent.

## Handling Follow-up Questions

If user asks follow-up questions:
- **For scope changes**: Re-run context-mapper with new scope
- **For deeper analysis**: Re-run code-investigator with focused direction
- **For alternative solutions**: Re-run solution-synthesizer with new constraints

## Quality Assurance

Before presenting final answer:
- Verify `/tmp/context_map.json` exists (use `ls`)
- Verify `/investigation_findings.md` exists (use `ls`)
- Verify `/architectural_answer.md` exists (use `ls`)
- Ensure solution-synthesizer provided comprehensive answer
- Offer to elaborate on specific sections if user wants more detail

## Remember

You coordinate, you don't execute. Your job is to:
1. Understand user's question
2. Delegate to right agents in right order
3. Track progress for user
4. Present final results

Let the specialist agents do their expert work!
"""


def create_archqa_agent():
    """
    Create the ArchQA agent (LangGraph compiled graph).

    This function initializes MCP Fairmind tools explicitly and assigns filtered
    tool subsets to each specialized agent. Uses shared library for infrastructure.

    Returns:
        Compiled LangGraph agent ready for architectural queries
    """
    # Initialize model from environment configuration using shared library
    model = initialize_model(agent_prefix="ARCHQA")
    model_info = get_model_info(agent_prefix="ARCHQA")

    # Initialize MCP tools from Fairmind via atlas_v1 mcp_client
    mcp_tools = _initialize_mcp_tools_sync()

    # Initialize custom tools (Tavily for web research)
    tavily_tools = _init_tavily_tools()

    # Filter MCP tools for each agent based on their needs
    context_mapper_tools = get_context_mapper_tools(mcp_tools) if mcp_tools else []
    code_investigator_tools = get_code_investigator_tools(mcp_tools) if mcp_tools else []
    solution_synthesizer_tools = get_solution_synthesizer_tools(mcp_tools) if mcp_tools else []

    # Create agent configurations with assigned tools
    # Each agent gets: their filtered MCP tools + Tavily (for investigators)
    context_mapper_with_tools = context_mapper_agent.copy()
    context_mapper_with_tools["tools"] = context_mapper_tools + tavily_tools

    code_investigator_with_tools = code_investigator_agent.copy()
    code_investigator_with_tools["tools"] = code_investigator_tools + tavily_tools

    solution_synthesizer_with_tools = solution_synthesizer_agent.copy()
    solution_synthesizer_with_tools["tools"] = solution_synthesizer_tools  # No Tavily needed

    # Log comprehensive configuration details
    logger.info("=" * 70)
    logger.info("ARCHQA AGENT CONFIGURATION")
    logger.info("=" * 70)
    logger.info("")
    logger.info("MODEL CONFIGURATION:")
    logger.info(f"  Provider: {model_info['provider']}")
    logger.info(f"  Model: {model_info['model']}")
    logger.info(f"  Temperature: {model_info['temperature']}")
    logger.info(f"  Max tokens: {model_info['max_tokens']}")
    logger.info("")

    if mcp_tools:
        logger.info(f"✅ MCP tools initialized: {len(mcp_tools)} tools available")
        logger.info("")
        logger.info("MCP tools assigned to agents:")

        # Context Mapper
        context_tool_names = [getattr(t, 'name', str(t)) for t in context_mapper_tools]
        logger.info(f"  - context-mapper: {len(context_mapper_tools)} MCP tools")
        if context_mapper_tools:
            logger.info(f"      Examples: {context_tool_names[:3]}")
            has_general = any('General_' in name for name in context_tool_names)
            has_studio = any('Studio_' in name for name in context_tool_names)
            has_code = any('Code_' in name for name in context_tool_names)
            logger.info(f"      Has General: {has_general}, Studio: {has_studio}, Code: {has_code}")

        # Code Investigator
        investigator_tool_names = [getattr(t, 'name', str(t)) for t in code_investigator_tools]
        logger.info(f"  - code-investigator: {len(code_investigator_tools)} MCP tools")
        if code_investigator_tools:
            logger.info(f"      Examples: {investigator_tool_names[:3]}")
            has_code_tools = any('Code_' in name for name in investigator_tool_names)
            logger.info(f"      Has Code tools: {has_code_tools}")

        # Solution Synthesizer
        logger.info(f"  - solution-synthesizer: {len(solution_synthesizer_tools)} MCP tools (filesystem only)")

        # Verification warnings
        logger.info("")
        if len(context_mapper_tools) == 0:
            logger.warning("⚠️  WARNING: context-mapper has NO MCP tools!")
            logger.warning("   This will prevent project discovery. Check MCP connection.")

        if len(code_investigator_tools) == 0:
            logger.warning("⚠️  WARNING: code-investigator has NO MCP tools!")
            logger.warning("   This will prevent code analysis. Check MCP connection.")

    else:
        logger.warning("⚠️  NO MCP tools available - agents will use only built-in tools")
        logger.warning("   This means project discovery and code analysis will NOT work")
        logger.warning("   Check: FAIRMIND_MCP_URL and FAIRMIND_MCP_TOKEN environment variables")

    logger.info("")
    logger.info(f"Custom tools: {len(tavily_tools)} ({'Tavily' if tavily_tools else 'None'})")
    logger.info("")
    logger.info("Built-in tools (added by deepagents middleware):")
    logger.info("  - File operations: ls, read_file, write_file, edit_file")
    logger.info("  - Task planning: write_todos")
    logger.info("  - Delegation: task (orchestrator only)")
    logger.info("")
    logger.info("ARCHITECTURE:")
    logger.info("  - Orchestrator: Delegates via 'task' tool (no MCP tools)")
    logger.info("  - Subagents: Receive filtered MCP tools based on their role")
    logger.info("  - In LangSmith: Look for tool calls in subagent traces")
    logger.info("")
    logger.info("CONTEXT MANAGEMENT:")
    logger.info("  - SafeSummarizationMiddleware enabled")
    logger.info("  - Summarization threshold: 50,000 tokens (lower than default 85k)")
    logger.info("  - Hard limit protection: 180,000 tokens (90% of 200k)")
    logger.info("  - Fallback: Aggressive trimming if summarization fails")
    logger.info("=" * 70)

    # Create SafeSummarizationMiddleware for context management
    safe_summarization = SafeSummarizationMiddleware(
        model=model,
        max_tokens_before_summary=50000,  # Lower threshold for earlier intervention
        messages_to_keep=20,
        hard_limit_tokens=180000,  # Emergency protection at 90% of 200k
    )

    # Create the deep agent with explicit tool assignment and middleware
    # Orchestrator has no tools - delegates to subagents with their assigned tools
    return async_create_deep_agent(
        tools=[],  # Orchestrator has no tools - only delegates
        instructions=ORCHESTRATOR_INSTRUCTIONS,
        model=model,  # Use configured model from environment
        middleware=[safe_summarization],  # Add safe context management
        subagents=[
            context_mapper_with_tools,      # Has: General, Studio, Code tools + Tavily
            code_investigator_with_tools,   # Has: Code, Studio tools + Tavily
            solution_synthesizer_with_tools # Has: No MCP tools (filesystem only)
        ]
    ).with_config({"recursion_limit": 1000})


# For LangGraph Studio/CLI - this is what langgraph.json references
agent = create_archqa_agent()


# CLI testing interface
if __name__ == "__main__":
    import asyncio

    async def test_query():
        """Test the agent with a sample architectural question."""

        # Sample question - replace with your own
        test_question = input("\nEnter your architectural question (or press Enter for example): ").strip()

        if not test_question:
            test_question = "How does authentication work in the backend-api repository?"

        print(f"\n{'='*70}")
        print(f"QUESTION: {test_question}")
        print(f"{'='*70}\n")

        # Run the agent
        # Note: LangGraph will handle state/persistence automatically
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": test_question}]
        })

        # Extract and display the answer
        print(f"\n{'='*70}")
        print("ANSWER:")
        print(f"{'='*70}\n")

        # Get the last message (should be from solution-synthesizer)
        if "messages" in result and result["messages"]:
            final_message = result["messages"][-1]
            if hasattr(final_message, "content"):
                print(final_message.content)
            else:
                print(final_message)
        else:
            print("No response generated. Check agent logs above.")

        print(f"\n{'='*70}")
        print("SESSION COMPLETE")
        print(f"{'='*70}\n")

    # Run the test
    print("\n🚀 ArchQA Agent - Architectural Q&A System")
    print("=" * 70)
    print("This agent answers architectural questions about codebases.")
    print("It uses MCP FairMind for code access and Tavily for technology research.")
    print("=" * 70)

    try:
        asyncio.run(test_query())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!")
    except Exception as e:
        logger.error(f"Error running agent: {e}", exc_info=True)
