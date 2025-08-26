# Atlas V1 with OpenPipe ART Integration

This experimental implementation extends Atlas V1 with reinforcement learning capabilities through [OpenPipe ART](https://art.openpipe.ai/). The integration enables the Atlas agent to learn and improve from execution trajectories, optimizing its performance across the 4-phase methodology.

## Overview

The OpenPipe ART integration adds three key capabilities to Atlas V1:

1. **Trajectory Capture**: Records all agent actions, tool calls, and phase transitions
2. **Reward Calculation**: Evaluates trajectory quality based on phase-specific objectives
3. **Reinforcement Learning**: Trains the agent to maximize rewards through iterative rollouts

## Architecture

```
atlas_v1_art/
├── reinforcement/          # Core RL components
│   ├── model_wrapper.py   # OpenPipe ART model integration
│   ├── trajectory_capture.py  # Trajectory recording system
│   └── reward_functions.py    # Phase-specific reward calculators
├── training/              # Training infrastructure
│   └── training_pipeline.py   # Orchestrates RL training
├── evaluation/            # Benchmarks and metrics (future)
└── atlas_agent_art.py     # Main agent with ART capabilities
```

## Installation

```bash
# Option 1: Standard installation (without backend features)
pip install -r requirements.txt

# Option 2: Minimal installation (if OpenPipe ART causes issues)
pip install -r requirements-minimal.txt

# Option 3: Try full installation with backend (may have compatibility issues)
pip install openpipe-art[backend,langgraph] --no-deps
pip install -r requirements.txt

# Copy and configure environment variables
cp .env.example .env
# Edit .env with your API keys

# Install LangGraph CLI (if not already installed)
pip install langgraph-cli
```

**Note on Dependencies**: Due to `bitsandbytes` version constraints, the `backend` extra for OpenPipe ART may not install on all systems. The core functionality (model wrapping and LangGraph integration) works without it.

## Quick Start

### Using LangGraph Studio (Recommended)

```bash
# Start LangGraph development server
langgraph dev

# The server will start at http://localhost:8123
# Open your browser and interact with the Atlas agent through the UI
```

### Configuration for LangGraph

The `langgraph.json` file is already configured to expose the Atlas graph:
```json
{
  "graphs": {
    "atlas_v1_art": "./graph.py:graph"
  }
}
```

To enable OpenPipe ART in LangGraph Studio:
1. Set `ENABLE_OPENPIPE_ART=true` in your `.env` file
2. Restart the LangGraph server
3. The agent will automatically use ART-wrapped models

### Programmatic Usage

### Basic Usage with ART

```python
from atlas_agent_art import create_atlas_agent_art
import asyncio

async def main():
    # Create ART-enabled agent
    agent = create_atlas_agent_art(
        temperature=0.7,
        enable_art=True,
        capture_trajectories=True
    )
    
    # Run a task
    result = await agent.run(
        task="Create a technical plan for implementing user authentication",
        project_id="your-project-id"
    )
    
    # Access trajectory and reward data
    print(f"Trajectory ID: {result['trajectory_id']}")
    print(f"Reward: {result['reward']:.2f}")
    print(f"Phases completed: {result['reward_breakdown']['phases_completed']}")

asyncio.run(main())
```

### Training with Reinforcement Learning

```python
from atlas_agent_art import create_atlas_agent_art
from training import TrainingPipeline, TrainingConfig
import asyncio

async def train_agent():
    # Configure training
    config = TrainingConfig(
        num_rollouts=100,
        batch_size=10,
        initial_temperature=0.7,
        temperature_decay=0.95,
        reward_threshold=3.0
    )
    
    # Create agent factory
    def agent_factory(temperature=0.7):
        return create_atlas_agent_art(
            temperature=temperature,
            enable_art=True,
            capture_trajectories=True
        )
    
    # Initialize training pipeline
    pipeline = TrainingPipeline(agent_factory, config)
    
    # Train on a specific task
    metrics = await pipeline.train(
        task_description="Analyze and plan implementation for user story US-123",
        project_context={"project_id": "your-project-id"}
    )
    
    # Review training results
    print(f"Best reward achieved: {metrics.best_reward:.2f}")
    print(f"Best trajectory: {metrics.best_trajectory_id}")
    print(f"Phase success rates: {metrics.phase_success_rates}")

asyncio.run(train_agent())
```

## Key Components

### Model Wrapper

The `reinforcement/model_wrapper.py` module provides seamless integration with OpenPipe ART:

- **Automatic Wrapping**: Models are wrapped with `init_chat_model()` when `ENABLE_OPENPIPE_ART=true`
- **Phase-Specific Models**: Different temperature and token settings per phase
- **Fallback Support**: Gracefully degrades if OpenPipe ART is not available

### Trajectory Capture

The `reinforcement/trajectory_capture.py` module records execution details:

- **Comprehensive Tracking**: Tool calls, model responses, sub-agent invocations
- **Phase Awareness**: Associates actions with specific Atlas phases
- **Persistent Storage**: Saves trajectories as JSONL for analysis and training

### Reward Functions

The `reinforcement/reward_functions.py` module evaluates trajectory quality:

#### Phase-Specific Rewards

- **Investigation Phase**:
  - MCP tool usage coverage
  - Generation of investigation_findings.md
  - Efficiency of data gathering

- **Discussion Phase**:
  - User interaction via human_input
  - Quality of clarification questions
  - Creation of requirements_clarified.md

- **Planning Phase**:
  - Repository analysis depth
  - Sub-agent utilization
  - Implementation plan comprehensiveness

- **Task Generation**:
  - Task structure clarity
  - Repository-task mapping
  - Actionability of generated tasks

#### Composite Scoring

Rewards combine multiple signals:
- Phase completion (30% weight)
- Execution efficiency (20% weight)
- Output quality (50% weight)
- Bonus for completing all phases
- Penalty for excessive duration

### Training Pipeline

The `training/training_pipeline.py` orchestrates reinforcement learning:

- **Parallel Rollouts**: Generate multiple trajectories concurrently
- **Temperature Annealing**: Gradually reduce exploration over time
- **Checkpoint System**: Save progress at regular intervals
- **Convergence Detection**: Stop when average reward exceeds threshold

## Configuration

### Environment Variables

```bash
# Core settings
ANTHROPIC_API_KEY=your_anthropic_key
FAIRMIND_MCP_URL=your_mcp_url
FAIRMIND_MCP_TOKEN=your_mcp_token

# OpenPipe ART settings
ENABLE_OPENPIPE_ART=true|false     # Enable ART integration
OPENPIPE_PROJECT=project_name      # OpenPipe project name
OPENPIPE_CACHE=true|false          # Enable caching

# Model settings
ATLAS_MODEL_NAME=claude-sonnet-4-20250514
ATLAS_MODEL_TEMPERATURE=0.7
ATLAS_MODEL_MAX_TOKENS=8192
```

### Training Configuration

```python
TrainingConfig(
    num_rollouts=100,          # Total training rollouts
    batch_size=10,             # Rollouts per batch
    learning_rate=0.001,       # Learning rate (if applicable)
    temperature_decay=0.95,    # Temperature decay factor
    initial_temperature=0.7,   # Starting temperature
    min_temperature=0.1,       # Minimum temperature
    reward_threshold=3.0,      # Convergence threshold
    checkpoint_interval=10,    # Checkpoint frequency
)
```

## Advanced Usage

### Custom Reward Functions

Create custom reward calculators for specific use cases:

```python
from reinforcement.reward_functions import PhaseRewardCalculator, RewardSignal, RewardType

class CustomRewardCalculator(PhaseRewardCalculator):
    def _check_quality(self, trajectory, expected_outputs=None):
        # Custom quality evaluation logic
        score = evaluate_custom_metrics(trajectory)
        
        return RewardSignal(
            reward_type=RewardType.QUALITY,
            value=score,
            weight=0.6,
            explanation="Custom quality assessment"
        )
```

### Trajectory Analysis

Analyze captured trajectories for insights:

```python
from reinforcement.trajectory_capture import TrajectoryCapture

# Load trajectories
capture = TrajectoryCapture()
trajectory = capture.load_trajectory("trajectory_20240101_120000")

# Analyze trajectory
print(f"Phases completed: {[p.value for p in trajectory.phases_completed]}")
print(f"Total steps: {len(trajectory.steps)}")
print(f"Duration: {trajectory.duration():.2f}s")

# Extract specific actions
tool_calls = [step for step in trajectory.steps 
              if step.action_type == ActionType.TOOL_CALL]
print(f"Tool calls made: {len(tool_calls)}")
```

### Export for External Training

Export trajectories for training with external RL frameworks:

```python
agent = create_atlas_agent_art()

# Run multiple tasks to collect trajectories
for task in tasks:
    await agent.run(task)

# Export all trajectories with rewards
export_path = agent.export_trajectories_for_training(
    output_path=Path("training_data.jsonl")
)
```

## Performance Considerations

### Memory Usage

- Trajectories are stored in memory during execution
- Large trajectories (>1000 steps) may consume significant RAM
- Use checkpoint intervals to persist progress

### Execution Speed

- ART wrapping adds minimal overhead (<5% typically)
- Trajectory capture is asynchronous and non-blocking
- Batch rollouts utilize concurrent execution

### Storage Requirements

- Each trajectory: ~10-100KB depending on complexity
- 1000 rollouts: ~10-100MB of storage
- Checkpoints: ~1MB per checkpoint

## Troubleshooting

### OpenPipe ART Not Available

```
Warning: OpenPipe ART not installed, using base model
```

**Solution**: Install OpenPipe ART:
```bash
pip install openpipe-art[backend,langgraph]>=0.4.9
```

### Trajectory Capture Failures

```
Error: No active trajectory to complete
```

**Solution**: Ensure trajectory capture is enabled:
```python
agent = create_atlas_agent_art(capture_trajectories=True)
```

### Low Rewards

If rewards are consistently negative:
1. Check phase completion rates
2. Verify MCP tools are accessible
3. Review task complexity vs. agent capabilities
4. Adjust reward weights if needed

## Future Enhancements

- [ ] Integration with RULER for automatic correctness evaluation
- [ ] Support for multi-task training
- [ ] Distributed rollout generation
- [ ] Online learning during deployment
- [ ] Reward learning from human feedback
- [ ] Integration with DSPy for prompt optimization

## Contributing

This is an experimental implementation. Contributions are welcome:

1. Test the integration with various tasks
2. Propose improvements to reward functions
3. Add evaluation benchmarks
4. Share training results and insights

## References

- [OpenPipe ART Documentation](https://art.openpipe.ai/)
- [LangGraph Integration Guide](https://art.openpipe.ai/integrations/langgraph-integration)
- [Atlas V1 Base Implementation](../atlas_v1/README.md)
- [DeepAgents Framework](../../README.md)