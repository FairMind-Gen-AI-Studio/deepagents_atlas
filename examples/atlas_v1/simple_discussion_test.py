#!/usr/bin/env python3

"""Simple test for discussion agent that shows if human_input questions are being generated."""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from deepagents.graph import create_deep_agent

async def test_simple_discussion():
    """Test the discussion behavior with just the basic deep agent framework."""
    print("Testing basic discussion agent behavior...")
    
    # Create a simple agent that should use human_input
    agent = create_deep_agent(
        tools=[],
        instructions="""You are a discussion agent. Your job is to:
1. Read the investigation findings from investigation_findings.md
2. Generate 5 targeted questions about the user story
3. Use the human_input tool to present each question to the user
4. Collect responses and consolidate them
5. Save results to clarification_questions.md, user_responses.md, and requirements_clarified.md

Always use the human_input tool when you need to ask the user a question.""",
        subagents=[]
    )
    
    # Initial state with investigation findings
    initial_state = {
        "messages": [{"role": "user", "content": "Please generate clarification questions for user story US-2025-1258 about work sessions in Fairmind Studio."}],
        "files": {
            "investigation_findings.md": """# Investigation Findings - Business Context

## Target User Story
- ID: US-2025-1258
- Title: Implement work sessions in Fairmind Studio
- Description: As a project manager, I want to create and manage work sessions to organize development activities

## Knowledge Gaps Identified
- Technical architecture preferences
- Integration requirements
- Performance requirements
- Security considerations
"""
        },
        "todos": []
    }
    
    try:
        response = await agent.ainvoke(initial_state)
        
        print("✅ Agent executed successfully")
        
        # Check messages for human_input usage
        messages = response.get('messages', [])
        found_questions = False
        
        for i, msg in enumerate(messages):
            if hasattr(msg, 'content'):
                content = msg.content
                print(f"\nMessage {i}: {content[:150]}...")
                
                # Look for signs that human_input was used
                if "USER_QUESTION:" in content:
                    print("✅ Found USER_QUESTION marker - human_input was used!")
                    found_questions = True
                elif any(keyword in content.lower() for keyword in ["question", "ask", "clarify", "input"]):
                    print("🔍 Message mentions questions/input")
        
        if not found_questions:
            print("❌ No USER_QUESTION markers found - human_input may not have been used")
        
        # Check files
        files = response.get('files', {})
        print(f"\nFiles created: {list(files.keys())}")
        for filename, content in files.items():
            print(f"\n--- {filename} ---")
            print(content[:300] + "..." if len(content) > 300 else content)
        
        return found_questions
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_simple_discussion())
    print(f"\nTest result: {'PASS' if success else 'FAIL'}")
    sys.exit(0 if success else 1)