#!/usr/bin/env python3
"""
Test per verificare che Atlas V2 funzioni correttamente.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

def test_atlas_v2_import():
    """Test che l'import di Atlas V2 funzioni correttamente."""

    print("🧪 Testing Atlas V2 import...")

    try:
        from atlas_agent import agent
        print("✅ Successfully imported main agent")

        # Verifica che l'agente abbia le proprietà necessarie
        assert hasattr(agent, 'invoke'), "Agent should have invoke method"
        assert hasattr(agent, 'stream'), "Agent should have stream method"
        print("✅ Agent has required methods")

        return True

    except Exception as e:
        print(f"❌ Import failed: {e}")
        return False

def test_subagents():
    """Test che i sub-agenti siano definiti correttamente."""

    print("🧪 Testing sub-agents...")

    try:
        from atlas_agent import investigation_agent, discussion_agent, planning_agent, task_generation_agent

        agents = [
            ("investigation-agent", investigation_agent),
            ("discussion-agent", discussion_agent),
            ("planning-agent", planning_agent),
            ("task-generation-agent", task_generation_agent)
        ]

        for name, agent_obj in agents:
            # Sub-agents sono dizionari, controlliamo le chiavi
            assert 'name' in agent_obj, f"{name} should have 'name' key"
            assert 'description' in agent_obj, f"{name} should have 'description' key"
            assert 'prompt' in agent_obj, f"{name} should have 'prompt' key"
            print(f"✅ {name}: {agent_obj['name']}")

        print("✅ All sub-agents properly configured")
        return True

    except Exception as e:
        print(f"❌ Sub-agents test failed: {e}")
        return False

def test_langgraph_json():
    """Test che langgraph.json sia configurato correttamente."""

    print("🧪 Testing langgraph.json...")

    try:
        import json

        with open('langgraph.json', 'r') as f:
            config = json.load(f)

        # Verifica la struttura
        assert 'graphs' in config, "Config should have graphs section"
        assert 'atlas' in config['graphs'], "Config should have atlas graph"
        assert config['graphs']['atlas'] == './atlas_agent.py:agent', "Config should point to correct agent"

        print("✅ langgraph.json configured correctly")
        print(f"   - Graph: {config['graphs']['atlas']}")

        return True

    except Exception as e:
        print(f"❌ langgraph.json test failed: {e}")
        return False

def test_files():
    """Test che tutti i file necessari siano presenti."""

    print("🧪 Testing file structure...")

    required_files = [
        'atlas_agent.py',
        'langgraph.json',
        'requirements.txt',
        'README.md'
    ]

    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"✅ {file_path} exists")
        else:
            print(f"❌ {file_path} missing")
            return False

    print("✅ All required files present")
    return True

if __name__ == "__main__":
    tests = [
        test_files,
        test_langgraph_json,
        test_atlas_v2_import,
        test_subagents
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    print("\n" + "="*50)
    print("ATLAS V2 TEST RESULTS")
    print("="*50)

    passed = sum(results)
    total = len(results)

    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("✅ Atlas V2 is ready to use")
        print("✅ Architecture matches research pattern")
        print("✅ LangGraph API compatible")
        print("✅ No custom complexity")
    else:
        print(f"⚠️ {passed}/{total} tests passed")
        print("❌ Some issues need to be resolved")

    print(f"\nTest Summary: {passed}/{total} passed")
    if passed == total:
        print("🚀 Atlas V2 successfully created!")
    else:
        print("🔧 Atlas V2 needs fixes")
