# Atlas V1 Agent - Deep Planning Orchestrator
# Implementation of the 4-phase Atlas methodology using deepagents framework

import os
import yaml
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from dotenv import load_dotenv

from deepagents import create_deep_agent, SubAgent
from langchain_litellm import ChatLiteLLM
from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool

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
        
        for agent_name, agent_config in AGENT_CONFIGS.items():
            subagent = {
                "name": agent_config["name"],
                "description": agent_config["description"], 
                "prompt": agent_config["prompt"],
                "tools": agent_config.get("tools", [])
            }
            subagents.append(subagent)
            logger.info(f"Created subagent config: {agent_name}")
        
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
        
        # Create all MCP tools as callable functions if available  
        all_tools = []
        if self.mcp_tools:
            all_tools.extend(self._create_all_mcp_tools())
        
        # Create orchestrator prompt
        orchestrator_instructions = self._create_orchestrator_prompt()
        
        # Create the orchestrator using deepagents
        # deepagents will automatically add: write_todos, write_file, read_file, ls, edit_file, task
        orchestrator = create_deep_agent(
            tools=all_tools,
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
        """Create all MCP tool wrappers as callable functions"""
        tools = []
        
        if not self.mcp_tools:
            return tools
            
        # General tools
        @tool(name="mcp__fairmind__General_list_projects", description="List all available projects")
        def list_projects():
            return self.mcp_tools.list_projects()
            
        @tool(name="mcp__fairmind__General_get_document_content", description="Get content of a document by ID")  
        def get_document_content(document_id: str, start_line: int = 0, end_line: int = 200):
            return self.mcp_tools.get_document_content(document_id, start_line, end_line)
            
        @tool(name="mcp__fairmind__General_rag_retrieve_documents", description="Retrieve documents from RAG by query")
        def rag_retrieve_documents(query: str, projectId: str, k: int = 20, score_threshold: float = 0.5):
            return self.mcp_tools.rag_retrieve_documents(query, projectId, k, score_threshold)
            
        @tool(name="mcp__fairmind__General_rag_retrieve_specific_documents", description="Retrieve specific documents from RAG")
        def rag_retrieve_specific_documents(query: str, projectId: str, focus_params: List[str] = None, k: int = 20, score_threshold: float = 0.5):
            return self.mcp_tools.rag_retrieve_specific_documents(query, projectId, focus_params, k, score_threshold)
            
        # Studio tools
        @tool(name="mcp__fairmind__Studio_list_needs_by_project", description="List all needs for a project")
        def list_needs_by_project(project_id: str):
            return self.mcp_tools.list_needs_by_project(project_id)
            
        @tool(name="mcp__fairmind__Studio_get_need", description="Get details of a specific need")
        def get_need(need_id: str):
            return self.mcp_tools.get_need(need_id)
            
        @tool(name="mcp__fairmind__Studio_list_user_stories_by_project", description="List all user stories for a project")
        def list_user_stories_by_project(project_id: str):
            return self.mcp_tools.list_user_stories_by_project(project_id)
            
        @tool(name="mcp__fairmind__Studio_list_user_stories_by_need", description="List user stories by need")
        def list_user_stories_by_need(need_id: str):
            return self.mcp_tools.list_user_stories_by_need(need_id)
            
        @tool(name="mcp__fairmind__Studio_get_user_story", description="Get details of a specific user story")
        def get_user_story(user_story_id: str):
            return self.mcp_tools.get_user_story(user_story_id)
            
        @tool(name="mcp__fairmind__Studio_get_related_user_stories", description="Get related user stories")
        def get_related_user_stories(user_story_id: str):
            return self.mcp_tools.get_related_user_stories(user_story_id)
            
        @tool(name="mcp__fairmind__Studio_list_tasks_by_project", description="List all tasks for a project")
        def list_tasks_by_project(project_id: str):
            return self.mcp_tools.list_tasks_by_project(project_id)
            
        @tool(name="mcp__fairmind__Studio_get_task", description="Get details of a specific task")
        def get_task(task_id: str):
            return self.mcp_tools.get_task(task_id)
            
        @tool(name="mcp__fairmind__Studio_list_requirements_by_project", description="List all requirements for a project")
        def list_requirements_by_project(project_id: str):
            return self.mcp_tools.list_requirements_by_project(project_id)
            
        @tool(name="mcp__fairmind__Studio_get_requirement", description="Get details of a specific requirement")
        def get_requirement(requirement_id: str):
            return self.mcp_tools.get_requirement(requirement_id)
            
        @tool(name="mcp__fairmind__Studio_list_tests_by_project", description="List all tests for a project")
        def list_tests_by_project(projectId: str):
            return self.mcp_tools.list_tests_by_project(projectId)
            
        @tool(name="mcp__fairmind__Studio_list_tests_by_userstory", description="List tests by user story")
        def list_tests_by_userstory(user_story_id: str):
            return self.mcp_tools.list_tests_by_userstory(user_story_id)
            
        # Code tools
        @tool(name="mcp__fairmind__Code_list_repositories", description="List all repositories for a project")
        def list_repositories(project_id: str):
            return self.mcp_tools.list_repositories(project_id)
            
        @tool(name="mcp__fairmind__Code_get_directory_structure", description="Get directory structure of a repository")
        def get_directory_structure(project_id: str, repository_id: str):
            return self.mcp_tools.get_directory_structure(project_id, repository_id)
            
        @tool(name="mcp__fairmind__Code_find_relevant_code_snippets", description="Find relevant code snippets")
        def find_relevant_code_snippets(natural_language_query: str, project_id: str, repository_id: str = None, top_k: int = 10):
            return self.mcp_tools.find_relevant_code_snippets(natural_language_query, project_id, repository_id, top_k)
            
        @tool(name="mcp__fairmind__Code_get_file", description="Get content of a specific file")
        def get_file(project_id: str, repository_id: str, entity_id: str = None, file_path: str = None):
            return self.mcp_tools.get_file(project_id, repository_id, entity_id, file_path)
            
        @tool(name="mcp__fairmind__Code_find_usages", description="Find usages of a code entity")
        def find_usages(project_id: str, repository_id: str, entity_id: str):
            return self.mcp_tools.find_usages(project_id, repository_id, entity_id)
        
        # Collect all tools
        tools.extend([
            list_projects, get_document_content, rag_retrieve_documents, rag_retrieve_specific_documents,
            list_needs_by_project, get_need, list_user_stories_by_project, list_user_stories_by_need,
            get_user_story, get_related_user_stories, list_tasks_by_project, get_task,
            list_requirements_by_project, get_requirement, list_tests_by_project, list_tests_by_userstory,
            list_repositories, get_directory_structure, find_relevant_code_snippets, get_file, find_usages
        ])
        
        logger.info(f"Created {len(tools)} MCP tool wrappers")
        return tools
        
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
    
    # Example usage
    agent = create_atlas_agent()
    
    result = await agent.run(
        user_request="I need to implement user authentication for the mobile app",
        project_id="mobile-app-project"
    )
    
    print("Atlas V1 Result:")
    print(f"Status: {result['status']}")
    print(f"Completion: {result['completion_percentage']}%")
    print(f"Response: {result['final_response'][:200]}...")
    
    return result

# Export the graph for use with LangGraph
def create_atlas_graph(available_tools: Optional[Dict[str, Any]] = None):
    """Factory function to create Atlas agent graph for LangGraph"""
    atlas_agent = create_atlas_agent(available_tools=available_tools)
    return atlas_agent.orchestrator

# Create default agent instance for LangGraph
agent = create_atlas_graph()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())