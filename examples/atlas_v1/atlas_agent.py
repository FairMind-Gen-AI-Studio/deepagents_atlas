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
        
        # Initialize MCP tools if not provided
        if available_tools is None:
            logger.info("Initializing MCP tools...")
            available_tools = _initialize_mcp_tools_sync()
            if available_tools:
                logger.info(f"Initialized {len(available_tools)} MCP tools")
            else:
                logger.info("No MCP tools available, using builtin tools only")
        
        # Create the coordinator with all the logic
        self.coordinator = AtlasCoordinator(mcp_tools=available_tools)
        
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
        return await self.coordinator.run(user_request, project_id, thread_id)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status."""
        return self.coordinator.get_status()
    
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
from deepagents.interrupt import HumanInterruptConfig
from agents import (
    investigation_agent,
    discussion_agent,
    planning_agent,
    task_generation_agent
)
from model_config import initialize_atlas_model
from langgraph.types import Command
# Import Atlas custom tools that aren't built-in to deepagents
from atlas_tools import approve_plan, human_confirm, human_input_multiline

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
The workflow is complete. Summarize what was accomplished.

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

    # Combine MCP tools with Atlas custom tools
    # Atlas custom tools extend the built-in deepagents tools with approval functionality
    atlas_custom_tools = [approve_plan, human_confirm, human_input_multiline]
    all_tools = mcp_tool_objects + atlas_custom_tools

    # Create the graph with new interrupt system
    # Note: LangGraph API handles persistence automatically - no custom checkpointer needed
    # Use async_create_deep_agent to support MCP tools that require async invocation
    # CRITICAL: The filesystem virtual depends on the 'files' field in DeepAgentState
    # which should now work correctly with LangGraph API after removing the custom reducer.
    return async_create_deep_agent(
        model=model,  # Use the configured model instead of default
        tools=all_tools,  # Pass both MCP and Atlas custom tools
        instructions=orchestrator_instructions,
        subagents=[
            investigation_agent,
            discussion_agent,
            planning_agent,
            task_generation_agent
        ],
        interrupt_config=interrupt_config
        # Note: checkpointer parameter removed - LangGraph API handles persistence automatically
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


# Create the LangGraph-compatible agent with built-in persistence
# This approach modifies the graph creation to include persistence hooks
def create_langgraph_agent_with_persistence():
    """Create agent with state_store persistence built-in."""
    # Import state store functions
    from state_store import get_atlas_store, sync_files_from_result, prepare_state_with_files
    from langgraph.errors import GraphInterrupt

    # Create the base agent first
    base_agent = create_langgraph_agent()

    # Add persistence by monkey-patching the invoke methods
    store = get_atlas_store()

    # Store original methods
    original_ainvoke = base_agent.ainvoke
    original_invoke = base_agent.invoke
    original_stream = base_agent.stream

    async def enhanced_ainvoke(input_data, config=None):
        """Enhanced ainvoke with state_store integration."""
        # PRE-LOAD: Enhance input with stored files
        enhanced_input = prepare_state_with_files(input_data)
        initial_file_count = len(enhanced_input.get('files', {}))
        print(f"🔄 ATLAS PERSISTENCE: PRE-LOAD {initial_file_count} files from store")

        try:
            # Call original method
            result = await original_ainvoke(enhanced_input, config)

            # POST-SYNC: Save any new files
            sync_files_from_result(result)
            final_files = store.get_files()
            print(f"🔄 ATLAS PERSISTENCE: POST-SYNC completed with {len(final_files)} files")

            # Replace result files with authoritative store files
            if isinstance(result, dict):
                result["files"] = final_files

            return result

        except GraphInterrupt as e:
            print(f"🔄 ATLAS PERSISTENCE: GraphInterrupt detected")

            # INTERRUPT RECOVERY: Get files from global cache
            try:
                import sys
                import os
                core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
                if core_path not in sys.path:
                    sys.path.insert(0, core_path)
                from deepagents.tools import _interrupt_file_cache
                from atlas_utils import clear_interrupt_cache
                if _interrupt_file_cache:
                    print(f"🔍 ATLAS PERSISTENCE: Found {len(_interrupt_file_cache)} files in interrupt cache")
                    store.update_files(_interrupt_file_cache)
                    clear_interrupt_cache()
                    print(f"🧹 ATLAS PERSISTENCE: Cache cleanup completed")
            except Exception as cache_e:
                print(f"🔍 ATLAS PERSISTENCE: Cache recovery failed: {cache_e}")

            # Re-raise the interrupt for frontend
            raise

    def enhanced_invoke(input_data, config=None):
        """Enhanced invoke with state_store integration."""
        # For sync version, use same logic but without await
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(enhanced_ainvoke(input_data, config))
        except RuntimeError:
            # If no loop, create one
            return asyncio.run(enhanced_ainvoke(input_data, config))

    def enhanced_stream(input_data, config=None):
        """Enhanced stream with state_store integration."""
        # PRE-LOAD: Enhance input with stored files
        enhanced_input = prepare_state_with_files(input_data)
        initial_file_count = len(enhanced_input.get('files', {}))
        print(f"🔄 ATLAS PERSISTENCE (stream): PRE-LOAD {initial_file_count} files from store")

        try:
            # Stream from original method
            for event in original_stream(enhanced_input, config):
                # Try to sync files from each event
                if isinstance(event, dict):
                    sync_files_from_result(event)
                yield event

            # POST-SYNC: Final sync after stream completes
            final_files = store.get_files()
            print(f"🔄 ATLAS PERSISTENCE (stream): POST-SYNC completed with {len(final_files)} files")

        except GraphInterrupt as e:
            print(f"🔄 ATLAS PERSISTENCE (stream): GraphInterrupt detected")

            # INTERRUPT RECOVERY: Get files from global cache
            try:
                import sys
                import os
                core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
                if core_path not in sys.path:
                    sys.path.insert(0, core_path)
                from deepagents.tools import _interrupt_file_cache
                from atlas_utils import clear_interrupt_cache
                if _interrupt_file_cache:
                    print(f"🔍 ATLAS PERSISTENCE: Found {len(_interrupt_file_cache)} files in interrupt cache")
                    store.update_files(_interrupt_file_cache)
                    clear_interrupt_cache()
                    print(f"🧹 ATLAS PERSISTENCE: Cache cleanup completed")
            except Exception as cache_e:
                print(f"🔍 ATLAS PERSISTENCE: Cache recovery failed: {cache_e}")

            # Re-raise the interrupt for frontend
            raise

    # Replace methods with enhanced versions
    base_agent.ainvoke = enhanced_ainvoke
    base_agent.invoke = enhanced_invoke
    base_agent.stream = enhanced_stream

    return base_agent

# Create the LangGraph-compatible agent - this is what langgraph.json expects to find
agent = create_langgraph_agent_with_persistence()

# For command-line testing
if __name__ == "__main__":
    def main():
        # Use the new interrupt-enabled agent
        test_agent = create_langgraph_agent()
        print("Atlas V1 Agent initialized successfully with enhanced human-in-the-loop support")
        print("Status: Agent initialized successfully")

        # Example usage with new interrupt handling
        result = handle_interrupts(
            test_agent,
            "Analyze user story US-123 and create implementation plan",
            "atlas-v1-session"  # Use consistent thread_id
        )
        print(f"Final result: {result}")

    main()