# CLAUDE.md - Atlas V1 ART Integration

This file provides guidance to Claude Code when working with the Atlas V1 OpenPipe ART integration in this experimental directory.

## Overview

**Atlas V1 ART** is an experimental extension of Atlas V1 that adds reinforcement learning capabilities through [OpenPipe ART](https://art.openpipe.ai/). This implementation demonstrates how to enhance the base Atlas agent with trajectory capture, reward calculation, and model optimization without modifying the core deepagents framework.

### Key Principle
This is an **experimental branch** - changes here should NOT affect the base Atlas V1 implementation in `../atlas_v1/`. The goal is to validate reinforcement learning benefits before considering integration into the main codebase.

## Architecture

### Core Components

#### 1. Model Wrapping (`reinforcement/model_wrapper.py`)
- Wraps language models with OpenPipe ART's `init_chat_model()`
- Supports phase-specific model configurations
- Gracefully falls back when ART is unavailable
- Environment variable controlled: `ENABLE_OPENPIPE_ART`

#### 2. Trajectory Capture (`reinforcement/trajectory_capture.py`)
- Records all agent actions, tool calls, and phase transitions
- Stores trajectories as JSONL files for analysis
- Tracks phase progression and execution metrics
- Asynchronous capture with minimal performance impact

#### 3. Reward Functions (`reinforcement/reward_functions.py`)
- Phase-specific reward calculators for each Atlas phase
- Composite scoring combining multiple signals:
  - Phase completion (30% weight)
  - Execution efficiency (20% weight)
  - Output quality (50% weight)
- Extensible design for custom reward metrics

#### 4. Training Pipeline (`training/training_pipeline.py`)
- Orchestrates reinforcement learning training
- Parallel rollout generation for efficiency
- Temperature annealing for exploration vs exploitation
- Checkpoint system for training persistence

#### 5. Main Agent (`atlas_agent_art.py`)
- Extends base `AtlasAgentV1` class
- Adds trajectory capture and reward calculation
- Maintains backward compatibility
- Can run with or without ART enabled

## LangGraph Integration

### Running with LangGraph Studio

```bash
# From this directory
langgraph dev

# Access at http://localhost:8123
```

The `graph.py` file exposes the agent as a LangGraph-compatible graph, enabling:
- Visual execution flow monitoring
- State inspection at each step
- Interactive debugging
- Tool call tracking

### Configuration Files

- `langgraph.json`: Defines graph entry point for LangGraph Studio
- `.env.example`: Template for environment variables
- `graph.py`: LangGraph-compatible graph creation

## Development Guidelines

### When Adding Features

1. **Maintain Isolation**: Changes should not require modifications to `../atlas_v1/` or `../../src/deepagents/`
2. **Feature Flags**: New capabilities should be controllable via environment variables
3. **Graceful Degradation**: The agent must work even if OpenPipe ART is not installed
4. **Document Rewards**: Any new reward signals should be clearly documented with rationale

### Testing Approach

```bash
# Run test suite
python test_art_integration.py

# Test with LangGraph
langgraph dev

# Test programmatically
python atlas_agent_art.py
```

### Key Environment Variables

```bash
# Core functionality
ENABLE_OPENPIPE_ART=true/false    # Toggle ART integration
CAPTURE_TRAJECTORIES=true/false   # Toggle trajectory recording

# OpenPipe configuration
OPENPIPE_PROJECT=atlas-v1-art     # Project identifier
OPENPIPE_API_KEY=<key>           # API key if required
OPENPIPE_CACHE=true/false        # Enable caching

# Model configuration
ATLAS_MODEL_TEMPERATURE=0.7       # Model temperature
ATLAS_MODEL_NAME=<model>         # Model selection
```

## Reward System Design

### Phase-Specific Objectives

#### Investigation Phase
- **Goal**: Comprehensive project exploration
- **Key Metrics**:
  - MCP tool usage coverage
  - Generation of `investigation_findings.md`
  - Efficiency of data gathering
- **Reward Range**: -0.5 to 1.0

#### Discussion Phase
- **Goal**: Effective user interaction
- **Key Metrics**:
  - Human input tool usage
  - Quality of clarification questions
  - Creation of `requirements_clarified.md`
- **Reward Range**: -0.5 to 1.0

#### Planning Phase
- **Goal**: Thorough technical analysis
- **Key Metrics**:
  - Repository analysis depth
  - Sub-agent utilization
  - Implementation plan quality
- **Reward Range**: -0.3 to 1.0

#### Task Generation Phase
- **Goal**: Actionable task creation
- **Key Metrics**:
  - Task structure clarity
  - Repository-task mapping
  - Implementation detail level
- **Reward Range**: -0.3 to 1.0

### Composite Scoring

Total reward = Σ(phase_rewards) + completion_bonus - time_penalty

- **Completion Bonus**: +1.0 for completing all 4 phases
- **Time Penalty**: -0.5 for executions over 5 minutes

## Training Strategy

### Rollout Generation
- Batch size: 10 (configurable)
- Temperature decay: 0.95 per epoch
- Convergence threshold: 3.0 average reward

### Best Practices
1. Start with small rollout counts (10-20) for testing
2. Use checkpoint system for long training runs
3. Monitor phase success rates for debugging
4. Export trajectories for offline analysis

## Common Issues and Solutions

### Issue: OpenPipe ART not wrapping model
**Check**: `ENABLE_OPENPIPE_ART=true` in environment
**Verify**: Look for "✅ OpenPipe ART wrapping enabled" in logs

### Issue: Trajectories not being saved
**Check**: `CAPTURE_TRAJECTORIES=true` in environment
**Verify**: `trajectories/` directory exists and is writable

### Issue: Low rewards consistently
**Debug Steps**:
1. Check phase completion rates
2. Verify MCP tools are accessible
3. Review task complexity
4. Examine individual phase rewards

### Issue: LangGraph not starting
**Check**: `langgraph.json` points to correct graph
**Verify**: All dependencies in `requirements.txt` installed

## Future Improvements

### Planned Enhancements
- [ ] RULER integration for automatic correctness evaluation
- [ ] Multi-task training support
- [ ] Distributed rollout generation
- [ ] Online learning during deployment
- [ ] Human feedback reward learning

### Experimental Ideas
- Phase-specific fine-tuning
- Curriculum learning (easy → hard tasks)
- Meta-learning across projects
- Adversarial training for robustness

## Integration Path

If ART proves beneficial, integration steps:
1. **Validation**: Confirm 20%+ improvement in key metrics
2. **Refactor**: Move core components to `src/deepagents/reinforcement/`
3. **Configuration**: Add ART settings to main Atlas config
4. **Migration**: Provide upgrade path for existing deployments
5. **Documentation**: Update main Atlas documentation

## Key Differences from Base Atlas V1

| Aspect | Base Atlas V1 | Atlas V1 ART |
|--------|--------------|--------------|
| Model Init | Direct ChatAnthropic | Wrapped with init_chat_model |
| Execution | Standard flow | Trajectory captured |
| Output | Task results | Results + rewards + trajectory |
| Configuration | config.yaml | config.yaml + .env ART settings |
| Dependencies | Base requirements | + openpipe-art package |

## Testing Checklist

Before committing changes:
- [ ] Test without ART enabled (fallback mode)
- [ ] Test with ART enabled
- [ ] Run test_art_integration.py
- [ ] Verify LangGraph compatibility
- [ ] Check trajectory storage
- [ ] Validate reward calculations
- [ ] Ensure no impact on base Atlas V1

## Important Notes

1. **Experimental Status**: This is a proof of concept - expect breaking changes
2. **Performance**: ART adds <5% overhead when enabled, negligible when disabled
3. **Storage**: Each trajectory ~10-100KB, plan accordingly for large-scale training
4. **Compatibility**: Requires Python 3.8+, LangGraph 0.1+, OpenPipe ART 0.4.9+

## Contact and Support

For questions about this integration:
1. Check the main [Atlas V1 documentation](../atlas_v1/README.md)
2. Review [OpenPipe ART docs](https://art.openpipe.ai/)
3. See [DeepAgents framework](../../README.md) for core concepts

Remember: This experimental branch allows safe exploration of reinforcement learning without risking the stable Atlas V1 implementation.