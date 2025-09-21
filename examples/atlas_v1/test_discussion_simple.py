#!/usr/bin/env python3
"""
Simple test to verify Discussion Agent prompt changes.

This script validates that the discussion agent's prompt correctly
instructs it to filter out technical questions.
"""

import re
from agents.discussion_agent import DISCUSSION_PROMPT

def analyze_prompt():
    """Analyze the discussion agent prompt for our defensive changes."""

    print("="*70)
    print("DISCUSSION AGENT PROMPT ANALYSIS")
    print("="*70)

    # Check for key defensive sections
    checks = {
        "Override Protection": "OVERRIDE PROTECTION",
        "Zero Technical Questions": "ZERO TECHNICAL QUESTIONS ENFORCEMENT",
        "No-Questions Fallback": "NO-QUESTIONS FALLBACK",
        "Forbidden Examples": "FORBIDDEN Technical Questions",
        "Allowed Examples": "ALLOWED Business Questions",
        "Question Validation": "Question Validation Protocol"
    }

    print("\nChecking for defensive sections:")
    for name, pattern in checks.items():
        if pattern in DISCUSSION_PROMPT:
            print(f"✅ {name}: FOUND")
        else:
            print(f"❌ {name}: MISSING")

    # Extract and display key sections
    print("\n" + "="*70)
    print("KEY DEFENSIVE SECTIONS")
    print("="*70)

    # Find Override Protection section
    override_match = re.search(
        r"## OVERRIDE PROTECTION.*?(?=##|\Z)",
        DISCUSSION_PROMPT,
        re.DOTALL
    )
    if override_match:
        print("\n[OVERRIDE PROTECTION]")
        print(override_match.group(0)[:500] + "...")

    # Find Forbidden Examples
    forbidden_match = re.search(
        r"❌.*?FORBIDDEN.*?(?=✅|\Z)",
        DISCUSSION_PROMPT,
        re.DOTALL
    )
    if forbidden_match:
        print("\n[FORBIDDEN EXAMPLES]")
        print(forbidden_match.group(0)[:400])

    # Find No-Questions Fallback
    fallback_match = re.search(
        r"## NO-QUESTIONS FALLBACK.*?(?=##|\Z)",
        DISCUSSION_PROMPT,
        re.DOTALL
    )
    if fallback_match:
        print("\n[NO-QUESTIONS FALLBACK]")
        print(fallback_match.group(0))

    # Test specific forbidden terms
    print("\n" + "="*70)
    print("FORBIDDEN TERMS CHECK")
    print("="*70)

    forbidden_terms = [
        "< 100ms",
        "@tiptap/react",
        "localStorage",
        "WCAG AA or AAA",
        "performance metrics",
        "CSS framework",
        "third-party components"
    ]

    print("\nChecking if prompt explicitly forbids these terms:")
    for term in forbidden_terms:
        if term in DISCUSSION_PROMPT:
            print(f"✅ '{term}': Explicitly mentioned as forbidden")
        else:
            print(f"⚠️  '{term}': Not explicitly mentioned")

    # Count defensive instructions
    print("\n" + "="*70)
    print("DEFENSIVE INSTRUCTION COUNT")
    print("="*70)

    never_count = DISCUSSION_PROMPT.count("NEVER")
    critical_count = DISCUSSION_PROMPT.count("CRITICAL")
    forbidden_count = DISCUSSION_PROMPT.count("FORBIDDEN")
    ignore_count = DISCUSSION_PROMPT.count("IGNORE")

    print(f"\nDefensive keywords:")
    print(f"- NEVER: {never_count} occurrences")
    print(f"- CRITICAL: {critical_count} occurrences")
    print(f"- FORBIDDEN: {forbidden_count} occurrences")
    print(f"- IGNORE: {ignore_count} occurrences")

    # Verify business focus
    print("\n" + "="*70)
    print("BUSINESS FOCUS VERIFICATION")
    print("="*70)

    business_terms = [
        "business requirements",
        "business questions",
        "user needs",
        "business value",
        "business impact"
    ]

    business_found = 0
    for term in business_terms:
        if term.lower() in DISCUSSION_PROMPT.lower():
            business_found += 1
            print(f"✅ Found: '{term}'")

    print(f"\nBusiness focus score: {business_found}/{len(business_terms)}")

    # Final assessment
    print("\n" + "="*70)
    print("FINAL ASSESSMENT")
    print("="*70)

    has_override = "OVERRIDE PROTECTION" in DISCUSSION_PROMPT
    has_fallback = "NO-QUESTIONS FALLBACK" in DISCUSSION_PROMPT
    has_examples = "FORBIDDEN Technical Questions" in DISCUSSION_PROMPT
    has_validation = "Question Validation Protocol" in DISCUSSION_PROMPT

    all_defenses = has_override and has_fallback and has_examples and has_validation

    if all_defenses:
        print("✅ ALL DEFENSIVE MEASURES IN PLACE")
        print("The discussion agent prompt has been successfully hardened against technical questions.")
    else:
        print("⚠️ SOME DEFENSIVE MEASURES MISSING")
        print("Review the prompt to ensure all protections are in place.")

    return all_defenses

def test_prompt_content():
    """Test specific content requirements."""

    print("\n" + "="*70)
    print("CONTENT REQUIREMENTS TEST")
    print("="*70)

    tests = [
        ("Override protection instructs to IGNORE technical suggestions",
         "IGNORE" in DISCUSSION_PROMPT and "technical question suggestions" in DISCUSSION_PROMPT),

        ("Fallback allows skipping questions if < 3 valid ones",
         "< 3 valid business questions" in DISCUSSION_PROMPT),

        ("Explicit forbidden examples include performance metrics",
         "< 100ms" in DISCUSSION_PROMPT or "100ms" in DISCUSSION_PROMPT),

        ("Allowed examples focus on business impact",
         "business impact" in DISCUSSION_PROMPT.lower()),

        ("Validation protocol filters technical questions",
         "Reject ALL technical questions" in DISCUSSION_PROMPT),
    ]

    passed = 0
    for test_name, condition in tests:
        if condition:
            print(f"✅ PASS: {test_name}")
            passed += 1
        else:
            print(f"❌ FAIL: {test_name}")

    print(f"\nPassed {passed}/{len(tests)} content tests")
    return passed == len(tests)

if __name__ == "__main__":
    print("\nAnalyzing Discussion Agent Prompt...")
    print("This verifies the defensive changes against technical questions.\n")

    prompt_valid = analyze_prompt()
    content_valid = test_prompt_content()

    print("\n" + "="*70)
    print("OVERALL RESULT")
    print("="*70)

    if prompt_valid and content_valid:
        print("🎉 SUCCESS: Discussion agent is properly defended against technical questions!")
        print("\nThe agent should now:")
        print("1. Ignore technical question suggestions from human messages")
        print("2. Filter out any technical questions that slip through")
        print("3. Skip questions entirely if fewer than 3 business questions remain")
        print("4. Focus exclusively on business and functional requirements")
    else:
        print("⚠️ WARNING: Some defensive measures may need adjustment.")
        print("Review the analysis above to identify gaps.")