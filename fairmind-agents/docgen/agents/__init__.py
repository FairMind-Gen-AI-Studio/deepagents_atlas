# DocGen Agents Module
# Exports all phase agents for the DocGen methodology

from .discovery_agent import discovery_agent, get_discovery_tools
from .scoping_agent import scoping_agent, get_scoping_tools, SCOPING_PROMPT  # Export prompt for middleware usage
from .analysis_agent import analysis_agent, get_analysis_tools
from .clarification_agent import clarification_agent, get_clarification_tools, CLARIFICATION_PROMPT  # Export prompt for middleware usage
from .generation_agent import generation_agent, get_generation_tools

__all__ = [
    # Agent configurations
    "discovery_agent",
    "scoping_agent",
    "analysis_agent",
    "clarification_agent",
    "generation_agent",
    # Tool filter functions
    "get_discovery_tools",
    "get_scoping_tools",
    "get_analysis_tools",
    "get_clarification_tools",
    "get_generation_tools",
    # Prompts for agents that need middleware-based interrupts
    "SCOPING_PROMPT",
    "CLARIFICATION_PROMPT",
]
