"""
Agent Loading Utility

Provides clean agent module loading with sys.path management.
"""

import sys
import importlib.util
from pathlib import Path
from typing import Any


def load_agent_from_file(agent_name: str, file_path: Path) -> Any:
    """
    Load an agent module directly from file to avoid sys.path conflicts.

    Args:
        agent_name: Name for the agent module
        file_path: Path to agent's main Python file

    Returns:
        Compiled agent instance from module.agent
    """
    spec = importlib.util.spec_from_file_location(agent_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {agent_name} from {file_path}")

    module = importlib.util.module_from_spec(spec)

    # Save current sys.path state
    agent_dir = str(file_path.parent)
    old_path = sys.path.copy()
    old_modules = set(sys.modules.keys())

    # Add agent directory temporarily for its dependencies
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)

    try:
        spec.loader.exec_module(module)
        agent_instance = module.agent

        # Clean up sys.modules - remove agent-specific modules
        new_modules = set(sys.modules.keys()) - old_modules
        keep_modules = {agent_name, 'langgraph', 'langchain', 'deepagents', 'shared'}

        for mod_name in new_modules:
            if not any(mod_name.startswith(keep) for keep in keep_modules):
                # Remove potentially conflicting modules
                if mod_name in ['agents', 'subagents', 'prompts', 'mcp_tools', 'mcp_client', 'model_config']:
                    sys.modules.pop(mod_name, None)

        return agent_instance
    finally:
        # Restore sys.path
        sys.path = old_path
