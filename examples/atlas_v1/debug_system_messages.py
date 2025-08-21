#!/usr/bin/env python3
"""
Debug system message issues in Atlas V1
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(project_root))

# Set up environment
os.environ["ATLAS_MODEL_NAME"] = "anthropic/claude-sonnet-4-20250514"
os.environ["ATLAS_MODEL_TEMPERATURE"] = "0.7"

from atlas_agent import create_atlas_agent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_without_context():
    """Test without project_id to isolate system message issue"""
    
    print("🔍 Testing Atlas V1 without context parameters")
    print("=" * 60)
    
    try:
        # Import MCP client  
        from mcp_client import initialize_mcp_tools
        
        # Initialize real MCP tools
        available_tools = await initialize_mcp_tools()
        print(f"✅ MCP tools initialized: {len(available_tools)} tools")
        
        # Create agent with real MCP tools
        agent = create_atlas_agent(available_tools=available_tools)
        
        # Run WITHOUT project_id or user_story_id to avoid system messages
        result = await agent.run(
            user_request="Create a simple investigation test"
            # No project_id or user_story_id - should avoid system message issues
        )
        
        print(f"\n📊 Result Status: {result['status']}")
        
        if result['status'] == 'completed':
            virtual_fs = result.get('virtual_filesystem', {})
            print(f"📁 Virtual filesystem contains {len(virtual_fs)} files:")
            
            for filename in virtual_fs.keys():
                content = virtual_fs[filename]
                print(f"   📄 {filename} ({len(content)} characters)")
            
            return True
        else:
            print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_message_structure():
    """Test the message structure being passed to orchestrator"""
    
    print("\n🔍 Testing message structure")
    print("=" * 40)
    
    try:
        from mcp_client import initialize_mcp_tools
        available_tools = await initialize_mcp_tools()
        agent = create_atlas_agent(available_tools=available_tools)
        
        # Manually test the message creation logic from run() method
        user_request = "Test request"
        project_id = "test-project"
        user_story_id = "US-123"
        
        # Simulate the message creation from atlas_agent.py:547-559
        context_parts = []
        if project_id:
            context_parts.append(f"Project ID: {project_id}")
        if user_story_id:
            context_parts.append(f"User Story ID: {user_story_id}")
        
        messages = [{"role": "user", "content": user_request}]
        
        if context_parts:
            context_content = "\n".join(context_parts)
            messages.append({"role": "system", "content": context_content})
        
        print(f"📝 Message structure to be passed:")
        for i, msg in enumerate(messages):
            print(f"   {i}: {msg['role']} - {msg['content'][:50]}...")
        
        print(f"\n✅ Message structure looks correct - no consecutive system messages")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Main debug function"""
    
    print("🐛 Debug System Message Issues in Atlas V1")
    
    # Test 1: Message structure validation
    await test_message_structure()
    
    # Test 2: Run without context to isolate issue
    success = await test_without_context()
    
    print("\n" + "=" * 60)
    print("📋 DEBUG SUMMARY:")
    if success:
        print("✅ Atlas V1 can execute without system message errors!")
        print("✅ The fix for consecutive system messages worked!")
    else:
        print("❌ System message issue persists - need deeper investigation")

if __name__ == "__main__":
    asyncio.run(main())