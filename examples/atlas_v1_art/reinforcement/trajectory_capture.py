"""
Trajectory capture system for Atlas V1 with OpenPipe ART.

This module provides functionality to capture, store, and manage
trajectories from Atlas agent executions across all phases.
"""

import json
import jsonlines
import logging
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
from enum import Enum

logger = logging.getLogger(__name__)


class PhaseType(Enum):
    """Atlas V1 phases."""
    INVESTIGATION = "investigation"
    DISCUSSION = "discussion"
    PLANNING = "planning"
    TASK_GENERATION = "task_generation"


class ActionType(Enum):
    """Types of actions in a trajectory."""
    TOOL_CALL = "tool_call"
    MODEL_RESPONSE = "model_response"
    SUB_AGENT_CALL = "sub_agent_call"
    PHASE_TRANSITION = "phase_transition"
    USER_INPUT = "user_input"


@dataclass
class TrajectoryStep:
    """
    Represents a single step in an agent trajectory.
    """
    timestamp: float
    action_type: ActionType
    phase: Optional[PhaseType]
    content: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "timestamp": self.timestamp,
            "action_type": self.action_type.value,
            "phase": self.phase.value if self.phase else None,
            "content": self.content,
            "metadata": self.metadata
        }


@dataclass
class AgentTrajectory:
    """
    Complete trajectory for an Atlas agent execution.
    """
    trajectory_id: str
    start_time: float
    end_time: Optional[float] = None
    steps: List[TrajectoryStep] = field(default_factory=list)
    phases_completed: List[PhaseType] = field(default_factory=list)
    final_output: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_step(self, step: TrajectoryStep):
        """Add a step to the trajectory."""
        self.steps.append(step)
        
    def complete(self, final_output: Dict[str, Any]):
        """Mark trajectory as complete."""
        self.end_time = time.time()
        self.final_output = final_output
        
    def duration(self) -> Optional[float]:
        """Calculate trajectory duration in seconds."""
        if self.end_time:
            return self.end_time - self.start_time
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "trajectory_id": self.trajectory_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration(),
            "steps": [step.to_dict() for step in self.steps],
            "phases_completed": [phase.value for phase in self.phases_completed],
            "final_output": self.final_output,
            "metadata": self.metadata,
            "step_count": len(self.steps)
        }


class TrajectoryCapture:
    """
    Captures and manages trajectories for Atlas agent executions.
    """
    
    def __init__(self, storage_dir: Optional[Path] = None):
        """
        Initialize trajectory capture.
        
        Args:
            storage_dir: Directory to store trajectory files
        """
        self.storage_dir = storage_dir or Path("trajectories")
        self.storage_dir.mkdir(exist_ok=True)
        self.current_trajectory: Optional[AgentTrajectory] = None
        self.current_phase: Optional[PhaseType] = None
        
    def start_trajectory(self, trajectory_id: Optional[str] = None) -> AgentTrajectory:
        """
        Start capturing a new trajectory.
        
        Args:
            trajectory_id: Optional ID for the trajectory
            
        Returns:
            New trajectory instance
        """
        if trajectory_id is None:
            trajectory_id = f"trajectory_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        self.current_trajectory = AgentTrajectory(
            trajectory_id=trajectory_id,
            start_time=time.time()
        )
        
        logger.info(f"Started trajectory capture: {trajectory_id}")
        return self.current_trajectory
    
    def set_phase(self, phase: Union[PhaseType, str]):
        """
        Set the current phase for trajectory tracking.
        
        Args:
            phase: Current phase (PhaseType or string)
        """
        if isinstance(phase, str):
            phase = PhaseType(phase)
            
        self.current_phase = phase
        
        if self.current_trajectory and phase not in self.current_trajectory.phases_completed:
            self.current_trajectory.phases_completed.append(phase)
            
        logger.debug(f"Set trajectory phase: {phase.value}")
    
    def capture_tool_call(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        execution_time: float
    ):
        """
        Capture a tool call in the trajectory.
        
        Args:
            tool_name: Name of the tool called
            tool_input: Input provided to the tool
            tool_output: Output from the tool
            execution_time: Time taken to execute the tool
        """
        if not self.current_trajectory:
            logger.warning("No active trajectory for tool call capture")
            return
            
        step = TrajectoryStep(
            timestamp=time.time(),
            action_type=ActionType.TOOL_CALL,
            phase=self.current_phase,
            content={
                "tool_name": tool_name,
                "input": tool_input,
                "output": tool_output
            },
            metadata={
                "execution_time": execution_time
            }
        )
        
        self.current_trajectory.add_step(step)
        logger.debug(f"Captured tool call: {tool_name}")
    
    def capture_model_response(
        self,
        prompt: str,
        response: str,
        model_name: str,
        tokens_used: Optional[Dict[str, int]] = None
    ):
        """
        Capture a model response in the trajectory.
        
        Args:
            prompt: Prompt sent to the model
            response: Response from the model
            model_name: Name of the model used
            tokens_used: Token usage statistics
        """
        if not self.current_trajectory:
            logger.warning("No active trajectory for model response capture")
            return
            
        step = TrajectoryStep(
            timestamp=time.time(),
            action_type=ActionType.MODEL_RESPONSE,
            phase=self.current_phase,
            content={
                "prompt": prompt[:500],  # Truncate for storage efficiency
                "response": response,
                "model": model_name
            },
            metadata={
                "tokens": tokens_used or {},
                "prompt_length": len(prompt),
                "response_length": len(response)
            }
        )
        
        self.current_trajectory.add_step(step)
        logger.debug(f"Captured model response from {model_name}")
    
    def capture_sub_agent_call(
        self,
        agent_name: str,
        task_description: str,
        result: Any,
        sub_trajectory: Optional['AgentTrajectory'] = None
    ):
        """
        Capture a sub-agent invocation.
        
        Args:
            agent_name: Name of the sub-agent
            task_description: Task given to the sub-agent
            result: Result from the sub-agent
            sub_trajectory: Optional nested trajectory from sub-agent
        """
        if not self.current_trajectory:
            logger.warning("No active trajectory for sub-agent capture")
            return
            
        step = TrajectoryStep(
            timestamp=time.time(),
            action_type=ActionType.SUB_AGENT_CALL,
            phase=self.current_phase,
            content={
                "agent_name": agent_name,
                "task": task_description,
                "result": result
            },
            metadata={
                "has_sub_trajectory": sub_trajectory is not None
            }
        )
        
        if sub_trajectory:
            step.metadata["sub_trajectory_id"] = sub_trajectory.trajectory_id
            step.metadata["sub_steps"] = len(sub_trajectory.steps)
            
        self.current_trajectory.add_step(step)
        logger.debug(f"Captured sub-agent call: {agent_name}")
    
    def capture_phase_transition(self, from_phase: str, to_phase: str, reason: str):
        """
        Capture a phase transition.
        
        Args:
            from_phase: Previous phase
            to_phase: New phase
            reason: Reason for transition
        """
        if not self.current_trajectory:
            logger.warning("No active trajectory for phase transition capture")
            return
            
        step = TrajectoryStep(
            timestamp=time.time(),
            action_type=ActionType.PHASE_TRANSITION,
            phase=self.current_phase,
            content={
                "from_phase": from_phase,
                "to_phase": to_phase,
                "reason": reason
            },
            metadata={}
        )
        
        self.current_trajectory.add_step(step)
        logger.info(f"Captured phase transition: {from_phase} -> {to_phase}")
    
    def complete_trajectory(self, final_output: Dict[str, Any]) -> AgentTrajectory:
        """
        Complete the current trajectory.
        
        Args:
            final_output: Final output from the agent
            
        Returns:
            Completed trajectory
        """
        if not self.current_trajectory:
            raise ValueError("No active trajectory to complete")
            
        self.current_trajectory.complete(final_output)
        trajectory = self.current_trajectory
        
        # Save to disk
        self.save_trajectory(trajectory)
        
        # Clear current trajectory
        self.current_trajectory = None
        self.current_phase = None
        
        logger.info(f"Completed trajectory: {trajectory.trajectory_id}")
        return trajectory
    
    def save_trajectory(self, trajectory: AgentTrajectory):
        """
        Save trajectory to disk.
        
        Args:
            trajectory: Trajectory to save
        """
        filepath = self.storage_dir / f"{trajectory.trajectory_id}.jsonl"
        
        with jsonlines.open(filepath, mode='w') as writer:
            writer.write(trajectory.to_dict())
            
        logger.info(f"Saved trajectory to {filepath}")
    
    def load_trajectory(self, trajectory_id: str) -> Optional[AgentTrajectory]:
        """
        Load a trajectory from disk.
        
        Args:
            trajectory_id: ID of trajectory to load
            
        Returns:
            Loaded trajectory or None if not found
        """
        filepath = self.storage_dir / f"{trajectory_id}.jsonl"
        
        if not filepath.exists():
            logger.warning(f"Trajectory file not found: {filepath}")
            return None
            
        with jsonlines.open(filepath) as reader:
            data = next(reader)
            
        # Reconstruct trajectory from data
        trajectory = AgentTrajectory(
            trajectory_id=data["trajectory_id"],
            start_time=data["start_time"],
            end_time=data.get("end_time"),
            final_output=data.get("final_output"),
            metadata=data.get("metadata", {})
        )
        
        # Reconstruct phases
        for phase_name in data.get("phases_completed", []):
            trajectory.phases_completed.append(PhaseType(phase_name))
            
        # Reconstruct steps
        for step_data in data.get("steps", []):
            step = TrajectoryStep(
                timestamp=step_data["timestamp"],
                action_type=ActionType(step_data["action_type"]),
                phase=PhaseType(step_data["phase"]) if step_data.get("phase") else None,
                content=step_data["content"],
                metadata=step_data.get("metadata", {})
            )
            trajectory.steps.append(step)
            
        logger.info(f"Loaded trajectory: {trajectory_id}")
        return trajectory
    
    def list_trajectories(self) -> List[str]:
        """
        List all saved trajectory IDs.
        
        Returns:
            List of trajectory IDs
        """
        trajectories = []
        for filepath in self.storage_dir.glob("*.jsonl"):
            trajectories.append(filepath.stem)
        return sorted(trajectories)