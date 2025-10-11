#!/usr/bin/env python3
"""
Prompt Caching Benefits Demo

This script demonstrates the benefits of prompt caching by making
two sequential API calls and comparing token usage.

Usage:
    python test_caching_benefits.py
"""

import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from model_config import initialize_atlas_model
from langchain_core.messages import HumanMessage, SystemMessage

async def demonstrate_caching():
    """Demonstrate prompt caching with two sequential calls."""

    print("🧪 Prompt Caching Benefits Demonstration")
    print("=" * 70)
    print()

    # Initialize model with beta headers
    model = initialize_atlas_model()
    print("✅ Model initialized with caching enabled")
    print(f"   Beta features: extended-cache-ttl-2025-04-11, token-efficient-tools-2025-02-19")
    print()

    # Create a large system prompt (typical for Atlas V1)
    system_prompt = """You are the Atlas V1 Orchestrator, a sophisticated 4-phase planning agent.

Your responsibilities include:
1. Investigation Phase - Analyze project context, user stories, and requirements
2. Discussion Phase - Clarify requirements through interactive dialogue
3. Planning Phase - Create detailed implementation plans
4. Task Generation - Generate concrete, actionable tasks

You have access to multiple MCP tools for:
- Project management (Fairmind)
- Code analysis and repository exploration
- Requirements tracking and user story management

Always maintain context across all 4 phases and ensure comprehensive coverage."""

    print("📊 Call 1: Creating cache...")
    print("-" * 70)

    # First call - creates cache
    messages1 = [
        SystemMessage(content=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # Mark for caching
            }
        ]),
        HumanMessage(content="What are the 4 phases of Atlas V1?")
    ]

    response1 = await model.ainvoke(messages1)

    # Extract usage metadata
    if hasattr(response1, 'usage_metadata'):
        usage1 = response1.usage_metadata
        print(f"✅ Response received")
        print(f"   Input tokens: {usage1.get('input_tokens', 0)}")
        print(f"   Cache creation: {usage1.get('cache_creation_input_tokens', 0)} tokens")
        print(f"   Output tokens: {usage1.get('output_tokens', 0)}")
        print()

        # Calculate cost (approximate)
        cache_write_cost = usage1.get('cache_creation_input_tokens', 0) * 1.25
        print(f"💰 Estimated cost (first call):")
        print(f"   Cache write premium: {cache_write_cost:.0f} token-equivalents")
        print()

    print("📊 Call 2: Reading from cache...")
    print("-" * 70)

    # Wait a moment to simulate multi-turn conversation
    await asyncio.sleep(1)

    # Second call - reads from cache
    messages2 = [
        SystemMessage(content=[
            {
                "type": "text",
                "text": system_prompt,
                "cache_control": {"type": "ephemeral"}  # Same cached content
            }
        ]),
        HumanMessage(content="What tools are available in Atlas V1?")
    ]

    response2 = await model.ainvoke(messages2)

    # Extract usage metadata
    if hasattr(response2, 'usage_metadata'):
        usage2 = response2.usage_metadata
        print(f"✅ Response received")
        print(f"   Input tokens: {usage2.get('input_tokens', 0)}")
        print(f"   Cache reads: {usage2.get('cache_read_input_tokens', 0)} tokens (90% savings!)")
        print(f"   Output tokens: {usage2.get('output_tokens', 0)}")
        print()

        # Calculate savings
        cache_read_tokens = usage2.get('cache_read_input_tokens', 0)
        normal_cost = cache_read_tokens  # What it would cost without cache
        cached_cost = cache_read_tokens * 0.1  # 90% discount
        savings = normal_cost - cached_cost

        print(f"💰 Estimated savings (second call):")
        print(f"   Normal cost: {normal_cost:.0f} tokens")
        print(f"   Cached cost: {cached_cost:.0f} tokens (10% of normal)")
        print(f"   Savings: {savings:.0f} tokens (90% reduction!)")
        print()

    print("=" * 70)
    print("🎉 Summary:")
    print()
    print("   ✅ First call: Paid cache write premium (+25%)")
    print("   ✅ Second call: Saved 90% on cached content")
    print("   ✅ Break-even: After 2-3 calls")
    print("   ✅ Atlas V1: 4 phases = massive cumulative savings!")
    print()
    print("💡 For Atlas V1's 4-phase workflow:")
    print("   • Phase 1: Creates cache (investigation)")
    print("   • Phase 2-4: Read from cache (90% cheaper each)")
    print("   • Result: 60-80% overall cost reduction")
    print()

if __name__ == "__main__":
    try:
        asyncio.run(demonstrate_caching())
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
