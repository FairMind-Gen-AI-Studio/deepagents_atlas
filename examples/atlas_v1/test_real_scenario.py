#!/usr/bin/env python3
"""
Test con scenario realistico che dovrebbe attivare i subagent
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')

async def test_real_atlas_scenario():
    """Test con scenario che dovrebbe attivare investigation-agent e discussion-agent"""
    
    print("🎯 Testing Real Atlas V1 Scenario...")
    
    try:
        from atlas_agent import create_atlas_agent
        
        # Create agent CON MCP tools se disponibili (più realistico)
        agent = create_atlas_agent()
        
        print("🚀 Running realistic Atlas scenario...")
        
        # Questo dovrebbe attivare investigation-agent first
        result = await agent.run(
            user_request="I need to analyze project US-2024-1234 and create a technical implementation plan for the authentication module",
            project_id="fairmind-studio"
        )
        
        print(f"\n📊 Final result: {result['status']}")
        print(f"📁 Virtual files: {agent.list_virtual_files()}")
        
        # Mostra i files creati
        for filename in agent.list_virtual_files():
            content = agent.get_virtual_file(filename)
            print(f"   📄 {filename}: {len(content)} characters")
            if filename.endswith('.md'):
                print(f"      Preview: {content[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in real scenario test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("="*60)
    print("ATLAS V1 REAL SCENARIO DEBUG TEST")  
    print("="*60)
    success = asyncio.run(test_real_atlas_scenario())
    print("="*60)
    sys.exit(0 if success else 1)