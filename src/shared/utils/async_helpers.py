"""
Async/Sync Helper Utilities

Common patterns for wrapping async functions for sync contexts.
"""

import asyncio
import logging
from typing import Any, Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


def run_async_in_sync_context(
    async_func: Callable[..., T],
    *args,
    **kwargs
) -> Optional[T]:
    """
    Run an async function in a synchronous context.

    Handles event loop creation and running/already-running scenarios.

    Args:
        async_func: Async function to execute
        *args: Positional arguments for async_func
        **kwargs: Keyword arguments for async_func

    Returns:
        Result of async_func, or None if execution fails
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    if loop.is_running():
        logger.warning(f"Event loop already running - cannot execute {async_func.__name__} synchronously")
        return None
    else:
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        except Exception as e:
            logger.error(f"Failed to execute {async_func.__name__}: {e}")
            return None


def initialize_mcp_tools_sync():
    """
    Synchronous wrapper for MCP tools initialization.

    Returns:
        Dictionary of MCP tools, or None if initialization fails
    """
    from shared.mcp.client import initialize_mcp_tools
    return run_async_in_sync_context(initialize_mcp_tools)
