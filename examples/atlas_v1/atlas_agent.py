# Atlas V1 Agent - Deep Planning Orchestrator
# Implementation of the 4-phase Atlas methodology using deepagents framework

import os
import yaml
import logging
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Add the src directory to Python path to use local deepagents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from deepagents import create_deep_agent, SubAgent
from deepagents.tools import write_todos, write_file, read_file, ls, edit_file
# Note: human_input is imported from atlas_tools instead to use our enhanced version
from langchain_litellm import ChatLiteLLM
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool, StructuredTool

# Import our properly typed state schema
from atlas_state import AtlasState

# Import the new StateGraph implementation
def _import_create_atlas_graph():
    """Dynamic import to avoid caching issues"""
    try:
        from .atlas_graph import create_atlas_graph
        return create_atlas_graph
    except ImportError:
        from atlas_graph import create_atlas_graph
        return create_atlas_graph

try:
    from .prompts import ORCHESTRATOR_PROMPT_TEMPLATE, TOOL_USAGE_INSTRUCTIONS
    from .subagents import (
        AGENT_CONFIGS, 
        PHASE_DEFINITIONS,
        get_agent_config,
        get_phase_definition,
        validate_phase_completion,
        get_next_phase,
        format_agent_prompt,
        get_tools_for_agent
    )
    from .mcp_tools import create_mcp_wrapper, MCPToolsWrapper
    from .atlas_tools import human_input, human_confirm, human_input_multiline
except ImportError:
    # Fallback for direct execution
    from prompts import ORCHESTRATOR_PROMPT_TEMPLATE, TOOL_USAGE_INSTRUCTIONS
    from subagents import (
        AGENT_CONFIGS, 
        PHASE_DEFINITIONS,
        get_agent_config,
        get_phase_definition,
        validate_phase_completion,
        get_next_phase,
        format_agent_prompt,
        get_tools_for_agent
    )
    from mcp_tools import create_mcp_wrapper, MCPToolsWrapper
    from atlas_tools import human_input, human_confirm, human_input_multiline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AtlasAgentV1:
    """
    Atlas V1 Deep Planning Agent
    
    Implements the 4-phase Atlas methodology:
    1. Investigation - Silent project exploration
    2. Discussion - Interactive requirements clarification  
    3. Planning - Code analysis and solution design
    4. Task Generation - Convert plan to actionable tasks
    """
    
    def __init__(self, config_path: Optional[str] = None, available_tools: Optional[Dict[str, Any]] = None):
        """Initialize Atlas Agent with configuration and available tools"""
        
        # Load environment variables from .env file
        load_dotenv()
        
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Note: State is now managed by LangGraph through AtlasState schema
        # The orchestrator will handle state initialization and updates
        # We don't need a custom self.state dictionary anymore
        
        # Initialize MCP tools wrapper if available
        self.mcp_tools: Optional[MCPToolsWrapper] = None
        if available_tools:
            self.mcp_tools = create_mcp_wrapper(available_tools)
            logger.info(f"MCP Tools initialized: {self.mcp_tools.get_available_tools()}")
        else:
            # Try to initialize MCP tools automatically if none provided
            available_tools = _initialize_mcp_tools_sync()
            if available_tools:
                self.mcp_tools = create_mcp_wrapper(available_tools)
                logger.info(f"MCP Tools initialized automatically: {self.mcp_tools.get_available_tools()}")
        
        # Initialize LiteLLM model
        self.model = self._initialize_model()
        
        # Create subagents configurations
        self.subagents = self._create_subagents()
        
        # Initialize orchestrator tools (will be provided by deepagents)
        self.orchestrator_tools = []
        
        # Create the main orchestrator agent
        self.orchestrator = self._create_orchestrator()
        
        # Create the StateGraph for intelligent phase routing
        self.use_state_graph = os.getenv("ATLAS_USE_STATE_GRAPH", "true").lower() == "true"
        if self.use_state_graph:
            try:
                # Dynamically import to avoid caching issues
                create_atlas_graph_func = _import_create_atlas_graph()
                # Use positional arguments
                self.state_graph = create_atlas_graph_func(self.orchestrator, self.mcp_tools)
                logger.info("StateGraph created successfully for intelligent phase routing")
            except Exception as e:
                logger.warning(f"Failed to create StateGraph: {e}. Falling back to linear orchestrator.")
                self.use_state_graph = False
                self.state_graph = None
        else:
            self.state_graph = None
            logger.info("StateGraph disabled, using linear orchestrator")
        
        logger.info("Atlas V1 Agent initialized successfully")
    
    def _load_config(self, config_path: Optional[str] = None) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        if config_path is None:
            config_path = Path(__file__).parent / "config.yaml"
        
        try:
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"Could not load config from {config_path}: {e}. Using defaults.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "model": {
                "provider": "litellm",
                "name": "claude-3-5-sonnet-20241022",
                "temperature": 0.7,
                "max_tokens": 8192
            },
            "phases": ["investigation", "discussion", "planning", "task_generation"],
            "mcp": {"fairmind": {"enabled": True}},
            "virtual_fs": {"max_file_size": 10000, "max_total_files": 50},
            "agents": {"orchestrator": {"recursion_limit": 100}}
        }
    
    def _initialize_model(self) -> BaseChatModel:
        """Initialize LiteLLM model based on configuration and environment variables"""
        model_config = self.config.get("model", {})
        
        # Check for environment variable overrides (priority order)
        model_name = (
            os.getenv("ATLAS_MODEL_NAME") or 
            os.getenv("LITELLM_MODEL") or 
            model_config.get("name", "claude-3-5-sonnet-20241022")
        )
        
        temperature = float(
            os.getenv("ATLAS_MODEL_TEMPERATURE") or 
            model_config.get("temperature", 0.7)
        )
        
        max_tokens = int(
            os.getenv("ATLAS_MODEL_MAX_TOKENS") or 
            model_config.get("max_tokens", 8192)
        )
        
        # Validate model name format for LiteLLM
        if not self._validate_litellm_model_name(model_name):
            logger.warning(f"Model name '{model_name}' might not follow LiteLLM format. Expected formats: 'provider/model' or 'model'")
        
        # Log configuration source
        config_source = "environment" if os.getenv("ATLAS_MODEL_NAME") or os.getenv("LITELLM_MODEL") else "config file"
        logger.info(f"Model configuration loaded from: {config_source}")
        
        # Check if it's an Anthropic model
        is_anthropic = (
            model_name.startswith("anthropic/") or 
            model_name.startswith("claude-") or
            "claude" in model_name.lower()
        )
        
        try:
            
            if is_anthropic:
                # Use ChatAnthropic for Anthropic models to ensure proper tool_calls formatting
                # Extract the actual model name if it has provider prefix
                actual_model_name = model_name.split("/")[-1] if "/" in model_name else model_name
                
                model = ChatAnthropic(
                    model_name=actual_model_name,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                logger.info(f"ChatAnthropic model initialized successfully:")
                logger.info(f"  Model: {actual_model_name}")
                logger.info(f"  Temperature: {temperature}")
                logger.info(f"  Max Tokens: {max_tokens}")
                
            else:
                # Use ChatLiteLLM for other models
                model = ChatLiteLLM(
                    model=model_name,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    # API key will be read from environment by LiteLLM
                )
                logger.info(f"ChatLiteLLM model initialized successfully:")
                logger.info(f"  Model: {model_name}")
                logger.info(f"  Temperature: {temperature}")
                logger.info(f"  Max Tokens: {max_tokens}")
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to initialize model '{model_name}': {e}")
            logger.error("Common issues:")
            logger.error("  - Check if the model name is correct")
            logger.error("  - Ensure the required API key environment variable is set")
            logger.error("  - Verify the model is supported by the provider")
            if is_anthropic:
                logger.error("  - For Anthropic models, ensure ANTHROPIC_API_KEY is set")
            else:
                logger.error("  - For LiteLLM, check format (e.g., 'openai/gpt-4', 'anthropic/claude-3')")
            raise
    
    def _validate_litellm_model_name(self, model_name: str) -> bool:
        """Validate that model name follows LiteLLM conventions"""
        if not model_name or not isinstance(model_name, str):
            return False
        
        # Common LiteLLM patterns
        valid_patterns = [
            # Provider/model format (preferred)
            "/" in model_name,
            # Direct model names for known models
            model_name.startswith(("gpt-", "claude-", "gemini-", "command-")),
            # Anthropic models
            model_name.startswith("anthropic/"),
            # OpenAI models
            model_name.startswith("openai/"),
            # OpenRouter models
            model_name.startswith("openrouter/"),
            # Azure models
            model_name.startswith("azure/"),
            # Other common providers
            any(provider in model_name for provider in [
                "cohere/", "huggingface/", "replicate/", "bedrock/", 
                "vertex_ai/", "palm/", "together_ai/", "ollama/"
            ])
        ]
        
        return any(valid_patterns)
    
    def _get_tool_categories(self) -> str:
        """Generate formatted string of available tool categories for prompt context"""
        if not self.mcp_tools:
            return "Filesystem and task delegation tools available (no MCP tools configured)"
        
        # Get available MCP tools and categorize them
        available_tools = self.mcp_tools.get_available_tools()
        categories = {}
        
        for tool_name in available_tools:
            if "__fairmind__General" in tool_name:
                categories.setdefault("General", []).append(tool_name)
            elif "__fairmind__Studio" in tool_name:
                categories.setdefault("Studio", []).append(tool_name)
            elif "__fairmind__Code" in tool_name:
                categories.setdefault("Code", []).append(tool_name)
            else:
                categories.setdefault("Other", []).append(tool_name)
        
        # Format categories with counts
        category_strings = []
        for category, tools in categories.items():
            category_strings.append(f"{category} ({len(tools)} tools)")
        
        if category_strings:
            return f"MCP Tools: {', '.join(category_strings)} + Built-in filesystem and task delegation tools"
        else:
            return "Built-in filesystem and task delegation tools available"
    
    def _create_subagents(self) -> List[SubAgent]:
        """Create subagent configurations for deepagents"""
        subagents = []
        
        # Determine available MCP tool names
        available_mcp_tool_names = set()
        if self.mcp_tools:
            mcp_tools_dict = self._create_all_mcp_tools()
            available_mcp_tool_names.update(mcp_tools_dict.keys())
        
        # Native tools that can be specifically assigned (human_input is special for discussion agent)
        # Include our custom Atlas tools that override deepagents defaults
        native_tool_names = {"human_input", "human_confirm", "human_input_multiline"}
        
        # Gather context for prompt formatting - include all possible template variables
        # Note: State is now managed by LangGraph, so we use default values here
        context = {
            # Core project context (defaults - will be set at runtime)
            "project_id": "unknown",
            "current_phase": "investigation",
            "completion_percentage": 0,
            "tool_categories": self._get_tool_categories(),
            
            # Phase-specific context
            "investigation_focus": "business requirements and project context analysis",
            "knowledge_gaps": "technical implementation details and architecture requirements",
            "project_type": "software development project", 
            "scope_summary": "implementation scope to be determined through investigation and planning",
            
            # Agent recommendation context (used by orchestrator)
            "recommended_agent": "investigation-agent",
            "recommended_next_action": "Deploy investigation-agent for current phase",
            
            # Repository and task context
            "repository_name": "to be determined during planning phase",
            "repository_count": "to be determined during code analysis",
            "task_count": "to be determined during task generation",
            "repo_count": "to be determined",
            "phase_count": "4",
            
            # Additional context variables that might be used
            "business_requirements_from_investigation_phase": "to be determined during investigation",
            "technical_requirements_from_discussion_and_planning_phases": "to be determined",
            "repository_assignment_recommendations": "to be determined during planning",
            
            # Tool usage instructions for open source models
            "tool_usage_instructions": TOOL_USAGE_INSTRUCTIONS
        }

        for agent_name, agent_config in AGENT_CONFIGS.items():
            # Format prompt with context variables
            formatted_prompt = format_agent_prompt(agent_name, **context)
            
            subagent = {
                "name": agent_config["name"],
                "description": agent_config["description"], 
                "prompt": formatted_prompt
            }
            
            # Get tools configured for this subagent
            configured_tools = agent_config.get("tools", [])
            
            # Filter to only include available tools
            available_specific_tools = []
            missing_tools = []
            
            for tool_name in configured_tools:
                if tool_name in available_mcp_tool_names or tool_name in native_tool_names:
                    available_specific_tools.append(tool_name)
                else:
                    missing_tools.append(tool_name)
            
            # Log missing tools with appropriate context
            if missing_tools:
                mcp_missing = [t for t in missing_tools if t.startswith("mcp__fairmind__")]
                other_missing = [t for t in missing_tools if not t.startswith("mcp__fairmind__")]
                
                if mcp_missing and not self.mcp_tools:
                    logger.info(f"Subagent '{agent_name}': {len(mcp_missing)} MCP tools not available (MCP not configured)")
                elif mcp_missing:
                    logger.warning(f"Subagent '{agent_name}' missing MCP tools: {mcp_missing}")
                    
                if other_missing:
                    logger.warning(f"Subagent '{agent_name}' missing tools: {other_missing}")
            
            # Only specify "tools" if there are specific tools available
            # Otherwise omit the key so subagent inherits ALL tools (including builtin filesystem tools)
            if available_specific_tools:
                # Add essential builtin tools that aren't already in the list
                essential_builtin_names = ['write_file', 'read_file', 'ls', 'write_todos', 'edit_file']
                
                for builtin_name in essential_builtin_names:
                    if builtin_name not in available_specific_tools:
                        available_specific_tools.append(builtin_name)
                
                subagent["tools"] = available_specific_tools
                logger.info(f"Created subagent config: {agent_name} with {len(available_specific_tools)} tools (including essential builtins)")
            else:
                logger.info(f"Created subagent config: {agent_name} (inherits all tools: filesystem + todos + task delegation)")
            
            subagents.append(subagent)
        
        return subagents
    
    def _create_orchestrator_prompt(self) -> str:
        """Create orchestrator prompt with initial context
        
        Note: State is now managed by LangGraph, so we use default values here.
        The actual state will be available to the orchestrator at runtime.
        """
        # Use default values for initial prompt generation
        current_phase = "investigation"  # Always start with investigation
        completion_percentage = 0
        project_id = "unknown"  # Will be set at runtime
        
        phase_def = get_phase_definition(current_phase)
        recommended_agent = phase_def.get("agent", "investigation-agent")
        
        recommended_next_action = f"""
task(
    description="{phase_def.get('goal', 'Execute current phase')}",
    subagent_type="{recommended_agent}"
)"""
        
        return ORCHESTRATOR_PROMPT_TEMPLATE.format(
            current_phase=current_phase,
            completion_percentage=completion_percentage,
            project_id=project_id,
            recommended_agent=recommended_agent,
            recommended_next_action=recommended_next_action,
            tool_usage_instructions=TOOL_USAGE_INSTRUCTIONS
        )
    
    def _create_orchestrator(self):
        """Create the main orchestrator deep agent using standard implementation"""
        
        # Import standard create_deep_agent from core library
        from deepagents import create_deep_agent
        
        # Create tools that will be available to subagents
        # MCP tools need to be in the tools list for subagents to access them via tools_by_name
        subagent_tools = []
        
        # Add our custom Atlas tools (human_input, human_confirm, etc.)
        # These override the default deepagents versions
        atlas_custom_tools = [human_input, human_confirm, human_input_multiline]
        subagent_tools.extend(atlas_custom_tools)
        logger.info(f"Added {len(atlas_custom_tools)} Atlas custom tools (human_input with interrupt support)")
        
        # Add MCP tools for subagent access (but not orchestrator access)
        if self.mcp_tools:
            mcp_tools_dict = self._create_all_mcp_tools()
            subagent_tools.extend(list(mcp_tools_dict.values()))
            logger.info(f"Added {len(mcp_tools_dict)} MCP tools for subagent access")
        
        # Create orchestrator prompt
        orchestrator_instructions = self._create_orchestrator_prompt()
        
        # IMPORTANT: When running as LangGraph API deployment, checkpointer is handled automatically
        # Only use InMemorySaver for local testing, not for deployment
        checkpointer = None
        
        # Check if we're running locally (not in LangGraph API)
        # LangGraph API/Studio sets specific environment variables
        # Adding more comprehensive checks for LangGraph environment detection
        is_langgraph_api = (
            os.getenv("LANGGRAPH_API") or 
            os.getenv("LANGSERVE_ENDPOINT") or
            os.getenv("LANGGRAPH_API_VERSION") or  # New check for API version
            os.getenv("LANGGRAPH_RUNTIME_IN_MEM") or  # Check for in-memory runtime
            os.getenv("IS_LANGGRAPH_CLOUD") or  # Cloud deployment flag
            os.getenv("LANGGRAPH_MODULE_IMPORT") or  # Set when imported by LangGraph
            # Check if running via langgraph dev command (local API server)
            (os.getenv("LANGGRAPH_ENV") == "local_dev")
        )
        
        if not is_langgraph_api:
            # Only use InMemorySaver for local testing (direct script execution)
            try:
                from langgraph.checkpoint.memory import InMemorySaver
                checkpointer = InMemorySaver()
                logger.info("Created InMemorySaver checkpointer for local testing (interrupt support)")
            except Exception as e:
                logger.warning(f"Could not create InMemorySaver: {e}. Interrupts may not work locally.")
                checkpointer = None
        else:
            logger.info("Running in LangGraph API/Studio - using platform-managed persistence")
        
        # Use STANDARD create_deep_agent instead of custom streaming version
        # This ensures virtual filesystem state is properly managed
        # Note: We lose streaming UI feedback but gain working state management
        orchestrator = create_deep_agent(
            tools=subagent_tools,
            instructions=orchestrator_instructions,
            model=self.model,
            subagents=self.subagents,
            checkpointer=checkpointer  # None for LangGraph API, InMemorySaver for local
        )
        
        # Set recursion limit
        recursion_limit = self.config.get("agents", {}).get("orchestrator", {}).get("recursion_limit", 100)
        orchestrator = orchestrator.with_config({"recursion_limit": recursion_limit})
        
        logger.info("Orchestrator deep agent created successfully with interrupt support")
        return orchestrator
    
    
    def _create_all_mcp_tools(self):
        """Return raw MCP tools with proper naming for orchestrator usage"""
        tools_dict = {}
        
        if not self.mcp_tools:
            return tools_dict
        
        # Get the original MCP tools and map them to expected names
        # The self.mcp_tools.tools contains the raw StructuredTool objects from MCP
        for original_name, mcp_tool in self.mcp_tools.tools.items():
            # Map the original MCP tool names to the expected prefixed names for subagents
            # The subagents expect names like "mcp__fairmind__General_list_projects"
            prefixed_name = f"mcp__fairmind__{original_name}"
            
            # Handle both real MCP tools (StructuredTool objects) and mock functions
            if hasattr(mcp_tool, 'description'):
                # Real MCP tool - create a proper copy
                renamed_tool = StructuredTool(
                    name=prefixed_name,
                    description=mcp_tool.description,
                    func=mcp_tool.func,
                    coroutine=getattr(mcp_tool, 'coroutine', None),
                    args_schema=getattr(mcp_tool, 'args_schema', None)
                )
            else:
                # Mock function - create a minimal StructuredTool wrapper
                renamed_tool = StructuredTool(
                    name=prefixed_name,
                    description=f"Mock MCP tool: {original_name}",
                    func=mcp_tool,
                    coroutine=None,
                    args_schema=None
                )
            
            tools_dict[prefixed_name] = renamed_tool
            logger.debug(f"Mapped MCP tool: {original_name} -> {prefixed_name}")
        
        logger.info(f"Mapped {len(tools_dict)} raw MCP tools for orchestrator")
        return tools_dict
        
    def _create_mcp_tool_wrapper(self, tool_name: str, mcp_function):
        """Create a wrapper function for MCP tools to be used by orchestrator"""
        @tool(name=tool_name, description=f"MCP tool: {tool_name}")
        def wrapper(*args, **kwargs):
            """Wrapper for MCP tool function"""
            try:
                return mcp_function(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error calling MCP tool {tool_name}: {e}")
                return {"error": str(e)}
        
        return wrapper
    
    async def run(self, user_request: str, project_id: Optional[str] = None, user_story_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the Atlas V1 agent on a user request
        
        Args:
            user_request: User's request/question
            project_id: Optional project ID to focus on
            user_story_id: Optional user story ID to implement
        
        Returns:
            Dict with results from all phases
        """
        
        logger.info(f"Starting Atlas V1 execution for: {user_request[:100]}...")
        
        # Prepare initial messages for orchestrator
        # System message must come before user message to avoid LangGraph errors
        messages = []
        
        # Add context as system message if any exists
        context_parts = []
        if project_id:
            context_parts.append(f"Project ID: {project_id}")
        if user_story_id:
            context_parts.append(f"User Story ID: {user_story_id}")
        
        if context_parts:
            context_content = "\n".join(context_parts)
            messages.append({"role": "system", "content": context_content})
        
        # Add user request
        messages.append({"role": "user", "content": user_request})
        
        # Prepare initial state using AtlasState schema
        initial_state = {
            "messages": messages,
            "current_phase": "investigation",
            "project_id": project_id,
            "user_story_id": user_story_id,
            "completed_phases": [],
            "phase_outputs": {},
            "validation_status": {},
            "context_summary": "",
            "completion_percentage": 0,
            "files": {}  # Virtual filesystem (was "virtual_filesystem")
        }
        
        try:
            # Choose between StateGraph and linear orchestrator
            if self.use_state_graph and self.state_graph:
                logger.info("Using StateGraph for intelligent phase routing")
                # Run the StateGraph with enhanced routing capabilities
                result = await self.state_graph.ainvoke(initial_state)
            else:
                logger.info("Using linear orchestrator (legacy mode)")
                # Run the traditional orchestrator
                result = await self.orchestrator.ainvoke(initial_state)
            
            # Extract final response
            final_messages = result.get("messages", [])
            final_response = final_messages[-1].content if final_messages else "No response generated"
            
            # Extract state from result for return value
            final_state = {
                "current_phase": result.get("current_phase", "investigation"),
                "completed_phases": result.get("completed_phases", []),
                "completion_percentage": result.get("completion_percentage", 0),
                "project_id": result.get("project_id"),
                "user_story_id": result.get("user_story_id"),
                "validation_status": result.get("validation_status", {})
            }
            
            logger.info("Atlas V1 execution completed successfully")
            
            return {
                "status": "completed",
                "final_response": final_response,
                "state": final_state,
                "virtual_filesystem": result.get("files", {}),
                "completion_percentage": final_state["completion_percentage"],
                "phases_completed": final_state["completed_phases"]
            }
            
        except Exception as e:
            error_str = str(e).lower()
            # Check if this is a tool validation error
            if "validation error" in error_str or "tool_call_id" in error_str:
                logger.error(f"Tool validation error: {e}")
                return {
                    "status": "error",
                    "error": "The AI model generated an invalid tool call format. Please retry your request.",
                    "phase": "unknown",
                    "details": "This error typically occurs with open source models. Try rephrasing your request or simplifying it.",
                    "state": initial_state,
                    "completion_percentage": 0
                }
            else:
                # Other errors
                logger.error(f"Error during Atlas V1 execution: {e}")
                return {
                    "status": "error",
                    "error": str(e),
                    "state": initial_state,
                    "completion_percentage": 0
                }
    
    # Note: These utility methods have been removed as state is now managed by LangGraph
    # The orchestrator and subagents handle state updates through Command objects
    # Status and file access should be obtained from the result of run() method
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Atlas agent
        
        Note: State is now managed by LangGraph. This returns a static status.
        For actual status, check the result from run() method.
        """
        return {
            "message": "State is managed by LangGraph. Run the agent to get current status.",
            "phases": self.config.get("phases", [])
        }
    
    def get_virtual_file(self, filename: str) -> Optional[str]:
        """Get content of a file from virtual filesystem
        
        Note: Virtual filesystem is managed by LangGraph state.
        Access files from the result of run() method.
        """
        logger.warning("Virtual filesystem is managed by LangGraph. Access files from run() result.")
        return None
    
    def list_virtual_files(self) -> List[str]:
        """List all files in virtual filesystem
        
        Note: Virtual filesystem is managed by LangGraph state.
        Access files from the result of run() method.
        """
        logger.warning("Virtual filesystem is managed by LangGraph. Access files from run() result.")
        return []

# Factory function to create Atlas agent
def create_atlas_agent(config_path: Optional[str] = None, available_tools: Optional[Dict[str, Any]] = None) -> AtlasAgentV1:
    """
    Create Atlas V1 Agent
    
    Args:
        config_path: Path to config.yaml file (optional)
        available_tools: Dictionary of available MCP tools (optional)
    
    Returns:
        Configured AtlasAgentV1 instance
    """
    return AtlasAgentV1(config_path=config_path, available_tools=available_tools)

# Main execution function for LangGraph
async def main():
    """Main function for testing Atlas agent"""
    
    try:
        # Import MCP client (import here to handle missing dependencies gracefully)
        from mcp_client import initialize_mcp_tools, get_mcp_status, close_mcp_client
        
        # Check MCP configuration status
        mcp_status = get_mcp_status()
        print("MCP Configuration Status:")
        print(f"  MCP Configured: {mcp_status['mcp_configured']}")
        print(f"  Anthropic Configured: {mcp_status['anthropic_configured']}")
        print(f"  Fairmind URL: {mcp_status['fairmind_url']}")
        
        # Initialize MCP tools
        print("\nInitializing MCP tools...")
        available_tools = await initialize_mcp_tools()
        
        if available_tools:
            print(f"✅ MCP tools initialized successfully: {len(available_tools)} tools")
        else:
            print("⚠️  No MCP tools available - agent will run with limited capabilities")
        
        # Create agent with MCP tools
        agent = create_atlas_agent(available_tools=available_tools)
        
        result = await agent.run(
            user_request="I need to implement user authentication for the mobile app",
            project_id="mobile-app-project"
        )
        
        print("\nAtlas V1 Result:")
        print(f"Status: {result['status']}")
        print(f"Completion: {result['completion_percentage']}%")
        print(f"Response: {result['final_response'][:200]}...")
        
        # Clean up MCP connections
        await close_mcp_client()
        
        return result
        
    except ImportError as e:
        logger.warning(f"MCP client not available: {e}")
        logger.info("Running Atlas agent without MCP tools")
        
        # Fallback: create agent without MCP tools
        agent = create_atlas_agent()
        result = await agent.run(
            user_request="I need to implement user authentication for the mobile app",
            project_id="mobile-app-project"
        )
        
        print("Atlas V1 Result (No MCP):")
        print(f"Status: {result['status']}")
        print(f"Completion: {result['completion_percentage']}%")
        print(f"Response: {result['final_response'][:200]}...")
        
        return result
    
    except Exception as e:
        logger.error(f"Error in main execution: {e}")
        raise

# Export the graph for use with LangGraph
def create_atlas_graph(available_tools: Optional[Dict[str, Any]] = None):
    """Factory function to create Atlas agent graph for LangGraph"""
    atlas_agent = create_atlas_agent(available_tools=available_tools)
    return atlas_agent.orchestrator

async def create_atlas_graph_with_mcp():
    """Factory function to create Atlas agent graph with MCP tools for LangGraph"""
    try:
        from mcp_client import initialize_mcp_tools
        available_tools = await initialize_mcp_tools()
        return create_atlas_graph(available_tools=available_tools)
    except ImportError:
        logger.warning("MCP client not available, creating graph without MCP tools")
        return create_atlas_graph(available_tools=None)

class LazyAtlasAgent:
    """Lazy-loading Atlas agent that initializes MCP tools on first use"""
    
    def __init__(self):
        self._agent = None
        self._initialized = False
    
    async def _ensure_initialized(self):
        """Initialize agent with MCP tools if not already done"""
        if not self._initialized:
            try:
                from mcp_client import initialize_mcp_tools
                available_tools = await initialize_mcp_tools()
                self._agent = create_atlas_agent(available_tools=available_tools)
                logger.info(f"Lazy Atlas agent initialized with {'MCP tools' if available_tools else 'no MCP tools'}")
            except ImportError:
                self._agent = create_atlas_agent(available_tools=None)
                logger.info("Lazy Atlas agent initialized without MCP tools (import error)")
            except Exception as e:
                logger.warning(f"Error initializing MCP tools, falling back to no MCP: {e}")
                self._agent = create_atlas_agent(available_tools=None)
            
            self._initialized = True
        
        return self._agent.orchestrator
    
    async def ainvoke(self, input_data, **kwargs):
        """Async invoke with lazy initialization"""
        orchestrator = await self._ensure_initialized()
        return await orchestrator.ainvoke(input_data, **kwargs)
    
    async def astream(self, input_data, **kwargs):
        """Async stream with lazy initialization"""
        orchestrator = await self._ensure_initialized()
        async for chunk in orchestrator.astream(input_data, **kwargs):
            yield chunk
    
    def invoke(self, input_data, **kwargs):
        """Sync invoke - raises error since MCP requires async"""
        raise RuntimeError("Sync invoke not supported with MCP tools. Use ainvoke() or create agent with create_atlas_graph() for sync usage without MCP.")

def _initialize_mcp_tools_sync():
    """Initialize MCP tools synchronously for LangGraph compatibility"""
    try:
        import asyncio
        from mcp_client import initialize_mcp_tools
        
        # Check if MCP is configured
        if not os.getenv("FAIRMIND_MCP_URL") or not os.getenv("FAIRMIND_MCP_TOKEN"):
            logger.info("MCP not configured - creating agent with builtin tools only")
            return None
        
        # Run async MCP initialization in new event loop
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're in an existing event loop, we can't run async here
                # Fallback to no MCP tools
                logger.warning("Cannot initialize MCP tools in running event loop - using agent without MCP")
                return None
        except RuntimeError:
            # No event loop exists, we can create one
            pass
        
        # Create new event loop for sync initialization
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            available_tools = loop.run_until_complete(initialize_mcp_tools())
            if available_tools:
                logger.info(f"MCP tools initialized synchronously: {len(available_tools)} tools")
                logger.info(f"Tool names: {list(available_tools.keys())}")
                # Log a sample tool structure  
                sample_tool_name = list(available_tools.keys())[0]
                sample_tool = available_tools[sample_tool_name]
                logger.debug(f"Sample tool '{sample_tool_name}': type={type(sample_tool).__name__}, methods={[m for m in dir(sample_tool) if not m.startswith('_')]}")
            else:
                logger.info("No MCP tools returned from initialization")
            return available_tools
        finally:
            loop.close()
            
    except ImportError:
        logger.info("MCP client not available - creating agent with builtin tools only")
        return None
    except Exception as e:
        logger.warning(f"Error initializing MCP tools: {e} - creating agent with builtin tools only")
        return None

# Create default agent instance for LangGraph (only when imported, not when executed)
if __name__ != "__main__":
    # Set environment variable to indicate we're being imported by LangGraph
    # This will be detected when creating the checkpointer
    os.environ["LANGGRAPH_MODULE_IMPORT"] = "true"
    
    try:
        # Initialize MCP tools synchronously and create agent
        available_tools = _initialize_mcp_tools_sync()
        agent = create_atlas_graph(available_tools=available_tools)
        
        if available_tools:
            logger.info(f"Atlas agent created for LangGraph with {len(available_tools)} MCP tools")
        else:
            logger.info("Atlas agent created for LangGraph with builtin tools only")
            
    except Exception as e:
        logger.error(f"Error creating Atlas agent: {e}")
        # Fallback to agent without MCP tools
        agent = create_atlas_graph()
        logger.info("Fallback: Atlas agent created with builtin tools only")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())