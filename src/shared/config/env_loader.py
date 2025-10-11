"""
Environment Variable Loading Utilities

Helper functions for loading agent-specific configuration from environment variables.
"""

import os
from typing import Optional, Any
from dotenv import load_dotenv


def load_agent_config(agent_prefix: str) -> dict:
    """
    Load agent-specific configuration from environment variables.

    Args:
        agent_prefix: Agent prefix (e.g., "ATLAS", "DOCGEN", "ARCHQA")

    Returns:
        Dictionary with agent configuration
    """
    load_dotenv()

    return {
        "model_name": get_agent_env_var(agent_prefix, "MODEL_NAME", ""),
        "temperature": float(get_agent_env_var(agent_prefix, "MODEL_TEMPERATURE", "0.7")),
        "max_tokens": int(get_agent_env_var(agent_prefix, "MODEL_MAX_TOKENS", "8192")),
        "debug_mode": get_agent_env_var(agent_prefix, "DEBUG_MODE", "false").lower() == "true",
    }


def get_agent_env_var(
    agent_prefix: str,
    var_name: str,
    default: Any = None,
    fallback_to_global: bool = True
) -> Any:
    """
    Get environment variable with agent-specific override support.

    Looks for {AGENT_PREFIX}_{VAR_NAME} first, then VAR_NAME, then default.

    Args:
        agent_prefix: Agent prefix (e.g., "ATLAS")
        var_name: Variable name (e.g., "MODEL_NAME")
        default: Default value if not found
        fallback_to_global: Whether to check global VAR_NAME if agent-specific not found

    Returns:
        Environment variable value or default

    Example:
        >>> get_agent_env_var("ATLAS", "MODEL_NAME", "claude-3-5-sonnet")
        # Checks: ATLAS_MODEL_NAME -> MODEL_NAME -> "claude-3-5-sonnet"
    """
    # Try agent-specific variable first
    agent_var = f"{agent_prefix}_{var_name}"
    value = os.getenv(agent_var)

    if value is not None:
        return value

    # Fall back to global variable
    if fallback_to_global:
        value = os.getenv(var_name)
        if value is not None:
            return value

    # Return default
    return default
