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
from deepagents.types import SubAgent
from deepagents.state import DeepAgentState
from deepagents.tools import write_todos, write_file, read_file, ls
from atlas_tools import human_input
from deepagents import create_deep_agent, async_create_deep_agent

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

# Import the external state store for file persistence
from state_store import get_atlas_store, sync_files_from_result, prepare_state_with_files

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

        # Initialize safety controls
        self.safety_config = self._load_safety_config()
        self.error_count = 0
        self.token_usage = {"investigation": 0, "discussion": 0, "planning": 0, "task_generation": 0}

        # Prepare sub-agents for deepagents framework
        self.agents = self._prepare_agents()

        # Prepare tools for the orchestrator
        self.orchestrator_tools = self._prepare_tools_for_orchestrator()
        
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

    def _load_safety_config(self) -> Dict[str, Any]:
        """Load safety configuration from config.yaml"""
        try:
            import yaml
            with open("config.yaml", "r") as f:
                config = yaml.safe_load(f)
                return config.get("safety", {
                    "max_retries": 3,
                    "max_tokens_per_phase": 50000,
                    "timeout_minutes_per_phase": 10,
                    "enable_cost_monitoring": True,
                    "circuit_breaker_errors": 5
                })
        except Exception as e:
            logger.warning(f"Could not load safety config: {e}, using defaults")
            return {
                "max_retries": 3,
                "max_tokens_per_phase": 50000,
                "timeout_minutes_per_phase": 10,
                "enable_cost_monitoring": True,
                "circuit_breaker_errors": 5
            }

    
    def _prepare_tools_for_orchestrator(self):
        """
        Prepare tools for the main orchestrator.
        Minimal tools to prevent circular references.

        Returns:
            List of tools for the orchestrator
        """
        # Only coordination tools for orchestrator
        orchestrator_tools = []

        logger.info(f"Prepared {len(orchestrator_tools)} coordination tools for orchestrator")
        return orchestrator_tools

    
    async def run(self, user_request: str, project_id: Optional[str] = None, thread_id: str = "atlas-v1-session") -> Dict[str, Any]:
        """
        Run the Atlas methodology for a user request with external state persistence.

        This method integrates with the AtlasStateStore to maintain file persistence
        across agent phases, working around the core deepagents state mutation issue.

        Args:
            user_request: The user's request or user story reference
            project_id: Optional project ID for context
            thread_id: Thread identifier for state persistence (MUST be consistent across all phases)

        Returns:
            Dict with final response and generated artifacts
        """
        # Initialize the external state store for this session
        store = get_atlas_store()
        store.set_thread_id(thread_id)

        # Prepare the initial message
        initial_message = f"User Request: {user_request}"
        if project_id:
            initial_message += f"\nProject ID: {project_id}"

        # Prepare initial state with persistent files from store
        initial_state = {"messages": [{"role": "user", "content": initial_message}]}
        enhanced_state = prepare_state_with_files(initial_state)

        logger.info(f"AtlasCoordinator: Starting with {len(enhanced_state.get('files', {}))} persistent files")

        # Create orchestrator instructions
        orchestrator_instructions = """You are the Atlas V1 Orchestrator coordinating a 4-phase methodology.

## Your Mission
Coordinate the 4-phase Atlas methodology by delegating work to specialized agents.
Use the `task` tool to deploy agents for each phase in sequence.

## The 4 Phases
1. **Investigation** (investigation-agent): Silent project exploration
2. **Discussion** (discussion-agent): Interactive requirements clarification
3. **Planning** (planning-agent): Repository analysis and solution design
4. **Task Generation** (task-generation-agent): Create actionable tasks

## Your Workflow
1. **Check Current State**: Use `ls` to see what files exist
2. **Deploy Phase Agent**: Use `task(description="Execute [PHASE] phase", subagent_type="[phase]-agent")`
3. **Validate Completion**: Check that expected output files were created
4. **Continue to Next Phase**: Repeat until all phases complete

## Phase Detection by Files
- No files → Start investigation
- investigation_findings.md exists → Start discussion
- requirements_clarified.md exists → Start planning
- implementation_plan.md exists → Start task_generation
- implementation_tasks.md exists → Complete!

## Important Rules
- NEVER skip phases - all phases must execute in sequence
- ALWAYS delegate to sub-agents - you are a coordinator, not an executor
- Use `write_todos` to track progress
- Let specialized agents handle all actual work"""

        # Pass agents directly to framework - let deepagents handle tool resolution internally
        # This prevents circular references that break LangSmith serialization
        main_agent = async_create_deep_agent(
            tools=self.orchestrator_tools,
            instructions=orchestrator_instructions,
            subagents=self.agents,  # Pass agents directly without pre-resolution
            model=self.model
        ).with_config({"recursion_limit": 1000})

        # Execute the agent with thread_id for state persistence (handled automatically by LangGraph API)
        config = {"configurable": {"thread_id": thread_id}}
        result = await main_agent.ainvoke(enhanced_state, config=config)

        # Sync any new files back to the persistent store
        sync_files_from_result(result)

        # Get final files from the store (authoritative source)
        final_files = store.get_files()

        logger.info(f"AtlasCoordinator: Completed with {len(final_files)} files in persistent store")

        return {
            "final_response": result.get("messages", [])[-1].content if result.get("messages") else "No response",
            "files": final_files,  # Return files from persistent store
            "todos": result.get("todos", []),
            "store_status": store.get_status()  # Include store status for debugging
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