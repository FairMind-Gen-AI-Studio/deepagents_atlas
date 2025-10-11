"""
Atlas V1 Agent with OpenPipe ART integration.

This module extends the base Atlas V1 agent with reinforcement learning
capabilities through OpenPipe ART.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import base Atlas agent
from atlas_v1.atlas_agent import AtlasAgentV1

# Import ART components
from reinforcement.model_wrapper import (
    get_art_enabled_model,
    create_phase_specific_model,
    wrap_existing_model
)
from reinforcement.trajectory_capture import (
    TrajectoryCapture,
    PhaseType
)
from reinforcement.reward_functions import CompositeRewardCalculator

logger = logging.getLogger(__name__)


class AtlasAgentART(AtlasAgentV1):
    """
    Atlas V1 Agent enhanced with OpenPipe ART reinforcement learning.
    
    This class extends the base Atlas V1 agent to add:
    - Model wrapping with OpenPipe ART
    - Trajectory capture during execution
    - Reward calculation for training
    - Phase-specific model optimization
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        available_tools: Optional[Dict[str, Any]] = None,
        enable_art: bool = True,
        capture_trajectories: bool = True,
        temperature: Optional[float] = None
    ):
        """
        Initialize Atlas Agent with ART capabilities.
        
        Args:
            config_path: Optional path to configuration file
            available_tools: Optional MCP tools dictionary
            enable_art: Whether to enable OpenPipe ART wrapping
            capture_trajectories: Whether to capture trajectories
            temperature: Override temperature for model
        """
        # Load environment variables
        load_dotenv()
        
        # Set ART environment variable if requested
        if enable_art:
            os.environ["ENABLE_OPENPIPE_ART"] = "true"
            logger.info("✅ OpenPipe ART integration enabled")
        
        # Initialize trajectory capture
        self.trajectory_capture = None
        if capture_trajectories:
            self.trajectory_capture = TrajectoryCapture()
            logger.info("📊 Trajectory capture enabled")
        
        # Store temperature override
        self.temperature_override = temperature
        
        # Initialize base Atlas agent
        super().__init__(config_path, available_tools)
        
        # Override model initialization if ART is enabled
        if enable_art:
            self._wrap_models_with_art()
        
        # Initialize reward calculator
        self.reward_calculator = CompositeRewardCalculator()
        
    def _wrap_models_with_art(self):
        """
        Wrap agent models with OpenPipe ART.
        """
        logger.info("Wrapping models with OpenPipe ART...")
        
        # Get temperature (use override if provided)
        temperature = self.temperature_override or float(
            os.getenv("ATLAS_MODEL_TEMPERATURE", "0.7")
        )
        
        # Replace the coordinator's model with ART-wrapped version
        if hasattr(self.coordinator, 'model'):
            original_model = self.coordinator.model
            wrapped_model = get_art_enabled_model(
                temperature=temperature
            )
            self.coordinator.model = wrapped_model
            logger.info("✅ Wrapped coordinator model with ART")
        
        # Wrap phase-specific models if they exist
        if hasattr(self.coordinator, 'agents'):
            for phase_name, agent_config in self.coordinator.agents.items():
                # Create phase-specific model
                phase_model = create_phase_specific_model(
                    phase_name,
                    base_config={"temperature": temperature}
                )
                
                # Update agent configuration
                if isinstance(agent_config, dict):
                    agent_config['model_settings'] = {
                        "model": phase_model
                    }
                    
                logger.info(f"✅ Created phase-specific model for {phase_name}")
    
    async def run(
        self,
        task: str,
        project_id: Optional[str] = None,
        user_story_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Run the Atlas agent with trajectory capture.
        
        Args:
            task: Task description
            project_id: Optional project ID
            user_story_id: Optional user story ID
            **kwargs: Additional arguments
            
        Returns:
            Agent execution result with trajectory data
        """
        # Start trajectory capture if enabled
        if self.trajectory_capture:
            trajectory = self.trajectory_capture.start_trajectory()
            logger.info(f"Started trajectory: {trajectory.trajectory_id}")
        
        try:
            # Run base agent
            result = await super().run(
                task=task,
                project_id=project_id,
                user_story_id=user_story_id,
                **kwargs
            )
            
            # Complete trajectory capture
            if self.trajectory_capture:
                trajectory = self.trajectory_capture.complete_trajectory(result)
                
                # Calculate reward
                reward, breakdown = self.reward_calculator.calculate_trajectory_reward(
                    trajectory
                )
                
                # Add trajectory data to result
                result['trajectory_id'] = trajectory.trajectory_id
                result['reward'] = reward
                result['reward_breakdown'] = breakdown
                
                logger.info(f"Completed trajectory with reward: {reward:.2f}")
            
            return result
            
        except Exception as e:
            # Handle errors gracefully
            logger.error(f"Agent execution failed: {e}")
            
            if self.trajectory_capture:
                # Complete trajectory with error
                trajectory = self.trajectory_capture.complete_trajectory({
                    "error": str(e)
                })
                
            raise
    
    def get_trajectory_stats(self) -> Dict[str, Any]:
        """
        Get statistics about captured trajectories.
        
        Returns:
            Dictionary with trajectory statistics
        """
        if not self.trajectory_capture:
            return {"error": "Trajectory capture not enabled"}
        
        trajectories = self.trajectory_capture.list_trajectories()
        
        stats = {
            "total_trajectories": len(trajectories),
            "trajectory_ids": trajectories[-10:],  # Last 10
        }
        
        # Calculate average rewards if we have trajectories
        if trajectories:
            rewards = []
            for traj_id in trajectories[-10:]:
                trajectory = self.trajectory_capture.load_trajectory(traj_id)
                if trajectory:
                    reward, _ = self.reward_calculator.calculate_trajectory_reward(
                        trajectory
                    )
                    rewards.append(reward)
            
            if rewards:
                import numpy as np
                stats["average_reward"] = np.mean(rewards)
                stats["best_reward"] = max(rewards)
                stats["worst_reward"] = min(rewards)
        
        return stats
    
    def export_trajectories_for_training(
        self,
        output_path: Optional[Path] = None
    ) -> str:
        """
        Export captured trajectories for training.
        
        Args:
            output_path: Optional output path for trajectories
            
        Returns:
            Path to exported trajectories
        """
        if not self.trajectory_capture:
            raise ValueError("Trajectory capture not enabled")
        
        output_path = output_path or Path("exported_trajectories.jsonl")
        
        import jsonlines
        
        with jsonlines.open(output_path, mode='w') as writer:
            for traj_id in self.trajectory_capture.list_trajectories():
                trajectory = self.trajectory_capture.load_trajectory(traj_id)
                if trajectory:
                    reward, breakdown = self.reward_calculator.calculate_trajectory_reward(
                        trajectory
                    )
                    
                    # Export trajectory with reward
                    export_data = trajectory.to_dict()
                    export_data['reward'] = reward
                    export_data['reward_breakdown'] = breakdown
                    
                    writer.write(export_data)
        
        logger.info(f"Exported trajectories to {output_path}")
        return str(output_path)


def create_atlas_agent_art(
    temperature: Optional[float] = None,
    enable_art: bool = True,
    capture_trajectories: bool = True,
    **kwargs
) -> AtlasAgentART:
    """
    Factory function to create an Atlas agent with ART.
    
    Args:
        temperature: Model temperature override
        enable_art: Whether to enable OpenPipe ART
        capture_trajectories: Whether to capture trajectories
        **kwargs: Additional arguments for AtlasAgentART
        
    Returns:
        Configured AtlasAgentART instance
    """
    return AtlasAgentART(
        enable_art=enable_art,
        capture_trajectories=capture_trajectories,
        temperature=temperature,
        **kwargs
    )


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def main():
        # Create ART-enabled agent
        agent = create_atlas_agent_art(
            temperature=0.7,
            enable_art=True,
            capture_trajectories=True
        )
        
        # Run a test task
        result = await agent.run(
            task="Analyze the requirements for implementing a user authentication system",
            project_id="test-project"
        )
        
        # Display results
        print("\n=== Execution Results ===")
        print(f"Trajectory ID: {result.get('trajectory_id')}")
        print(f"Reward: {result.get('reward', 'N/A')}")
        
        if 'reward_breakdown' in result:
            print("\n=== Reward Breakdown ===")
            breakdown = result['reward_breakdown']
            print(f"Total Reward: {breakdown.get('total_reward', 0):.2f}")
            print(f"Phases Completed: {breakdown.get('phases_completed', [])}")
            print(f"Duration: {breakdown.get('duration', 0):.2f}s")
            print(f"Step Count: {breakdown.get('step_count', 0)}")
        
        # Get trajectory statistics
        stats = agent.get_trajectory_stats()
        print("\n=== Trajectory Statistics ===")
        print(f"Total Trajectories: {stats.get('total_trajectories', 0)}")
        print(f"Average Reward: {stats.get('average_reward', 'N/A')}")
        
    # Run the example
    asyncio.run(main())