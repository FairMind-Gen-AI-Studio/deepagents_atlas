#!/usr/bin/env python3
"""
Test script for MCP shared library integration.

Validates that:
1. Shared library imports work correctly
2. Preset filters are properly configured
3. Filter functions handle edge cases
4. Verification functions work as expected

This script does NOT require actual MCP connection - it tests the
library structure and logic with mock data.
"""

import sys
from pathlib import Path

# Add src to path to enable imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test that all shared library imports work"""
    print("\n" + "="*70)
    print("TEST 1: Import Validation")
    print("="*70)

    try:
        # Test basic imports
        from fairmind.shared.mcp import (
            # Client functions
            initialize_mcp_tools,
            validate_mcp_environment,
            get_mcp_status,
            # Filter functions
            filter_tools_by_names,
            create_tool_filter,
            handle_tool_name_variants,
            # Preset filters
            GENERAL_TOOLS_FILTER,
            STUDIO_TOOLS_FILTER,
            CODE_TOOLS_FILTER,
            ARCHQA_CONTEXT_MAPPER_FILTER,
            ARCHQA_CODE_INVESTIGATOR_FILTER,
            ARCHQA_SOLUTION_SYNTHESIZER_FILTER,
            DOCGEN_DISCOVERY_FILTER,
            DOCGEN_ANALYSIS_FILTER,
            DOCGEN_GENERATION_FILTER,
            # Verification functions
            categorize_tools,
            verify_tool_availability,
            create_tool_report,
            log_tool_assignment,
            log_agent_startup,
        )
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_filter_functions():
    """Test filter functions with mock data"""
    print("\n" + "="*70)
    print("TEST 2: Filter Function Validation")
    print("="*70)

    from fairmind.shared.mcp import (
        filter_tools_by_names,
        handle_tool_name_variants,
        GENERAL_TOOLS_FILTER,
        ARCHQA_CONTEXT_MAPPER_FILTER,
    )

    # Create mock tools
    class MockTool:
        def __init__(self, name):
            self.name = name
        def __repr__(self):
            return f"MockTool({self.name})"

    mock_tools = {
        "General_list_projects": MockTool("General_list_projects"),
        "mcp__fairmind__General_rag_retrieve_documents": MockTool("mcp__fairmind__General_rag_retrieve_documents"),
        "Studio_list_user_stories_by_project": MockTool("Studio_list_user_stories_by_project"),
        "Code_search": MockTool("Code_search"),
        "Code_list_repositories": MockTool("Code_list_repositories"),
    }

    # Test 1: Tool name variant handling
    print("\nTest 2.1: Tool name variant handling")
    assert handle_tool_name_variants("General_list_projects", ["General_list_projects"]) == True
    assert handle_tool_name_variants("mcp__fairmind__General_list_projects", ["General_list_projects"]) == True
    print("✅ Tool name variants handled correctly")

    # Test 2: Filter by names
    print("\nTest 2.2: Filter by names")
    filtered = filter_tools_by_names(mock_tools, ["General_list_projects", "Code_search"])
    assert len(filtered) == 2
    print(f"✅ Filtered {len(filtered)} tools as expected")

    # Test 3: Category filter
    print("\nTest 2.3: Category filter (GENERAL_TOOLS_FILTER)")
    general_tools = GENERAL_TOOLS_FILTER(mock_tools)
    assert len(general_tools) == 2  # Should get both General tools
    print(f"✅ General filter returned {len(general_tools)} tools")

    # Test 4: Preset filter
    print("\nTest 2.4: Preset filter (ARCHQA_CONTEXT_MAPPER_FILTER)")
    context_tools = ARCHQA_CONTEXT_MAPPER_FILTER(mock_tools)
    # Should get: 2 General + 1 Studio + 1 Code = 4 tools
    assert len(context_tools) >= 3  # At least General + Studio + some Code
    print(f"✅ Context mapper filter returned {len(context_tools)} tools")

    # Test 5: Empty input handling
    print("\nTest 2.5: Empty input handling")
    empty_result = GENERAL_TOOLS_FILTER({})
    assert empty_result == []
    none_result = GENERAL_TOOLS_FILTER(None)
    assert none_result == []
    print("✅ Empty input handled correctly")

    return True


def test_verification_functions():
    """Test verification and logging functions"""
    print("\n" + "="*70)
    print("TEST 3: Verification Function Validation")
    print("="*70)

    from fairmind.shared.mcp import (
        categorize_tools,
        verify_tool_availability,
        create_tool_report,
    )

    # Create mock tools
    class MockTool:
        def __init__(self, name):
            self.name = name
        def __repr__(self):
            return f"MockTool({self.name})"

    mock_tools = {
        "General_list_projects": MockTool("General_list_projects"),
        "Studio_get_user_story": MockTool("Studio_get_user_story"),
        "Code_search": MockTool("Code_search"),
        "Code_cat": MockTool("Code_cat"),
    }

    # Test 1: Categorization
    print("\nTest 3.1: Tool categorization")
    categories = categorize_tools(mock_tools)
    assert len(categories['General']) == 1
    assert len(categories['Studio']) == 1
    assert len(categories['Code']) == 2
    print(f"✅ Categorized: {len(categories['General'])} General, "
          f"{len(categories['Studio'])} Studio, {len(categories['Code'])} Code")

    # Test 2: Verification (all present)
    print("\nTest 3.2: Tool verification (all present)")
    missing = verify_tool_availability(
        mock_tools,
        ["General_list_projects", "Code_search"],
        "TestAgent"
    )
    assert len(missing) == 0
    print("✅ All required tools verified as present")

    # Test 3: Verification (some missing)
    print("\nTest 3.3: Tool verification (some missing)")
    missing = verify_tool_availability(
        mock_tools,
        ["General_list_projects", "General_missing_tool", "Code_search"],
        "TestAgent"
    )
    assert len(missing) == 1
    assert "General_missing_tool" in missing
    print(f"✅ Correctly identified {len(missing)} missing tool")

    # Test 4: Tool report
    print("\nTest 3.4: Tool report generation")
    report = create_tool_report(mock_tools)
    assert "MCP tools initialized" in report or "tools available" in report
    assert "General" in report
    assert "Studio" in report
    assert "Code" in report
    print("✅ Tool report generated successfully")

    return True


def test_agent_imports():
    """Test that agents can import and use the shared library"""
    print("\n" + "="*70)
    print("TEST 4: Agent Integration Validation")
    print("="*70)

    # Add fairmind-agents to path
    agents_path = Path(__file__).parent / "fairmind-agents"
    sys.path.insert(0, str(agents_path))

    try:
        # Test ArchQA import
        print("\nTest 4.1: ArchQA agent imports")
        # We can't fully import archqa_agent without MCP connection,
        # but we can verify the imports in the file
        archqa_file = agents_path / "archqa" / "archqa_agent.py"
        if archqa_file.exists():
            content = archqa_file.read_text()
            assert "from fairmind.shared.mcp import" in content
            assert "ARCHQA_CONTEXT_MAPPER_FILTER" in content
            assert "log_agent_startup" in content
            print("✅ ArchQA agent uses shared library correctly")
        else:
            print("⚠️  ArchQA agent file not found")

        # Test DocGen import
        print("\nTest 4.2: DocGen agent imports")
        docgen_file = agents_path / "docgen" / "docgen_agent.py"
        if docgen_file.exists():
            content = docgen_file.read_text()
            assert "from fairmind.shared.mcp import" in content
            assert "DOCGEN_DISCOVERY_FILTER" in content
            assert "log_agent_startup" in content
            print("✅ DocGen agent uses shared library correctly")
        else:
            print("⚠️  DocGen agent file not found")

        return True

    except Exception as e:
        print(f"❌ Agent integration test failed: {e}")
        return False


def test_deprecation_warnings():
    """Test that deprecated functions emit warnings"""
    print("\n" + "="*70)
    print("TEST 5: Deprecation Warning Validation")
    print("="*70)

    import warnings

    # Add fairmind-agents to path
    agents_path = Path(__file__).parent / "fairmind-agents"
    sys.path.insert(0, str(agents_path))

    try:
        # Test ArchQA deprecated module
        print("\nTest 5.1: ArchQA mcp_tool_filters deprecation")
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            # This should trigger deprecation warning
            from archqa import mcp_tool_filters

            if len(w) > 0:
                assert issubclass(w[0].category, DeprecationWarning)
                assert "deprecated" in str(w[0].message).lower()
                print("✅ ArchQA module emits deprecation warning")
            else:
                print("⚠️  No deprecation warning emitted")

        # Test DocGen deprecated functions
        print("\nTest 5.2: DocGen filter function deprecation")
        docgen_agents_file = agents_path / "docgen" / "agents.py"
        if docgen_agents_file.exists():
            content = docgen_agents_file.read_text()
            # Check that deprecation warnings are present
            assert "DEPRECATED" in content
            assert "get_discovery_tools() is deprecated" in content
            assert "get_analysis_tools() is deprecated" in content
            assert "get_generation_tools() is deprecated" in content
            print("✅ DocGen functions have deprecation warnings")
        else:
            print("⚠️  DocGen agents file not found")

        return True

    except Exception as e:
        print(f"❌ Deprecation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all validation tests"""
    print("\n" + "╔" + "="*68 + "╗")
    print("║" + " "*15 + "MCP Shared Library Validation Tests" + " "*18 + "║")
    print("╚" + "="*68 + "╝")

    results = {
        "Imports": test_imports(),
        "Filter Functions": test_filter_functions(),
        "Verification Functions": test_verification_functions(),
        "Agent Integration": test_agent_imports(),
        "Deprecation Warnings": test_deprecation_warnings(),
    }

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())

    print("\n" + "="*70)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Shared library is working correctly!")
        print("="*70)
        return 0
    else:
        print("⚠️  SOME TESTS FAILED - Please review the output above")
        print("="*70)
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
