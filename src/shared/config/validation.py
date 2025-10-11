"""
Configuration Validation Utilities

Functions for validating agent configuration.
"""

import os
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


def validate_agent_config(agent_name: str, required_vars: List[str]) -> Dict[str, bool]:
    """
    Validate that required environment variables are set for an agent.

    Args:
        agent_name: Name of the agent (for logging)
        required_vars: List of required environment variable names

    Returns:
        Dictionary mapping variable name to whether it's set

    Example:
        >>> validation = validate_agent_config("Atlas V1", ["ANTHROPIC_API_KEY", "FAIRMIND_MCP_URL"])
        >>> if not all(validation.values()):
        ...     logger.warning("Missing required configuration")
    """
    validation = {}

    for var in required_vars:
        is_set = bool(os.getenv(var))
        validation[var] = is_set

        if not is_set:
            logger.warning(f"{agent_name}: Missing required environment variable {var}")

    return validation


def check_api_keys() -> Dict[str, bool]:
    """
    Check which API keys are configured.

    Returns:
        Dictionary with API key availability
    """
    return {
        "anthropic": bool(os.getenv("ANTHROPIC_API_KEY")),
        "openrouter": bool(os.getenv("OPENROUTER_API_KEY")),
        "openai": bool(os.getenv("OPENAI_API_KEY")),
        "tavily": bool(os.getenv("TAVILY_API_KEY")),
        "langsmith": bool(os.getenv("LANGCHAIN_API_KEY")),
    }


def check_mcp_config() -> Dict[str, bool]:
    """
    Check MCP configuration.

    Returns:
        Dictionary with MCP configuration status
    """
    return {
        "fairmind_url": bool(os.getenv("FAIRMIND_MCP_URL")),
        "fairmind_token": bool(os.getenv("FAIRMIND_MCP_TOKEN")),
    }
