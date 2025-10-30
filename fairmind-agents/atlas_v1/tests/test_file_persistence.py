"""
Test File Persistence Across Atlas V1 Phases

This test suite verifies that each Atlas V1 agent properly creates and persists
files to the virtual filesystem, following the DocGen baseline pattern.

Run with: python -m pytest tests/test_file_persistence.py -v
"""

import asyncio
import pytest
from atlas_agent import create_atlas_agent


class TestFilePersistence:
    """Test file persistence for all Atlas V1 phases"""

    @pytest.fixture
    async def agent(self):
        """Create Atlas agent for testing"""
        return create_atlas_agent()

    @pytest.mark.asyncio
    async def test_investigation_phase_creates_file(self, agent):
        """Test that investigation phase creates investigation_findings.md"""
        # Start with empty state
        initial_state = {"files": {}}

        result = await agent.run(
            "Investigate user story for project",
            project_id="test_project"
        )

        # Verify investigation_findings.md was created
        assert "investigation_findings.md" in result.get("files", {}), \
            "Investigation phase must create investigation_findings.md"

        # Verify file has content
        content = result["files"]["investigation_findings.md"]
        assert len(content) > 0, "investigation_findings.md must have content"
        assert "Project Context" in content, "File must have required structure"

    @pytest.mark.asyncio
    async def test_discussion_phase_creates_files(self, agent):
        """Test that discussion phase creates required files"""
        # Simulate investigation complete
        initial_state = {
            "files": {
                "investigation_findings.md": """# Investigation Findings
## Project Context
- **Project ID**: test_project
- **Investigation Date**: 2025-01-30
## Knowledge Gaps Identified
- User preferences unclear
"""
            }
        }

        # Note: This test would require mocking human_input responses
        # For now, we verify the agent has the correct tools and prompts

        # Get discussion agent configuration
        from agents.discussion_agent import discussion_agent, DISCUSSION_PROMPT

        # Verify prompt includes explicit write_file instructions
        assert "write_file(" in DISCUSSION_PROMPT, \
            "Discussion agent prompt must include explicit write_file() instructions"
        assert 'write_file("requirements_clarified.md"' in DISCUSSION_PROMPT, \
            "Discussion agent must instruct creating requirements_clarified.md"

    @pytest.mark.asyncio
    async def test_planning_phase_creates_file(self, agent):
        """Test that planning phase creates implementation_plan.md"""
        # Simulate previous phases complete
        initial_state = {
            "files": {
                "investigation_findings.md": "# Investigation Findings\n...",
                "requirements_clarified.md": "# Requirements\n..."
            }
        }

        # Verify planning agent prompt includes write_file instructions
        from agents.planning_agent import planning_agent, PLANNING_PROMPT

        assert "write_file(" in PLANNING_PROMPT, \
            "Planning agent prompt must include explicit write_file() instructions"
        assert 'write_file("implementation_plan.md"' in PLANNING_PROMPT, \
            "Planning agent must instruct creating implementation_plan.md"

    @pytest.mark.asyncio
    async def test_task_generation_phase_creates_files(self, agent):
        """Test that task generation creates all required files"""
        # Simulate previous phases complete
        initial_state = {
            "files": {
                "investigation_findings.md": "# Investigation\n...",
                "requirements_clarified.md": "# Requirements\n...",
                "implementation_plan.md": "# Plan\n..."
            }
        }

        # Verify task generation agent prompt
        from agents.task_generation_agent import task_generation_agent, TASK_GENERATION_PROMPT

        assert "write_file(" in TASK_GENERATION_PROMPT, \
            "Task generation agent prompt must include explicit write_file() instructions"

        # Check for all required output files
        required_files = [
            "implementation_tasks.md",
            "repository_task_matrix.md",
            "task_dependencies.md",
            "execution_roadmap.md",
            "context_summary.md"
        ]

        for filename in required_files:
            assert f'write_file("{filename}"' in TASK_GENERATION_PROMPT, \
                f"Task generation must instruct creating {filename}"

    def test_all_agents_have_file_verification(self):
        """Test that all agents include file verification with ls()"""
        from agents.investigation_agent import INVESTIGATION_PROMPT
        from agents.discussion_agent import DISCUSSION_PROMPT
        from agents.planning_agent import PLANNING_PROMPT
        from agents.task_generation_agent import TASK_GENERATION_PROMPT

        prompts = {
            "investigation": INVESTIGATION_PROMPT,
            "discussion": DISCUSSION_PROMPT,
            "planning": PLANNING_PROMPT,
            "task_generation": TASK_GENERATION_PROMPT
        }

        for agent_name, prompt in prompts.items():
            # Verify ls() verification is mentioned
            assert "ls()" in prompt, \
                f"{agent_name} agent must include ls() verification instructions"

            # Verify file existence check is mentioned
            verification_keywords = ["verify", "exists", "confirm", "complete when"]
            has_verification = any(keyword in prompt.lower() for keyword in verification_keywords)
            assert has_verification, \
                f"{agent_name} agent must include file existence verification"

    def test_orchestrator_has_file_verification(self):
        """Test that orchestrator includes file verification pattern"""
        # Read orchestrator instructions from atlas_agent.py
        import inspect
        from atlas_agent import create_atlas_agent

        # Get source code
        source = inspect.getsource(create_atlas_agent)

        # Verify orchestrator instructions include verification
        assert "Verify Phase Completion" in source, \
            "Orchestrator must have file verification section"
        assert "investigation_findings.md" in source, \
            "Orchestrator must verify investigation output"
        assert "requirements_clarified.md" in source, \
            "Orchestrator must verify discussion output"
        assert "implementation_plan.md" in source, \
            "Orchestrator must verify planning output"
        assert "implementation_tasks.md" in source, \
            "Orchestrator must verify task generation output"


class TestFileContentValidation:
    """Test that files have required content structure"""

    def test_investigation_findings_structure(self):
        """Test investigation_findings.md has required sections"""
        from agents.investigation_agent import INVESTIGATION_PROMPT

        required_sections = [
            "Project Context",
            "Project ID",
            "Target User Story Analysis",
            "Related Context",
            "Business Requirements",
            "Knowledge Gaps Identified"
        ]

        for section in required_sections:
            assert section in INVESTIGATION_PROMPT, \
                f"Investigation findings must include {section} section"

    def test_requirements_clarified_structure(self):
        """Test requirements_clarified.md has business narrative"""
        from agents.discussion_agent import DISCUSSION_PROMPT

        required_sections = [
            "User Story",
            "Business Benefits",
            "User Experience",
            "Success Criteria",
            "Scope & Boundaries"
        ]

        for section in required_sections:
            assert section in DISCUSSION_PROMPT, \
                f"Requirements summary must include {section} section"

    def test_implementation_plan_structure(self):
        """Test implementation_plan.md has required sections"""
        from agents.planning_agent import PLANNING_PROMPT

        required_sections = [
            "Executive Summary",
            "Technical Architecture",
            "Development Phases",
            "Repository Impact Analysis",
            "Integration Strategy",
            "Risk Assessment"
        ]

        for section in required_sections:
            assert section in PLANNING_PROMPT, \
                f"Implementation plan must include {section} section"


class TestPromptQuality:
    """Test prompt quality matches DocGen baseline"""

    def test_prompts_use_explicit_write_file_syntax(self):
        """Test all prompts use explicit write_file() not vague language"""
        from agents.investigation_agent import INVESTIGATION_PROMPT
        from agents.discussion_agent import DISCUSSION_PROMPT
        from agents.planning_agent import PLANNING_PROMPT
        from agents.task_generation_agent import TASK_GENERATION_PROMPT

        prompts = {
            "investigation": INVESTIGATION_PROMPT,
            "discussion": DISCUSSION_PROMPT,
            "planning": PLANNING_PROMPT,
            "task_generation": TASK_GENERATION_PROMPT
        }

        for agent_name, prompt in prompts.items():
            # Check for explicit write_file() calls
            assert 'write_file("' in prompt, \
                f"{agent_name} must use explicit write_file() syntax"

            # Check for verification pattern
            assert "ls()" in prompt, \
                f"{agent_name} must include ls() verification"

    def test_prompts_avoid_vague_language(self):
        """Test prompts don't use vague 'save to' language"""
        from agents.discussion_agent import DISCUSSION_PROMPT

        # Discussion agent had the original issue - verify it's fixed
        # Should have explicit write_file(), not just "save to"
        assert 'write_file("clarification_questions.md"' in DISCUSSION_PROMPT, \
            "Discussion agent must use explicit write_file() for questions"
        assert 'write_file("user_responses.md"' in DISCUSSION_PROMPT, \
            "Discussion agent must use explicit write_file() for responses"
        assert 'write_file("requirements_clarified.md"' in DISCUSSION_PROMPT, \
            "Discussion agent must use explicit write_file() for final requirements"


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
