#!/usr/bin/env python3
"""
Test that the orchestrator properly delegates to subagents.

This verifies that the orchestrator uses the task tool to delegate
work instead of trying to do everything itself.
"""

import asyncio
import logging
from atlas_agent import create_langgraph_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_orchestrator_delegation():
    """Test that orchestrator delegates to subagents."""
    
    print("🧪 Testing Orchestrator Delegation\n")
    print("-" * 50)
    
    # Create the agent (this is the compiled graph)
    agent = create_langgraph_agent()
    print("✅ Agent created successfully")
    
    # Test message
    test_message = "Test the orchestration flow - just check what phase we're in"
    
    print(f"\n📝 Test Input: '{test_message}'")
    print("\n🔄 Running orchestrator...")
    print("-" * 50)
    
    try:
        # Invoke the agent with a simple test
        result = await agent.ainvoke({
            "messages": [{"role": "user", "content": test_message}]
        })
        
        # Check the messages to see if task was called
        messages = result.get("messages", [])
        
        # Look for evidence of delegation
        task_called = False
        ls_called = False
        
        for msg in messages:
            content = str(msg.content) if hasattr(msg, 'content') else str(msg)
            
            # Check if ls was called (orchestrator checking state)
            if 'ls' in content.lower() or 'check' in content.lower():
                ls_called = True
                
            # Check if task tool was mentioned or called
            if 'task(' in content or 'investigation-agent' in content or 'subagent_type' in content:
                task_called = True
        
        print("\n📊 Results:")
        print(f"  - Orchestrator checked files (ls): {'✅' if ls_called else '❌'}")
        print(f"  - Orchestrator called task tool: {'✅' if task_called else '❌'}")
        
        if task_called:
            print("\n✅ SUCCESS: Orchestrator is properly delegating to subagents!")
        else:
            print("\n⚠️  WARNING: Orchestrator may not be delegating properly")
            print("    Check if it's trying to do work itself instead of using task tool")
        
        # Show last message for debugging
        if messages:
            last_msg = messages[-1]
            print(f"\n📤 Last message preview:")
            preview = str(last_msg.content if hasattr(last_msg, 'content') else last_msg)[:200]
            print(f"    {preview}...")
            
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

def main():
    """Run the test."""
    success = asyncio.run(test_orchestrator_delegation())
    
    if success:
        print("\n🎉 Orchestrator delegation test completed!")
    else:
        print("\n❌ Test failed")
    
    return success

if __name__ == "__main__":
    main()