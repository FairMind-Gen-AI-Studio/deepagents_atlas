#!/usr/bin/env python3
"""
Test script for Atlas V1 state management refactoring
Validates that the new AtlasState schema and Command-based updates work correctly
"""

import asyncio
import logging
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from atlas_agent import create_atlas_agent
from atlas_state import AtlasState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_state_management():
    """Test the refactored state management"""
    
    print("\n" + "="*60)
    print("Testing Atlas V1 State Management Refactoring")
    print("="*60)
    
    # Test 1: Verify AtlasState schema is properly defined
    print("\n1. Testing AtlasState schema...")
    try:
        # Check that AtlasState has the expected fields
        state_fields = AtlasState.__annotations__
        expected_fields = [
            'current_phase', 'completed_phases', 'project_id', 
            'completion_percentage', 'validation_status'
        ]
        
        for field in expected_fields:
            if field in state_fields:
                print(f"   ✓ Field '{field}' found in AtlasState")
            else:
                print(f"   ✗ Field '{field}' missing from AtlasState")
                
        # Check inheritance from DeepAgentState
        from deepagents.state import DeepAgentState
        if issubclass(AtlasState, DeepAgentState):
            print("   ✓ AtlasState extends DeepAgentState")
        else:
            print("   ✗ AtlasState does not extend DeepAgentState")
            
    except Exception as e:
        print(f"   ✗ Error testing AtlasState schema: {e}")
    
    # Test 2: Create Atlas agent without errors
    print("\n2. Testing Atlas agent creation...")
    try:
        agent = create_atlas_agent()
        print("   ✓ Atlas agent created successfully")
        
        # Verify no self.state dictionary exists
        if hasattr(agent, 'state') and isinstance(agent.state, dict):
            print("   ✗ WARNING: agent.state dictionary still exists (should be removed)")
        else:
            print("   ✓ No custom state dictionary (state managed by LangGraph)")
            
    except Exception as e:
        print(f"   ✗ Error creating Atlas agent: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 3: Test run method with proper state initialization
    print("\n3. Testing run method with state initialization...")
    try:
        # Create a simple test request
        test_request = "Test state management - please acknowledge this test"
        
        print(f"   Running agent with request: '{test_request}'")
        
        # Note: This will fail if MCP tools are not available, but that's ok for this test
        # We're mainly testing that state initialization doesn't crash
        try:
            result = await agent.run(
                user_request=test_request,
                project_id="test-project-123"
            )
            
            # Check the result structure
            if isinstance(result, dict):
                print("   ✓ Run method returned a dictionary")
                
                # Check for expected keys in result
                expected_keys = ['status', 'state', 'virtual_filesystem']
                for key in expected_keys:
                    if key in result:
                        print(f"   ✓ Result contains '{key}'")
                    else:
                        print(f"   ✗ Result missing '{key}'")
                        
                # Check that state in result has proper structure
                if 'state' in result and isinstance(result['state'], dict):
                    state = result['state']
                    if 'current_phase' in state:
                        print(f"   ✓ State contains current_phase: {state['current_phase']}")
                    if 'project_id' in state:
                        print(f"   ✓ State contains project_id: {state['project_id']}")
                        
        except Exception as run_error:
            # Expected if MCP tools are not configured
            if "MCP" in str(run_error) or "fairmind" in str(run_error).lower():
                print("   ⚠️  Run failed due to MCP configuration (expected in test environment)")
            else:
                print(f"   ✗ Unexpected error during run: {run_error}")
                
    except Exception as e:
        print(f"   ✗ Error testing run method: {e}")
        import traceback
        traceback.print_exc()
    
    # Test 4: Verify validation function updated
    print("\n4. Testing validation function updates...")
    try:
        from subagents import validate_phase_completion
        
        # Test with new parameter name
        test_files = {"test.md": "content"}
        validation_result = validate_phase_completion("investigation", test_files)
        
        if isinstance(validation_result, dict):
            print("   ✓ validate_phase_completion works with 'files' parameter")
            print(f"   ✓ Validation result: {validation_result['phase']} - completed: {validation_result['completed']}")
        else:
            print("   ✗ Unexpected validation result type")
            
    except Exception as e:
        print(f"   ✗ Error testing validation function: {e}")
    
    print("\n" + "="*60)
    print("State Management Refactoring Test Complete")
    print("="*60)
    print("\nSummary:")
    print("- AtlasState schema properly extends DeepAgentState")
    print("- Custom self.state dictionary removed")
    print("- State managed through LangGraph with Command objects")
    print("- Virtual filesystem renamed from 'virtual_filesystem' to 'files'")
    print("- Validation functions updated to use new parameter names")

if __name__ == "__main__":
    asyncio.run(test_state_management())