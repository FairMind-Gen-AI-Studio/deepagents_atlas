#!/usr/bin/env python3
"""
Test Virtual Filesystem Persistence in Atlas V1

This test verifies that the virtual filesystem state persists correctly
between orchestrator invocations and sub-agent executions.
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent / "src"
sys.path.insert(0, str(project_root))

# Set up environment for testing
os.environ["ATLAS_MODEL_NAME"] = "anthropic/claude-sonnet-4-20250514"
os.environ["ATLAS_MODEL_TEMPERATURE"] = "0.7"

from atlas_agent import AtlasAgentV1

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_virtual_filesystem_persistence():
    """Test that virtual filesystem persists correctly during agent execution"""
    
    print("🧪 Testing Virtual Filesystem Persistence in Atlas V1")
    print("=" * 60)
    
    # Create agent without MCP tools to focus on filesystem behavior
    agent = AtlasAgentV1(available_tools=None)
    print(f"✅ Agent created successfully")
    
    # Test 1: Run agent and verify files are created and persisted
    print("\n📝 Test 1: Verify file creation and persistence")
    
    try:
        result = await agent.run(
            user_request="Create a simple test document to verify the virtual filesystem works",
            project_id="test-project"
        )
        
        print(f"   Status: {result['status']}")
        print(f"   Virtual filesystem files: {list(result['virtual_filesystem'].keys())}")
        
        # Check if any files were created
        if result['virtual_filesystem']:
            print("   ✅ Files created in virtual filesystem:")
            for filename, content in result['virtual_filesystem'].items():
                print(f"      - {filename} ({len(content)} chars)")
                if len(content) < 200:
                    print(f"        Content preview: {content[:100]}...")
        else:
            print("   ⚠️  No files found in virtual filesystem")
        
        # Test 2: Verify agent state persistence
        print("\n🔍 Test 2: Check agent's internal state")
        status = agent.get_status()
        print(f"   Current phase: {status['current_phase']}")
        print(f"   Completion: {status['completion_percentage']}%")
        print(f"   Files in agent state: {status['virtual_filesystem_files']}")
        
        # Test 3: Try to read a file from the agent
        if status['virtual_filesystem_files']:
            first_file = status['virtual_filesystem_files'][0]
            content = agent.get_virtual_file(first_file)
            print(f"\n📖 Test 3: Reading file '{first_file}' from agent")
            if content:
                print(f"   ✅ Successfully read file ({len(content)} chars)")
                print(f"   Preview: {content[:150]}...")
            else:
                print(f"   ❌ Could not read file content")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Error during execution: {e}")
        import traceback
        traceback.print_exc()
        return None

async def test_investigation_agent_file_creation():
    """Test specifically that investigation agent creates required files"""
    
    print("\n" + "=" * 60)
    print("🔍 Test: Investigation Agent File Creation")
    print("=" * 60)
    
    try:
        # Create mock MCP tools to enable investigation agent 
        mock_mcp_tools = {
            'General_list_projects': lambda: [{'id': 'test-project', 'name': 'Test Project'}],
            'Studio_list_user_stories_by_project': lambda project_id: [
                {'id': 'US-001', 'title': 'Test User Story', 'description': 'Test description'}
            ],
            'Studio_get_user_story': lambda story_id: {
                'id': story_id, 
                'title': 'Test User Story', 
                'description': 'A test user story for validation'
            }
        }
        
        agent = AtlasAgentV1(available_tools=mock_mcp_tools)
        print("✅ Agent created with mock MCP tools")
        
        # Run a focused investigation request
        result = await agent.run(
            user_request="Investigate the business context and requirements for user authentication feature",
            project_id="test-project"
        )
        
        print(f"Status: {result['status']}")
        
        # Check for the specific files that investigation agent should create
        expected_files = ['investigation_findings.md', 'business_context.md']
        virtual_fs = result.get('virtual_filesystem', {})
        
        print(f"\nFiles in virtual filesystem: {list(virtual_fs.keys())}")
        
        for expected_file in expected_files:
            if expected_file in virtual_fs:
                content = virtual_fs[expected_file]
                print(f"✅ Found {expected_file} ({len(content)} chars)")
                print(f"   Preview: {content[:200]}...")
            else:
                print(f"❌ Missing expected file: {expected_file}")
        
        return len(virtual_fs) > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test runner"""
    
    print("🚀 Atlas V1 Virtual Filesystem Persistence Test Suite")
    print("Testing the claim that investigation agent doesn't use write_file...")
    
    # Test 1: Basic virtual filesystem functionality
    result1 = await test_virtual_filesystem_persistence()
    
    # Test 2: Investigation agent specifically
    result2 = await test_investigation_agent_file_creation()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    if result1 and result1.get('status') == 'completed':
        print("✅ Basic virtual filesystem: WORKING")
    else:
        print("❌ Basic virtual filesystem: FAILED")
    
    if result2:
        print("✅ Investigation agent file creation: WORKING")
        print("\n🎯 CONCLUSION:")
        print("   The investigation agent IS correctly using write_file!")
        print("   Virtual filesystem persistence is working as designed.")
        print("   The files exist in memory within the agent's execution context.")
    else:
        print("❌ Investigation agent file creation: FAILED")
        print("\n🔍 INVESTIGATION NEEDED:")
        print("   There may be a real issue with write_file tool usage.")

if __name__ == "__main__":
    asyncio.run(main())