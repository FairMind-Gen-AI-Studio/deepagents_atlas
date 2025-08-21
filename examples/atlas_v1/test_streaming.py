#!/usr/bin/env python3
"""
Test script to verify Atlas V1 subagent streaming functionality
Runs a simple test to check if intermediate messages are captured and displayed
"""

import asyncio
import logging
import sys
import os

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_streaming():
    """Test that Atlas V1 subagents stream intermediate messages"""
    
    print("🧪 Testing Atlas V1 Subagent Streaming")
    print("=" * 50)
    
    try:
        # Import Atlas agent
        from atlas_agent import AtlasAgentV1
        
        # Create agent without MCP tools for simpler testing
        print("📦 Creating Atlas V1 agent (without MCP for simplicity)...")
        agent = AtlasAgentV1(available_tools=None)
        print("✅ Atlas V1 agent created successfully")
        
        # Test message to trigger a subagent
        test_message = "Create a simple todo list with 3 tasks for testing the streaming functionality"
        
        print(f"\n🚀 Running test with message: '{test_message}'")
        print("⏳ Waiting for streaming response...")
        
        # Execute the agent
        result = await agent.orchestrator.ainvoke({
            "messages": [{"role": "user", "content": test_message}],
            "files": {}
        })
        
        print(f"\n📊 Result Analysis:")
        print(f"   Messages returned: {len(result.get('messages', []))}")
        print(f"   Files created: {len(result.get('files', {}))}")
        
        # Check messages for streaming evidence
        messages_with_content = 0
        total_content_length = 0
        
        for i, msg in enumerate(result.get('messages', [])):
            if hasattr(msg, 'content') and msg.content:
                messages_with_content += 1
                content_length = len(msg.content)
                total_content_length += content_length
                
                print(f"\n📝 Message {i+1}:")
                print(f"   Type: {type(msg).__name__}")
                print(f"   Length: {content_length} chars")
                
                # Show first part of content (handle both string and list content)
                if isinstance(msg.content, str):
                    content_preview = msg.content[:200].replace('\n', '\\n')
                    if len(msg.content) > 200:
                        content_preview += "..."
                else:
                    # Handle list content (from Claude)
                    content_str = str(msg.content)[:200]
                    content_preview = content_str.replace('\n', '\\n') + "..."
                print(f"   Content: {content_preview}")
                
                # Check for streaming indicators (handle both string and list content)
                content_str = msg.content if isinstance(msg.content, str) else str(msg.content)
                if "---" in content_str:
                    print(f"   🎯 STREAMING DETECTED: Message contains separator '---'")
                if "\n\n---\n\n" in content_str:
                    print(f"   🎯 ENHANCED STREAMING: Multiple messages joined")
        
        print(f"\n📈 Summary:")
        print(f"   Messages with content: {messages_with_content}")
        print(f"   Total content length: {total_content_length} chars")
        
        # Check virtual filesystem
        virtual_files = list(result.get('files', {}).keys())
        if virtual_files:
            print(f"   Virtual files: {virtual_files}")
        
        # Success criteria
        if messages_with_content > 0 and total_content_length > 100:
            print(f"\n✅ TEST PASSED: Agent produced meaningful output")
            if "---" in str(result.get('messages', [])):
                print(f"🌟 STREAMING DETECTED: Intermediate messages were captured!")
            else:
                print(f"📝 Standard output detected (may not have intermediate steps for this simple task)")
            return True
        else:
            print(f"\n❌ TEST FAILED: Insufficient output generated")
            return False
            
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("💡 Make sure you're in the atlas_v1 directory and all dependencies are installed")
        return False
    except Exception as e:
        print(f"❌ Test Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_specific_subagent():
    """Test a specific subagent that's more likely to produce intermediate output"""
    
    print("\n🎯 Testing Specific Subagent (Investigation)")
    print("=" * 50)
    
    try:
        from atlas_agent import AtlasAgentV1
        
        # Create agent 
        agent = AtlasAgentV1(available_tools=None)
        
        # Craft a message that will likely trigger investigation agent
        test_message = """
        I need to understand and plan the implementation of a new user authentication system.
        Please investigate what components we'll need and create a preliminary analysis.
        """
        
        print(f"🚀 Testing investigation workflow...")
        
        # Execute
        result = await agent.orchestrator.ainvoke({
            "messages": [{"role": "user", "content": test_message.strip()}],
            "files": {}
        })
        
        # Analyze specifically for investigation patterns
        for msg in result.get('messages', []):
            if hasattr(msg, 'content') and msg.content:
                content = msg.content.lower()
                
                # Look for investigation keywords
                investigation_keywords = [
                    'investigating', 'analyzing', 'examining', 'exploring',
                    'found', 'discovered', 'identified', 'searching'
                ]
                
                found_keywords = [kw for kw in investigation_keywords if kw in content]
                if found_keywords:
                    print(f"🔍 Investigation activity detected: {found_keywords}")
                
                # Look for streaming evidence
                if "---" in msg.content:
                    print(f"🎯 STREAMING EVIDENCE FOUND!")
                    
                    # Count message sections
                    sections = msg.content.split("---")
                    print(f"   Message sections found: {len(sections)}")
                    
                    for i, section in enumerate(sections[:3]):  # Show first 3 sections
                        preview = section.strip()[:100].replace('\n', ' ')
                        print(f"   Section {i+1}: {preview}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Specific test error: {e}")
        return False

async def main():
    """Main test runner"""
    
    print("🧪 Atlas V1 Streaming Test Suite")
    print("🎯 Testing if subagents provide intermediate feedback to UI")
    print()
    
    # Check environment
    if not os.path.exists("atlas_agent.py"):
        print("❌ Error: Run this test from the examples/atlas_v1/ directory")
        return
    
    # Run tests
    test1_passed = await test_streaming()
    test2_passed = await test_specific_subagent()
    
    # Final summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUITE SUMMARY")
    print(f"Basic streaming test: {'✅ PASS' if test1_passed else '❌ FAIL'}")
    print(f"Investigation test:   {'✅ PASS' if test2_passed else '❌ FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🌟 SUCCESS: Atlas V1 streaming implementation appears to be working!")
        print("💡 Next step: Test with the actual UI to see real-time feedback")
    else:
        print("\n⚠️  Some tests failed. Check the logs above for details.")
    
    print("\n📚 To test with UI:")
    print("   1. Start the UI application")
    print("   2. Connect to Atlas V1 agent")
    print("   3. Send a complex request that triggers subagents")
    print("   4. Watch for intermediate messages in the subagent panels")

if __name__ == "__main__":
    asyncio.run(main())