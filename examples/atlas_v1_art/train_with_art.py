#!/usr/bin/env python3
"""
Training script for Atlas V1 with OpenPipe ART.

This script implements the correct pattern for using OpenPipe ART with LangGraph,
following the documentation at https://art.openpipe.ai/integrations/langgraph-integration
"""

import os
import sys
import asyncio
import logging
import uuid
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import ART components
try:
    import art
    from art.langgraph import init_chat_model, wrap_rollout
    import weave
    ART_AVAILABLE = True
    logger.info("✅ OpenPipe ART imported successfully")
except ImportError as e:
    logger.error(f"❌ Failed to import OpenPipe ART: {e}")
    ART_AVAILABLE = False
    sys.exit(1)

# Import deepagents and Atlas components
from deepagents import create_deep_agent, SubAgent
from deepagents.state import DeepAgentState
from langchain_core.messages import SystemMessage, HumanMessage

# Import Atlas configuration
from agents import (
    investigation_agent,
    discussion_agent,
    planning_agent,
    task_generation_agent
)
from prompts import ORCHESTRATOR_PROMPT_TEMPLATE as ORCHESTRATOR_PROMPT_V2


@dataclass
class AtlasScenario:
    """Represents a task scenario for Atlas agent."""
    project_id: str
    user_story_id: str
    request: str
    expected_phases: List[str] = None
    
    def __post_init__(self):
        if self.expected_phases is None:
            self.expected_phases = ["investigation", "discussion", "planning", "task_generation"]


@dataclass
class AtlasTrajectory:
    """Captures the execution trajectory of an Atlas rollout."""
    scenario: AtlasScenario
    messages: List[Dict[str, Any]]
    phase_completions: Dict[str, bool]
    total_steps: int
    success: bool
    error: Optional[str] = None


@weave.op
async def atlas_rollout(model: art.Model, scenario: AtlasScenario) -> AtlasTrajectory:
    """
    Execute a single rollout of the Atlas agent with ART integration.
    
    This function follows the pattern from the OpenPipe documentation:
    1. Initialize chat model using init_chat_model
    2. Create the agent with tools
    3. Execute the agent with proper configuration
    4. Capture the trajectory
    
    Args:
        model: ART model configuration
        scenario: Atlas task scenario to execute
        
    Returns:
        AtlasTrajectory capturing the execution
    """
    logger.info(f"Starting rollout for scenario: {scenario.request}")
    
    # Initialize chat model with ART - this is the key integration point
    chat_model = init_chat_model(
        model.name,
        temperature=model.temperature if hasattr(model, 'temperature') else 0.7
    )
    
    # Initialize MCP tools if available (simplified for this example)
    tools = []
    
    # Create sub-agents
    subagents = [
        SubAgent(
            name=agent["name"],
            description=agent["description"],
            prompt=agent["prompt"]
        )
        for agent in [investigation_agent, discussion_agent, planning_agent, task_generation_agent]
    ]
    
    # Create the Atlas graph using deepagents
    graph = create_deep_agent(
        tools=tools,
        instructions=ORCHESTRATOR_PROMPT_V2,
        model=chat_model,  # Use the ART-wrapped model here
        subagents=subagents,
        state_schema=DeepAgentState
    )
    
    # Configure execution
    config = {
        "configurable": {"thread_id": str(uuid.uuid4())},
        "recursion_limit": 50,  # Limit recursion for safety
    }
    
    # Initialize trajectory tracking
    trajectory = AtlasTrajectory(
        scenario=scenario,
        messages=[],
        phase_completions={},
        total_steps=0,
        success=False
    )
    
    try:
        # Execute the agent
        result = await graph.ainvoke(
            {
                "messages": [
                    SystemMessage(content="You are the Atlas V1 orchestrator agent."),
                    HumanMessage(content=f"Project ID: {scenario.project_id}\n"
                                       f"User Story: {scenario.user_story_id}\n"
                                       f"Request: {scenario.request}")
                ]
            },
            config=config
        )
        
        # Extract trajectory information
        if "messages" in result:
            trajectory.messages = result["messages"]
            trajectory.total_steps = len(result["messages"])
        
        # Check phase completions
        for phase in scenario.expected_phases:
            phase_key = f"{phase}_complete"
            if phase_key in result:
                trajectory.phase_completions[phase] = result[phase_key]
        
        # Determine success
        all_phases_complete = all(
            trajectory.phase_completions.get(phase, False)
            for phase in scenario.expected_phases
        )
        trajectory.success = all_phases_complete
        
        logger.info(f"Rollout completed. Success: {trajectory.success}")
        
    except Exception as e:
        logger.error(f"Rollout failed: {e}")
        trajectory.error = str(e)
        trajectory.success = False
    
    return trajectory


async def train_atlas_with_art(
    scenarios: List[AtlasScenario],
    model_name: str = "claude-3-5-sonnet-20241022",
    rollouts_per_scenario: int = 3,
    epochs: int = 1
):
    """
    Train the Atlas agent using OpenPipe ART.
    
    This follows the training pattern from the documentation:
    1. Create trajectory groups using wrap_rollout
    2. Generate multiple rollouts per scenario
    3. Collect trajectories for training
    
    Args:
        scenarios: List of task scenarios to train on
        model_name: Base model to use
        rollouts_per_scenario: Number of rollouts per scenario
        epochs: Number of training epochs
    """
    logger.info(f"Starting ART training with {len(scenarios)} scenarios")
    
    # Initialize the ART model
    model = art.Model(name=model_name, temperature=0.7)
    
    for epoch in range(epochs):
        logger.info(f"Epoch {epoch + 1}/{epochs}")
        
        # Generate trajectory groups for each scenario
        trajectory_groups = []
        
        for scenario in scenarios:
            # Create a trajectory group with multiple rollouts
            group = art.TrajectoryGroup([
                wrap_rollout(model, atlas_rollout)(model, scenario)
                for _ in range(rollouts_per_scenario)
            ])
            trajectory_groups.append(group)
        
        # Wait for all rollouts to complete
        all_trajectories = []
        for group in trajectory_groups:
            trajectories = await group.gather()
            all_trajectories.extend(trajectories)
        
        # Calculate metrics
        successful = sum(1 for t in all_trajectories if t.success)
        total = len(all_trajectories)
        success_rate = successful / total if total > 0 else 0
        
        logger.info(f"Epoch {epoch + 1} Results:")
        logger.info(f"  Success rate: {success_rate:.2%} ({successful}/{total})")
        logger.info(f"  Avg steps: {sum(t.total_steps for t in all_trajectories) / total:.1f}")
        
        # In a real implementation, you would:
        # 1. Send trajectories to OpenPipe for training
        # 2. Update the model with new weights
        # 3. Continue training until convergence


def main():
    """Main entry point for training."""
    
    # Check if ART is available
    if not ART_AVAILABLE:
        logger.error("OpenPipe ART is required for training. Please install it first.")
        return
    
    # Create sample training scenarios
    scenarios = [
        AtlasScenario(
            project_id="sample_project_1",
            user_story_id="US-001",
            request="Create a technical implementation plan for user authentication"
        ),
        AtlasScenario(
            project_id="sample_project_2", 
            user_story_id="US-002",
            request="Design API endpoints for user management"
        ),
        AtlasScenario(
            project_id="sample_project_3",
            user_story_id="US-003",
            request="Plan database schema for e-commerce platform"
        ),
    ]
    
    # Run training
    asyncio.run(train_atlas_with_art(
        scenarios=scenarios,
        model_name=os.getenv("ATLAS_MODEL_NAME", "claude-3-5-sonnet-20241022"),
        rollouts_per_scenario=2,
        epochs=1
    ))


if __name__ == "__main__":
    main()