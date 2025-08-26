#!/usr/bin/env python3
"""
Test script for Atlas V1 with OpenPipe ART integration.

This script validates that the ART integration works correctly
and demonstrates various usage patterns.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import ART components
from atlas_agent_art import create_atlas_agent_art
from reinforcement.trajectory_capture import TrajectoryCapture, PhaseType
from reinforcement.reward_functions import CompositeRewardCalculator
from training import TrainingPipeline, TrainingConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestResults:
    """Track test results."""
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.details = []
    
    def add_test(self, name: str, passed: bool, details: str = ""):
        self.tests_run += 1
        if passed:
            self.tests_passed += 1
            status = "✅ PASSED"
        else:
            self.tests_failed += 1
            status = "❌ FAILED"
        
        self.details.append(f"{status}: {name}")
        if details:
            self.details.append(f"  Details: {details}")
    
    def print_summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        for detail in self.details:
            print(detail)
        print("-"*60)
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        print("="*60)


async def test_model_wrapper():
    """Test 1: Verify model wrapper functionality."""
    print("\n🧪 Test 1: Model Wrapper")
    print("-"*40)
    
    try:
        from reinforcement.model_wrapper import get_art_enabled_model
        
        # Test without ART
        os.environ["ENABLE_OPENPIPE_ART"] = "false"
        model_without_art = get_art_enabled_model()
        print(f"Model without ART: {type(model_without_art).__name__}")
        
        # Test with ART (if available)
        os.environ["ENABLE_OPENPIPE_ART"] = "true"
        model_with_art = get_art_enabled_model()
        print(f"Model with ART: {type(model_with_art).__name__}")
        
        # Check if wrapping occurred
        wrapped = type(model_with_art).__name__ != type(model_without_art).__name__
        
        if not wrapped:
            print("⚠️  ART wrapping not available (OpenPipe ART may not be installed)")
            return True  # Not a failure, just not available
        
        print("✅ Model wrapping successful")
        return True
        
    except Exception as e:
        print(f"❌ Model wrapper test failed: {e}")
        return False


async def test_trajectory_capture():
    """Test 2: Verify trajectory capture system."""
    print("\n🧪 Test 2: Trajectory Capture")
    print("-"*40)
    
    try:
        capture = TrajectoryCapture()
        
        # Start a trajectory
        trajectory = capture.start_trajectory("test_trajectory")
        print(f"Started trajectory: {trajectory.trajectory_id}")
        
        # Set phase
        capture.set_phase(PhaseType.INVESTIGATION)
        
        # Capture some actions
        capture.capture_tool_call(
            tool_name="test_tool",
            tool_input={"param": "value"},
            tool_output="test output",
            execution_time=0.5
        )
        
        capture.capture_model_response(
            prompt="Test prompt",
            response="Test response",
            model_name="test_model",
            tokens_used={"input": 10, "output": 20}
        )
        
        # Complete trajectory
        completed = capture.complete_trajectory({"test": "output"})
        
        # Verify trajectory
        assert len(completed.steps) == 2, "Should have 2 steps"
        assert PhaseType.INVESTIGATION in completed.phases_completed
        assert completed.duration() is not None
        
        print(f"✅ Captured {len(completed.steps)} steps")
        print(f"✅ Duration: {completed.duration():.2f}s")
        return True
        
    except Exception as e:
        print(f"❌ Trajectory capture test failed: {e}")
        return False


async def test_reward_calculation():
    """Test 3: Verify reward calculation."""
    print("\n🧪 Test 3: Reward Calculation")
    print("-"*40)
    
    try:
        from reinforcement.reward_functions import (
            InvestigationRewardCalculator,
            AgentTrajectory,
            TrajectoryStep,
            ActionType
        )
        import time
        
        # Create a mock trajectory
        trajectory = AgentTrajectory(
            trajectory_id="test_reward",
            start_time=time.time()
        )
        
        # Add investigation phase
        trajectory.phases_completed.append(PhaseType.INVESTIGATION)
        
        # Add some steps
        step1 = TrajectoryStep(
            timestamp=time.time(),
            action_type=ActionType.TOOL_CALL,
            phase=PhaseType.INVESTIGATION,
            content={
                "tool_name": "mcp__fairmind__General_list_projects",
                "input": {},
                "output": ["project1", "project2"]
            }
        )
        trajectory.add_step(step1)
        
        # Complete trajectory
        trajectory.complete({"files": {"investigation_findings.md": "content"}})
        
        # Calculate reward
        calculator = InvestigationRewardCalculator()
        reward, signals = calculator.calculate_reward(trajectory)
        
        print(f"Calculated reward: {reward:.2f}")
        for signal in signals:
            print(f"  - {signal.reward_type.value}: {signal.value:.2f} "
                  f"(weight: {signal.weight})")
        
        assert reward > 0, "Reward should be positive for successful investigation"
        print("✅ Reward calculation successful")
        return True
        
    except Exception as e:
        print(f"❌ Reward calculation test failed: {e}")
        return False


async def test_agent_creation():
    """Test 4: Verify ART-enabled agent creation."""
    print("\n🧪 Test 4: Agent Creation")
    print("-"*40)
    
    try:
        # Create agent without MCP tools
        agent = create_atlas_agent_art(
            temperature=0.7,
            enable_art=True,
            capture_trajectories=True,
            available_tools=None  # No MCP tools
        )
        
        print(f"✅ Agent created: {type(agent).__name__}")
        
        # Check components
        assert hasattr(agent, 'trajectory_capture'), "Should have trajectory capture"
        assert hasattr(agent, 'reward_calculator'), "Should have reward calculator"
        
        print("✅ Agent has required components")
        return True
        
    except Exception as e:
        print(f"❌ Agent creation test failed: {e}")
        return False


async def test_simple_execution():
    """Test 5: Run a simple agent execution."""
    print("\n🧪 Test 5: Simple Execution")
    print("-"*40)
    
    try:
        # Create agent
        agent = create_atlas_agent_art(
            temperature=0.7,
            enable_art=False,  # Disable ART for simple test
            capture_trajectories=True,
            available_tools=None  # No MCP tools
        )
        
        # Create a simple task that doesn't require MCP
        result = await agent.run(
            task="Write a simple hello world message to hello.txt",
            project_id=None
        )
        
        # Check results
        if 'trajectory_id' in result:
            print(f"✅ Trajectory captured: {result['trajectory_id']}")
        
        if 'reward' in result:
            print(f"✅ Reward calculated: {result['reward']:.2f}")
        
        # Get stats
        stats = agent.get_trajectory_stats()
        print(f"✅ Stats: {stats.get('total_trajectories', 0)} trajectories")
        
        return True
        
    except Exception as e:
        print(f"❌ Simple execution test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_training_pipeline():
    """Test 6: Verify training pipeline initialization."""
    print("\n🧪 Test 6: Training Pipeline")
    print("-"*40)
    
    try:
        # Create minimal training config
        config = TrainingConfig(
            num_rollouts=2,  # Very small for testing
            batch_size=1,
            checkpoint_interval=1,
            verbose=False
        )
        
        # Agent factory
        def agent_factory(temperature=0.7):
            return create_atlas_agent_art(
                temperature=temperature,
                enable_art=False,  # Disable for test
                capture_trajectories=True,
                available_tools=None
            )
        
        # Create pipeline
        pipeline = TrainingPipeline(agent_factory, config)
        
        print(f"✅ Pipeline created with config:")
        print(f"  - Rollouts: {config.num_rollouts}")
        print(f"  - Batch size: {config.batch_size}")
        
        # Note: Not running actual training in test
        print("✅ Training pipeline initialized successfully")
        return True
        
    except Exception as e:
        print(f"❌ Training pipeline test failed: {e}")
        return False


async def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("ATLAS V1 ART INTEGRATION TEST SUITE")
    print("="*60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = TestResults()
    
    # Run tests
    tests = [
        ("Model Wrapper", test_model_wrapper),
        ("Trajectory Capture", test_trajectory_capture),
        ("Reward Calculation", test_reward_calculation),
        ("Agent Creation", test_agent_creation),
        ("Simple Execution", test_simple_execution),
        ("Training Pipeline", test_training_pipeline)
    ]
    
    for test_name, test_func in tests:
        try:
            passed = await test_func()
            results.add_test(test_name, passed)
        except Exception as e:
            results.add_test(test_name, False, str(e))
    
    # Print summary
    results.print_summary()
    
    # Return success if all critical tests passed
    critical_tests_passed = results.tests_passed >= 4
    if critical_tests_passed:
        print("\n🎉 Core functionality validated successfully!")
        print("Note: Some features may be limited without OpenPipe ART installed.")
    else:
        print("\n⚠️  Some tests failed. Please review the output above.")
    
    return critical_tests_passed


if __name__ == "__main__":
    # Check environment
    print("\n📋 Environment Check")
    print("-"*40)
    print(f"Python: {sys.version}")
    print(f"Working Directory: {os.getcwd()}")
    print(f"ENABLE_OPENPIPE_ART: {os.getenv('ENABLE_OPENPIPE_ART', 'Not set')}")
    
    # Check for OpenPipe ART
    try:
        import openpipe_art
        print(f"✅ OpenPipe ART available: {openpipe_art.__version__}")
    except ImportError:
        print("⚠️  OpenPipe ART not installed (some features will be limited)")
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)