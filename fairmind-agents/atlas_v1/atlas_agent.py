# Atlas V1 Agent - Clean Modular Architecture
# 4-phase methodology implementation using DeepAgents framework

"""
Atlas V1 Agent

This is the main entry point for the Atlas V1 agent, implementing a 
4-phase methodology through modular agents and clean orchestration.

Phases:
1. Investigation - Silent project exploration
2. Discussion - Interactive requirements clarification  
3. Planning - Repository analysis and solution design
4. Task Generation - Create actionable tasks
"""

import os
import sys
import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add src to path for deepagents
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the lightweight coordinator
from atlas_coordinator import AtlasCoordinator

# Import MCP tools initialization if available
try:
    from mcp_client import initialize_mcp_tools
except ImportError:
    initialize_mcp_tools = None
    logging.warning("MCP client not available - using builtin tools only")

logger = logging.getLogger(__name__)

def _check_langsmith_status():
    """Check and log LangSmith tracing status."""
    tracing_enabled = os.getenv("LANGCHAIN_TRACING_V2") == "true"
    project_name = os.getenv("LANGCHAIN_PROJECT")
    api_key = os.getenv("LANGCHAIN_API_KEY")

    if tracing_enabled and project_name and api_key:
        logger.info(f"🔍 LangSmith tracing enabled for project: {project_name}")
        return {"enabled": True, "project": project_name}
    elif tracing_enabled:
        logger.warning("⚠️ LangSmith tracing enabled but missing configuration (project or API key)")
        return {"enabled": False, "issue": "missing_config"}
    else:
        logger.info("📝 LangSmith tracing disabled")
        return {"enabled": False, "disabled": True}

def create_langsmith_diagnostics() -> Dict[str, Any]:
    """
    Create comprehensive LangSmith diagnostics for troubleshooting.

    Returns:
        Dictionary with diagnostic information and troubleshooting tips
    """
    import time

    status = _check_langsmith_status()

    diagnostics = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": status,
        "configuration": {
            "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2"),
            "LANGCHAIN_PROJECT": os.getenv("LANGCHAIN_PROJECT"),
            "LANGCHAIN_API_KEY_SET": bool(os.getenv("LANGCHAIN_API_KEY")),
        },
        "troubleshooting": {
            "verify_traces_url": "https://smith.langchain.com",
            "expected_project": os.getenv("LANGCHAIN_PROJECT", "unknown"),
            "thread_id_format": "atlas-{hash_number}",
            "trace_delay": "Traces may take 5-10 seconds to appear in UI",
        }
    }

    # Add specific recommendations based on status
    if status.get("enabled"):
        diagnostics["recommendations"] = [
            f"✅ LangSmith is correctly configured",
            f"🔍 Check traces at: https://smith.langchain.com/projects/{os.getenv('LANGCHAIN_PROJECT')}",
            f"🕐 Traces may take 5-10 seconds to appear",
            f"🔍 Filter by thread_id format: atlas-*"
        ]
    elif status.get("issue") == "missing_config":
        diagnostics["recommendations"] = [
            "⚠️ LangSmith tracing enabled but configuration incomplete",
            "🔧 Check LANGCHAIN_PROJECT and LANGCHAIN_API_KEY in .env",
            "📄 Verify .env file is loaded correctly"
        ]
    else:
        diagnostics["recommendations"] = [
            "📝 LangSmith tracing is disabled",
            "🔧 Set LANGCHAIN_TRACING_V2=true in .env to enable",
            "📊 Add LANGCHAIN_PROJECT and LANGCHAIN_API_KEY"
        ]

    return diagnostics

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
        # If loop is already running, we can't use run_until_complete
        logger.warning("Cannot initialize MCP tools - event loop already running")
        return None
    else:
        try:
            return loop.run_until_complete(initialize_mcp_tools())
        except Exception as e:
            logger.warning(f"Failed to initialize MCP tools: {e}")
            return None

class AtlasAgentV1:
    """
    Atlas V1 Agent
    
    This class provides the main interface for the Atlas V1 agent,
    delegating all functionality to the modular AtlasCoordinator.
    
    The architecture follows DeepAgents patterns with:
    - 4 focused agent modules (~100 lines each)
    - Lightweight coordinator for orchestration
    - Clean separation of concerns
    """
    
    def __init__(self, config_path: Optional[str] = None, available_tools: Optional[Dict[str, Any]] = None):
        """
        Initialize Atlas Agent.
        
        Args:
            config_path: Optional path to configuration file (for compatibility)
            available_tools: Optional MCP tools dictionary
        """
        # Load environment variables
        load_dotenv()

        # Check and log LangSmith status
        self.langsmith_status = _check_langsmith_status()
        
        # Initialize MCP tools if not provided
        if available_tools is None:
            logger.info("Initializing MCP tools...")
            available_tools = _initialize_mcp_tools_sync()
            if available_tools:
                logger.info(f"Initialized {len(available_tools)} MCP tools")
            else:
                logger.info("No MCP tools available, using builtin tools only")
        
        # Create the coordinator with all the logic
        # Note: Coordinator is created but new system bypasses it
        try:
            self.coordinator = AtlasCoordinator(mcp_tools=available_tools)
        except Exception as e:
            logger.warning(f"Failed to create AtlasCoordinator: {e}. Using new deepagents system directly.")
            self.coordinator = None
        
        # Store for compatibility
        self.mcp_tools = available_tools
        
    async def run(self, user_request: str, project_id: Optional[str] = None, user_story_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the Atlas methodology.
        
        Args:
            user_request: The user's request
            project_id: Optional project ID
            user_story_id: Optional user story ID (incorporated into request)
            
        Returns:
            Execution results with final response, files, and todos
        """
        # Enhance request with user story if provided
        if user_story_id:
            user_request = f"{user_request} (User Story: {user_story_id})"
        
        # Delegate to coordinator with consistent thread_id
        thread_id = f"atlas-{hash(user_request) % 1000000}"  # Generate consistent thread_id
        return await self.coordinator.run(user_request, project_id, thread_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        status = self.coordinator.get_status() if self.coordinator else {"coordinator": "not_available"}
        status["langsmith"] = self.langsmith_status
        return status
    
    def get_virtual_file(self, filename: str) -> Optional[str]:
        """
        Get content from virtual filesystem.
        
        Note: This requires access to the agent's state. 
        Use the 'files' key from run() results instead.
        """
        logger.info("Virtual files are available in the run() result under 'files' key")
        return None
    
    def list_virtual_files(self) -> list:
        """
        List files in virtual filesystem.
        
        Note: This requires access to the agent's state.
        Use the 'files' key from run() results instead.
        """
        logger.info("Virtual files are available in the run() result under 'files' key")
        return []

    def get_langsmith_diagnostics(self) -> Dict[str, Any]:
        """
        Get comprehensive LangSmith diagnostics and troubleshooting information.

        Returns:
            Dictionary with diagnostic information and recommendations
        """
        return create_langsmith_diagnostics()

# Convenience function for creating Atlas agent
def create_atlas_agent(available_tools: Optional[Dict[str, Any]] = None) -> AtlasAgentV1:
    """
    Create an Atlas V1 agent instance.
    
    Args:
        available_tools: Optional MCP tools dictionary
        
    Returns:
        Configured AtlasAgentV1 instance
    """
    return AtlasAgentV1(available_tools=available_tools)

# For LangGraph compatibility - we need to export the actual graph
# Import what we need to create the graph directly
from deepagents import async_create_deep_agent
from langchain.agents.middleware.human_in_the_loop import ToolConfig
from agents import (
    investigation_agent,
    discussion_agent,
    planning_agent,
    task_generation_agent
)
# Import MCP tool filtering functions
from agents.investigation_agent import get_investigation_tools
from agents.discussion_agent import get_discussion_tools
from agents.planning_agent import get_planning_tools
from agents.task_generation_agent import get_task_generation_tools
from model_config import initialize_atlas_model
from langgraph.types import Command
# Import Atlas custom tools that aren't built-in to deepagents
from atlas_tools import approve_plan, human_confirm, human_input_multiline

def deduplicate_tools_by_name(tools):
    """
    Remove duplicate tools by name, keeping the first occurrence.
    This prevents 'Tool names must be unique' errors from Anthropic API.

    Args:
        tools: List of tool objects that may contain duplicates

    Returns:
        List of unique tools (no duplicate names)
    """
    seen_names = set()
    unique_tools = []
    for tool in tools:
        if hasattr(tool, 'name'):
            if tool.name not in seen_names:
                seen_names.add(tool.name)
                unique_tools.append(tool)
        else:
            # Include tools without names (shouldn't happen, but defensive)
            unique_tools.append(tool)
    return unique_tools




def create_langgraph_agent():
    """Create the LangGraph-compatible agent (compiled graph)."""
    # Initialize MCP tools if available
    mcp_tools = _initialize_mcp_tools_sync()
    mcp_tool_objects = []
    if mcp_tools and isinstance(mcp_tools, dict):
        mcp_tool_objects = list(mcp_tools.values())

    # Note: LangGraph API handles persistence automatically
    # No custom checkpointer needed - the platform manages state persistence
    
    # Main orchestrator instructions - directive and explicit
    orchestrator_instructions = """You are the Atlas V1 Orchestrator. You MUST delegate ALL work to specialized agents.

## CRITICAL RULES
1. You are ONLY a coordinator - you CANNOT do any investigation, discussion, planning, or task generation yourself
2. You MUST use the `task` tool to delegate all actual work to the appropriate agents
3. Never try to use MCP tools directly - let the specialized agents handle them

## Your Step-by-Step Workflow

### Step 1: Check Current State
First, use the `ls` tool to see what files exist.

### Step 2: Determine Phase and Delegate
Based on the files present, you MUST call the appropriate agent:

**If NO files exist or no phase files:**
You MUST call: `task(description="Investigate the project context and analyze the user story", subagent_type="investigation-agent")`

**If investigation_findings.md exists but NOT requirements_clarified.md:**
You MUST call: `task(description="Conduct requirements discussion with the user", subagent_type="discussion-agent")`

**If requirements_clarified.md exists but NOT implementation_plan.md:**
You MUST call: `task(description="Analyze repositories and create implementation plan", subagent_type="planning-agent")`

**If implementation_plan.md exists but NOT implementation_tasks.md:**
You MUST call: `task(description="Generate concrete implementation tasks from the plan", subagent_type="task-generation-agent")`

**If implementation_tasks.md exists:**
The workflow is complete. Summarize what was accomplished and **CRITICAL**: End your final message with the marker: `[WORKFLOW_COMPLETE]`

The `[WORKFLOW_COMPLETE]` marker signals to the router that Atlas has finished its work and the user's next message should be re-routed based on intent.

### Step 3: Wait and Monitor
After calling task, the agent will work autonomously. Wait for it to complete.

### Step 4: Check Results and Continue
After the agent completes, use `ls` again to verify outputs, then proceed to the next phase.

## Example Execution

User: "Analyze user story US-123"

Your response should be:
1. "Let me check the current state..." → Use `ls`
2. "No files found. Starting investigation phase..." → Use `task(description="Investigate project context for user story US-123", subagent_type="investigation-agent")`
3. Wait for completion
4. "Investigation complete. Moving to discussion phase..." → Continue workflow

REMEMBER: You coordinate, you don't execute. Always delegate using the task tool."""
    
    # Initialize the configured model (respects .env settings)
    model = initialize_atlas_model()
    
    # Configure human-in-the-loop interrupt for human_input and approve_plan tools
    # This allows users to approve, edit, or respond to these calls
    interrupt_config = {
        "human_input": {
            "allow_ignore": False,    # Don't allow skipping human_input
            "allow_respond": True,    # Allow text responses
            "allow_edit": True,       # Allow editing arguments
            "allow_accept": True,     # Allow accepting as-is
        },
        "approve_plan": True  # Use default config with all buttons (accept/edit/respond)
    }

    # Import Atlas custom tools that extend deepagents tools
    from atlas_tools import human_input

    # CRITICAL: Do NOT import or pass deepagents built-in tools explicitly!
    # The deepagents middleware automatically adds these tools:
    # - PlanningMiddleware adds: write_todos
    # - FilesystemMiddleware adds: ls, read_file, write_file, edit_file
    # Passing them explicitly would create "Tool names must be unique" errors

    # Assign MCP tools to each agent based on their phase requirements
    # Following the research example pattern - passing tools directly avoids circular references

    # Create copies of agent configs with MCP tools assigned
    # NOTE: Agents that need human_input interrupts use the "middleware" key with
    # HumanInTheLoopMiddleware. The "graph" key bypasses middleware, so NEVER use it
    # for agents that need interrupts. Framework applies middleware at creation time.

    investigation_agent_with_tools = investigation_agent.copy()
    investigation_agent_with_tools["tools"] = get_investigation_tools(mcp_tools)

    # DISCUSSION AGENT: Use middleware key for human_input + approve_plan interrupt support
    # The framework will apply HumanInTheLoopMiddleware to create proper LangGraph interrupts
    # DO NOT use "graph" key - that bypasses middleware!
    from agents.discussion_agent import DISCUSSION_PROMPT
    from langchain.agents.middleware import HumanInTheLoopMiddleware

    discussion_agent_with_tools = {
        "name": "discussion-agent",
        "description": "Phase 2: Interactive requirements clarification through targeted questions",
        "prompt": DISCUSSION_PROMPT,
        "tools": get_discussion_tools(mcp_tools),
        "middleware": [HumanInTheLoopMiddleware(interrupt_on={"human_input": True, "approve_plan": True})],
    }

    planning_agent_with_tools = planning_agent.copy()
    planning_agent_with_tools["tools"] = get_planning_tools(mcp_tools)

    task_generation_agent_with_tools = task_generation_agent.copy()
    task_generation_agent_with_tools["tools"] = get_task_generation_tools(mcp_tools)

    # Log the MCP tool assignment
    if mcp_tool_objects:
        print(f"✅ MCP tools assigned to agents:")
        print(f"   - Investigation: {len(investigation_agent_with_tools['tools'])} tools (Studio + General + Code)")
        print(f"   - Discussion: Dict-based with HumanInTheLoopMiddleware for human_input + approve_plan interrupts")
        print(f"   - Planning: {len(planning_agent_with_tools['tools'])} tools (Code + Studio)")
        print(f"   - Task Generation: {len(task_generation_agent_with_tools['tools'])} tools (All)")
    else:
        print("⚠️  MCP tools not available - agents will use only built-in tools")

    print("📝 Built-in tools: ls, read_file, write_file, write_todos, edit_file (added automatically by middleware)")
    print("📋 Human-in-the-loop: Discussion uses middleware key with HumanInTheLoopMiddleware for interrupt propagation")

    # Orchestrator gets no custom tools - just delegates to sub-agents
    all_tools = []

    # Pass agents with MCP tools to framework
    # Discussion agent uses "middleware" key with HumanInTheLoopMiddleware for proper interrupt support
    subagents = [
        investigation_agent_with_tools,
        discussion_agent_with_tools,  # Dict-based with HumanInTheLoopMiddleware for interrupts
        planning_agent_with_tools,
        task_generation_agent_with_tools
    ]

    # Note on Prompt Caching:
    # The core deepagents framework already includes AnthropicPromptCachingMiddleware (ttl="5m")
    # We enhance this with beta headers in model_config.py for:
    # - extended-cache-ttl-2025-04-11: Extended cache support
    # - token-efficient-tools-2025-02-19: Optimized tool definitions
    # This provides optimal caching without middleware duplication

    # Create the graph with new interrupt system
    # Note: LangGraph API handles persistence automatically - no custom checkpointer needed
    # Use async_create_deep_agent to support MCP tools that require async invocation
    # CRITICAL: The filesystem virtual depends on the 'files' field in DeepAgentState
    # which should now work correctly with LangGraph API after removing the custom reducer.
    # NOTE: Discussion agent uses "middleware" key with HumanInTheLoopMiddleware
    # instead of "graph" key to ensure middleware is properly applied during agent creation
    return async_create_deep_agent(
        model=model,  # Use the configured model with beta headers for caching
        tools=all_tools,  # Orchestrator has no tools - sub-agents have MCP tools assigned
        instructions=orchestrator_instructions,
        subagents=subagents,  # Sub-agents with phase-specific MCP tools and middleware
        tool_configs=interrupt_config
        # Note: checkpointer parameter removed - LangGraph API handles persistence automatically
        # Note: Prompt caching enabled via core middleware + model beta headers
    ).with_config({"recursion_limit": 1000})

def handle_interrupts(agent_executor, user_message: str, thread_id: str = "atlas-v1-session"):
    """
    Handle human-in-the-loop interrupts for the agent.

    Args:
        agent_executor: The compiled agent graph
        user_message: The initial user message
        thread_id: Thread identifier for state persistence (MUST be consistent across all phases)

    Returns:
        Final agent response
    """
    # Pass thread_id for state persistence (handled automatically by LangGraph API)
    config = {"configurable": {"thread_id": thread_id}}

    print("🧠 Starting Atlas V1 Agent with enhanced human-in-the-loop support...")
    print(f"📝 User message: {user_message}")
    print("⏳ Running agent (may require human approval for human_input calls)...")

    # Run the agent - it will interrupt on human_input calls
    # State persistence is handled automatically by LangGraph API
    for event in agent_executor.stream(
        {"messages": [{"role": "user", "content": user_message}]},
        config=config
    ):
        print(f"📊 Event: {event}")

        # Check if this event contains an interrupt
        if "__interrupt__" in event:
            print("⚡ INTERRUPT DETECTED!")
            interrupt_data = event["__interrupt__"]
            print(f"🔍 Interrupt details: {interrupt_data}")

            # For now, automatically accept human_input calls
            # In a real application, you'd prompt the user here
            print("✅ Auto-approving human_input call...")

            # Resume with acceptance
            from langgraph.types import Command
            resume_command = Command(resume=[{"type": "accept"}])
            for resume_event in agent_executor.stream(resume_command, config=config):
                print(f"📊 Resume event: {resume_event}")

            return "Agent completed with human input"

    return "Agent completed without interrupts"


# Lazy initialization to prevent multiple instantiation and tool duplication
_agent_instance = None

def get_agent():
    """Get the singleton Atlas agent instance with persistence support."""
    global _agent_instance
    if _agent_instance is None:
        print("🚀 Creating Atlas V1.1 agent instance with persistence...")

        # Initialize MCP tools for the coordinator
        mcp_tools = _initialize_mcp_tools_sync()

        # Use AtlasCoordinator which uses LangGraph's native state persistence
        _agent_instance = AtlasCoordinator(mcp_tools=mcp_tools)
        print("✅ Atlas V1.1 agent instance created successfully with persistence")
    return _agent_instance

# Create the LangGraph-compatible agent - this is what langgraph.json expects to find
agent = create_langgraph_agent()

# For command-line testing
if __name__ == "__main__":
    def main():
        # Use the module-level agent instead of creating a duplicate
        print("Atlas V1 Agent initialized successfully with enhanced human-in-the-loop support")
        print("Status: Agent initialized successfully")

        # Example usage with new interrupt handling
        result = handle_interrupts(
            agent,  # Use the module-level agent instance
            "Analyze user story US-123 and create implementation plan",
            "atlas-v1-session"  # Use consistent thread_id
        )
        print(f"Final result: {result}")

    main()