#!/usr/bin/env python3

"""Test script to verify the human_input tool is working correctly."""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from deepagents.tools import human_input
from langchain_core.messages import ToolMessage

async def test_human_input_tool():
    """Test the human_input tool directly."""
    print("Testing human_input tool...")
    
    try:
        # Test the human_input tool directly
        result = human_input("What is your preferred authentication method for the work sessions feature?", "test-call-id")
        
        print("✅ human_input tool executed successfully")
        print(f"Result type: {type(result)}")
        print(f"Result: {result}")
        
        # Check if it returns a Command with the expected structure
        if hasattr(result, 'update') and 'messages' in result.update:
            messages = result.update['messages']
            if messages and len(messages) > 0:
                message = messages[0]
                print(f"Message type: {type(message)}")
                print(f"Message content: {message.content}")
                if "USER_QUESTION:" in message.content:
                    print("✅ USER_QUESTION prefix found in message")
                else:
                    print("❌ USER_QUESTION prefix not found in message")
            else:
                print("❌ No messages in result")
        else:
            print("❌ Invalid result structure")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing human_input tool: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_human_input_tool())
    sys.exit(0 if success else 1)