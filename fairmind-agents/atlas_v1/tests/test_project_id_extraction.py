#!/usr/bin/env python3

"""
Test that the investigation agent correctly extracts and stores project ID.
"""

import asyncio
from atlas_agent import agent

async def test_project_id_extraction():
    """Test project ID extraction and storage."""

    print("🧪 Testing Project ID Extraction in Investigation Agent")
    print("=" * 60)

    config = {"configurable": {"thread_id": "test-project-id-extraction"}}

    # Test with project ID
    test_message = "User Request: Analyze user story US-2025-1342 for dark mode navigation\nProject ID: blogmaster_ai_project_123"

    print(f"📝 Input message: {test_message}")
    print("\n🚀 Running agent...")

    try:
        result = await agent.ainvoke(
            {"messages": [{"role": "user", "content": test_message}]},
            config=config
        )

        print("✅ Agent completed")

        # Get files from LangGraph state (preserved automatically)
        result_files = result.get("files", {})
        print(f"\n📁 Result has {len(result_files)} files: {list(result_files.keys())}")

        if "investigation_findings.md" in result_files:
            findings_content = result_files["investigation_findings.md"]
            print(f"\n📋 investigation_findings.md content preview:")
            print("-" * 50)
            # Show first 500 characters
            print(findings_content[:500] + "..." if len(findings_content) > 500 else findings_content)
            print("-" * 50)

            # Check if project ID is included
            if "blogmaster_ai_project_123" in findings_content:
                print("✅ SUCCESS: Project ID found in investigation findings!")
                return True
            else:
                print("❌ FAILURE: Project ID NOT found in investigation findings")
                return False
        else:
            print("❌ FAILURE: investigation_findings.md not created")
            return False

    except Exception as e:
        print(f"❌ Agent failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_project_id_extraction())
    exit(0 if success else 1)