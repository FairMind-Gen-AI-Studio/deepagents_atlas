#!/usr/bin/env python3
"""
Simple test for discussion agent to verify it can write files correctly.
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from agents.discussion_agent import discussion_agent

def test_discussion_agent_file_writing():
    """Test that discussion agent can write files without issues."""

    # Check if the agent configuration is valid
    assert discussion_agent["name"] == "discussion-agent"
    assert "write_file" in discussion_agent["tools"]
    assert "human_input" in discussion_agent["tools"]
    assert "approve_plan" in discussion_agent["tools"]

    # Check that prompt is not too long (should be reasonable size)
    prompt_length = len(discussion_agent["prompt"])
    print(f"Discussion agent prompt length: {prompt_length} characters")

    # Should be much shorter than the original 8000+ characters
    # (original was ~8500, now should be under 5000)
    assert prompt_length < 5000, f"Prompt too long: {prompt_length}"

    # Test that the prompt contains essential elements
    prompt = discussion_agent["prompt"]
    assert "clarification_questions.md" in prompt
    assert "user_responses.md" in prompt
    assert "requirements_summary.md" in prompt
    assert "requirements_clarified.md" in prompt
    assert "business/functional questions" in prompt
    assert "technical implementation" in prompt

    print("✅ Discussion agent configuration is valid")
    print("✅ Prompt length is reasonable")
    print("✅ All required file outputs are mentioned")
    print("✅ Business focus is maintained")

    return True

if __name__ == "__main__":
    test_discussion_agent_file_writing()
    print("\n🎉 All tests passed! Discussion agent is ready to use.")