#!/usr/bin/env python3

"""Test script for the discussion phase user interaction fix."""

import os
import sys
import asyncio
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from deepagents.graph import create_deep_agent
from deepagents.state import DeepAgentState
from subagents import get_discussion_agent_config

async def test_discussion_phase():
    """Test the discussion phase with mock human input."""
    print("Testing discussion phase user interaction...")
    
    # Create a discussion agent
    discussion_config = get_discussion_agent_config()
    
    # Create the deep agent with discussion subagent
    agent = create_deep_agent(
        tools=[],
        instructions="Test discussion phase agent.",
        subagents=[discussion_config]
    )
    
    # Initial state with mock investigation findings
    initial_state = {
        "messages": [{"role": "user", "content": "Test discussion phase for user story US-2025-1258"}],
        "files": {
            "investigation_findings.md": """# Investigation Findings - Business Context

## Target User Story
- ID: US-2025-1258
- Title: Implement work sessions in Fairmind Studio
- Description: As a project manager, I want to create and manage work sessions to organize development activities
- Status: In Progress

## Associated Need
- Need ID: N-2025-100
- Need Title: Enhanced project organization capabilities
- Need Description: Improve project managers' ability to organize and track development activities
- Priority: High

## Related User Stories
- US-2025-1259: Session scheduling and notifications
- US-2025-1260: Session reporting and analytics
- US-2025-1261: Integration with existing workflow tools

## Knowledge Gaps Identified
- Technical architecture preferences
- Integration requirements with Agile Studio and Requirement Studio
- Performance requirements
- Security considerations
- Specific UI/UX requirements
"""
        },
        "todos": []
    }
    
    try:
        # Invoke the agent with a task to start discussion
        response = await agent.ainvoke({
            **initial_state,
            "messages": [
                {"role": "user", "content": "task(description='Generate clarification questions and collect user responses for user story US-2025-1258', subagent_type='discussion-agent')"}
            ]
        })
        
        print("✅ Discussion phase agent executed successfully")
        print(f"Last message: {response['messages'][-1].content if response.get('messages') else 'No messages'}")
        print(f"Files created: {list(response.get('files', {}).keys())}")
        
        # Check if the expected output files were created
        expected_files = ["clarification_questions.md", "user_responses.md", "requirements_clarified.md"]
        created_files = response.get('files', {})
        missing_files = [f for f in expected_files if f not in created_files]
        
        if missing_files:
            print(f"⚠️  Missing expected output files: {missing_files}")
            for filename, content in created_files.items():
                print(f"\n--- {filename} ---")
                print(content[:200] + "..." if len(content) > 200 else content)
        else:
            print("✅ All expected output files were created")
        
        return len(missing_files) == 0
        
    except Exception as e:
        print(f"❌ Error testing discussion phase: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_discussion_phase())
    sys.exit(0 if success else 1)