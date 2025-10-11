"""
Atlas V1 Custom Tools
Enhanced tool implementations for Atlas V1 that override deepagents defaults
with LangGraph Studio-compatible interrupt functionality.

UPGRADED: Now leverages the new upstream interrupt system for better human-in-the-loop support:
- Uses new interrupt_config in create_deep_agent for proper human approval workflow
- Simplifies tool implementations by delegating interrupt handling to upstream
- Better integration with LangGraph Studio and checkpointer support
- More robust state management and user interaction flows
"""

from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from typing import Optional, Literal, Annotated
import logging
from langgraph.prebuilt import InjectedState
from langgraph.types import Command
from deepagents.state import DeepAgentState

logger = logging.getLogger(__name__)


@tool  # Name is inferred from function name
def human_input(question: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    """
    Ask the user a question and wait for their response using the new upstream interrupt system.

    This enhanced version leverages the new deepagents interrupt system for:
    - Proper human-in-the-loop approval workflow
    - Better integration with LangGraph Studio
    - More robust state management
    - Support for approve/edit/respond actions

    The upstream interrupt system handles the complex logic of:
    - Detecting when human input is needed
    - Pausing execution until user responds
    - Resuming with user feedback

    Args:
        question: The question to ask the user
        tool_call_id: Injected tool call ID for state tracking

    Returns:
        Command object that triggers the interrupt workflow
    """
    logger.debug(f"[human_input] Called with question: {question}")

    # With the new upstream interrupt system, we simply trigger an interrupt
    # The interrupt system will handle all the complex logic of pausing execution,
    # waiting for user input, and resuming with the response

    # Create a message that will be processed by the interrupt system
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"USER_INPUT_REQUEST: {question}",
                    tool_call_id=tool_call_id
                )
            ]
        }
    )


@tool
def human_confirm(message: str, tool_call_id: Annotated[str, InjectedToolCallId], default: bool = False) -> Command:
    """
    Ask user for yes/no confirmation using the new upstream interrupt system.

    Enhanced confirmation tool for Atlas V1 that leverages the new deepagents interrupt system
    for better human-in-the-loop support.

    Args:
        message: The confirmation message to show the user
        default: Default value if no response (default: False)
        tool_call_id: Injected tool call ID for state tracking

    Returns:
        Command object that triggers the interrupt workflow
    """
    logger.info(f"[human_confirm] Asking for confirmation: {message}")

    # Use the new upstream interrupt system
    # The system will handle user interaction and return the response

    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"USER_CONFIRMATION_REQUEST: {message} (yes/no)",
                    tool_call_id=tool_call_id
                )
            ]
        }
    )


@tool
def human_input_multiline(question: str, tool_call_id: Annotated[str, InjectedToolCallId], placeholder: Optional[str] = None) -> Command:
    """
    Ask the user for potentially multi-line input using the new upstream interrupt system.

    Enhanced version that leverages the new deepagents interrupt system
    for better human-in-the-loop support.

    Args:
        question: The question or prompt for the user
        placeholder: Optional placeholder text to show as example
        tool_call_id: Injected tool call ID for state tracking

    Returns:
        Command object that triggers the interrupt workflow
    """
    logger.info(f"[human_input_multiline] Requesting multi-line input: {question}")

    # Prepare the prompt
    if placeholder:
        full_prompt = f"{question}\n(Example: {placeholder})"
    else:
        full_prompt = question

    # Use the new upstream interrupt system
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"USER_MULTILINE_REQUEST: {full_prompt}",
                    tool_call_id=tool_call_id
                )
            ]
        }
    )


@tool
def approve_plan(plan_content: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    """
    Request user approval for plans, requirements, or important decisions.

    This tool is specifically designed for approval requests where the user should have
    the option to approve, edit, or provide alternative feedback. Unlike human_input,
    this will show appropriate approval UI with buttons in the frontend.

    Use this for:
    - Requirements approval (discussion phase)
    - Technical plan approval (planning phase)
    - Any decision that needs explicit user confirmation

    Args:
        plan_content: The plan, requirements, or decision to be approved
        tool_call_id: Injected tool call ID for state tracking

    Returns:
        Command object that triggers the interrupt workflow with approval UI
    """
    logger.info(f"[approve_plan] Requesting approval for plan/requirements")

    # Use the new upstream interrupt system
    # The frontend will recognize this is NOT human_input and show full approval UI
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"APPROVAL_REQUEST: {plan_content}",
                    tool_call_id=tool_call_id
                )
            ]
        }
    )


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


# Export the tools for easy import
__all__ = ['human_input', 'human_confirm', 'human_input_multiline', 'approve_plan', 'read_phase_state', 'write_phase_state']


# Log initialization status
logger.info("Atlas tools initialized with new upstream interrupt system ✓")