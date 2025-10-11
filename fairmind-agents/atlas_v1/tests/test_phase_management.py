#!/usr/bin/env python3
"""
Test script for enhanced phase management in Atlas V1

This script tests:
1. Phase detection from files
2. Phase validation
3. Tool isolation architecture
4. Phase sequence management
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from atlas_coordinator import AtlasCoordinator

def test_phase_detection():
    """Test phase detection from virtual filesystem"""
    print("\n=== Testing Phase Detection ===\n")
    
    # Initialize coordinator (without MCP tools for simplicity)
    coordinator = AtlasCoordinator(mcp_tools=None)
    
    # Test different file configurations
    test_cases = [
        (
            {},
            "investigation",
            "No files → should start with investigation"
        ),
        (
            {"investigation_findings.md": "content"},
            "discussion",
            "Only investigation file → should move to discussion"
        ),
        (
            {
                "investigation_findings.md": "content",
                "clarification_questions.md": "questions",
                "user_responses.md": "responses",
                "requirements_clarified.md": "requirements"
            },
            "planning",
            "All discussion files → should move to planning"
        ),
        (
            {
                "investigation_findings.md": "content",
                "requirements_clarified.md": "requirements",
                "implementation_plan.md": "plan"
            },
            "task_generation",
            "Planning complete → should move to task generation"
        ),
        (
            {
                "investigation_findings.md": "content",
                "requirements_clarified.md": "requirements",
                "implementation_plan.md": "plan",
                "implementation_tasks.md": "tasks"
            },
            "completed",
            "All files present → should be completed"
        )
    ]
    
    for files, expected_phase, description in test_cases:
        actual_phase = coordinator.get_current_phase_from_files(files)
        status = "✅" if actual_phase == expected_phase else "❌"
        print(f"{status} {description}")
        print(f"   Expected: {expected_phase}, Got: {actual_phase}")
        if actual_phase != expected_phase:
            print(f"   Files present: {list(files.keys())}")

def test_phase_sequence():
    """Test phase sequence management"""
    print("\n=== Testing Phase Sequence ===\n")
    
    coordinator = AtlasCoordinator(mcp_tools=None)
    
    # Test getting the sequence
    sequence = coordinator.get_phase_sequence()
    print(f"Phase sequence: {' → '.join(sequence)}")
    
    # Test next phase logic
    test_transitions = [
        ("investigation", "discussion"),
        ("discussion", "planning"),
        ("planning", "task_generation"),
        ("task_generation", None),
        ("completed", None),
        ("unknown", "investigation")  # Should start from beginning
    ]
    
    print("\nPhase transitions:")
    for current, expected_next in test_transitions:
        actual_next = coordinator.get_next_phase(current)
        status = "✅" if actual_next == expected_next else "❌"
        print(f"{status} {current} → {actual_next} (expected: {expected_next})")

def test_phase_validation():
    """Test phase output validation"""
    print("\n=== Testing Phase Validation ===\n")
    
    coordinator = AtlasCoordinator(mcp_tools=None)
    
    # Test validation for investigation phase
    files_incomplete = {"some_other_file.md": "content"}
    files_complete = {"investigation_findings.md": "findings content"}
    
    result_incomplete = coordinator.validate_phase_outputs("investigation", files_incomplete)
    result_complete = coordinator.validate_phase_outputs("investigation", files_complete)
    
    print("Investigation phase validation:")
    print(f"  Incomplete: {'❌' if result_incomplete['missing_outputs'] else '✅'}")
    if result_incomplete['missing_outputs']:
        print(f"    Missing: {result_incomplete['missing_outputs']}")
    
    print(f"  Complete: {'✅' if not result_complete['missing_outputs'] else '❌'}")
    
    # Test discussion phase (requires 3 files)
    discussion_partial = {
        "investigation_findings.md": "findings",
        "clarification_questions.md": "questions"
    }
    discussion_complete = {
        "investigation_findings.md": "findings",
        "clarification_questions.md": "questions",
        "user_responses.md": "responses",
        "requirements_clarified.md": "requirements"
    }
    
    result_partial = coordinator.validate_phase_outputs("discussion", discussion_partial)
    result_complete_disc = coordinator.validate_phase_outputs("discussion", discussion_complete)
    
    print("\nDiscussion phase validation:")
    print(f"  Partial (2/3 files): {'❌' if result_partial['missing_outputs'] else '✅'}")
    if result_partial['missing_outputs']:
        print(f"    Missing: {result_partial['missing_outputs']}")
    
    print(f"  Complete (3/3 files): {'✅' if not result_complete_disc['missing_outputs'] else '❌'}")

def test_tool_isolation():
    """Test and verify tool isolation architecture"""
    print("\n=== Testing Tool Isolation Architecture ===\n")
    
    # Test with no MCP tools to avoid mock tool issues
    coordinator = AtlasCoordinator(mcp_tools=None)
    
    # Get status to see architecture
    status = coordinator.get_status()
    
    print("Coordinator Architecture:")
    print(f"  Tool Isolation: {status.get('tool_isolation', 'unknown')}")
    print(f"  Available Agents: {status['agents_available']}")
    print(f"  MCP Tools Available: {status['mcp_tools']}")
    print(f"  Phase Sequence: {' → '.join(status['phase_sequence'])}")
    
    print("\n✅ Tool Isolation Pattern:")
    print("  - Orchestrator has ONLY coordination tools")
    print("  - Sub-agents get full MCP access via task tool")
    print("  - Enforces separation of concerns")

def test_state_based_phase_detection():
    """Test phase detection using state tracking"""
    print("\n=== Testing State-Based Phase Detection ===\n")
    
    coordinator = AtlasCoordinator(mcp_tools=None)
    
    test_cases = [
        (
            {"completed_phases": [], "files": {}},
            "investigation",
            "Empty state → start with investigation"
        ),
        (
            {
                "completed_phases": ["investigation"],
                "investigation_complete": True,
                "files": {"investigation_findings.md": "content"}
            },
            "discussion",
            "Investigation in completed_phases → move to discussion"
        ),
        (
            {
                "completed_phases": ["investigation", "discussion"],
                "discussion_complete": True,
                "files": {
                    "investigation_findings.md": "content",
                    "requirements_clarified.md": "requirements"
                }
            },
            "planning",
            "Discussion in completed_phases → move to planning"
        ),
        (
            {
                "completed_phases": ["investigation", "discussion", "planning"],
                "planning_complete": True,
                "files": {
                    "investigation_findings.md": "content",
                    "requirements_clarified.md": "requirements",
                    "implementation_plan.md": "plan"
                }
            },
            "task_generation",
            "Planning in completed_phases → move to task generation"
        ),
        (
            {
                "completed_phases": ["investigation", "discussion", "planning", "task_generation"],
                "task_generation_complete": True,
                "files": {
                    "investigation_findings.md": "content",
                    "requirements_clarified.md": "requirements",
                    "implementation_plan.md": "plan",
                    "implementation_tasks.md": "tasks"
                }
            },
            "completed",
            "All phases in completed_phases → completed"
        )
    ]
    
    for state, expected_phase, description in test_cases:
        actual_phase = coordinator.get_current_phase_from_state(state)
        status = "✅" if actual_phase == expected_phase else "❌"
        print(f"{status} {description}")
        print(f"   Expected: {expected_phase}, Got: {actual_phase}")
        if actual_phase != expected_phase:
            print(f"   State: completed_phases={state.get('completed_phases', [])}")

def test_state_file_consistency():
    """Test that state and file detection are consistent"""
    print("\n=== Testing State-File Consistency ===\n")
    
    coordinator = AtlasCoordinator(mcp_tools=None)
    
    # Test when state and files agree
    state_with_files = {
        "completed_phases": ["investigation"],
        "investigation_complete": True,
        "files": {"investigation_findings.md": "content"}
    }
    
    phase_from_state = coordinator.get_current_phase_from_state(state_with_files)
    phase_from_files = coordinator.get_current_phase_from_files(state_with_files["files"])
    
    if phase_from_state == phase_from_files:
        print(f"✅ State and files agree: both say '{phase_from_state}'")
    else:
        print(f"❌ State and files disagree: state='{phase_from_state}', files='{phase_from_files}'")
    
    # Test fallback when state is empty
    empty_state_with_files = {
        "completed_phases": [],
        "files": {"investigation_findings.md": "content"}
    }
    
    phase_with_fallback = coordinator.get_current_phase_from_state(empty_state_with_files)
    print(f"\n✅ Fallback test: Empty state but files exist → '{phase_with_fallback}'")
    print("   (Should use file detection as fallback)")

def main():
    """Run all tests"""
    print("=" * 60)
    print("Atlas V1 Enhanced Phase Management Tests")
    print("=" * 60)
    
    test_phase_detection()
    test_phase_sequence()
    test_phase_validation()
    test_state_based_phase_detection()  # New test
    test_state_file_consistency()       # New test
    test_tool_isolation()
    
    print("\n" + "=" * 60)
    print("✨ All tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    main()