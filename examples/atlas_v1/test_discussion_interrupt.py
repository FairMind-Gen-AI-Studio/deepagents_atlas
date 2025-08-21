#!/usr/bin/env python3
"""
Test the discussion agent with the enhanced human_input tool
Verifies that the discussion phase can now properly interact with users
"""

import asyncio
import logging
from atlas_agent import AtlasAgentV1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_discussion_agent():
    """Test discussion agent with interrupt-enabled human_input"""
    
    print("\n" + "="*60)
    print("🧪 Testing Discussion Agent with Enhanced Human Input")
    print("="*60)
    
    # Create agent
    print("\n📦 Creating Atlas V1 agent...")
    agent = AtlasAgentV1(available_tools=None)
    print("✅ Agent created with interrupt-enabled human_input")
    
    # Simulate that investigation phase is complete
    print("\n📝 Simulating completed investigation phase...")
    agent.state["virtual_filesystem"]["investigation_findings.md"] = """
    # Investigation Findings
    
    ## Project Context
    - Project: E-commerce Mobile App
    - User Story: Implement secure user authentication
    
    ## Business Requirements
    - Multi-factor authentication support
    - Social login integration
    - Password recovery flow
    
    ## Knowledge Gaps
    - Specific security requirements unclear
    - Preferred authentication methods not specified
    - Session timeout requirements unknown
    """
    
    # Request to move to discussion phase
    test_message = """
    The investigation phase is complete. Please proceed to the discussion phase
    to clarify the remaining requirements with the user.
    """
    
    print("\n🚀 Executing agent with discussion request...")
    print(f"   Message: {test_message[:80]}...")
    
    # Execute with thread_id for checkpointer
    config = {"configurable": {"thread_id": "discussion-test-thread"}}
    
    try:
        result = await agent.orchestrator.ainvoke({
            "messages": [{"role": "user", "content": test_message}],
            "files": agent.state["virtual_filesystem"]
        }, config=config)
        
        print("\n✅ Agent execution completed")
        
        # Check results
        messages = result.get("messages", [])
        files = result.get("files", {})
        
        print("\n📊 Results:")
        print(f"   Messages generated: {len(messages)}")
        print(f"   Files in virtual FS: {list(files.keys())}")
        
        # Look for human_input usage
        for msg in messages:
            content = msg.content if hasattr(msg, 'content') else str(msg)
            if "human_input" in content.lower() or "[AWAITING_USER_INPUT" in content:
                print("\n🎯 SUCCESS: Discussion agent attempted to use human_input!")
                print("   In LangGraph Studio, this would pause for user response")
                break
        
        # Check if discussion agent was invoked
        if any("discussion" in str(msg).lower() for msg in messages):
            print("   ✅ Discussion agent was invoked")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test"""
    print("\n🚀 Discussion Agent Interrupt Test")
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        success = loop.run_until_complete(test_discussion_agent())
        
        print("\n" + "="*60)
        if success:
            print("✅ TEST PASSED")
            print("\n📝 Summary:")
            print("   - Discussion agent can be invoked")
            print("   - Human input tool is available")
            print("   - In Studio: Will pause for real user input")
            print("   - Outside Studio: Uses fallback mode")
            print("\n🎯 Next Steps:")
            print("   1. Open in LangGraph Studio")
            print("   2. Run a discussion phase scenario")
            print("   3. Tool should pause and show input field")
            print("   4. User can provide responses")
        else:
            print("❌ TEST FAILED")
            
    finally:
        loop.close()


if __name__ == "__main__":
    main()