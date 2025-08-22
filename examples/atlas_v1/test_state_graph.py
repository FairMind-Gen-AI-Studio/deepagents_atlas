#!/usr/bin/env python3
"""
Test script for Atlas V1 StateGraph implementation.

This script tests the new intelligent phase routing capabilities including:
- Conditional routing between phases
- Validation nodes
- Quality cycles
- Parallel repository analysis
"""

import os
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set environment to use StateGraph
os.environ["ATLAS_USE_STATE_GRAPH"] = "true"

# Import Atlas agent
from atlas_agent import AtlasAgentV1

def create_mock_mcp_tools():
    """Create mock MCP tools for testing without real MCP connection"""
    mock_tools = {
        "General_list_projects": lambda: [
            {"id": "test-project-1", "name": "Test Project 1"},
            {"id": "test-project-2", "name": "Test Project 2"}
        ],
        "Studio_list_user_stories_by_project": lambda project_id: [
            {"id": "US-001", "title": "User authentication", "description": "Implement user login"},
            {"id": "US-002", "title": "Data processing", "description": "Process user data"}
        ],
        "Code_list_repositories": lambda project_id: [
            {"id": "repo-1", "name": "backend-api"},
            {"id": "repo-2", "name": "frontend-ui"},
            {"id": "repo-3", "name": "data-service"}
        ],
        "Code_get_directory_structure": lambda project_id, repository_id: {
            "structure": """
            backend-api/
            ├── src/
            │   ├── controllers/
            │   ├── models/
            │   └── services/
            └── tests/
            """
        }
    }
    return mock_tools

async def test_state_graph_creation():
    """Test that StateGraph is created successfully"""
    logger.info("=" * 60)
    logger.info("TEST 1: StateGraph Creation")
    logger.info("=" * 60)
    
    try:
        # Create agent with mock tools
        mock_tools = create_mock_mcp_tools()
        agent = AtlasAgentV1(available_tools=mock_tools)
        
        # Check if StateGraph was created
        if agent.use_state_graph and agent.state_graph:
            logger.info("✅ StateGraph created successfully")
            logger.info(f"   - use_state_graph: {agent.use_state_graph}")
            logger.info(f"   - state_graph type: {type(agent.state_graph).__name__}")
            return True
        else:
            logger.error("❌ StateGraph not created")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to create StateGraph: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_phase_routing():
    """Test phase routing logic"""
    logger.info("=" * 60)
    logger.info("TEST 2: Phase Routing Logic")
    logger.info("=" * 60)
    
    try:
        from atlas_graph import AtlasGraphBuilder
        from atlas_state import AtlasState
        
        # Create a minimal test state
        test_state = {
            "messages": [],
            "files": {},
            "current_phase": "investigation",
            "investigation_complete": False,
            "validation_status": {}
        }
        
        # Create mock agent executor
        async def mock_executor(state):
            return state
        
        # Create graph builder
        builder = AtlasGraphBuilder(mock_executor)
        
        # Test routing functions
        logger.info("Testing routing after investigation validation:")
        
        # Test 1: Failed validation should route to retry
        test_state["validation_status"] = {"investigation": {"valid": False}}
        route = builder._route_after_investigation_validation(test_state)
        logger.info(f"   - Failed validation → {route} (expected: retry)")
        assert route == "retry", f"Expected 'retry', got '{route}'"
        
        # Test 2: Successful validation should route to discussion
        test_state["validation_status"] = {"investigation": {"valid": True}}
        route = builder._route_after_investigation_validation(test_state)
        logger.info(f"   - Successful validation → {route} (expected: discussion)")
        assert route == "discussion", f"Expected 'discussion', got '{route}'"
        
        logger.info("✅ Phase routing logic working correctly")
        return True
        
    except Exception as e:
        logger.error(f"❌ Phase routing test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_parallel_repository_analysis():
    """Test parallel repository analysis extraction"""
    logger.info("=" * 60)
    logger.info("TEST 3: Parallel Repository Analysis")
    logger.info("=" * 60)
    
    try:
        from atlas_graph import AtlasGraphBuilder
        
        # Create mock findings with repositories
        mock_findings = """
        # Investigation Findings
        
        ## Repositories
        - backend-api: Main API service
        - frontend-ui: React frontend
        - data-service: Data processing service
        
        ## Analysis
        The project has 3 main repositories...
        """
        
        # Create graph builder
        builder = AtlasGraphBuilder(None)
        
        # Test repository extraction
        repositories = builder._extract_repositories_from_findings(mock_findings)
        
        logger.info(f"Extracted repositories: {repositories}")
        logger.info(f"   - Count: {len(repositories)}")
        logger.info(f"   - Expected: ['backend-api', 'frontend-ui', 'data-service']")
        
        expected = ['backend-api', 'frontend-ui', 'data-service']
        if repositories == expected:
            logger.info("✅ Repository extraction working correctly")
            return True
        else:
            logger.error(f"❌ Repository extraction mismatch")
            return False
            
    except Exception as e:
        logger.error(f"❌ Parallel repository test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_validation_nodes():
    """Test validation node creation and execution"""
    logger.info("=" * 60)
    logger.info("TEST 4: Validation Nodes")
    logger.info("=" * 60)
    
    try:
        from atlas_graph import AtlasGraphBuilder
        from atlas_state import AtlasState
        
        # Create test state with files
        test_state = {
            "messages": [],
            "files": {
                "investigation_findings.md": "# Findings\nTest content"
            },
            "current_phase": "investigation",
            "validation_status": {}
        }
        
        # Create mock executor
        async def mock_executor(state):
            return state
        
        # Create graph builder
        builder = AtlasGraphBuilder(mock_executor)
        
        # Create validation node
        validation_node = builder._create_validation_node("investigation")
        
        # Execute validation
        result_state = validation_node(test_state)
        
        # Check validation status was updated
        if "validation_status" in result_state:
            validation = result_state["validation_status"].get("investigation", {})
            logger.info(f"Validation result: {validation}")
            logger.info(f"   - Outputs present: {validation.get('outputs_present')}")
            logger.info(f"   - Valid: {validation.get('valid')}")
            
            if validation.get("outputs_present"):
                logger.info("✅ Validation node working correctly")
                return True
            else:
                logger.error("❌ Validation failed to detect outputs")
                return False
        else:
            logger.error("❌ Validation status not updated")
            return False
            
    except Exception as e:
        logger.error(f"❌ Validation node test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests"""
    logger.info("Starting Atlas V1 StateGraph Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Run tests
    results.append(await test_state_graph_creation())
    results.append(await test_phase_routing())
    results.append(await test_parallel_repository_analysis())
    results.append(await test_validation_nodes())
    
    # Summary
    logger.info("=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    logger.info(f"Tests passed: {passed}/{total}")
    
    if passed == total:
        logger.info("✅ All tests passed!")
        return 0
    else:
        logger.error(f"❌ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)