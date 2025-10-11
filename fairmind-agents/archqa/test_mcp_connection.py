#!/usr/bin/env python3
"""
MCP Connection Verification for ArchQA Agent

Tests that MCP Fairmind tools are properly initialized and assigned to subagents.
Run this before debugging agent issues to verify MCP connectivity.

Usage:
    python test_mcp_connection.py
"""

import sys
import asyncio
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)

# Add src to path for deepagents
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Add atlas_v1 to path for MCP client
atlas_path = str(Path(__file__).parent.parent / "atlas_v1")
if atlas_path not in sys.path:
    sys.path.insert(0, atlas_path)


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


def print_result(test_name: str, passed: bool, details: str = ""):
    """Print test result"""
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"{status}: {test_name}")
    if details:
        for line in details.split('\n'):
            print(f"       {line}")


def test_environment_variables():
    """Test 1: Verify required environment variables are set"""
    print_header("TEST 1: Environment Variables")

    import os

    required_vars = {
        'FAIRMIND_MCP_URL': 'MCP server endpoint',
        'FAIRMIND_MCP_TOKEN': 'MCP authentication token',
        'ANTHROPIC_API_KEY': 'Anthropic API key for Claude models',
    }

    optional_vars = {
        'TAVILY_API_KEY': 'Tavily API key for web search (optional)',
    }

    all_required_set = True
    details = "Required variables:\n"

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Show first 10 chars of value for verification
            masked = value[:10] + "..." if len(value) > 10 else value
            details += f"  {var_name}: {masked} ✓\n"
        else:
            details += f"  {var_name}: NOT SET ✗\n"
            all_required_set = False

    details += "\nOptional variables:\n"
    for var_name, description in optional_vars.items():
        value = os.getenv(var_name)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            details += f"  {var_name}: {masked} ✓\n"
        else:
            details += f"  {var_name}: NOT SET (web search disabled)\n"

    print_result("Environment Variables", all_required_set, details.strip())
    return all_required_set


async def test_mcp_connection():
    """Test 2: Verify MCP client can connect and retrieve tools"""
    print_header("TEST 2: MCP Connection")

    try:
        from mcp_client import initialize_mcp_tools

        logger.info("Attempting to connect to Fairmind MCP server...")
        mcp_tools = await initialize_mcp_tools()

        if mcp_tools and len(mcp_tools) > 0:
            tool_names = list(mcp_tools.keys())
            details = f"Connected successfully\n"
            details += f"Tools available: {len(tool_names)}\n"
            details += f"Sample tools: {tool_names[:5]}"
            print_result("MCP Connection", True, details)
            return mcp_tools
        else:
            print_result("MCP Connection", False, "No tools returned from MCP server")
            return None

    except ImportError:
        print_result(
            "MCP Connection",
            False,
            "Cannot import mcp_client from atlas_v1\n"
            "Make sure atlas_v1 example exists with mcp_client.py"
        )
        return None
    except Exception as e:
        print_result("MCP Connection", False, f"Error: {e}")
        logger.exception("Full traceback:")
        return None


def test_tool_filtering(mcp_tools):
    """Test 3: Verify tool filtering functions work correctly"""
    print_header("TEST 3: Tool Filtering")

    if not mcp_tools:
        print_result("Tool Filtering", False, "No MCP tools available to test")
        return False

    try:
        from mcp_tool_filters import (
            get_context_mapper_tools,
            get_code_investigator_tools,
            get_solution_synthesizer_tools,
            verify_tool_assignment,
        )

        # Get filtered tools
        context_tools = get_context_mapper_tools(mcp_tools)
        investigator_tools = get_code_investigator_tools(mcp_tools)
        synthesizer_tools = get_solution_synthesizer_tools(mcp_tools)

        # Test context mapper tools
        context_names = [getattr(t, 'name', str(t)) for t in context_tools]
        has_general = any('General_' in name for name in context_names)
        has_studio = any('Studio_' in name for name in context_names)
        has_code = any('Code_' in name for name in context_names)

        context_passed = (
            len(context_tools) > 0 and
            has_general and
            has_studio and
            has_code
        )

        details = f"Context Mapper tools: {len(context_tools)}\n"
        details += f"Has General tools: {has_general}\n"
        details += f"Has Studio tools: {has_studio}\n"
        details += f"Has Code tools: {has_code}\n"
        details += f"Examples: {context_names[:3]}"

        print_result("Context Mapper Filter", context_passed, details)

        # Test code investigator tools
        investigator_names = [getattr(t, 'name', str(t)) for t in investigator_tools]
        has_code_tools = any('Code_' in name for name in investigator_names)
        has_studio_tools = any('Studio_' in name for name in investigator_names)

        investigator_passed = len(investigator_tools) > 0 and has_code_tools

        details = f"Code Investigator tools: {len(investigator_tools)}\n"
        details += f"Has Code tools: {has_code_tools}\n"
        details += f"Has Studio tools: {has_studio_tools}\n"
        details += f"Examples: {investigator_names[:3]}"

        print_result("Code Investigator Filter", investigator_passed, details)

        # Test solution synthesizer tools (should be empty)
        synthesizer_passed = len(synthesizer_tools) == 0

        details = f"Solution Synthesizer tools: {len(synthesizer_tools)}\n"
        details += "Expected: 0 (uses only filesystem)"

        print_result("Solution Synthesizer Filter", synthesizer_passed, details)

        return context_passed and investigator_passed and synthesizer_passed

    except Exception as e:
        print_result("Tool Filtering", False, f"Error: {e}")
        logger.exception("Full traceback:")
        return False


def test_agent_creation(mcp_tools):
    """Test 4: Verify agent can be created with MCP tools"""
    print_header("TEST 4: Agent Creation")

    try:
        from archqa_agent import create_archqa_agent

        logger.info("Creating ArchQA agent with MCP tools...")
        agent = create_archqa_agent()

        if agent:
            details = "Agent created successfully\n"
            details += "Check logs above for tool assignment details"
            print_result("Agent Creation", True, details)
            return agent
        else:
            print_result("Agent Creation", False, "Agent creation returned None")
            return None

    except Exception as e:
        print_result("Agent Creation", False, f"Error: {e}")
        logger.exception("Full traceback:")
        return None


async def main():
    """Run all tests"""
    print_header("ArchQA MCP Connection Verification")
    print("This script tests MCP tools connectivity and configuration")
    print("=" * 70)

    # Test 1: Environment (synchronous, run first)
    env_ok = test_environment_variables()

    if not env_ok:
        print("\n⚠️  WARNING: Some environment variables are not set!")
        print("   MCP connection may fail without proper configuration.")
        print("   Set variables in .env file or export them in your shell.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting.")
            return

    # Test 2: MCP Connection (async)
    mcp_tools = await test_mcp_connection()

    if not mcp_tools:
        print("\n❌ CRITICAL: Cannot proceed without MCP tools")
        print("   Fix MCP connection before running other tests")
        print("\n   Troubleshooting:")
        print("   - Check FAIRMIND_MCP_URL is reachable")
        print("   - Verify FAIRMIND_MCP_TOKEN is valid")
        print("   - Ensure atlas_v1/mcp_client.py exists")
        return

    # Test 3: Tool Filtering (synchronous)
    filtering_ok = test_tool_filtering(mcp_tools)

    # Test 4: Agent Creation (synchronous, but internally creates async graph)
    agent = test_agent_creation(mcp_tools)

    # Summary
    print_header("SUMMARY")

    tests_passed = sum([
        env_ok,
        mcp_tools is not None,
        filtering_ok,
        agent is not None
    ])
    total_tests = 4

    print(f"\nTests passed: {tests_passed}/{total_tests}")

    if tests_passed == total_tests:
        print("\n✅ ALL TESTS PASSED")
        print("\nYour ArchQA agent is properly configured!")
        print("MCP tools should be available to subagents during execution.")
        print("\nNext steps:")
        print("  1. Run: langgraph dev")
        print("  2. Send a test architectural question")
        print("  3. Check LangSmith traces - look for MCP tool calls in subagents")
        print("  4. Verify context-mapper has General/Studio/Code tools")
        print("  5. Verify code-investigator has Code/Studio tools")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nReview the failed tests above and fix issues before proceeding.")
        print("Common fixes:")
        print("  - Set missing environment variables in .env")
        print("  - Check FAIRMIND_MCP_URL is reachable")
        print("  - Verify FAIRMIND_MCP_TOKEN is valid")
        print("  - Ensure atlas_v1/mcp_client.py exists")

    print("\nFor debugging, check logs when running: langgraph dev")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.exception("Full traceback:")
        sys.exit(1)
