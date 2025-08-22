# Atlas V1 StateGraph Implementation
# Intelligent decision graph for 4-phase methodology with conditional routing

import logging
from typing import Dict, Any, Literal, Optional, List
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

# Import our state schema
from atlas_state import AtlasState

# Import subagent configurations
from subagents import (
    get_agent_config,
    validate_phase_completion,
    get_phase_definition,
    PHASE_DEFINITIONS
)

logger = logging.getLogger(__name__)

class AtlasGraphBuilder:
    """
    Builder for Atlas V1 StateGraph with intelligent routing.
    
    This replaces the linear phase progression with a dynamic decision graph
    that supports:
    - Conditional routing based on validation
    - Quality cycles for phase repetition
    - Parallel repository analysis
    - User-controlled phase transitions
    """
    
    def __init__(self, agent_executor, mcp_tools=None):
        """
        Initialize the graph builder.
        
        Args:
            agent_executor: The main agent executor (from create_deep_agent)
            mcp_tools: Optional MCP tools wrapper for phase agents
        """
        self.agent_executor = agent_executor
        self.mcp_tools = mcp_tools
        self.graph = StateGraph(AtlasState)
        
    def build(self):
        """
        Build the complete Atlas StateGraph with all phases and routing.
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Add phase nodes
        self._add_phase_nodes()
        
        # Add validation nodes
        self._add_validation_nodes()
        
        # Add routing logic
        self._add_routing_edges()
        
        # Compile and return
        return self.graph.compile()
    
    def _add_phase_nodes(self):
        """Add nodes for each phase of the Atlas methodology"""
        
        # Investigation Phase Node
        self.graph.add_node(
            "investigation",
            self._create_investigation_node()
        )
        
        # Discussion Phase Node
        self.graph.add_node(
            "discussion", 
            self._create_discussion_node()
        )
        
        # Planning Phase Node (with parallel sub-graph capability)
        self.graph.add_node(
            "planning",
            self._create_planning_node()
        )
        
        # Task Generation Phase Node
        self.graph.add_node(
            "task_generation",
            self._create_task_generation_node()
        )
        
        logger.info("Added all phase nodes to StateGraph")
    
    def _add_validation_nodes(self):
        """Add validation nodes that check phase completion"""
        
        # Validation after investigation
        self.graph.add_node(
            "validate_investigation",
            self._create_validation_node("investigation")
        )
        
        # Validation after discussion
        self.graph.add_node(
            "validate_discussion",
            self._create_validation_node("discussion")
        )
        
        # Validation after planning
        self.graph.add_node(
            "validate_planning",
            self._create_validation_node("planning")
        )
        
        # Final validation
        self.graph.add_node(
            "validate_final",
            self._create_validation_node("task_generation")
        )
        
        logger.info("Added validation nodes to StateGraph")
    
    def _add_routing_edges(self):
        """Add edges with conditional routing logic"""
        
        # Entry point
        self.graph.add_edge(START, "investigation")
        
        # Investigation → Validation → Discussion or Retry
        self.graph.add_edge("investigation", "validate_investigation")
        self.graph.add_conditional_edges(
            "validate_investigation",
            self._route_after_investigation_validation,
            {
                "discussion": "discussion",
                "retry": "investigation",
                "skip": "planning"  # With user permission only
            }
        )
        
        # Discussion → Validation → Planning or Retry
        self.graph.add_edge("discussion", "validate_discussion")
        self.graph.add_conditional_edges(
            "validate_discussion",
            self._route_after_discussion_validation,
            {
                "planning": "planning",
                "retry": "discussion",
                "back": "investigation"  # Quality cycle
            }
        )
        
        # Planning → Validation → Task Generation or Retry
        self.graph.add_edge("planning", "validate_planning")
        self.graph.add_conditional_edges(
            "validate_planning",
            self._route_after_planning_validation,
            {
                "task_generation": "task_generation",
                "retry": "planning",
                "discussion": "discussion"  # Back for clarification
            }
        )
        
        # Task Generation → Final Validation → End
        self.graph.add_edge("task_generation", "validate_final")
        self.graph.add_conditional_edges(
            "validate_final",
            self._route_after_final_validation,
            {
                "end": END,
                "retry": "task_generation",
                "planning": "planning"  # Back to refine plan
            }
        )
        
        logger.info("Added routing edges with conditional logic")
    
    # Phase Node Implementations
    
    def _create_investigation_node(self):
        """Create investigation phase node"""
        def investigation_node(state: AtlasState) -> AtlasState:
            logger.info("Executing Investigation Phase")
            
            # Check if already completed
            if state.get("investigation_complete", False):
                logger.info("Investigation already complete, skipping")
                return state
            
            # Execute investigation agent via the main executor
            # This maintains the sub-agent pattern from DeepAgents
            messages = state.get("messages", [])
            messages.append(HumanMessage(
                content="Execute investigation phase: Analyze project and user story silently"
            ))
            
            # The agent executor will handle the actual investigation
            result = self.agent_executor.invoke({"messages": messages, "files": state.get("files", {})})
            
            # Update state with results
            state["messages"] = result.get("messages", messages)
            state["files"] = result.get("files", state.get("files", {}))
            state["current_phase"] = "investigation"
            state["investigation_complete"] = "investigation_findings.md" in state.get("files", {})
            
            # Update completion percentage
            if state["investigation_complete"]:
                state["completion_percentage"] = 25
                completed = state.get("completed_phases", [])
                if "investigation" not in completed:
                    completed.append("investigation")
                state["completed_phases"] = completed
            
            return state
        
        return investigation_node
    
    def _create_discussion_node(self):
        """Create discussion phase node"""
        def discussion_node(state: AtlasState) -> AtlasState:
            logger.info("Executing Discussion Phase")
            
            # Check if already completed
            if state.get("discussion_complete", False):
                logger.info("Discussion already complete, skipping")
                return state
            
            # Execute discussion agent
            messages = state.get("messages", [])
            messages.append(HumanMessage(
                content="Execute discussion phase: Generate clarification questions and collect user responses"
            ))
            
            result = self.agent_executor.invoke({"messages": messages, "files": state.get("files", {})})
            
            # Update state
            state["messages"] = result.get("messages", messages)
            state["files"] = result.get("files", state.get("files", {}))
            state["current_phase"] = "discussion"
            state["discussion_complete"] = "requirements_clarified.md" in state.get("files", {})
            
            # Update completion
            if state["discussion_complete"]:
                state["completion_percentage"] = 50
                completed = state.get("completed_phases", [])
                if "discussion" not in completed:
                    completed.append("discussion")
                state["completed_phases"] = completed
            
            return state
        
        return discussion_node
    
    def _create_planning_node(self):
        """Create planning phase node with parallel repository analysis capability"""
        def planning_node(state: AtlasState) -> AtlasState:
            logger.info("Executing Planning Phase")
            
            # Check if already completed
            if state.get("planning_complete", False):
                logger.info("Planning already complete, skipping")
                return state
            
            # Check if we have repositories to analyze in parallel
            files = state.get("files", {})
            if "investigation_findings.md" in files:
                # Extract repository list from investigation findings
                repositories = self._extract_repositories_from_findings(files["investigation_findings.md"])
                
                if len(repositories) > 1:
                    logger.info(f"Found {len(repositories)} repositories for parallel analysis")
                    # Create parallel analysis sub-graph
                    parallel_results = self._run_parallel_repository_analysis(state, repositories)
                    
                    # Merge parallel results into state
                    for repo_name, repo_analysis in parallel_results.items():
                        files[f"repo_analysis_{repo_name}.md"] = repo_analysis
                    state["files"] = files
            
            # Execute main planning agent to synthesize results
            messages = state.get("messages", [])
            messages.append(HumanMessage(
                content="Execute planning phase: Synthesize repository analyses and create implementation plan"
            ))
            
            result = self.agent_executor.invoke({"messages": messages, "files": state.get("files", {})})
            
            # Update state
            state["messages"] = result.get("messages", messages)
            state["files"] = result.get("files", state.get("files", {}))
            state["current_phase"] = "planning"
            state["planning_complete"] = "implementation_plan.md" in state.get("files", {})
            
            # Update completion
            if state["planning_complete"]:
                state["completion_percentage"] = 75
                completed = state.get("completed_phases", [])
                if "planning" not in completed:
                    completed.append("planning")
                state["completed_phases"] = completed
            
            return state
        
        return planning_node
    
    def _create_task_generation_node(self):
        """Create task generation phase node"""
        def task_generation_node(state: AtlasState) -> AtlasState:
            logger.info("Executing Task Generation Phase")
            
            # Check if already completed
            if state.get("task_generation_complete", False):
                logger.info("Task generation already complete, skipping")
                return state
            
            # Execute task generation agent
            messages = state.get("messages", [])
            messages.append(HumanMessage(
                content="Execute task generation phase: Convert plan to actionable tasks with 1:1 repository mapping"
            ))
            
            result = self.agent_executor.invoke({"messages": messages, "files": state.get("files", {})})
            
            # Update state
            state["messages"] = result.get("messages", messages)
            state["files"] = result.get("files", state.get("files", {}))
            state["current_phase"] = "task_generation"
            state["task_generation_complete"] = "implementation_tasks.md" in state.get("files", {})
            
            # Update completion
            if state["task_generation_complete"]:
                state["completion_percentage"] = 100
                completed = state.get("completed_phases", [])
                if "task_generation" not in completed:
                    completed.append("task_generation")
                state["completed_phases"] = completed
            
            return state
        
        return task_generation_node
    
    # Validation Node Implementation
    
    def _create_validation_node(self, phase: str):
        """Create a validation node for a specific phase"""
        def validation_node(state: AtlasState) -> AtlasState:
            logger.info(f"Validating {phase} phase completion")
            
            # Get phase definition
            phase_def = PHASE_DEFINITIONS.get(phase, {})
            agent_config = get_agent_config(phase_def.get("agent", ""))
            
            # Check required outputs
            required_outputs = agent_config.get("outputs", [])
            files = state.get("files", {})
            
            outputs_present = all(output in files for output in required_outputs)
            
            # Validate using criteria from subagents.py
            validation_result = validate_phase_completion(phase, state)
            
            # Update validation status in state
            validation_status = state.get("validation_status", {})
            validation_status[phase] = {
                "valid": validation_result.get("valid", outputs_present),
                "outputs_present": outputs_present,
                "missing": validation_result.get("missing", []),
                "timestamp": validation_result.get("timestamp")
            }
            state["validation_status"] = validation_status
            
            logger.info(f"Validation result for {phase}: {validation_result}")
            
            return state
        
        return validation_node
    
    # Routing Functions
    
    def _route_after_investigation_validation(self, state: AtlasState) -> Literal["discussion", "retry", "skip"]:
        """Determine next step after investigation validation"""
        validation = state.get("validation_status", {}).get("investigation", {})
        
        if validation.get("valid", False):
            # Check if user wants to skip discussion
            if self._check_skip_permission(state, "discussion"):
                return "skip"
            return "discussion"
        else:
            # Retry investigation if validation failed
            logger.warning("Investigation validation failed, retrying")
            return "retry"
    
    def _route_after_discussion_validation(self, state: AtlasState) -> Literal["planning", "retry", "back"]:
        """Determine next step after discussion validation"""
        validation = state.get("validation_status", {}).get("discussion", {})
        
        if validation.get("valid", False):
            return "planning"
        else:
            # Check if we need to go back to investigation
            if self._needs_reinvestigation(state):
                return "back"
            return "retry"
    
    def _route_after_planning_validation(self, state: AtlasState) -> Literal["task_generation", "retry", "discussion"]:
        """Determine next step after planning validation"""
        validation = state.get("validation_status", {}).get("planning", {})
        
        if validation.get("valid", False):
            return "task_generation"
        else:
            # Check if we need more clarification
            if self._needs_clarification(state):
                return "discussion"
            return "retry"
    
    def _route_after_final_validation(self, state: AtlasState) -> Literal["end", "retry", "planning"]:
        """Determine next step after final validation"""
        validation = state.get("validation_status", {}).get("task_generation", {})
        
        if validation.get("valid", False):
            return "end"
        else:
            # Check if we need to refine the plan
            if self._needs_plan_refinement(state):
                return "planning"
            return "retry"
    
    # Helper Functions
    
    def _check_skip_permission(self, state: AtlasState, phase: str) -> bool:
        """Check if user has given permission to skip a phase"""
        # Look for skip decision in files
        files = state.get("files", {})
        skip_decision = files.get("phase_transition_decision.md", "")
        
        return f"skip_{phase}" in skip_decision.lower() and "approved" in skip_decision.lower()
    
    def _needs_reinvestigation(self, state: AtlasState) -> bool:
        """Determine if we need to go back to investigation phase"""
        # Check if discussion revealed missing context
        files = state.get("files", {})
        discussion_output = files.get("requirements_clarified.md", "")
        
        return "need_more_context" in discussion_output.lower() or "investigate_further" in discussion_output.lower()
    
    def _needs_clarification(self, state: AtlasState) -> bool:
        """Determine if we need more clarification from user"""
        files = state.get("files", {})
        planning_output = files.get("implementation_plan.md", "")
        
        return "unclear_requirements" in planning_output.lower() or "need_clarification" in planning_output.lower()
    
    def _needs_plan_refinement(self, state: AtlasState) -> bool:
        """Determine if the plan needs refinement"""
        validation = state.get("validation_status", {}).get("task_generation", {})
        missing = validation.get("missing", [])
        
        return "repository_mapping" in missing or "task_clarity" in missing
    
    # Parallel Repository Analysis Methods
    
    def _extract_repositories_from_findings(self, findings_content: str) -> List[str]:
        """Extract repository names from investigation findings"""
        repositories = []
        
        # Look for repository mentions in the findings
        lines = findings_content.split('\n')
        in_repo_section = False
        
        for line in lines:
            # Look for repository section markers
            if 'repositories' in line.lower() or 'repository' in line.lower():
                in_repo_section = True
            elif line.startswith('#') and in_repo_section:
                # New section, stop looking
                in_repo_section = False
            elif in_repo_section and line.strip().startswith('-'):
                # Extract repository name from bullet point
                repo_name = line.strip().lstrip('-').strip()
                # Clean up the name (remove any markdown formatting)
                repo_name = repo_name.split(':')[0].split('(')[0].strip()
                if repo_name and not repo_name.startswith('['):
                    repositories.append(repo_name)
        
        return repositories
    
    def _run_parallel_repository_analysis(self, state: AtlasState, repositories: List[str]) -> Dict[str, str]:
        """
        Run parallel analysis for multiple repositories.
        
        This creates a sub-graph for parallel execution of repository analyzers.
        
        Args:
            state: Current Atlas state
            repositories: List of repository names to analyze
        
        Returns:
            Dictionary mapping repository names to their analysis results
        """
        import asyncio
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        results = {}
        
        # Create a thread pool for parallel execution
        with ThreadPoolExecutor(max_workers=min(len(repositories), 5)) as executor:
            # Submit analysis tasks for each repository
            future_to_repo = {}
            
            for repo_name in repositories:
                # Create a specialized message for repository analysis
                repo_messages = [
                    HumanMessage(
                        content=f"Analyze repository '{repo_name}': structure, patterns, and implementation opportunities"
                    )
                ]
                
                # Submit the task
                future = executor.submit(
                    self._analyze_single_repository,
                    repo_name,
                    state,
                    repo_messages
                )
                future_to_repo[future] = repo_name
            
            # Collect results as they complete
            for future in as_completed(future_to_repo):
                repo_name = future_to_repo[future]
                try:
                    analysis_result = future.result(timeout=60)  # 60 second timeout per repo
                    results[repo_name] = analysis_result
                    logger.info(f"Completed analysis for repository: {repo_name}")
                except Exception as e:
                    logger.error(f"Failed to analyze repository {repo_name}: {e}")
                    results[repo_name] = f"# Analysis Failed for {repo_name}\n\nError: {str(e)}"
        
        return results
    
    def _analyze_single_repository(self, repo_name: str, state: AtlasState, messages: List[BaseMessage]) -> str:
        """
        Analyze a single repository.
        
        This method is called in parallel for each repository.
        
        Args:
            repo_name: Name of the repository to analyze
            state: Current Atlas state
            messages: Messages for the analysis
        
        Returns:
            Analysis result as a string
        """
        try:
            # Create a mini-state for this repository analysis
            repo_state = {
                "messages": messages,
                "files": state.get("files", {}),
                "project_id": state.get("project_id"),
                "current_phase": "planning",
                "analyzing_repository": repo_name
            }
            
            # Invoke the agent for this specific repository
            result = self.agent_executor.invoke(repo_state)
            
            # Extract the analysis from the result
            final_messages = result.get("messages", [])
            if final_messages and hasattr(final_messages[-1], 'content'):
                return final_messages[-1].content
            else:
                return f"# Repository Analysis: {repo_name}\n\nNo detailed analysis available."
                
        except Exception as e:
            logger.error(f"Error analyzing repository {repo_name}: {e}")
            return f"# Repository Analysis: {repo_name}\n\nAnalysis failed: {str(e)}"


def create_atlas_graph(agent_executor=None, mcp_tools=None, **kwargs):
    """
    Create the Atlas V1 StateGraph with intelligent routing.
    
    This is the main entry point for creating the decision graph.
    
    Args:
        agent_executor: The main agent executor from create_deep_agent
        mcp_tools: Optional MCP tools wrapper
        **kwargs: Additional optional parameters for future extensibility
    
    Returns:
        Compiled StateGraph ready for execution
    """
    # Handle both positional and keyword arguments
    if agent_executor is None and 'agent_executor' in kwargs:
        agent_executor = kwargs['agent_executor']
    if mcp_tools is None and 'mcp_tools' in kwargs:
        mcp_tools = kwargs['mcp_tools']
    
    builder = AtlasGraphBuilder(agent_executor, mcp_tools)
    return builder.build()