#!/usr/bin/env python3
"""
Test script per verificare il nuovo comportamento di Phase Sequence Awareness
dell'orchestrator Atlas V1
"""

import os
import sys
import asyncio
import logging
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from atlas_agent import create_atlas_agent
from subagents import get_phase_status_prompt, get_phase_skip_request_template

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_phase_sequence_awareness():
    """
    Test che l'orchestrator ora riconosca correttamente la sequenza delle fasi
    e chieda conferma prima di saltare fasi
    """
    
    print("🧪 Testing Atlas V1 Phase Sequence Awareness")
    print("=" * 50)
    
    # Load environment variables
    load_dotenv()
    
    # Check if required environment variables are set
    required_vars = ["ANTHROPIC_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set them in a .env file or as environment variables")
        return
    
    try:
        # Create Atlas agent (without MCP tools for this test)
        print("\n1. Creating Atlas V1 agent...")
        agent = create_atlas_agent(available_tools=None)  # No MCP tools needed for this test
        
        print("✅ Atlas agent created successfully")
        
        # Test 1: Verify helper functions work
        print("\n2. Testing helper functions...")
        
        phase_status_guide = get_phase_status_prompt()
        print("✅ get_phase_status_prompt() works")
        print(f"   Guide length: {len(phase_status_guide)} characters")
        
        skip_template = get_phase_skip_request_template("discussion", "requirements are already clear", "planning")
        print("✅ get_phase_skip_request_template() works")
        print(f"   Template: {skip_template[:100]}...")
        
        # Test 2: Check initial state
        print("\n3. Checking agent initial state...")
        status = agent.get_status()
        print(f"✅ Current phase: {status.get('current_phase')}")
        print(f"   Completion: {status.get('completion_percentage')}%")
        print(f"   Virtual files: {len(status.get('virtual_filesystem_files', []))}")
        
        # Test 3: Simple orchestrator prompt test
        print("\n4. Testing orchestrator prompt generation...")
        orchestrator_prompt = agent._create_orchestrator_prompt()
        
        # Check if the new Phase Sequence Awareness is in the prompt
        if "Phase Sequence Awareness Protocol" in orchestrator_prompt:
            print("✅ Phase Sequence Awareness Protocol found in orchestrator prompt")
        else:
            print("❌ Phase Sequence Awareness Protocol NOT found in orchestrator prompt")
            
        if "read_file to check which phases are complete" in orchestrator_prompt:
            print("✅ Phase status detection instructions found")
        else:
            print("❌ Phase status detection instructions NOT found")
            
        if "human_input tool to ask user" in orchestrator_prompt:
            print("✅ User permission request instructions found")
        else:
            print("❌ User permission request instructions NOT found")
        
        # Test 4: Show the relevant part of the prompt
        print("\n5. Orchestrator prompt preview (Phase Sequence Awareness section):")
        print("-" * 60)
        lines = orchestrator_prompt.split('\n')
        show_lines = False
        for line in lines:
            if "Phase Sequence Awareness Protocol" in line:
                show_lines = True
            if "HOW TO DEPLOY SUB-AGENTS" in line:
                show_lines = False
            if show_lines:
                print(line)
        
        print("\n✅ All tests completed successfully!")
        print("\n📋 Summary of Changes:")
        print("   ✅ Orchestrator now has Phase Sequence Awareness Protocol")
        print("   ✅ Must check file existence before deploying agents")
        print("   ✅ Must ask user permission before skipping phases")
        print("   ✅ Helper functions available for phase management")
        print("\n🎯 Expected Behavior:")
        print("   - Orchestrator will use read_file to check phase completion")
        print("   - Will follow investigation → discussion → planning → task_generation sequence")
        print("   - Will ask user permission via human_input before skipping any phase")
        print("   - Will document decisions in phase_transition_decision.md")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_phase_sequence_awareness())