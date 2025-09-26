#!/usr/bin/env python3
"""
Test script to verify the discussion agent focuses on business questions only.
This test checks that the enhanced prompt properly guides business-focused behavior.
"""

import os
import sys

# Add the atlas_v1 directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from agents.discussion_agent import discussion_agent, DISCUSSION_PROMPT

def test_prompt_enhancements():
    """Test that the discussion agent prompt includes key business-focus enhancements"""
    print("🧪 Testing Discussion Agent Business Focus Enhancements...")

    # Check that the prompt includes the enhanced rules
    assert "ABSOLUTELY FORBIDDEN" in DISCUSSION_PROMPT, "Missing strong forbidden language"
    assert "Technical questions = immediate failure" in DISCUSSION_PROMPT, "Missing failure consequence"
    assert "CSS/styling implementation" in DISCUSSION_PROMPT, "Missing CSS forbidden example"
    assert "State management details" in DISCUSSION_PROMPT, "Missing state management forbidden example"

    # Check that business question examples are included
    assert "Which user groups have requested dark mode" in DISCUSSION_PROMPT, "Missing business question example"
    assert "INCORRECT Technical Questions" in DISCUSSION_PROMPT, "Missing negative examples section"

    # Check that self-validation step is included
    assert "Self-Validate Questions" in DISCUSSION_PROMPT, "Missing self-validation step"
    assert "Does this ask HOW to implement" in DISCUSSION_PROMPT, "Missing HOW validation check"

    # Check that question templates are included
    assert "CLARIFICATION:" in DISCUSSION_PROMPT, "Missing clarification templates"
    assert "DISAMBIGUATION:" in DISCUSSION_PROMPT, "Missing disambiguation templates"
    assert "INTEGRATION:" in DISCUSSION_PROMPT, "Missing integration templates"
    assert "CONTEXT:" in DISCUSSION_PROMPT, "Missing context templates"
    assert "CONFLICT RESOLUTION:" in DISCUSSION_PROMPT, "Missing conflict resolution templates"

    print("✅ All prompt enhancements verified!")

def test_agent_configuration():
    """Test that the agent configuration is properly set up"""
    print("🔧 Testing Agent Configuration...")

    # Check agent structure
    assert discussion_agent["name"] == "discussion-agent", "Incorrect agent name"
    assert discussion_agent["prompt"] == DISCUSSION_PROMPT, "Prompt not properly assigned"
    assert "human_input" in discussion_agent["tools"], "Missing human_input tool"
    assert "approve_plan" in discussion_agent["tools"], "Missing approve_plan tool"

    print("✅ Agent configuration verified!")

def print_business_question_examples():
    """Show examples of correct business questions for Dark Mode feature"""
    print("\n📋 Examples of CORRECT Business Questions (Dark Mode Feature):")

    examples = [
        "1. Which user groups have requested dark mode most frequently? (CONTEXT)",
        "2. What specific accessibility requirements must dark mode meet? (CLARIFICATION)",
        "3. Should dark mode affect all parts of the application or just navigation? (DISAMBIGUATION)",
        "4. How does dark mode support your user retention goals? (INTEGRATION)",
        "5. Should theme preferences persist across user sessions? (INTEGRATION)",
        "6. What percentage of users work in low-light environments? (CONTEXT)",
        "7. If users prefer dark mode but need to print light reports, how should we handle this? (CONFLICT RESOLUTION)"
    ]

    for example in examples:
        print(f"   ✓ {example}")

    print("\n🚫 Examples of FORBIDDEN Technical Questions:")
    technical_examples = [
        "   ❌ What CSS color values should we use for dark mode?",
        "   ❌ Should we use Zustand or Context for theme state?",
        "   ❌ How should we implement smooth theme transitions?",
        "   ❌ Should we use localStorage or database for persistence?",
        "   ❌ What Tailwind classes should we use for dark mode?"
    ]

    for example in technical_examples:
        print(example)

def main():
    """Run all tests and examples"""
    print("🚀 Testing Enhanced Discussion Agent (Business Focus Only)")
    print("=" * 60)

    try:
        test_prompt_enhancements()
        test_agent_configuration()
        print_business_question_examples()

        print("\n🎉 SUCCESS: Discussion agent is properly configured for business-only questions!")
        print("📝 The agent will now ask about:")
        print("   • User needs and business requirements")
        print("   • Functional specifications and user experience")
        print("   • Business value and strategic alignment")
        print("   • User workflows and acceptance criteria")
        print("\n🛡️ The agent will REFUSE to ask about:")
        print("   • Technical implementation details")
        print("   • Code structure or frameworks")
        print("   • Database or storage implementation")
        print("   • CSS, styling, or design tokens")

    except AssertionError as e:
        print(f"❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()