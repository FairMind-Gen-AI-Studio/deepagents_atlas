"""
Standardized Logging Configuration

Provides consistent logging setup across all agents.
"""

import logging
import sys
from typing import Optional


def setup_logging(
    level: str = "INFO",
    format_string: Optional[str] = None,
    agent_name: Optional[str] = None
) -> logging.Logger:
    """
    Setup standardized logging configuration.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        format_string: Custom format string (optional)
        agent_name: Agent name for logger (optional)

    Returns:
        Configured logger instance
    """
    if format_string is None:
        if agent_name:
            format_string = f'[{agent_name}] %(levelname)s: %(message)s'
        else:
            format_string = '%(levelname)s: %(message)s'

    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        stream=sys.stdout
    )

    logger = logging.getLogger(agent_name or __name__)
    return logger


def log_agent_startup(
    agent_name: str,
    model_info: dict,
    mcp_tools: Optional[dict],
    subagents: list
):
    """
    Log standardized agent startup information.

    Args:
        agent_name: Name of the agent
        model_info: Model configuration dict from get_model_info()
        mcp_tools: MCP tools dictionary (or None)
        subagents: List of subagent names
    """
    logger = logging.getLogger(agent_name)
    logger.info("=" * 70)
    logger.info(f"{agent_name.upper()} AGENT STARTUP")
    logger.info("=" * 70)
    logger.info(f"Model: {model_info['provider']} - {model_info['model']}")
    logger.info(f"Temperature: {model_info['temperature']}")
    logger.info(f"MCP Tools: {len(mcp_tools) if mcp_tools else 0}")
    logger.info(f"Subagents: {', '.join(subagents)}")
    logger.info("=" * 70)
