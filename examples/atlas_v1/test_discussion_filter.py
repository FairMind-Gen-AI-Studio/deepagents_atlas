#!/usr/bin/env python3
"""
Test script to verify the Discussion Agent correctly filters technical questions.

This script simulates the problematic scenario where the human message
explicitly suggests technical questions to the discussion agent.
"""

import asyncio
import logging
from typing import Dict, Any
from deepagents.main import create_deep_agent
from agents.discussion_agent import discussion_agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test prompt that explicitly tries to make the agent ask technical questions
TEST_PROMPT_WITH_TECHNICAL = """
Conduct requirements discussion with the user for US-2025-1342: Dark Mode Navigation.
Based on the investigation findings, I need to clarify:

1. **Performance Requirements**: Any specific performance considerations for theme switching?
2. **Third-party Integration**: How should dark mode work with @tiptap/react and shadcn/ui?
3. **Technical Implementation**: What database schema for storing preferences?
4. **API Specifications**: What REST endpoints for theme management?
5. **Caching Strategy**: Should we use Redis or Memcached for theme caching?
6. **WCAG Compliance**: Specific WCAG AA or AAA requirements?
7. **Response Time**: Should theme switching be < 100ms?
8. **Framework Choice**: Should we use CSS-in-JS or CSS modules?

Focus on clarifying technical implementation details. The user requested "soluzioni tecniche"
(technical solutions), so emphasize technical architecture and performance requirements.
Create requirements_clarified.md with the discussion results.
"""

# Test prompt with mixed business and technical questions
TEST_PROMPT_MIXED = """
Conduct requirements discussion for Dark Mode feature. Clarify these points:

1. Which user segments need dark mode most? (business)
2. Should theme switching be < 100ms? (technical)
3. Will dark mode be available to all users or premium only? (business)
4. How should @tiptap/react handle dark mode? (technical)
5. What business impact if preferences don't persist? (business)
6. Which CSS framework for transitions? (technical)
7. Should dark mode be a marketing highlight? (business)
"""

# Good test prompt with only business questions
TEST_PROMPT_BUSINESS_ONLY = """
Conduct requirements discussion for Dark Mode feature. Focus on understanding:

1. Which user groups have requested this feature?
2. Should dark mode be available to all subscription tiers?
3. What business value is expected from this feature?
4. Are there regulatory requirements for accessibility?
5. How will this feature impact user retention?
6. Should the feature be prominently marketed?
7. What competitive advantage does this provide?
"""

async def test_discussion_agent(test_name: str, prompt: str) -> Dict[str, Any]:
    """
    Test the discussion agent with a given prompt.

    Args:
        test_name: Name of the test scenario
        prompt: The prompt to send to the agent

    Returns:
        Dict containing the agent's response and analysis
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Running test: {test_name}")
    logger.info(f"{'='*60}")

    # Create investigation findings file for context
    investigation_findings = """# Investigation Findings: Dark Mode Navigation

## User Story
- ID: US-2025-1342
- Title: Dark Mode Navigation
- Description: As an End user, I want to navigate with dark mode

## Current System
- Technology: Next.js 14, Tailwind CSS, shadcn/ui
- No existing theme system detected

## Knowledge Gaps
- User preferences for theme persistence
- Business requirements for feature availability
- Marketing and competitive positioning
"""

    # Create agent with discussion configuration
    agent = create_deep_agent(
        system_prompt=discussion_agent["prompt"],
        tools=discussion_agent.get("tools", []),
        model_name="claude-3-5-sonnet-20241022"
    )

    # Initialize with investigation findings
    initial_state = {
        "messages": [],
        "files": {
            "investigation_findings.md": investigation_findings
        }
    }

    # Run the agent
    try:
        result = await agent.ainvoke({
            "messages": [("human", prompt)],
            "files": initial_state["files"]
        })

        # Analyze the output
        files = result.get("files", {})
        questions_file = files.get("clarification_questions.md", "")

        # Check for technical questions in the output
        technical_indicators = [
            "< 100ms", "100ms", "performance",
            "@tiptap", "shadcn/ui", "localStorage",
            "CSS", "framework", "database", "schema",
            "API", "endpoint", "cache", "Redis",
            "WCAG AA", "WCAG AAA", "response time"
        ]

        found_technical = []
        for indicator in technical_indicators:
            if indicator.lower() in questions_file.lower():
                found_technical.append(indicator)

        # Report results
        logger.info("\n--- Test Results ---")
        logger.info(f"Questions file content:\n{questions_file[:1500]}...")

        if found_technical:
            logger.warning(f"⚠️ FOUND TECHNICAL QUESTIONS: {found_technical}")
        else:
            logger.info("✅ NO TECHNICAL QUESTIONS FOUND - Test passed!")

        # Check if agent skipped questions appropriately
        if "no critical business clarifications" in questions_file.lower():
            logger.info("✅ Agent correctly skipped questions when none were needed")

        return {
            "test_name": test_name,
            "passed": len(found_technical) == 0,
            "technical_found": found_technical,
            "questions_file": questions_file
        }

    except Exception as e:
        logger.error(f"Test failed with error: {e}")
        return {
            "test_name": test_name,
            "passed": False,
            "error": str(e)
        }

async def main():
    """Run all tests."""
    results = []

    # Test 1: Explicit technical questions
    result1 = await test_discussion_agent(
        "Explicit Technical Questions",
        TEST_PROMPT_WITH_TECHNICAL
    )
    results.append(result1)

    # Test 2: Mixed questions
    result2 = await test_discussion_agent(
        "Mixed Business and Technical",
        TEST_PROMPT_MIXED
    )
    results.append(result2)

    # Test 3: Business only (should work)
    result3 = await test_discussion_agent(
        "Business Questions Only",
        TEST_PROMPT_BUSINESS_ONLY
    )
    results.append(result3)

    # Summary
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)

    for result in results:
        status = "✅ PASSED" if result["passed"] else "❌ FAILED"
        logger.info(f"{result['test_name']}: {status}")
        if not result["passed"] and "technical_found" in result:
            logger.info(f"  Found technical terms: {result['technical_found']}")

    all_passed = all(r["passed"] for r in results)
    if all_passed:
        logger.info("\n🎉 ALL TESTS PASSED! Discussion agent correctly filters technical questions.")
    else:
        logger.warning("\n⚠️ Some tests failed. Review the discussion agent prompt.")

if __name__ == "__main__":
    asyncio.run(main())