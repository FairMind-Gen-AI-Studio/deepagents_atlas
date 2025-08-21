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
from deepagents.tools import write_todos, write_file, read_file, ls, edit_file, human_input
from langchain_litellm import ChatLiteLLM
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool, StructuredTool

try:
    from .prompts import ORCHESTRATOR_PROMPT_TEMPLATE
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
except ImportError:
    # Fallback for direct execution
    from prompts import ORCHESTRATOR_PROMPT_TEMPLATE
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
        
        # Initialize state
        self.state = {
            "current_phase": "investigation",
            "completed_phases": [],
            "phase_outputs": {},
            "validation_status": {},
            "project_id": None,
            "user_story_id": None,
            "context_summary": "",
            "virtual_filesystem": {},
            "completion_percentage": 0
        }
        
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
    
    def _create_subagents(self) -> List[SubAgent]:
        """Create subagent configurations for deepagents"""
        subagents = []
        
        # Determine available MCP tool names
        available_mcp_tool_names = set()
        if self.mcp_tools:
            mcp_tools_dict = self._create_all_mcp_tools()
            available_mcp_tool_names.update(mcp_tools_dict.keys())
        
        # Native tools that can be specifically assigned (human_input is special for discussion agent)
        native_tool_names = {"human_input"}
        
        for agent_name, agent_config in AGENT_CONFIGS.items():
            subagent = {
                "name": agent_config["name"],
                "description": agent_config["description"], 
                "prompt": agent_config["prompt"]
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
                subagent["tools"] = available_specific_tools
                logger.info(f"Created subagent config: {agent_name} with {len(available_specific_tools)} specific tools")
            else:
                logger.info(f"Created subagent config: {agent_name} (inherits all tools: filesystem + todos + task delegation)")
            
            subagents.append(subagent)
        
        return subagents
    
    def _create_orchestrator_prompt(self) -> str:
        """Create orchestrator prompt with current context"""
        current_phase = self.state.get("current_phase", "investigation")
        completion_percentage = self.state.get("completion_percentage", 0)
        project_id = self.state.get("project_id", "unknown")
        
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
            recommended_next_action=recommended_next_action
        )
    
    def _create_orchestrator(self):
        """Create the main orchestrator deep agent"""
        
        # Create tools that will be available to subagents
        # MCP tools need to be in the tools list for subagents to access them via tools_by_name
        subagent_tools = []
        
        # Add MCP tools for subagent access (but not orchestrator access)
        if self.mcp_tools:
            mcp_tools_dict = self._create_all_mcp_tools()
            subagent_tools.extend(list(mcp_tools_dict.values()))
            logger.info(f"Added {len(mcp_tools_dict)} MCP tools for subagent access")
        
        # Create orchestrator prompt
        orchestrator_instructions = self._create_orchestrator_prompt()
        
        # Create the orchestrator using deepagents
        # HYBRID APPROACH: Technical access but prompt-enforced restriction
        # - MCP tools are included for subagent access via tools_by_name
        # - Orchestrator technically has access but is forbidden by prompt to use them
        # - Orchestrator should ONLY use: write_todos, write_file, read_file, ls, edit_file, human_input, task
        # - All project work must be delegated via the 'task' tool
        orchestrator = create_deep_agent(
            tools=subagent_tools,  # MCP tools for subagents to access, but orchestrator won't use them directly
            instructions=orchestrator_instructions,
            subagents=self.subagents,
            model=self.model
        )
        
        # Set recursion limit
        recursion_limit = self.config.get("agents", {}).get("orchestrator", {}).get("recursion_limit", 100)
        orchestrator = orchestrator.with_config({"recursion_limit": recursion_limit})
        
        logger.info("Orchestrator deep agent created successfully")
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
            
            # Create a copy of the tool with the new prefixed name
            # This is needed because the tool's name is used as the key in tools_by_name
            renamed_tool = StructuredTool(
                name=prefixed_name,
                description=mcp_tool.description,
                func=mcp_tool.func,
                coroutine=mcp_tool.coroutine,
                args_schema=mcp_tool.args_schema
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
        
        # Update state with request context
        self.state.update({
            "project_id": project_id,
            "user_story_id": user_story_id,
            "user_request": user_request,
            "current_phase": "investigation"
        })
        
        logger.info(f"Starting Atlas V1 execution for: {user_request[:100]}...")
        
        # Prepare initial message for orchestrator
        messages = [{"role": "user", "content": user_request}]
        
        # Add context if available
        if project_id:
            messages.append({"role": "system", "content": f"Project ID: {project_id}"})
        if user_story_id:
            messages.append({"role": "system", "content": f"User Story ID: {user_story_id}"})
        
        try:
            # Run the orchestrator
            result = await self.orchestrator.ainvoke({
                "messages": messages,
                "files": self.state.get("virtual_filesystem", {})
            })
            
            # Update virtual filesystem from result
            if "files" in result:
                self.state["virtual_filesystem"].update(result["files"])
            
            # Extract final response
            final_messages = result.get("messages", [])
            final_response = final_messages[-1].content if final_messages else "No response generated"
            
            # Update completion status
            self._update_completion_status()
            
            logger.info("Atlas V1 execution completed successfully")
            
            return {
                "status": "completed",
                "final_response": final_response,
                "state": self.state,
                "virtual_filesystem": self.state["virtual_filesystem"],
                "completion_percentage": self.state["completion_percentage"],
                "phases_completed": self.state["completed_phases"]
            }
            
        except Exception as e:
            logger.error(f"Error during Atlas V1 execution: {e}")
            return {
                "status": "error",
                "error": str(e),
                "state": self.state,
                "completion_percentage": self.state["completion_percentage"]
            }
    
    def _update_completion_status(self):
        """Update completion status based on phase progress"""
        total_phases = len(self.config.get("phases", []))
        completed_phases = len(self.state.get("completed_phases", []))
        
        if total_phases > 0:
            self.state["completion_percentage"] = int((completed_phases / total_phases) * 100)
        
        # Validate current phase completion
        current_phase = self.state.get("current_phase")
        if current_phase:
            validation = validate_phase_completion(current_phase, self.state.get("virtual_filesystem", {}))
            self.state["validation_status"][current_phase] = validation
            
            # Auto-advance if phase is complete and auto-advance is enabled
            phase_def = get_phase_definition(current_phase)
            if validation["completed"] and phase_def.get("auto_advance", False):
                if current_phase not in self.state["completed_phases"]:
                    self.state["completed_phases"].append(current_phase)
                
                next_phase = get_next_phase(current_phase)
                if next_phase != "completed":
                    self.state["current_phase"] = next_phase
                    logger.info(f"Auto-advanced from {current_phase} to {next_phase}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Atlas agent"""
        return {
            "current_phase": self.state.get("current_phase"),
            "completion_percentage": self.state.get("completion_percentage", 0),
            "completed_phases": self.state.get("completed_phases", []),
            "validation_status": self.state.get("validation_status", {}),
            "virtual_filesystem_files": list(self.state.get("virtual_filesystem", {}).keys()),
            "project_id": self.state.get("project_id"),
            "user_story_id": self.state.get("user_story_id")
        }
    
    def get_virtual_file(self, filename: str) -> Optional[str]:
        """Get content of a file from virtual filesystem"""
        return self.state.get("virtual_filesystem", {}).get(filename)
    
    def list_virtual_files(self) -> List[str]:
        """List all files in virtual filesystem"""
        return list(self.state.get("virtual_filesystem", {}).keys())

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