"""
Test script for router intent classification.

Tests both keyword-based and LLM-based classification with various queries.
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Import classification functions
from router_graph import classify_intent, classify_intent_keyword_based, classify_intent_with_llm

# Test queries
test_queries = [
    # DocGen queries
    ("Generate API documentation for the authentication module", "docgen"),
    ("I need to create a README file for this project", "docgen"),
    ("Can you document this codebase?", "docgen"),

    # ArchQA queries
    ("How does the authentication system work?", "archqa"),
    ("Explain the overall architecture of this application", "archqa"),
    ("What design patterns are used in the payment module?", "archqa"),
    ("Why was this specific approach chosen?", "archqa"),

    # Ambiguous queries (interesting to see how LLM handles them)
    ("Tell me about the user management system", "archqa"),  # Could be either
    ("What are the main components?", "archqa"),
]

def test_classification():
    """Test the classification functions."""
    print("=" * 80)
    print("ROUTER INTENT CLASSIFICATION TEST")
    print("=" * 80)

    # Check if LLM is enabled
    use_llm = os.getenv("ROUTER_USE_LLM", "false").lower() == "true"
    print(f"\n🔧 Configuration:")
    print(f"   ROUTER_USE_LLM: {use_llm}")
    print(f"   ROUTER_MODEL_NAME: {os.getenv('ROUTER_MODEL_NAME', 'not set')}")
    print()

    for i, (query, expected) in enumerate(test_queries, 1):
        print(f"\n{'='*80}")
        print(f"Test {i}/{len(test_queries)}")
        print(f"{'='*80}")
        print(f"Query: {query}")
        print(f"Expected: {expected}")
        print()

        # Test keyword-based classification
        keyword_result = classify_intent_keyword_based(query)
        print(f"📝 Keyword-based: {keyword_result} {'✅' if keyword_result == expected else '❌'}")

        # Test LLM-based classification (if enabled)
        if use_llm:
            try:
                llm_result = classify_intent_with_llm(query)
                print(f"🤖 LLM-based: {llm_result} {'✅' if llm_result == expected else '❌'}")
            except Exception as e:
                print(f"❌ LLM classification failed: {e}")

        # Test main wrapper function
        main_result = classify_intent(query)
        print(f"🎯 Main function: {main_result} {'✅' if main_result == expected else '❌'}")

    print(f"\n{'='*80}")
    print("TEST COMPLETE")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    test_classification()
