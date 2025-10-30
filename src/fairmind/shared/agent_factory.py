"""
Shared Agent Factory for Lazy MCP Tools Initialization

This module provides a factory pattern for creating LangGraph agents with
MCP tools loaded from state cache. Solves the "agent compiled at boot without
tools" problem by creating agents on-demand with user-specific MCP credentials.

Problem:
    When agents are compiled at module import time (e.g., `agent = create_agent(None)`),
    they get compiled without MCP tools because:
    1. No user credentials available at boot
    2. MCP tools are loaded into state.mcp_tools_cache only when first request arrives
    3. LangGraph is already compiled, can't use tools even if cache is populated

Solution:
    Export a factory function instead of compiled agent:
    - Factory receives state (with mcp_tools_cache)
    - Creates fresh agent with tools from cache
    - Caches compiled agent to avoid recompilation overhead
    - Router calls factory with state to get agent instance

Usage:
    # In agent file (docgen_agent.py, archqa_agent.py):
    from fairmind.shared.agent_factory import create_stateful_agent_factory

    # Create agent creation function
    def create_my_agent(mcp_tools: Optional[Dict[str, Any]] = None):
        # ... agent logic with mcp_tools
        return compiled_langgraph_agent

    # Export factory instead of compiled agent
    agent = create_stateful_agent_factory(
        agent_creator=create_my_agent,
        agent_name="MyAgent"
    )

    # Router will detect factory and call: agent_instance = agent(state)
"""

from typing import Callable, Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


def create_stateful_agent_factory(
    agent_creator: Callable[[Optional[Dict[str, Any]]], Any],
    agent_name: str,
    cache_compiled: bool = True
) -> Callable:
    """
    Create a factory function that produces agents with MCP tools from state.

    This factory solves the "tools unavailable at boot" problem by deferring
    agent compilation until runtime when MCP tools are available in state cache.

    Args:
        agent_creator: Function that creates the agent.
                      Signature: (mcp_tools: Optional[Dict]) -> compiled_agent
                      Example: create_langgraph_agent, create_archqa_agent
        agent_name: Agent name for logging (e.g., "DocGen", "ArchQA")
        cache_compiled: If True, cache the compiled agent with tools (default: True).
                       Avoids recompilation overhead on subsequent calls.
                       Recompiles only if tool count changes.

    Returns:
        Factory function with signature: (state: dict) -> compiled_agent

        The factory function:
        - Extracts mcp_tools_cache from state
        - Calls agent_creator with those tools
        - Caches compiled agent for reuse
        - Returns compiled agent ready for ainvoke()

    Flow:
        1. Router loads agent module: agent = create_stateful_agent_factory(...)
        2. Router receives first request from user with API key
        3. Router initializes MCP tools into state.mcp_tools_cache
        4. Router wrapper detects factory: hasattr(agent, 'is_agent_factory')
        5. Router calls: agent_instance = agent(state)  # Factory creates agent
        6. Factory caches agent for subsequent calls
        7. Router invokes: result = await agent_instance.ainvoke(state)

    Example:
        >>> # In docgen_agent.py:
        >>> def create_langgraph_agent(mcp_tools):
        ...     discovery_tools = DOCGEN_DISCOVERY_FILTER(mcp_tools)
        ...     # ... create agent with tools
        ...     return compiled_agent
        >>>
        >>> agent = create_stateful_agent_factory(
        ...     agent_creator=create_langgraph_agent,
        ...     agent_name="DocGen"
        ... )
        >>>
        >>> # In router_graph.py wrapper:
        >>> if hasattr(agent, 'is_agent_factory'):
        ...     agent_instance = agent(state)  # Call factory with state
        ...     result = await agent_instance.ainvoke(state)
    """
    # Closure variables for caching
    _cached_agent = None
    _cached_tool_count = None

    def factory(state: dict) -> Any:
        """
        Factory function that creates agent with MCP tools from state cache.

        Args:
            state: LangGraph state dict containing mcp_tools_cache field.
                  Expected structure:
                  {
                      "mcp_tools_cache": {
                          "mcp__fairmind__General_list_projects": <tool>,
                          "mcp__fairmind__Code_search": <tool>,
                          ...
                      },
                      "messages": [...],
                      "user_api_key": "...",
                      ...
                  }

        Returns:
            Compiled LangGraph agent with MCP tools assigned to subagents.
            Ready to be invoked with: await agent.ainvoke(state)

        Caching behavior:
            - First call: Creates and caches agent
            - Subsequent calls: Reuses cached agent if tool count unchanged
            - Tool count change: Recompiles and updates cache
        """
        nonlocal _cached_agent, _cached_tool_count

        # Extract MCP tools from state cache
        mcp_tools_cache = state.get('mcp_tools_cache')
        tool_count = len(mcp_tools_cache) if isinstance(mcp_tools_cache, dict) else 0

        # Check if we can reuse cached compiled agent
        if cache_compiled and _cached_agent is not None:
            if tool_count == _cached_tool_count:
                logger.debug(f"♻️  [{agent_name}] Reusing cached compiled agent ({tool_count} tools)")
                return _cached_agent
            else:
                logger.info(f"🔄 [{agent_name}] Tool count changed ({_cached_tool_count} -> {tool_count}), recompiling agent")

        # Create fresh agent with tools from cache
        logger.info(f"🏗️  [{agent_name}] Creating agent with {tool_count} MCP tools from state cache")

        try:
            compiled_agent = agent_creator(mcp_tools_cache)
        except Exception as e:
            logger.error(f"❌ [{agent_name}] Failed to create agent: {e}", exc_info=True)
            raise

        # Cache for future calls (avoid recompilation overhead)
        if cache_compiled:
            _cached_agent = compiled_agent
            _cached_tool_count = tool_count
            logger.debug(f"💾 [{agent_name}] Cached compiled agent for reuse")

        return compiled_agent

    # Add metadata for router detection and debugging
    factory.__name__ = f"{agent_name}_factory"
    factory.__doc__ = f"Factory for creating {agent_name} agent with MCP tools from state"
    factory.agent_name = agent_name
    factory.is_agent_factory = True  # Router checks this flag

    return factory
