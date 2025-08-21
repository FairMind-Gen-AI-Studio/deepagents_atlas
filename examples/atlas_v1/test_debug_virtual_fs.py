#!/usr/bin/env python3
"""
Test specifico per il debug del virtual filesystem
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the src directory to Python path to use local deepagents
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

# Set up more verbose logging to catch debug messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_debug_virtual_filesystem():
    """Test con focus sul debug dei files nello state"""
    
    print("🔍 Test Debug Virtual Filesystem...")
    
    try:
        from atlas_agent import create_atlas_agent
        
        # Create agent senza MCP per semplicità
        print("📦 Creating Atlas agent (debug mode)...")
        agent = create_atlas_agent(available_tools=None)
        
        # Test con un task molto semplice che dovrebbe creare files
        print("🚀 Running simple virtual filesystem test...")
        
        result = await agent.run(
            user_request="Write 'hello' to test.txt, then create todo.md with 'task1', then list all files",
            project_id="debug-test"
        )
        
        print(f"\n📊 Result: {result['status']}")
        print(f"📁 Virtual files after: {agent.list_virtual_files()}")
        
        # Mostra il contenuto dei files se ci sono
        for filename in agent.list_virtual_files():
            content = agent.get_virtual_file(filename)
            print(f"   📄 {filename}: '{content[:50]}...' ({len(content)} chars)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_debug_virtual_filesystem())
    sys.exit(0 if success else 1)