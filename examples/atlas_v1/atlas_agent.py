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
        
        # Delegate to coordinator
        return await self.coordinator.run(user_request, project_id)
    
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
from deepagents import create_deep_agent
from agents import (
    investigation_agent,
    discussion_agent,
    planning_agent,
    task_generation_agent
)

def create_langgraph_agent():
    """Create the LangGraph-compatible agent (compiled graph)."""
    # Initialize MCP tools if available
    mcp_tools = _initialize_mcp_tools_sync()
    mcp_tool_objects = []
    if mcp_tools and isinstance(mcp_tools, dict):
        mcp_tool_objects = list(mcp_tools.values())
    
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
    
    # Create the graph directly
    return create_deep_agent(
        tools=mcp_tool_objects,
        instructions=orchestrator_instructions,
        subagents=[
            investigation_agent,
            discussion_agent,
            planning_agent,
            task_generation_agent
        ]
    ).with_config({"recursion_limit": 1000})

# Create the LangGraph-compatible agent
# This is what langgraph.json expects to find
agent = create_langgraph_agent()

# For command-line testing
if __name__ == "__main__":
    async def main():
        test_agent = create_atlas_agent()
        print("Atlas V1 Agent initialized successfully")
        print(f"Status: {test_agent.get_status()}")
        
        # Example usage
        result = await test_agent.run(
            "Analyze user story US-123",
            project_id="test-project"
        )
        print(f"Result: {result.get('final_response', 'No response')}")
    
    asyncio.run(main())