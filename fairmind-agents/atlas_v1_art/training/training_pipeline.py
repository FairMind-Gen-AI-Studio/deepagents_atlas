"""
Training pipeline for Atlas V1 with OpenPipe ART.

This module provides the infrastructure for training Atlas agents
using reinforcement learning with trajectory rollouts.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from tqdm import tqdm

from ..reinforcement.trajectory_capture import (
    TrajectoryCapture,
    AgentTrajectory,
    PhaseType
)
from ..reinforcement.reward_functions import CompositeRewardCalculator

logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """
    Configuration for training pipeline.
    """
    num_rollouts: int = 100
    batch_size: int = 10
    learning_rate: float = 0.001
    temperature_decay: float = 0.95
    initial_temperature: float = 0.7
    min_temperature: float = 0.1
    reward_threshold: float = 3.0  # Stop training if average reward exceeds this
    checkpoint_interval: int = 10
    output_dir: Path = field(default_factory=lambda: Path("training_outputs"))
    trajectories_dir: Path = field(default_factory=lambda: Path("trajectories"))
    use_cached_trajectories: bool = False
    verbose: bool = True


@dataclass
class TrainingMetrics:
    """
    Metrics collected during training.
    """
    rollout_rewards: List[float] = field(default_factory=list)
    phase_success_rates: Dict[str, float] = field(default_factory=dict)
    average_duration: float = 0.0
    average_steps: float = 0.0
    best_reward: float = float('-inf')
    best_trajectory_id: Optional[str] = None
    convergence_epoch: Optional[int] = None


class TrainingPipeline:
    """
    Manages the training pipeline for Atlas V1 agents.
    """
    
    def __init__(
        self,
        agent_factory: callable,
        config: Optional[TrainingConfig] = None
    ):
        """
        Initialize training pipeline.
        
        Args:
            agent_factory: Callable that creates an Atlas agent instance
            config: Training configuration
        """
        self.agent_factory = agent_factory
        self.config = config or TrainingConfig()
        self.trajectory_capture = TrajectoryCapture(self.config.trajectories_dir)
        self.reward_calculator = CompositeRewardCalculator()
        self.metrics = TrainingMetrics()
        
        # Create output directories
        self.config.output_dir.mkdir(exist_ok=True)
        self.config.trajectories_dir.mkdir(exist_ok=True)
        
    async def generate_rollout(
        self,
        task_description: str,
        project_context: Dict[str, Any],
        temperature: float
    ) -> Tuple[AgentTrajectory, float]:
        """
        Generate a single rollout trajectory.
        
        Args:
            task_description: Task for the agent
            project_context: Project context and metadata
            temperature: Model temperature for this rollout
            
        Returns:
            Tuple of (trajectory, reward)
        """
        # Create agent with specified temperature
        agent = self.agent_factory(temperature=temperature)
        
        # Start trajectory capture
        trajectory_id = f"rollout_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        trajectory = self.trajectory_capture.start_trajectory(trajectory_id)
        
        try:
            # Run agent
            result = await agent.arun({
                "messages": [{"role": "user", "content": task_description}],
                "project_context": project_context
            })
            
            # Complete trajectory
            trajectory = self.trajectory_capture.complete_trajectory(result)
            
            # Calculate reward
            reward, breakdown = self.reward_calculator.calculate_trajectory_reward(
                trajectory
            )
            
            if self.config.verbose:
                logger.info(f"Rollout {trajectory_id}: Reward = {reward:.2f}")
                
        except Exception as e:
            logger.error(f"Rollout failed: {e}")
            # Complete trajectory with error
            trajectory = self.trajectory_capture.complete_trajectory({
                "error": str(e)
            })
            reward = -1.0  # Penalty for failure
            
        return trajectory, reward
    
    async def generate_batch_rollouts(
        self,
        task_description: str,
        project_context: Dict[str, Any],
        batch_size: int,
        temperature: float
    ) -> List[Tuple[AgentTrajectory, float]]:
        """
        Generate a batch of rollouts in parallel.
        
        Args:
            task_description: Task for the agent
            project_context: Project context
            batch_size: Number of rollouts to generate
            temperature: Model temperature
            
        Returns:
            List of (trajectory, reward) tuples
        """
        tasks = []
        for i in range(batch_size):
            task = self.generate_rollout(
                task_description,
                project_context,
                temperature
            )
            tasks.append(task)
        
        # Run rollouts in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Batch rollout failed: {result}")
            else:
                valid_results.append(result)
                
        return valid_results
    
    def update_metrics(
        self,
        trajectories: List[AgentTrajectory],
        rewards: List[float]
    ):
        """
        Update training metrics based on rollout results.
        
        Args:
            trajectories: List of trajectories
            rewards: Corresponding rewards
        """
        # Update reward metrics
        self.metrics.rollout_rewards.extend(rewards)
        
        # Find best trajectory
        for trajectory, reward in zip(trajectories, rewards):
            if reward > self.metrics.best_reward:
                self.metrics.best_reward = reward
                self.metrics.best_trajectory_id = trajectory.trajectory_id
        
        # Calculate phase success rates
        phase_counts = {phase: 0 for phase in PhaseType}
        phase_successes = {phase: 0 for phase in PhaseType}
        
        for trajectory in trajectories:
            for phase in PhaseType:
                phase_counts[phase] += 1
                if phase in trajectory.phases_completed:
                    phase_successes[phase] += 1
        
        for phase in PhaseType:
            if phase_counts[phase] > 0:
                success_rate = phase_successes[phase] / phase_counts[phase]
                self.metrics.phase_success_rates[phase.value] = success_rate
        
        # Calculate average duration and steps
        durations = [t.duration() for t in trajectories if t.duration()]
        if durations:
            self.metrics.average_duration = np.mean(durations)
            
        steps = [len(t.steps) for t in trajectories]
        if steps:
            self.metrics.average_steps = np.mean(steps)
    
    def save_checkpoint(self, epoch: int):
        """
        Save training checkpoint.
        
        Args:
            epoch: Current training epoch
        """
        checkpoint = {
            "epoch": epoch,
            "metrics": {
                "average_reward": np.mean(self.metrics.rollout_rewards[-10:])
                if self.metrics.rollout_rewards else 0.0,
                "best_reward": self.metrics.best_reward,
                "best_trajectory_id": self.metrics.best_trajectory_id,
                "phase_success_rates": self.metrics.phase_success_rates,
                "average_duration": self.metrics.average_duration,
                "average_steps": self.metrics.average_steps,
            },
            "config": {
                "num_rollouts": self.config.num_rollouts,
                "batch_size": self.config.batch_size,
                "learning_rate": self.config.learning_rate,
            }
        }
        
        checkpoint_path = self.config.output_dir / f"checkpoint_epoch_{epoch}.json"
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint, f, indent=2)
            
        logger.info(f"Saved checkpoint: {checkpoint_path}")
    
    async def train(
        self,
        task_description: str,
        project_context: Dict[str, Any]
    ) -> TrainingMetrics:
        """
        Run the complete training pipeline.
        
        Args:
            task_description: Task to train on
            project_context: Project context
            
        Returns:
            Training metrics
        """
        logger.info("Starting training pipeline")
        logger.info(f"Task: {task_description}")
        logger.info(f"Config: {self.config.num_rollouts} rollouts, "
                   f"batch size {self.config.batch_size}")
        
        temperature = self.config.initial_temperature
        num_epochs = self.config.num_rollouts // self.config.batch_size
        
        # Training loop
        with tqdm(total=self.config.num_rollouts, desc="Training") as pbar:
            for epoch in range(num_epochs):
                # Generate batch of rollouts
                rollouts = await self.generate_batch_rollouts(
                    task_description,
                    project_context,
                    self.config.batch_size,
                    temperature
                )
                
                # Extract trajectories and rewards
                trajectories = [r[0] for r in rollouts]
                rewards = [r[1] for r in rollouts]
                
                # Update metrics
                self.update_metrics(trajectories, rewards)
                
                # Update progress bar
                pbar.update(len(rollouts))
                avg_reward = np.mean(rewards)
                pbar.set_postfix({
                    "epoch": epoch,
                    "avg_reward": f"{avg_reward:.2f}",
                    "temperature": f"{temperature:.3f}"
                })
                
                # Check for convergence
                if avg_reward >= self.config.reward_threshold:
                    logger.info(f"Converged at epoch {epoch} with "
                               f"average reward {avg_reward:.2f}")
                    self.metrics.convergence_epoch = epoch
                    break
                
                # Save checkpoint
                if (epoch + 1) % self.config.checkpoint_interval == 0:
                    self.save_checkpoint(epoch + 1)
                
                # Decay temperature
                temperature = max(
                    self.config.min_temperature,
                    temperature * self.config.temperature_decay
                )
        
        # Save final checkpoint
        self.save_checkpoint(num_epochs)
        
        # Save final metrics
        self.save_final_metrics()
        
        logger.info("Training complete")
        logger.info(f"Best reward: {self.metrics.best_reward:.2f}")
        logger.info(f"Best trajectory: {self.metrics.best_trajectory_id}")
        
        return self.metrics
    
    def save_final_metrics(self):
        """Save final training metrics."""
        metrics_path = self.config.output_dir / "final_metrics.json"
        
        metrics_data = {
            "best_reward": self.metrics.best_reward,
            "best_trajectory_id": self.metrics.best_trajectory_id,
            "convergence_epoch": self.metrics.convergence_epoch,
            "phase_success_rates": self.metrics.phase_success_rates,
            "average_duration": self.metrics.average_duration,
            "average_steps": self.metrics.average_steps,
            "reward_history": self.metrics.rollout_rewards,
            "final_average_reward": np.mean(self.metrics.rollout_rewards[-10:])
            if self.metrics.rollout_rewards else 0.0,
        }
        
        with open(metrics_path, 'w') as f:
            json.dump(metrics_data, f, indent=2)
            
        logger.info(f"Saved final metrics: {metrics_path}")
    
    def load_checkpoint(self, checkpoint_path: Path) -> Dict[str, Any]:
        """
        Load a training checkpoint.
        
        Args:
            checkpoint_path: Path to checkpoint file
            
        Returns:
            Checkpoint data
        """
        with open(checkpoint_path, 'r') as f:
            checkpoint = json.load(f)
            
        logger.info(f"Loaded checkpoint from epoch {checkpoint['epoch']}")
        return checkpoint
    
    def get_best_trajectory(self) -> Optional[AgentTrajectory]:
        """
        Load and return the best trajectory from training.
        
        Returns:
            Best trajectory or None if not found
        """
        if self.metrics.best_trajectory_id:
            return self.trajectory_capture.load_trajectory(
                self.metrics.best_trajectory_id
            )
        return None