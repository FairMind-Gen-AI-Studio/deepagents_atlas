"""
Atlas V1 Custom Tools

Phase-specific tools for Atlas V1. User interaction tools have been moved to
the shared library (fairmind.shared.interaction) and are re-exported here for
backward compatibility.

Atlas V1-specific tools:
- read_phase_state: Read current phase state information
- write_phase_state: Mark a phase as completed

Shared interaction tools (re-exported):
- human_input: Ask user questions
- human_confirm: Yes/no confirmations
- human_input_multiline: Multi-line text input
- approve_plan: Plan approval with edit capability
"""

from typing import Literal, Annotated
import logging
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from deepagents.state import DeepAgentState
from langchain_core.tools import InjectedToolCallId
from langchain_core.messages import ToolMessage

# Import user interaction tools from shared library
# These were originally defined here and have been extracted to fairmind.shared.interaction
# for reuse across all Fairmind agents (ArchQA, DocGen, etc.)
from fairmind.shared.interaction import (
    human_input,
    human_confirm,
    human_input_multiline,
    approve_plan,
)

logger = logging.getLogger(__name__)


# State management tools for phase tracking
# NOT decorated with @tool - will be wrapped by framework when needed
# This avoids JSON schema serialization issues with InjectedState

def read_phase_state(state: Annotated[DeepAgentState, InjectedState]) -> dict:
    """
    Read current phase state information.
    Used by orchestrator to determine next phase.
    """
    return {
        "current_phase": state.get("current_phase", None),
        "completed_phases": state.get("completed_phases", []),
        "investigation_complete": state.get("investigation_complete", False),
        "discussion_complete": state.get("discussion_complete", False),
        "planning_complete": state.get("planning_complete", False),
        "task_generation_complete": state.get("task_generation_complete", False)
    }

def write_phase_state(
    phase: Literal["investigation", "discussion", "planning", "task_generation"],
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """
    Mark a phase as completed.
    Used by sub-agents when they finish their phase.
    
    Args:
        phase: The phase that was completed
    """
    # Simple updates - phase is complete
    updates = {
        "current_phase": phase,
        f"{phase}_complete": True
    }
    
    # Add to completed_phases list
    completed_phases = state.get("completed_phases", [])
    if phase not in completed_phases:
        completed_phases.append(phase)
        updates["completed_phases"] = completed_phases
    
    # Return Command with state updates and tool message
    return Command(
        update={
            **updates,
            "messages": [
                ToolMessage(f"Phase '{phase}' marked as complete", tool_call_id=tool_call_id)
            ]
        }
    )


# Export the tools for easy import (re-exports shared interaction tools + Atlas-specific phase tools)
__all__ = [
    # Re-exported from fairmind.shared.interaction
    'human_input',
    'human_confirm',
    'human_input_multiline',
    'approve_plan',
    # Atlas V1-specific tools
    'read_phase_state',
    'write_phase_state'
]


# Log initialization status
logger.info("Atlas V1 tools loaded (interaction tools from shared library, phase tools local) ✓")