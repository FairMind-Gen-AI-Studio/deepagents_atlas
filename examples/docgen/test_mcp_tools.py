#!/usr/bin/env python3
"""
MCP Tools Verification Script for DocGen Agent

This script tests that MCP tools are properly initialized and assigned to subagents.
Run this before debugging agent issues to verify MCP connectivity.

Usage:
    python test_mcp_tools.py
"""

import sys
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any

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


async def test_mcp_connection():
    """Test 1: Verify MCP client can connect and retrieve tools"""
    print_header("TEST 1: MCP Connection")

    try:
        from mcp_client import initialize_mcp_tools

        logger.info("Attempting to connect to Fairmind MCP server...")
        mcp_tools = await initialize_mcp_tools()

        if mcp_tools and len(mcp_tools) > 0:
            tool_names = list(mcp_tools.keys())
            details = f"Connected successfully\n"
            details += f"Tools available: {len(tool_names)}\n"
            details += f"Sample tools: {tool_names[:3]}"
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
        return None


def test_tool_filtering(mcp_tools: Dict[str, Any]):
    """Test 2: Verify tool filtering functions work correctly"""
    print_header("TEST 2: Tool Filtering")

    if not mcp_tools:
        print_result("Tool Filtering", False, "No MCP tools available to test")
        return False

    try:
        # Import filter functions
        from agents.discovery_agent import get_discovery_tools
        from agents.analysis_agent import get_analysis_tools
        from agents.generation_agent import get_generation_tools

        # Test discovery tools filter
        discovery_tools = get_discovery_tools(mcp_tools)
        discovery_names = [getattr(t, 'name', str(t)) for t in discovery_tools]
        has_general = any('General_' in name for name in discovery_names)
        has_code = any('Code_' in name for name in discovery_names)
        has_studio = any('Studio_' in name for name in discovery_names)

        discovery_passed = (
            len(discovery_tools) > 0 and
            has_general and
            has_code and
            not has_studio  # Should NOT have Studio tools
        )

        details = f"Discovery tools: {len(discovery_tools)}\n"
        details += f"Has General tools: {has_general}\n"
        details += f"Has Code tools: {has_code}\n"
        details += f"Has Studio tools (should be False): {has_studio}\n"
        details += f"Examples: {discovery_names[:3]}"

        print_result("Discovery Tool Filter", discovery_passed, details)

        # Test analysis tools filter
        analysis_tools = get_analysis_tools(mcp_tools)
        analysis_names = [getattr(t, 'name', str(t)) for t in analysis_tools]
        has_code_tools = any('Code_' in name for name in analysis_names)

        analysis_passed = len(analysis_tools) > 0 and has_code_tools

        details = f"Analysis tools: {len(analysis_tools)}\n"
        details += f"Has Code tools: {has_code_tools}\n"
        details += f"Examples: {analysis_names[:3]}"

        print_result("Analysis Tool Filter", analysis_passed, details)

        # Test generation tools filter
        generation_tools = get_generation_tools(mcp_tools)
        generation_names = [getattr(t, 'name', str(t)) for t in generation_tools]

        generation_passed = len(generation_tools) > 0

        details = f"Generation tools: {len(generation_tools)}\n"
        details += f"Examples: {generation_names[:3]}"

        print_result("Generation Tool Filter", generation_passed, details)

        return discovery_passed and analysis_passed and generation_passed

    except Exception as e:
        print_result("Tool Filtering", False, f"Error: {e}")
        return False


def test_agent_creation(mcp_tools: Dict[str, Any]):
    """Test 3: Verify agent can be created with MCP tools"""
    print_header("TEST 3: Agent Creation")

    try:
        from docgen_agent import create_langgraph_agent

        logger.info("Creating DocGen agent with MCP tools...")
        agent = create_langgraph_agent(mcp_tools)

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


def test_environment_variables():
    """Test 4: Verify required environment variables are set"""
    print_header("TEST 4: Environment Variables")

    import os

    required_vars = {
        'FAIRMIND_MCP_URL': 'MCP server endpoint',
        'FAIRMIND_MCP_TOKEN': 'MCP authentication token',
        'ANTHROPIC_API_KEY': 'Anthropic API key for Claude models',
    }

    all_set = True
    details = ""

    for var_name, description in required_vars.items():
        value = os.getenv(var_name)
        if value:
            # Show first 10 chars of value for verification
            masked = value[:10] + "..." if len(value) > 10 else value
            details += f"{var_name}: {masked} ✓\n"
        else:
            details += f"{var_name}: NOT SET ✗\n"
            all_set = False

    print_result("Environment Variables", all_set, details.strip())
    return all_set


async def main():
    """Run all tests"""
    print_header("DocGen MCP Tools Verification")
    print("This script tests MCP tools connectivity and configuration")
    print("=" * 70)

    # Test 4: Environment (synchronous, run first)
    env_ok = test_environment_variables()

    if not env_ok:
        print("\n⚠️  WARNING: Some environment variables are not set!")
        print("   MCP connection may fail without proper configuration.")
        print("   Set variables in .env file or export them in your shell.")
        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Exiting.")
            return

    # Test 1: MCP Connection (async)
    mcp_tools = await test_mcp_connection()

    if not mcp_tools:
        print("\n❌ CRITICAL: Cannot proceed without MCP tools")
        print("   Fix MCP connection before running other tests")
        return

    # Test 2: Tool Filtering (synchronous)
    filtering_ok = test_tool_filtering(mcp_tools)

    # Test 3: Agent Creation (synchronous, but internally creates async graph)
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
        print("\nYour DocGen agent is properly configured!")
        print("MCP tools should be available to subagents during execution.")
        print("\nNext steps:")
        print("  1. Run: langgraph dev")
        print("  2. Send a test request in LangSmith Studio")
        print("  3. Check LangSmith traces - look for 'task' tool invocations")
        print("  4. Inside task execution, verify discovery agent has MCP tools")
    else:
        print("\n❌ SOME TESTS FAILED")
        print("\nReview the failed tests above and fix issues before proceeding.")
        print("Common fixes:")
        print("  - Set missing environment variables in .env")
        print("  - Check FAIRMIND_MCP_URL is reachable")
        print("  - Verify FAIRMIND_MCP_TOKEN is valid")
        print("  - Ensure atlas_v1/mcp_client.py exists")

    print("\nFor detailed debugging, see DEBUG.md")


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
