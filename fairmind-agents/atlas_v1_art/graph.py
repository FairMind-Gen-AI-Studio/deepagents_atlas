"""
LangGraph entry point for Atlas V1 with OpenPipe ART.

This module exposes the Atlas agent as a LangGraph graph for use with
langgraph dev and LangGraph Studio.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Apply nest_asyncio to allow nested event loops (required for LangGraph)
import nest_asyncio
nest_asyncio.apply()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import deepagents framework
from deepagents import create_deep_agent, SubAgent
from deepagents.state import DeepAgentState

# Import reinforcement components - ART is ALWAYS ON
from reinforcement.model_wrapper import get_art_enabled_model
from reinforcement.trajectory_storage import get_trajectory_storage

# Ensure current directory is in path for MCP client import
# This is critical for LangGraph which may load the module from a different context
current_dir = Path(__file__).parent
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))
    logger.debug(f"Added {current_dir} to Python path for MCP import")

# Import MCP tools if available
MCP_IMPORT_SUCCESS = False
try:
    from mcp_client import initialize_mcp_tools
    import asyncio
    MCP_IMPORT_SUCCESS = True
    logger.info("✅ MCP client module imported successfully")
    
    def _initialize_mcp_tools_sync():
        """Synchronous wrapper for MCP tools initialization.
        
        Uses nest_asyncio to handle nested event loops when running
        under LangGraph or other async environments.
        """
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # nest_asyncio allows run_until_complete even in running loops
        try:
            logger.info("🔄 Attempting MCP tools initialization...")
            result = loop.run_until_complete(initialize_mcp_tools())
            if result:
                logger.info(f"✅ MCP tools initialized successfully: {len(result)} tools available")
                for tool_name in list(result.keys())[:5]:
                    logger.debug(f"   - {tool_name}")
            else:
                logger.info("⚠️ MCP initialization completed but no tools returned (check credentials)")
            return result or {}
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg:
                logger.warning("⚠️ MCP authentication failed (403 Forbidden) - check your FAIRMIND_MCP_TOKEN")
            else:
                logger.warning(f"⚠️ MCP initialization failed: {error_msg}")
            logger.info("Atlas V1 will continue without MCP tools")
            return {}
except ImportError as e:
    import_error = str(e)
    logger.warning(f"MCP client import failed: {import_error}")
    logger.info(f"Current working directory: {os.getcwd()}")
    logger.info(f"Python path includes: {sys.path[:3]}")
    logger.info("Atlas V1 will continue without MCP tools")
    _initialize_mcp_tools_sync = lambda: {}


# Import Atlas agents configuration from local copies
try:
    # Import the 4 phase agents from local agents directory
    from agents import (
        investigation_agent,
        discussion_agent,
        planning_agent,
        task_generation_agent
    )
    
    # Import prompts from local copy
    from prompts import ORCHESTRATOR_PROMPT_TEMPLATE as ORCHESTRATOR_PROMPT_V2
    
    # Create AGENT_CONFIGS list from individual agents
    AGENT_CONFIGS = [
        investigation_agent,
        discussion_agent,
        planning_agent,
        task_generation_agent
    ]
    
    logger.info(f"✅ Atlas V1 agents loaded successfully: {len(AGENT_CONFIGS)} agents configured")
    
except ImportError as e:
    logger.warning(f"Failed to load Atlas agents: {e}")
    logger.warning("Using minimal fallback configuration")
    
    # Minimal fallback configuration
    AGENT_CONFIGS = [
        {
            "name": "research-agent",
            "description": "Used to research and investigate topics in depth",
            "prompt": "You are a research assistant. Your job is to investigate topics thoroughly and provide detailed analysis."
        },
        {
            "name": "planning-agent", 
            "description": "Used to create implementation plans and technical designs",
            "prompt": "You are a planning assistant. Create detailed technical plans and break down complex tasks into actionable steps."
        }
    ]
    
    ORCHESTRATOR_PROMPT_V2 = """You are an AI assistant helping with software development tasks.
        
You have access to specialized sub-agents for different tasks. Use them when appropriate:
- research-agent: For investigating topics and gathering information
- planning-agent: For creating technical plans and designs

Always use the write_todos tool to track your progress and break down complex tasks."""


def create_atlas_graph_with_art():
    """
    Create the Atlas V1 graph with OpenPipe ART integration.
    
    This function creates a LangGraph-compatible graph that can be used
    with langgraph dev and LangGraph Studio.
    """
    logger.info("Creating Atlas V1 graph with ART integration...")
    
    # Initialize model with ALWAYS-ON ART support
    logger.info("Initializing ART-wrapped model for automatic trajectory capture...")
    
    # Create ART-enabled model - ART is ALWAYS active
    # Supports:
    # - OpenRouter (via OPENROUTER_API_KEY)
    # - Anthropic (via ANTHROPIC_API_KEY) 
    # - OpenAI (via OPENAI_API_KEY)
    model = get_art_enabled_model()
    
    logger.info("🎯 OpenPipe ART is ACTIVE - All executions will be tracked")
    logger.info("📊 Trajectories will be saved for continuous learning")
    
    # Initialize MCP tools
    if MCP_IMPORT_SUCCESS:
        mcp_tools = _initialize_mcp_tools_sync()
        if mcp_tools:
            logger.info(f"✅ Successfully loaded {len(mcp_tools)} MCP tools for Atlas V1")
        else:
            logger.info("⚠️ No MCP tools loaded - Atlas V1 will use builtin tools only")
    else:
        logger.info("⚠️ MCP client module not available - using builtin tools only") 
        mcp_tools = {}
    
    # Convert MCP tools to list format for deepagents
    tools = list(mcp_tools.values()) if mcp_tools else []
    
    # Prepare sub-agents from Atlas configuration
    subagents = []
    for agent_config in AGENT_CONFIGS:
        subagent = SubAgent(
            name=agent_config["name"],
            description=agent_config["description"],
            prompt=agent_config["prompt"]
        )
        
        # Add tools if specified
        if "tools" in agent_config:
            subagent["tools"] = agent_config["tools"]
            
        subagents.append(subagent)
    
    # Create the deep agent graph with ART-enabled model
    # The model is already wrapped with ART, so trajectories are captured automatically
    graph = create_deep_agent(
        tools=tools,
        instructions=ORCHESTRATOR_PROMPT_V2,
        model=model,  # This model is already ART-wrapped with LoggingLLM
        subagents=subagents,
        state_schema=DeepAgentState
    )
    
    logger.info(f"✅ Created graph with {len(subagents)} sub-agents")
    logger.info("✅ ART trajectory capture is active via LoggingLLM model wrapper")
    
    # Initialize trajectory storage for statistics
    storage = get_trajectory_storage(
        base_dir=os.getenv("ART_TRAJECTORIES_DIR", ".art/trajectories"),
        max_size_mb=int(os.getenv("ART_MAX_SIZE_MB", "500")),
        max_age_days=int(os.getenv("ART_MAX_AGE_DAYS", "30"))
    )
    
    # Log storage statistics
    stats = storage.get_statistics()
    logger.info(f"📊 Trajectory storage: {stats.get('total_trajectories', 0)} existing trajectories")
    logger.info(f"   Storage location: {storage.base_dir}")
    
    # Note: We return the standard graph, not wrapped
    # ART capture happens at the model level via LoggingLLM
    return graph


# Create the graph instance that langgraph will use
graph = create_atlas_graph_with_art()

# Export for langgraph
__all__ = ['graph']


if __name__ == "__main__":
    # Test graph creation
    print("Testing Atlas V1 ART graph creation...")
    print(f"Graph type: {type(graph)}")
    print(f"Graph nodes: {graph.nodes if hasattr(graph, 'nodes') else 'N/A'}")
    print("\nTo run with LangGraph Studio:")
    print("  langgraph dev")
    print("\n🎯 OpenPipe ART is ALWAYS ACTIVE - no configuration needed!")
    print("\nOptional environment variables:")
    print("  ART_TRAJECTORIES_DIR=.art/trajectories  # Where to save trajectories")
    print("  ART_MAX_SIZE_MB=500                     # Max storage size")
    print("  ART_MAX_AGE_DAYS=30                     # Trajectory retention")
    print("  ART_PROJECT_NAME=atlas-v1-art           # Project identifier")
    print("\nRequired API keys:")
    print("  ANTHROPIC_API_KEY=your_key   # For Claude models")
    print("  OPENROUTER_API_KEY=your_key  # For OpenRouter models")