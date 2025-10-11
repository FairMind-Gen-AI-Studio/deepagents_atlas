"""
Reward functions for Atlas V1 phases with OpenPipe ART.

This module provides reward calculation for different phases of the Atlas
methodology, enabling reinforcement learning optimization.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum

from .trajectory_capture import AgentTrajectory, PhaseType, ActionType

logger = logging.getLogger(__name__)


class RewardType(Enum):
    """Types of rewards in the system."""
    PHASE_COMPLETION = "phase_completion"
    CORRECTNESS = "correctness"
    EFFICIENCY = "efficiency"
    QUALITY = "quality"
    COMPLIANCE = "compliance"


@dataclass
class RewardSignal:
    """
    A single reward signal with explanation.
    """
    reward_type: RewardType
    value: float  # Typically between -1.0 and 1.0
    weight: float = 1.0
    explanation: str = ""
    
    def weighted_value(self) -> float:
        """Get weighted reward value."""
        return self.value * self.weight


class PhaseRewardCalculator:
    """
    Base class for phase-specific reward calculations.
    """
    
    def __init__(self, phase: PhaseType):
        self.phase = phase
        
    def calculate_reward(
        self,
        trajectory: AgentTrajectory,
        expected_outputs: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, List[RewardSignal]]:
        """
        Calculate reward for a trajectory.
        
        Args:
            trajectory: Agent execution trajectory
            expected_outputs: Optional expected outputs for evaluation
            
        Returns:
            Tuple of (total_reward, list_of_signals)
        """
        signals = []
        
        # Phase completion reward
        completion_signal = self._check_phase_completion(trajectory)
        signals.append(completion_signal)
        
        # Efficiency reward
        efficiency_signal = self._check_efficiency(trajectory)
        signals.append(efficiency_signal)
        
        # Quality reward
        quality_signal = self._check_quality(trajectory, expected_outputs)
        signals.append(quality_signal)
        
        # Calculate total reward
        total_reward = sum(s.weighted_value() for s in signals)
        
        return total_reward, signals
    
    def _check_phase_completion(self, trajectory: AgentTrajectory) -> RewardSignal:
        """Check if phase was completed successfully."""
        if self.phase in trajectory.phases_completed:
            return RewardSignal(
                reward_type=RewardType.PHASE_COMPLETION,
                value=1.0,
                weight=0.3,
                explanation=f"{self.phase.value} phase completed"
            )
        else:
            return RewardSignal(
                reward_type=RewardType.PHASE_COMPLETION,
                value=-0.5,
                weight=0.3,
                explanation=f"{self.phase.value} phase not completed"
            )
    
    def _check_efficiency(self, trajectory: AgentTrajectory) -> RewardSignal:
        """Check execution efficiency."""
        # Count tool calls and model responses
        tool_calls = sum(1 for step in trajectory.steps 
                        if step.action_type == ActionType.TOOL_CALL)
        model_calls = sum(1 for step in trajectory.steps 
                         if step.action_type == ActionType.MODEL_RESPONSE)
        
        # Efficiency based on step count (fewer is better, within reason)
        total_steps = len(trajectory.steps)
        
        if total_steps < 5:
            # Too few steps might indicate incomplete work
            value = 0.3
            explanation = "Very few steps - possibly incomplete"
        elif total_steps < 20:
            # Optimal range
            value = 1.0
            explanation = f"Efficient execution with {total_steps} steps"
        elif total_steps < 50:
            # Acceptable but could be more efficient
            value = 0.5
            explanation = f"Moderate efficiency with {total_steps} steps"
        else:
            # Too many steps
            value = -0.2
            explanation = f"Inefficient with {total_steps} steps"
            
        return RewardSignal(
            reward_type=RewardType.EFFICIENCY,
            value=value,
            weight=0.2,
            explanation=explanation
        )
    
    def _check_quality(
        self,
        trajectory: AgentTrajectory,
        expected_outputs: Optional[Dict[str, Any]] = None
    ) -> RewardSignal:
        """Check output quality - to be overridden by phase-specific classes."""
        return RewardSignal(
            reward_type=RewardType.QUALITY,
            value=0.0,
            weight=0.5,
            explanation="Base quality check"
        )


class InvestigationRewardCalculator(PhaseRewardCalculator):
    """
    Reward calculator for the Investigation phase.
    """
    
    def __init__(self):
        super().__init__(PhaseType.INVESTIGATION)
        
    def _check_quality(
        self,
        trajectory: AgentTrajectory,
        expected_outputs: Optional[Dict[str, Any]] = None
    ) -> RewardSignal:
        """
        Check investigation quality based on:
        - Coverage of project aspects
        - Use of appropriate MCP tools
        - Generation of investigation_findings.md
        """
        # Check for MCP tool usage
        mcp_tools_used = set()
        for step in trajectory.steps:
            if step.action_type == ActionType.TOOL_CALL:
                tool_name = step.content.get("tool_name", "")
                if "mcp__fairmind" in tool_name:
                    mcp_tools_used.add(tool_name)
        
        # Check for key investigation tools
        key_tools = [
            "General_list_projects",
            "Studio_list_user_stories",
            "Code_list_repositories"
        ]
        
        tools_coverage = sum(1 for tool in key_tools 
                            if any(tool in used for used in mcp_tools_used))
        
        # Check for output file
        has_findings = False
        if trajectory.final_output:
            files = trajectory.final_output.get("files", {})
            has_findings = "investigation_findings.md" in files
        
        # Calculate quality score
        if has_findings and tools_coverage >= 2:
            value = 1.0
            explanation = "Comprehensive investigation with good tool usage"
        elif has_findings:
            value = 0.6
            explanation = "Investigation complete but limited tool usage"
        elif tools_coverage >= 2:
            value = 0.3
            explanation = "Good tool usage but missing findings file"
        else:
            value = -0.3
            explanation = "Incomplete investigation"
            
        return RewardSignal(
            reward_type=RewardType.QUALITY,
            value=value,
            weight=0.5,
            explanation=explanation
        )


class DiscussionRewardCalculator(PhaseRewardCalculator):
    """
    Reward calculator for the Discussion phase.
    """
    
    def __init__(self):
        super().__init__(PhaseType.DISCUSSION)
        
    def _check_quality(
        self,
        trajectory: AgentTrajectory,
        expected_outputs: Optional[Dict[str, Any]] = None
    ) -> RewardSignal:
        """
        Check discussion quality based on:
        - Generation of clarification questions
        - User interaction via human_input
        - Creation of requirements_clarified.md
        """
        # Check for human_input usage
        human_interactions = sum(1 for step in trajectory.steps
                               if step.action_type == ActionType.TOOL_CALL
                               and step.content.get("tool_name") == "human_input")
        
        # Check for output files
        has_questions = False
        has_responses = False
        has_requirements = False
        
        if trajectory.final_output:
            files = trajectory.final_output.get("files", {})
            has_questions = "clarification_questions.md" in files
            has_responses = "user_responses.md" in files
            has_requirements = "requirements_clarified.md" in files
        
        # Calculate quality score
        if has_requirements and human_interactions > 0:
            value = 1.0
            explanation = "Complete discussion with user interaction"
        elif has_questions and has_responses:
            value = 0.7
            explanation = "Good discussion but missing final requirements"
        elif human_interactions > 0:
            value = 0.4
            explanation = "User interaction but incomplete outputs"
        else:
            value = -0.5
            explanation = "No user interaction in discussion phase"
            
        return RewardSignal(
            reward_type=RewardType.QUALITY,
            value=value,
            weight=0.5,
            explanation=explanation
        )


class PlanningRewardCalculator(PhaseRewardCalculator):
    """
    Reward calculator for the Planning phase.
    """
    
    def __init__(self):
        super().__init__(PhaseType.PLANNING)
        
    def _check_quality(
        self,
        trajectory: AgentTrajectory,
        expected_outputs: Optional[Dict[str, Any]] = None
    ) -> RewardSignal:
        """
        Check planning quality based on:
        - Repository analysis depth
        - Use of sub-agents for parallel analysis
        - Generation of implementation_plan.md
        """
        # Check for sub-agent usage
        sub_agent_calls = sum(1 for step in trajectory.steps
                             if step.action_type == ActionType.SUB_AGENT_CALL)
        
        # Check for code analysis tools
        code_tools_used = sum(1 for step in trajectory.steps
                             if step.action_type == ActionType.TOOL_CALL
                             and "Code_" in step.content.get("tool_name", ""))
        
        # Check for output file
        has_plan = False
        if trajectory.final_output:
            files = trajectory.final_output.get("files", {})
            has_plan = "implementation_plan.md" in files
        
        # Calculate quality score
        if has_plan and sub_agent_calls >= 2 and code_tools_used >= 3:
            value = 1.0
            explanation = "Comprehensive planning with parallel analysis"
        elif has_plan and (sub_agent_calls > 0 or code_tools_used > 0):
            value = 0.6
            explanation = "Planning complete with some analysis"
        elif has_plan:
            value = 0.3
            explanation = "Basic plan without deep analysis"
        else:
            value = -0.3
            explanation = "Planning phase incomplete"
            
        return RewardSignal(
            reward_type=RewardType.QUALITY,
            value=value,
            weight=0.5,
            explanation=explanation
        )


class TaskGenerationRewardCalculator(PhaseRewardCalculator):
    """
    Reward calculator for the Task Generation phase.
    """
    
    def __init__(self):
        super().__init__(PhaseType.TASK_GENERATION)
        
    def _check_quality(
        self,
        trajectory: AgentTrajectory,
        expected_outputs: Optional[Dict[str, Any]] = None
    ) -> RewardSignal:
        """
        Check task generation quality based on:
        - Clear task structure
        - Repository-task mapping
        - Generation of implementation_tasks.md
        """
        # Check for output file
        has_tasks = False
        task_content = ""
        
        if trajectory.final_output:
            files = trajectory.final_output.get("files", {})
            has_tasks = "implementation_tasks.md" in files
            if has_tasks:
                task_content = files.get("implementation_tasks.md", "")
        
        # Check task structure quality
        has_structure = False
        has_repo_mapping = False
        
        if task_content:
            # Check for task structure markers
            has_structure = all(marker in task_content.lower() 
                              for marker in ["task", "repository", "description"])
            # Check for repository references
            has_repo_mapping = "repository:" in task_content.lower()
        
        # Calculate quality score
        if has_tasks and has_structure and has_repo_mapping:
            value = 1.0
            explanation = "Well-structured tasks with repository mapping"
        elif has_tasks and has_structure:
            value = 0.7
            explanation = "Good task structure but missing repository mapping"
        elif has_tasks:
            value = 0.4
            explanation = "Tasks generated but structure needs improvement"
        else:
            value = -0.3
            explanation = "Task generation incomplete"
            
        return RewardSignal(
            reward_type=RewardType.QUALITY,
            value=value,
            weight=0.5,
            explanation=explanation
        )


class CompositeRewardCalculator:
    """
    Calculates composite rewards across all phases.
    """
    
    def __init__(self):
        self.phase_calculators = {
            PhaseType.INVESTIGATION: InvestigationRewardCalculator(),
            PhaseType.DISCUSSION: DiscussionRewardCalculator(),
            PhaseType.PLANNING: PlanningRewardCalculator(),
            PhaseType.TASK_GENERATION: TaskGenerationRewardCalculator()
        }
        
    def calculate_trajectory_reward(
        self,
        trajectory: AgentTrajectory,
        expected_outputs: Optional[Dict[str, Any]] = None
    ) -> Tuple[float, Dict[str, Any]]:
        """
        Calculate overall reward for a complete trajectory.
        
        Args:
            trajectory: Complete agent trajectory
            expected_outputs: Optional expected outputs
            
        Returns:
            Tuple of (total_reward, detailed_breakdown)
        """
        phase_rewards = {}
        all_signals = []
        
        # Calculate rewards for each phase completed
        for phase in trajectory.phases_completed:
            if phase in self.phase_calculators:
                calculator = self.phase_calculators[phase]
                reward, signals = calculator.calculate_reward(
                    trajectory, expected_outputs
                )
                phase_rewards[phase.value] = {
                    "reward": reward,
                    "signals": [
                        {
                            "type": s.reward_type.value,
                            "value": s.value,
                            "weight": s.weight,
                            "explanation": s.explanation
                        }
                        for s in signals
                    ]
                }
                all_signals.extend(signals)
        
        # Calculate overall reward
        total_reward = sum(s.weighted_value() for s in all_signals)
        
        # Add bonus for completing all phases
        if len(trajectory.phases_completed) == 4:
            total_reward += 1.0
            phase_rewards["completion_bonus"] = 1.0
        
        # Add efficiency penalty for very long executions
        if trajectory.duration() and trajectory.duration() > 300:  # 5 minutes
            total_reward -= 0.5
            phase_rewards["time_penalty"] = -0.5
        
        return total_reward, {
            "total_reward": total_reward,
            "phase_rewards": phase_rewards,
            "phases_completed": [p.value for p in trajectory.phases_completed],
            "duration": trajectory.duration(),
            "step_count": len(trajectory.steps)
        }
    
    def calculate_batch_rewards(
        self,
        trajectories: List[AgentTrajectory]
    ) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Calculate rewards for a batch of trajectories.
        
        Args:
            trajectories: List of trajectories to evaluate
            
        Returns:
            List of (reward, breakdown) tuples
        """
        results = []
        for trajectory in trajectories:
            reward, breakdown = self.calculate_trajectory_reward(trajectory)
            results.append((reward, breakdown))
            
        logger.info(f"Calculated rewards for {len(trajectories)} trajectories")
        return results