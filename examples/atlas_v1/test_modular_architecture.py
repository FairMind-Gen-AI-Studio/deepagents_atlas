#!/usr/bin/env python3
"""
Test suite for the modular Atlas V1 architecture.

Verifies that the clean architecture works correctly after
decomposing the God class into focused agents.
"""

import sys
import asyncio
import logging
from pathlib import Path

# Add src to path for deepagents
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import the main agent
from atlas_agent import AtlasAgentV1, create_atlas_agent, agent as langgraph_agent
from atlas_coordinator import AtlasCoordinator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_modular_agents():
    """Test that all modular agents are properly structured."""
    try:
        from agents import (
            investigation_agent,
            discussion_agent,
            planning_agent,
            task_generation_agent,
            create_repository_analyzer
        )
        
        # Verify each agent has required fields
        for agent_config in [investigation_agent, discussion_agent, planning_agent, task_generation_agent]:
            assert "name" in agent_config, f"Missing 'name' in {agent_config}"
            assert "description" in agent_config, f"Missing 'description' in {agent_config}"
            assert "prompt" in agent_config, f"Missing 'prompt' in {agent_config}"
            print(f"✅ {agent_config['name']} structure valid")
        
        # Test dynamic repository analyzer creation
        repo_analyzer = create_repository_analyzer("test-repo")
        assert repo_analyzer["name"] == "repository-analyzer-test-repo"
        print("✅ Repository analyzer creation works")
        
        return True
    except Exception as e:
        print(f"❌ Modular agents test failed: {e}")
        return False

def test_coordinator():
    """Test the lightweight coordinator."""
    try:
        # Create coordinator without MCP tools for simplicity
        coordinator = AtlasCoordinator(mcp_tools={})
        assert coordinator is not None
        assert len(coordinator.agents) == 4
        print("✅ Coordinator created successfully")
        
        status = coordinator.get_status()
        assert status["coordinator"] == "active"
        assert status["agents_available"] == 4
        print(f"✅ Coordinator status: {status}")
        
        return True
    except Exception as e:
        print(f"❌ Coordinator test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_main_agent():
    """Test the main AtlasAgentV1 class."""
    try:
        # Test with empty tools dict
        agent = AtlasAgentV1(available_tools={})
        assert agent is not None
        assert agent.coordinator is not None
        print("✅ AtlasAgentV1 created successfully")
        
        status = agent.get_status()
        assert "coordinator" in status
        print(f"✅ Agent status: {status}")
        
        # Test convenience function
        agent2 = create_atlas_agent(available_tools={})
        assert agent2 is not None
        print("✅ create_atlas_agent function works")
        
        return True
    except Exception as e:
        print(f"❌ Main agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_langgraph_compatibility():
    """Test that the agent works with langgraph.json."""
    try:
        # Import the graph types
        from langgraph.graph.state import CompiledStateGraph
        
        # Check that the agent is created
        assert langgraph_agent is not None
        print("✅ LangGraph agent exists")
        
        # Verify it's a CompiledStateGraph
        assert isinstance(langgraph_agent, CompiledStateGraph)
        print("✅ LangGraph agent is CompiledStateGraph")
        
        # Check required methods
        assert hasattr(langgraph_agent, 'ainvoke')
        assert hasattr(langgraph_agent, 'invoke')
        print("✅ LangGraph agent has required methods")
        
        return True
    except Exception as e:
        print(f"❌ LangGraph compatibility test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def analyze_architecture():
    """Analyze the new architecture metrics."""
    files = {
        "agents/investigation_agent.py": Path("agents/investigation_agent.py"),
        "agents/discussion_agent.py": Path("agents/discussion_agent.py"),
        "agents/planning_agent.py": Path("agents/planning_agent.py"),
        "agents/task_generation_agent.py": Path("agents/task_generation_agent.py"),
        "atlas_coordinator.py": Path("atlas_coordinator.py"),
        "atlas_agent.py": Path("atlas_agent.py"),
    }
    
    print("\n📊 Architecture Analysis:")
    print("-" * 40)
    
    total_lines = 0
    for name, path in files.items():
        if path.exists():
            lines = len(path.read_text().splitlines())
            total_lines += lines
            print(f"{name:40} {lines:4} lines")
    
    print("-" * 40)
    print(f"{'Total':40} {total_lines:4} lines")
    
    # Compare with old implementation
    old_path = Path("atlas_agent_old.py")
    if old_path.exists():
        old_lines = len(old_path.read_text().splitlines())
        reduction = ((old_lines - total_lines) / old_lines) * 100
        print(f"\n📈 Comparison:")
        print(f"  Old implementation: {old_lines} lines")
        print(f"  New implementation: {total_lines} lines")
        print(f"  Reduction: {reduction:.1f}%")
    
    return total_lines

async def test_basic_execution():
    """Test basic execution flow."""
    try:
        agent = create_atlas_agent(available_tools={})
        
        # Test that the agent can be invoked
        # Note: Full execution would require mocking deepagents
        print("✅ Agent ready for execution")
        
        # Verify async methods exist
        assert hasattr(agent, 'run')
        assert asyncio.iscoroutinefunction(agent.run)
        print("✅ Async run method available")
        
        return True
    except Exception as e:
        print(f"❌ Execution test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing Atlas V1 Modular Architecture\n")
    
    tests = [
        ("Modular Agents", test_modular_agents),
        ("Coordinator", test_coordinator),
        ("Main Agent", test_main_agent),
        ("LangGraph Compatibility", test_langgraph_compatibility),
    ]
    
    passed = 0
    for test_name, test_func in tests:
        print(f"\n📝 {test_name}:")
        print("-" * 40)
        if test_func():
            passed += 1
    
    # Run async test
    print(f"\n📝 Basic Execution:")
    print("-" * 40)
    if asyncio.run(test_basic_execution()):
        passed += 1
    
    # Architecture analysis
    analyze_architecture()
    
    print(f"\n\n✨ Results: {passed}/{len(tests) + 1} tests passed")
    
    if passed == len(tests) + 1:
        print("🎉 All tests passed! Architecture is clean and working.")
    else:
        print("⚠️  Some tests failed. Please review.")
    
    return passed == len(tests) + 1

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)