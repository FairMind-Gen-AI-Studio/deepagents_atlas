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
from deepagents.tools import write_todos, write_file, read_file, ls
from atlas_tools import human_input
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

    def _create_custom_task_tool(self):
        """
        Create a custom task tool that has access to MCP tools for sub-agents
        and integrates with the external state store for persistence.

        Returns:
            Task tool configured with all tools for sub-agent access
        """
        # Import here to avoid circular imports
        from langchain_core.tools import tool as create_tool, InjectedToolCallId
        from langgraph.types import Command
        from langchain_core.messages import ToolMessage
        from typing import Annotated
        from langgraph.prebuilt import InjectedState
        from deepagents.state import DeepAgentState

        # Combine MCP tools and builtin tools for sub-agents
        all_tools_for_subagents = []

        # Add MCP tools if available
        if self.mcp_tools and isinstance(self.mcp_tools, dict):
            all_tools_for_subagents.extend(list(self.mcp_tools.values()))

        # Add essential builtin tools - ensure they're proper tool objects
        from langchain_core.tools import BaseTool
        builtin_tools = [write_todos, write_file, read_file, ls, human_input, write_phase_state]
        for tool_obj in builtin_tools:
            if isinstance(tool_obj, BaseTool):
                all_tools_for_subagents.append(tool_obj)
            elif callable(tool_obj):
                # Convert function to tool if needed
                all_tools_for_subagents.append(create_tool(tool_obj) if not hasattr(tool_obj, 'name') else tool_obj)

        # Create agents mapping for task resolution
        agents = {}
        # Create general-purpose agent
        from langgraph.prebuilt import create_react_agent
        agents["general-purpose"] = create_react_agent(
            self.model,
            prompt="",  # Instructions come from task call
            tools=all_tools_for_subagents,
            checkpointer=False,
            state_schema=DeepAgentState,
        )

        # Add our specialized agents
        for agent_config in self.agents:
            # Get specified tools for this agent
            if "tools" in agent_config:
                agent_tools = []
                tools_by_name = {}
                # Build tools mapping, handling both BaseTool objects and function tools
                for tool in all_tools_for_subagents:
                    if hasattr(tool, 'name'):
                        tools_by_name[tool.name] = tool
                    elif callable(tool) and hasattr(tool, '__name__'):
                        tools_by_name[tool.__name__] = tool

                for tool_name in agent_config["tools"]:
                    if tool_name in tools_by_name:
                        agent_tools.append(tools_by_name[tool_name])

                # Add essential builtin tools that aren't already specified
                essential_builtins = {'write_file', 'read_file', 'ls', 'write_todos'}
                for tool in all_tools_for_subagents:
                    tool_name = getattr(tool, 'name', getattr(tool, '__name__', None))
                    if tool_name and tool_name in essential_builtins:
                        if tool_name not in agent_config["tools"]:
                            agent_tools.append(tool)
            else:
                # No specific tools = inherit all tools
                agent_tools = all_tools_for_subagents

            # Create the agent
            agents[agent_config["name"]] = create_react_agent(
                self.model,
                prompt=agent_config["prompt"],
                tools=agent_tools,
                state_schema=DeepAgentState,
                checkpointer=False,
            )

        # Create description for available sub-agents
        other_agents_string = [f"- {agent['name']}: {agent['description']}" for agent in self.agents]

        @create_tool(description=f"Launch a specialized agent to handle complex tasks. Available agents:\n" + "\n".join(other_agents_string))
        async def task(
            description: str,
            subagent_type: str,
            state: Annotated[DeepAgentState, InjectedState],
            tool_call_id: Annotated[str, InjectedToolCallId],
        ):
            """Task tool with external state store integration and safety controls."""
            if subagent_type not in agents:
                return f"Error: invoked agent of type {subagent_type}, the only allowed types are {[f'`{k}`' for k in agents]}"

            # Safety check: Circuit breaker
            if self.error_count >= self.safety_config.get("circuit_breaker_errors", 5):
                logger.error(f"Circuit breaker activated: {self.error_count} consecutive errors")
                return f"Safety circuit breaker activated after {self.error_count} errors. Execution halted."

            # Get the external state store
            store = get_atlas_store()

            # Prepare state with persistent files for the sub-agent
            sub_agent_state = prepare_state_with_files({
                **state,
                "messages": [{"role": "user", "content": description}]
            })

            initial_files = list(sub_agent_state.get('files', {}).keys())
            print(f"🚀 Task tool: Starting {subagent_type} with {len(initial_files)} files from store: {initial_files}")

            # Safety monitoring
            import time
            start_time = time.time()
            timeout_seconds = self.safety_config.get("timeout_minutes_per_phase", 10) * 60

            sub_agent = agents[subagent_type]

            try:
                result = await sub_agent.ainvoke(sub_agent_state)
                # Reset error count on success
                self.error_count = 0
            except Exception as e:
                from langgraph.errors import GraphInterrupt
                error_str = str(e).lower()

                # Handle GraphInterrupt specially - this is expected for human_input calls
                if isinstance(e, GraphInterrupt):
                    print(f"🔄 ATLAS COORDINATOR: {subagent_type} was interrupted for user input")
                    print(f"🔄 Current state files before interrupt: {list(sub_agent_state.get('files', {}).keys())}")

                    # SOLUTION: Recover files from the global interrupt cache
                    # write_file stores files in _interrupt_file_cache even if Command updates are lost
                    recovered_files = {}
                    try:
                        # Import the global cache from tools module
                        import sys
                        import os
                        core_path = os.path.join(os.path.dirname(__file__), '..', '..', 'src')
                        if core_path not in sys.path:
                            sys.path.insert(0, core_path)
                        from deepagents.tools import _interrupt_file_cache
                        if _interrupt_file_cache:
                            recovered_files = _interrupt_file_cache.copy()
                            print(f"🔍 ATLAS CACHE RECOVERY: Found {len(recovered_files)} files in interrupt cache")
                            print(f"🔍 CACHED FILES: {list(recovered_files.keys())}")
                        else:
                            print(f"🔍 ATLAS CACHE RECOVERY: Interrupt cache is empty")
                    except (ImportError, NameError) as cache_e:
                        print(f"🔍 ATLAS CACHE RECOVERY FAILED: {cache_e}")

                    # Store the recovered files in our Atlas state store for persistence
                    if recovered_files:
                        store.update_files(recovered_files)
                        print(f"🔄 ATLAS STORE: Saved {len(recovered_files)} recovered files to persistent store")

                    # Re-raise the original exception so frontend receives the interrupt
                    print(f"✅ ATLAS FRONTEND: Re-raising GraphInterrupt for modal display")
                    raise
                elif "validation error" in error_str or "tool_call_id" in error_str:
                    # Increment error count for validation errors
                    self.error_count += 1
                    logger.error(f"Validation error #{self.error_count}: {e}")
                    return f"Error: Sub-agent {subagent_type} failed with validation error #{self.error_count}. Tool call format invalid. Please check prompts and retry."
                elif "timeout" in error_str:
                    self.error_count += 1
                    logger.error(f"Timeout error #{self.error_count}: {e}")
                    return f"Error: Sub-agent {subagent_type} timed out after {timeout_seconds}s. Execution halted."
                # Re-raise other errors
                raise

            # DEBUG: Log the complete structure of what the sub-agent returned
            import json

            print(f"🔍🔍🔍 TASK TOOL - Sub-agent {subagent_type} returned result!")
            print(f"🔍 Sub-agent {subagent_type} returned result type: {type(result)}")
            if isinstance(result, dict):
                print(f"🔍 Result keys: {list(result.keys())}")

                # Check for files at top level
                if "files" in result:
                    files_list = list(result['files'].keys()) if result['files'] else []
                    print(f"🔍 Found files at result['files']: {files_list}")
                    if result['files']:
                        for fname, content in result['files'].items():
                            print(f"🔍   {fname}: {len(content)} characters")
                else:
                    print("🔍 No files found at result['files']")

                # Check for files in update
                if "update" in result:
                    print(f"🔍 Found 'update' key, type: {type(result['update'])}")
                    if isinstance(result['update'], dict):
                        print(f"🔍 Update keys: {list(result['update'].keys())}")
                        if "files" in result['update']:
                            files_list = list(result['update']['files'].keys()) if result['update']['files'] else []
                            print(f"🔍 Found files at result['update']['files']: {files_list}")
                            if result['update']['files']:
                                for fname, content in result['update']['files'].items():
                                    print(f"🔍   {fname}: {len(content)} characters")
                        else:
                            print("🔍 No 'files' key in result['update']")
                    else:
                        print(f"🔍 result['update'] is not a dict, it's: {type(result['update'])}")
                else:
                    print("🔍 No 'update' key in result")

                # Dump structure preview for inspection
                try:
                    # Create a safe preview without file contents
                    safe_result = {}
                    for key, value in result.items():
                        if key == "files" and isinstance(value, dict):
                            safe_result[key] = {fname: f"<content-{len(content)}-chars>" for fname, content in value.items()}
                        elif key == "update" and isinstance(value, dict):
                            safe_update = {}
                            for ukey, uvalue in value.items():
                                if ukey == "files" and isinstance(uvalue, dict):
                                    safe_update[ukey] = {fname: f"<content-{len(content)}-chars>" for fname, content in uvalue.items()}
                                else:
                                    safe_update[ukey] = f"<{type(uvalue).__name__}>"
                            safe_result[key] = safe_update
                        else:
                            safe_result[key] = f"<{type(value).__name__}>"

                    result_preview = json.dumps(safe_result, indent=2)
                    print(f"🔍 Result structure preview:\n{result_preview}")
                except Exception as preview_error:
                    print(f"🔍 Could not create result preview: {preview_error}")
            else:
                print(f"🔍 Result is not a dict: {result}")

            # Sync new files from sub-agent result to the persistent store
            sync_files_from_result(result)

            # Get updated files from the store (authoritative source)
            final_files = store.get_files()

            print(f"✅ Task tool: {subagent_type} completed, store now has {len(final_files)} files: {list(final_files.keys())}")

            # Check if the last message contains a user question that needs to be surfaced
            last_message = result["messages"][-1].content
            if "USER_QUESTION:" in last_message:
                question = last_message.replace("USER_QUESTION:", "").strip()
                return Command(
                    update={
                        "files": final_files,  # Use files from persistent store
                        "messages": [
                            ToolMessage(question, tool_call_id=tool_call_id)
                        ],
                    }
                )
            else:
                return Command(
                    update={
                        "files": final_files,  # Use files from persistent store
                        "messages": [
                            ToolMessage(
                                result["messages"][-1].content, tool_call_id=tool_call_id
                            )
                        ],
                    }
                )

        logger.info(f"Created enhanced task tool with {len(all_tools_for_subagents)} tools and state store integration")
        return task
    
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

        # Execute the agent with thread_id for state persistence (handled automatically by LangGraph API)
        config = {"configurable": {"thread_id": thread_id}}
        result = await self.main_agent.ainvoke(enhanced_state, config=config)

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