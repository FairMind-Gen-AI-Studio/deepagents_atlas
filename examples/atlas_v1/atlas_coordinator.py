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
from deepagents import SubAgent
from deepagents.state import DeepAgentState
from deepagents.tools import write_todos, write_file, read_file, ls, human_input
from deepagents.sub_agent import _create_task_tool
from langgraph.prebuilt import create_react_agent
from atlas_tools import read_phase_state, write_phase_state

# Import model configuration
from model_config import initialize_atlas_model, get_model_info

# Import our modular agents
from agents import (
    investigation_agent,
    discussion_agent,
    planning_agent,
    task_generation_agent,
    create_repository_analyzer
)

# We'll import validation function when needed to avoid circular imports

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
        
        # Initialize model with environment configuration
        self.model = initialize_atlas_model()
        model_info = get_model_info()
        logger.info(f"Initialized model: {model_info['provider']}/{model_info['model']}")
        
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
    
    def _create_custom_task_tool(self):
        """
        Create a custom task tool that has access to MCP tools for sub-agents.
        
        Returns:
            Task tool configured with all tools for sub-agent access
        """
        # Combine MCP tools and builtin tools for sub-agents
        all_tools_for_subagents = []
        
        # Add MCP tools if available
        if self.mcp_tools and isinstance(self.mcp_tools, dict):
            all_tools_for_subagents.extend(list(self.mcp_tools.values()))
        
        # Add essential builtin tools
        all_tools_for_subagents.extend([
            write_todos, write_file, read_file, ls, human_input,
            write_phase_state  # Allow sub-agents to update phase state
        ])
        
        # Create task tool with access to all tools for sub-agents
        task_tool = _create_task_tool(
            tools=all_tools_for_subagents,
            instructions="",  # Not used for sub-agents
            subagents=self.agents,
            model=self.model,
            state_schema=DeepAgentState
        )
        
        logger.info(f"Created task tool with {len(all_tools_for_subagents)} tools for sub-agent access")
        return task_tool
    
    def _create_main_agent(self):
        """
        Create the main orchestrator agent with ONLY coordination tools.
        This custom implementation bypasses create_deep_agent to achieve
        proper tool isolation.
        
        Returns:
            Configured orchestrator agent with limited tool access
        """
        # Main orchestrator instructions - enhanced with validation rules
        orchestrator_instructions = """You are the Atlas V1 Orchestrator coordinating a 4-phase methodology.

## Your Available Tools
You have access to ONLY these coordination tools:
- `task` - Deploy sub-agents for each phase
- `read_file` / `ls` - Check phase completion
- `write_todos` - Track phase progression
- NOTE: NO human_input - all user interaction must go through discussion agent

## `write_todos`

You have access to the `write_todos` tools to help you manage and plan tasks. Use these tools VERY frequently to ensure that you are tracking your tasks and giving the user visibility into your progress.
These tools are also EXTREMELY helpful for planning tasks, and for breaking down larger complex tasks into smaller steps. If you do not use this tool when planning, you may forget to do important tasks - and that is unacceptable.

It is critical that you mark todos as completed as soon as you are done with a task. Do not batch up multiple tasks before marking them as completed.

## The 4 Phases

1. **Investigation** (investigation-agent): Silent project exploration
2. **Discussion** (discussion-agent): Interactive requirements clarification  
3. **Planning** (planning-agent): Repository analysis and solution co-design
4. **Task Generation** (task-generation-agent): Create actionable tasks

## Phase Management via State

The phases MUST proceed in this order:
1. investigation → 2. discussion → 3. planning → 4. task_generation

### State-Based Phase Detection
The state tracks phase progress with these fields:
- `current_phase`: Which phase is currently active
- `completed_phases`: List of successfully completed phases
- `[phase]_complete`: Boolean flags for each phase completion

### Phase Management (Simple)

1. **Check State**: 
   Use `read_phase_state` to get current status. This returns:
   - completed_phases: List of completed phases
   - current_phase: The active phase
   - [phase]_complete: Boolean flags for each phase

2. **Decide Next Phase**: 
   Based on completed_phases from read_phase_state:
   - [] → Start investigation
   - ["investigation"] → Start discussion
   - ["investigation", "discussion"] → Start planning
   - ["investigation", "discussion", "planning"] → Start task_generation
   - All 4 phases → Complete!

3. **Deploy Agent**: 
   Use task(description="Execute [PHASE] phase", subagent_type="[phase]-agent")

4. **Validate Output Files**:
   After agent completes, verify expected files exist:
   - investigation → investigation_findings.md
   - discussion → requirements_clarified.md
   - planning → implementation_plan.md
   - task_generation → implementation_tasks.md

### Phase Transition Rules
- NEVER skip phases - all phases must execute in sequence
- Always check BOTH state flags AND file existence for validation
- Use `write_todos` to track retry attempts and phase progress
- The sub-agents will update state flags when they complete their work
- All user interaction happens through the discussion agent only

## Your Workflow

1. **Check Current State**:
   - Use `ls` to see what files exist
   - Determine which phase was last completed
   - Identify the next phase to execute

2. **Deploy Phase Agent**:
   ```
   task(
       description="Execute [PHASE] phase",
       subagent_type="[AGENT-NAME]"
   )
   ```

3. **Validate Completion**:
   - Check that expected output files were created
   - If files are missing, re-run the phase with additional guidance
   - Document any issues in todos

## Handling Phase Failures

If a phase agent fails or produces incomplete output:
1. Use `write_todos` to document what went wrong
2. Re-run the same phase with additional context/instructions
3. If it fails 3 times, proceed to discussion phase for user clarification
4. Remember: Only the discussion agent can interact with users

Example recovery:
- Investigation agent didn't create investigation_findings.md
- Action: Re-run with instruction "Ensure you save findings to investigation_findings.md"

## Important Rules

1. **Never skip phases** without explicit user permission
2. **Always validate files** exist AND have content before proceeding
3. **Let agents work** - don't micromanage their execution
4. **Respect phase outputs** - each phase builds on the previous
5. **ALWAYS delegate to sub-agents** - you are a coordinator, not an executor
6. **Track progress** - Use write_todos to maintain phase status

## Repository Analyzers

During the Planning phase, the planning-agent may create repository-specific
sub-agents. These are dynamically created and managed by the planning-agent itself.

Your job is simple: coordinate the phases, ensure proper sequencing, validate outputs,
and let the specialized agents do their work."""

        # Create custom task tool with MCP access for sub-agents
        task_tool = self._create_custom_task_tool()
        
        # Define ONLY coordination tools for the orchestrator
        orchestrator_tools = [
            write_todos,
            read_file,
            ls,
            # human_input removed - orchestrator should delegate all user interaction to discussion agent
            task_tool,  # Custom task tool with MCP access for sub-agents
            read_phase_state  # Allow orchestrator to read phase state
        ]
        
        logger.info(f"Creating orchestrator with {len(orchestrator_tools)} coordination tools (NO direct MCP access)")

        # Create the orchestrator with LIMITED tools
        # This bypasses create_deep_agent to achieve proper tool isolation
        # Note: LangGraph API handles persistence automatically - no custom checkpointer needed
        return create_react_agent(
            model=self.model,
            prompt=orchestrator_instructions,
            tools=orchestrator_tools,  # ONLY coordination tools, NO MCP tools!
            state_schema=DeepAgentState
            # Note: checkpointer parameter removed - LangGraph API handles persistence automatically
        ).with_config({"recursion_limit": 1000})
    
    async def run(self, user_request: str, project_id: Optional[str] = None, thread_id: str = "atlas-v1-session") -> Dict[str, Any]:
        """
        Run the Atlas methodology for a user request.

        Args:
            user_request: The user's request or user story reference
            project_id: Optional project ID for context
            thread_id: Thread identifier for state persistence (MUST be consistent across all phases)

        Returns:
            Dict with final response and generated artifacts
        """
        # Prepare the initial message
        initial_message = f"User Request: {user_request}"
        if project_id:
            initial_message += f"\nProject ID: {project_id}"
        
        # Execute the agent with thread_id for state persistence (handled automatically by LangGraph API)
        config = {"configurable": {"thread_id": thread_id}}
        result = await self.main_agent.ainvoke({
            "messages": [{"role": "user", "content": initial_message}]
        }, config=config)
        
        return {
            "final_response": result.get("messages", [])[-1].content if result.get("messages") else "No response",
            "files": result.get("files", {}),
            "todos": result.get("todos", [])
        }
    
    def get_current_phase_from_state(self, state: Dict[str, Any]) -> str:
        """
        Determine current phase from state, with file validation as backup.
        
        Primary source: state["completed_phases"]
        Fallback: file detection
        
        Args:
            state: Full agent state including completed_phases and files
            
        Returns:
            Current phase name or "completed" if all phases are done
        """
        completed = state.get("completed_phases", [])
        
        # Use state as primary source
        if "task_generation" in completed:
            return "completed"
        elif "planning" in completed:
            return "task_generation"
        elif "discussion" in completed:
            return "planning"
        elif "investigation" in completed:
            return "discussion"
        else:
            # Fallback to file detection if state is empty
            files = state.get("files", {})
            return self.get_current_phase_from_files(files)
    
    def get_current_phase_from_files(self, files: Dict[str, str]) -> str:
        """
        Determine current phase from file presence.
        
        This helper method analyzes the virtual filesystem to determine
        which phase the Atlas methodology is currently in.
        
        Args:
            files: Virtual filesystem dictionary from state
            
        Returns:
            Current phase name or "completed" if all phases are done
        """
        # Check phases in reverse order to find the most advanced phase
        if "implementation_tasks.md" in files:
            return "completed"
        elif "implementation_plan.md" in files:
            # Planning complete, ready for task generation
            return "task_generation"
        elif all(f in files for f in ["clarification_questions.md", "user_responses.md", "requirements_clarified.md"]):
            # Discussion complete, ready for planning
            return "planning"
        elif "requirements_clarified.md" in files:
            # Partial discussion, still in discussion phase
            return "discussion"
        elif "investigation_findings.md" in files:
            # Investigation complete, ready for discussion
            return "discussion"
        else:
            # No phases complete, start with investigation
            return "investigation"
    
    def validate_phase_outputs(self, phase: str, files: Dict[str, str]) -> Dict[str, Any]:
        """
        Validate that a phase has produced its expected outputs.
        
        Args:
            phase: Name of the phase to validate
            files: Virtual filesystem dictionary
            
        Returns:
            Validation result with status and any missing outputs
        """
        # Simple inline validation to avoid import issues
        phase_outputs = {
            "investigation": ["investigation_findings.md"],
            "discussion": ["clarification_questions.md", "user_responses.md", "requirements_clarified.md"],
            "planning": ["implementation_plan.md"],
            "task_generation": ["implementation_tasks.md"]
        }
        
        required_outputs = phase_outputs.get(phase, [])
        missing_outputs = [f for f in required_outputs if f not in files]
        
        return {
            "phase": phase,
            "completed": len(missing_outputs) == 0,
            "missing_outputs": missing_outputs,
            "missing_criteria": [],  # Simplified for now
            "errors": []
        }
    
    def get_phase_sequence(self) -> List[str]:
        """Get the ordered list of phases in the Atlas methodology."""
        return ["investigation", "discussion", "planning", "task_generation"]
    
    def get_next_phase(self, current_phase: str) -> Optional[str]:
        """
        Get the next phase in the sequence.
        
        Args:
            current_phase: The current phase name
            
        Returns:
            Next phase name or None if completed
        """
        sequence = self.get_phase_sequence()
        
        if current_phase == "completed":
            return None
        elif current_phase in sequence:
            current_index = sequence.index(current_phase)
            if current_index < len(sequence) - 1:
                return sequence[current_index + 1]
        elif current_phase not in sequence:
            # If phase is unknown, start from beginning
            return sequence[0]
        
        return None
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current execution status with enhanced phase information.
        
        Returns:
            Dictionary with coordinator status and phase tracking
        """
        return {
            "coordinator": "active",
            "agents_available": len(self.agents),
            "mcp_tools": len(self.mcp_tools) if self.mcp_tools else 0,
            "phase_sequence": self.get_phase_sequence(),
            "tool_isolation": "enabled"  # Highlight our architecture choice
        }