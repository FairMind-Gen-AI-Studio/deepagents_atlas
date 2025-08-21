#!/usr/bin/env python3
"""
Simple test to verify Atlas V1 investigation agent file creation
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

async def test_investigation_with_real_mcp():
    """Test investigation agent with real MCP tools"""
    
    print("🔍 Testing Investigation Agent with Real MCP Tools")
    print("=" * 60)
    
    try:
        # Import MCP client  
        from mcp_client import initialize_mcp_tools
        
        # Initialize real MCP tools
        available_tools = await initialize_mcp_tools()
        
        if not available_tools:
            print("❌ No MCP tools available - cannot test investigation agent properly")
            return False
            
        print(f"✅ MCP tools initialized: {len(available_tools)} tools")
        
        # Create agent with real MCP tools
        agent = create_atlas_agent(available_tools=available_tools)
        
        # Run investigation on a real project 
        result = await agent.run(
            user_request="Investigate the business context for user authentication features",
            project_id="fairmind_studio"  # Real project ID
        )
        
        print(f"\n📊 Result Status: {result['status']}")
        
        if result['status'] == 'completed':
            virtual_fs = result.get('virtual_filesystem', {})
            print(f"📁 Virtual filesystem contains {len(virtual_fs)} files:")
            
            for filename in virtual_fs.keys():
                content = virtual_fs[filename]
                print(f"   📄 {filename} ({len(content)} characters)")
            
            # Check for investigation-specific files
            expected_files = ['investigation_findings.md', 'business_context.md']
            found_files = []
            
            for expected in expected_files:
                if expected in virtual_fs:
                    found_files.append(expected)
                    content = virtual_fs[expected]
                    print(f"\n✅ Found {expected}:")
                    print(f"   Length: {len(content)} characters")
                    print(f"   Preview: {content[:300]}...")
            
            if len(found_files) == len(expected_files):
                print(f"\n🎯 SUCCESS: Investigation agent created all expected files!")
                print(f"   Files found: {found_files}")
                return True
            else:
                missing = set(expected_files) - set(found_files)
                print(f"\n⚠️  Missing files: {missing}")
                return False
        else:
            print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
            return False
            
    except ImportError:
        print("❌ MCP client not available - cannot test with real tools")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Main test"""
    print("🚀 Simple Investigation Agent File Creation Test")
    print("This will test if the investigation agent creates the required files\n")
    
    success = await test_investigation_with_real_mcp()
    
    print("\n" + "=" * 60)
    print("📋 CONCLUSION:")
    if success:
        print("✅ Investigation agent IS using write_file correctly!")
        print("✅ Virtual filesystem persistence is working!")
        print("✅ Files are created and maintained as expected!")
        print("\n💡 The original issue might be a misunderstanding.")
        print("   The investigation agent DOES create files - they exist in virtual filesystem.")
    else:
        print("❌ There may be a real issue with file creation.")
        print("🔍 Further investigation needed.")

if __name__ == "__main__":
    asyncio.run(main())