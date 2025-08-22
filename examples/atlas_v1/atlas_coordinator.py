# Atlas V1 Coordinator - Lightweight orchestration following DeepAgents patterns
# Replaces the 906-line God class with ~150 lines of clean coordination

"""
Atlas Coordinator - Clean orchestration for 4-phase methodology

This lightweight coordinator replaces the monolithic AtlasAgentV1 class,
using the DeepAgents framework directly with modular agents.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from deepagents import create_deep_agent, SubAgent

# Import our modular agents
from agents import (
    investigation_agent,
    discussion_agent,
    planning_agent,
    task_generation_agent,
    create_repository_analyzer
)

logger = logging.getLogger(__name__)

class AtlasCoordinator:
    """
    Lightweight coordinator for Atlas V1 agents.
    
    This class only handles:
    - Agent initialization
    - Phase orchestration via create_deep_agent
    - Simple run interface
    
    All complex logic is delegated to specialized agents.
    """
    
    def __init__(self, mcp_tools: Optional[Dict[str, Any]] = None):
        """
        Initialize the Atlas coordinator.
        
        Args:
            mcp_tools: Optional MCP tools dictionary for agent use
        """
        self.mcp_tools = mcp_tools or {}
        self.agents = self._prepare_agents()
        self.main_agent = self._create_main_agent()
        
    def _prepare_agents(self) -> List[SubAgent]:
        """
        Prepare the 4 phase agents for the Atlas methodology.
        
        Returns:
            List of SubAgent configurations
        """
        # Start with our core 4 agents
        agents = [
            investigation_agent,
            discussion_agent,
            planning_agent,
            task_generation_agent
        ]
        
        # Add MCP tool names to agents if available
        if self.mcp_tools:
            # Agents already have their tool lists defined
            # The framework will handle tool resolution
            logger.info(f"MCP tools available: {len(self.mcp_tools)} tools")
        
        return agents
    
    def _create_main_agent(self):
        """
        Create the main orchestrator agent using create_deep_agent.
        
        Returns:
            Configured deep agent ready for execution
        """
        # Main orchestrator instructions - concise and focused
        orchestrator_instructions = """You are the Atlas V1 Orchestrator coordinating a 4-phase methodology.

## The 4 Phases

1. **Investigation** (investigation-agent): Silent project exploration
2. **Discussion** (discussion-agent): Interactive requirements clarification  
3. **Planning** (planning-agent): Repository analysis and solution design
4. **Task Generation** (task-generation-agent): Create actionable tasks

## Your Role

You coordinate these phases in sequence:
1. Check what phase we're in by looking for output files
2. Deploy the appropriate agent for the current phase
3. Monitor phase completion via expected output files
4. Transition to the next phase when ready

## Phase Detection via Files

- No files → Start with Investigation
- investigation_findings.md exists → Move to Discussion
- requirements_clarified.md exists → Move to Planning  
- implementation_plan.md exists → Move to Task Generation
- implementation_tasks.md exists → All phases complete

## Phase Deployment

Use the 'task' tool to deploy phase agents:
```
task(
    description="Execute Investigation phase",
    subagent_type="investigation-agent"
)
```

## Important Rules

1. **Never skip phases** without explicit user permission
2. **Always check files** before deploying agents
3. **Let agents work** - don't micromanage their execution
4. **Respect phase outputs** - each phase builds on the previous

## Repository Analyzers

During the Planning phase, the planning-agent may create repository-specific
sub-agents. These are dynamically created and managed by the planning-agent itself.

Your job is simple: coordinate the phases, ensure proper sequencing, and let
the specialized agents do their work."""

        # Create the main agent with sub-agents
        # Pass MCP tools as actual objects if available
        mcp_tool_objects = []
        if self.mcp_tools and isinstance(self.mcp_tools, dict):
            # Convert MCP tools dict to list of tool objects
            mcp_tool_objects = list(self.mcp_tools.values())
        
        return create_deep_agent(
            tools=mcp_tool_objects,  # MCP tools as objects, built-in tools auto-included
            instructions=orchestrator_instructions,
            subagents=self.agents
        ).with_config({"recursion_limit": 1000})
    
    async def run(self, user_request: str, project_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the Atlas methodology for a user request.
        
        Args:
            user_request: The user's request or user story reference
            project_id: Optional project ID for context
            
        Returns:
            Dict with final response and generated artifacts
        """
        # Prepare the initial message
        initial_message = f"User Request: {user_request}"
        if project_id:
            initial_message += f"\nProject ID: {project_id}"
        
        # Execute the agent
        result = await self.main_agent.ainvoke({
            "messages": [{"role": "user", "content": initial_message}]
        })
        
        return {
            "final_response": result.get("messages", [])[-1].content if result.get("messages") else "No response",
            "files": result.get("files", {}),
            "todos": result.get("todos", [])
        }
    
    def get_status(self) -> Dict[str, str]:
        """Get current execution status."""
        return {
            "coordinator": "active",
            "agents_available": len(self.agents),
            "mcp_tools": len(self.mcp_tools) if self.mcp_tools else 0
        }