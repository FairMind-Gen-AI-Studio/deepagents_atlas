# Atlas V1 State Management
# Properly typed state schema following DeepAgents patterns

from typing import Literal, NotRequired, Optional, Dict, List, Any
from deepagents.state import DeepAgentState

class AtlasState(DeepAgentState):
    """
    Atlas V1 state schema extending DeepAgentState.
    
    This provides typed state management for the 4-phase Atlas methodology,
    eliminating the need for custom state dictionaries and ensuring
    atomic updates through Command objects.
    
    Inherits from DeepAgentState:
    - todos: List of todo items with status tracking
    - files: Virtual filesystem for context management (replaces virtual_filesystem)
    - messages: Conversation history (from AgentState)
    """
    
    # Phase management
    current_phase: NotRequired[Literal["investigation", "discussion", "planning", "task_generation"]]
    completed_phases: NotRequired[List[Literal["investigation", "discussion", "planning", "task_generation"]]]
    
    # Project context
    project_id: NotRequired[Optional[str]]
    user_story_id: NotRequired[Optional[str]]
    
    # Completion tracking
    completion_percentage: NotRequired[int]
    investigation_complete: NotRequired[bool]
    discussion_complete: NotRequired[bool]
    planning_complete: NotRequired[bool]
    task_generation_complete: NotRequired[bool]
    
    # Phase outputs and validation
    phase_outputs: NotRequired[Dict[str, Any]]
    validation_status: NotRequired[Dict[str, Dict[str, Any]]]
    
    # Context management
    context_summary: NotRequired[str]
    
    # Note: The 'files' field from DeepAgentState replaces the custom 'virtual_filesystem'
    # All file operations should use the inherited 'files' field