# Atlas V1 Agent Package

from .atlas_agent import create_atlas_agent, AtlasAgentV1
from .mcp_tools import create_mcp_wrapper, MCPToolsWrapper
from .subagents import (
    AGENT_CONFIGS,
    PHASE_DEFINITIONS,
    get_agent_config,
    get_phase_definition,
    validate_phase_completion,
    get_next_phase
)

__version__ = "1.0.0"
__all__ = [
    "create_atlas_agent",
    "AtlasAgentV1",
    "create_mcp_wrapper", 
    "MCPToolsWrapper",
    "AGENT_CONFIGS",
    "PHASE_DEFINITIONS",
    "get_agent_config",
    "get_phase_definition",
    "validate_phase_completion",
    "get_next_phase"
]