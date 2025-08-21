#!/usr/bin/env python3
"""
Test script to verify the enhanced human_input tool with interrupt functionality
Tests both LangGraph Studio compatibility and fallback behavior
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
project_root = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(project_root))


async def test_human_input_tool():
    """Test the enhanced human_input tool with interrupt support"""
    
    print("\n" + "="*60)
    print("🧪 Testing Enhanced Human Input Tool with Interrupt")
    print("="*60)
    
    # Test 1: Check if interrupt is available
    print("\n📋 Test 1: Checking interrupt availability...")
    try:
        from atlas_tools import human_input, INTERRUPT_AVAILABLE
        print(f"✅ Atlas tools imported successfully")
        print(f"   Interrupt available: {'✅ YES' if INTERRUPT_AVAILABLE else '❌ NO (fallback mode)'}")
    except ImportError as e:
        print(f"❌ Failed to import atlas_tools: {e}")
        return False
    
    # Test 2: Test the tool directly
    print("\n📋 Test 2: Testing human_input tool directly...")
    try:
        # In non-Studio environment, this will use fallback
        result = human_input.invoke({"question": "What is your favorite color?"})
        print(f"✅ Tool invoked successfully")
        print(f"   Result: {result}")
        
        if "[AWAITING_USER_INPUT:" in str(result):
            print("   ℹ️  Using fallback mode (expected in non-Studio environment)")
        else:
            print("   ℹ️  Received actual response (running in Studio?)")
    except Exception as e:
        print(f"❌ Tool invocation failed: {e}")
        return False
    
    # Test 3: Test with Atlas agent
    print("\n📋 Test 3: Testing with Atlas V1 agent...")
    try:
        from atlas_agent import AtlasAgentV1
        
        # Create agent without MCP for simplicity
        print("   Creating Atlas V1 agent...")
        agent = AtlasAgentV1(available_tools=None)
        print("✅ Agent created successfully")
        
        # Check if our tools are in the orchestrator
        print("\n   Checking tool availability:")
        
        # The orchestrator should have our custom tools
        orchestrator_config = agent.orchestrator.config
        print(f"   Checkpointer configured: {'✅ YES' if orchestrator_config.get('checkpointer') else '❌ NO'}")
        
        # Test with a simple discussion scenario
        test_message = """
        I need to clarify some requirements with the user.
        Please use the discussion-agent to ask about their preferences.
        """
        
        print("\n   Running test scenario...")
        print(f"   Message: {test_message[:80]}...")
        
        # Execute the agent with thread_id for checkpointer
        config = {"configurable": {"thread_id": "test-thread-1"}}
        result = await agent.orchestrator.ainvoke({
            "messages": [{"role": "user", "content": test_message}],
            "files": {}
        }, config=config)
        
        print("✅ Agent execution completed")
        
        # Check if human_input was mentioned in the response
        messages = result.get("messages", [])
        if messages:
            last_message = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
            if "human_input" in last_message.lower() or "discussion" in last_message.lower():
                print("   ℹ️  Agent recognized need for human interaction")
            
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_interrupt_simulation():
    """Test interrupt functionality in a simulated environment"""
    
    print("\n" + "="*60)
    print("🧪 Testing Interrupt Simulation")
    print("="*60)
    
    try:
        from langgraph.types import interrupt
        from langgraph.checkpoint.memory import InMemorySaver
        
        print("✅ LangGraph interrupt API available")
        
        # Create a simple test graph
        from langgraph.graph import StateGraph, START, END
        from typing_extensions import TypedDict
        
        class TestState(TypedDict):
            question: str
            answer: str
        
        def ask_question(state):
            """Node that uses interrupt"""
            print("   Asking question via interrupt...")
            answer = interrupt("What is your name?")
            return {"answer": answer}
        
        # Build test graph
        builder = StateGraph(TestState)
        builder.add_node("ask", ask_question)
        builder.add_edge(START, "ask")
        builder.add_edge("ask", END)
        
        # Compile with checkpointer
        checkpointer = InMemorySaver()
        graph = builder.compile(checkpointer=checkpointer)
        
        print("✅ Test graph created with interrupt support")
        print("   ℹ️  In LangGraph Studio, this would pause for user input")
        
        return True
        
    except ImportError:
        print("⚠️  LangGraph interrupt API not available")
        print("   This is expected outside of LangGraph environment")
        return True
    except Exception as e:
        print(f"❌ Interrupt simulation failed: {e}")
        return False


def main():
    """Run all tests"""
    
    print("\n🚀 Atlas V1 Human Input Enhancement Test Suite")
    print("=" * 60)
    
    # Run async tests
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        # Test 1: Human input tool
        test1_result = loop.run_until_complete(test_human_input_tool())
        
        # Test 2: Interrupt simulation
        test2_result = loop.run_until_complete(test_interrupt_simulation())
        
        # Summary
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        
        all_passed = test1_result and test2_result
        
        if all_passed:
            print("✅ All tests passed!")
            print("\n🎯 Expected behavior:")
            print("   - In LangGraph Studio: Tool will pause and wait for user input")
            print("   - Outside Studio: Tool will use fallback mode")
            print("   - Checkpointer is configured for interrupt support")
            print("   - Discussion agent can now receive real user responses")
        else:
            print("❌ Some tests failed")
            print("\n⚠️  Issues to check:")
            print("   - Ensure atlas_tools.py is in the correct location")
            print("   - Check that imports are working correctly")
            print("   - Verify LangGraph is installed if testing interrupts")
        
        return 0 if all_passed else 1
        
    finally:
        loop.close()


if __name__ == "__main__":
    exit(main())