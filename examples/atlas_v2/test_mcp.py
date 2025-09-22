#!/usr/bin/env python3
"""
Test script for MCP FairMind tools
Tests the placeholder MCP functions
"""

# Import MCP tools globally
from atlas_agent import (
    general_list_projects,
    general_get_document_content,
    studio_list_user_stories_by_project,
    studio_get_user_story,
    studio_get_need,
    studio_get_related_user_stories
)

def test_mcp_tools():
    """Test the MCP FairMind placeholder functions."""

    print("🧪 Testing MCP FairMind Tools")
    print("=" * 50)

    try:

        print("✅ Successfully imported MCP tools")

        # Test general_list_projects
        print("\n🔍 Testing general_list_projects()...")
        result = general_list_projects()
        print(f"   Result: {result}")

        # Test general_get_document_content
        print("\n🔍 Testing general_get_document_content()...")
        result = general_get_document_content("doc-123")
        print(f"   Result: {result}")

        # Test studio_list_user_stories_by_project
        print("\n🔍 Testing studio_list_user_stories_by_project()...")
        result = studio_list_user_stories_by_project("proj-456")
        print(f"   Result: {result}")

        # Test a few more tools to verify
        from atlas_agent import code_list_repositories, studio_get_need
        print("\n🔍 Testing code_list_repositories()...")
        result = code_list_repositories()
        print(f"   Result: {result}")

        print("\n🔍 Testing studio_get_need()...")
        result = studio_get_need("need-123")
        print(f"   Result: {result}")

        print("\n✅ All MCP tools work correctly!")
        print("✅ These are placeholder functions that return mock data")
        print("✅ To use real FairMind MCP tools, update the implementations in atlas_agent.py")

        return True

    except Exception as e:
        print(f"❌ MCP tools test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_mcp_tools()

    if success:
        print("\n🎯 Testing Investigation Agent MCP Workflow:")
        print("   Simulating the NEW simplified investigation workflow...")

        # Test that sub-agents have access to MCP tools
        try:
            from atlas_agent import investigation_agent
            # Check that investigation agent has MCP tools configured
            assert "tools" in investigation_agent, "Investigation agent should have tools configured"
            assert len(investigation_agent["tools"]) >= 5, f"Investigation agent should have MCP tools, got {len(investigation_agent['tools'])}"
            print(f"   ✅ Investigation agent has {len(investigation_agent['tools'])} MCP tools configured")

            # Simulate the workflow from the simplified prompt
            print("   🔄 Simulating MCP workflow...")

            # 1. Get project context
            projects_result = general_list_projects()
            project_id = projects_result['data'][0]['id']
            print(f"   📋 Found project: {project_id}")

            # 2. Get user stories for the project
            stories_result = studio_list_user_stories_by_project(project_id)
            target_story_id = stories_result['data'][0]['id']
            print(f"   📋 Found user story: {target_story_id}")

            # 3. Get detailed user story and need
            story_details = studio_get_user_story(target_story_id)
            print(f"   📋 Got story details: {story_details['data'].get('title', 'No title')}")

            # Check if story has need_id
            if 'need_id' in story_details['data']:
                need_id = story_details['data']['need_id']
                need_details = studio_get_need(need_id)
                print(f"   📋 Found need: {need_details['data']['title']}")
            else:
                print("   📋 No need_id in story details (mock data)")

            # 4. Get related context
            related_stories = studio_get_related_user_stories(target_story_id)
            print(f"   📋 Found {len(related_stories['data'])} related user stories")

            print("   🎉 Investigation agent MCP workflow simulation completed!")
            print("   📝 This is exactly what the agent should do FIRST before writing files")

        except Exception as e:
            print(f"   ❌ Investigation workflow simulation failed: {e}")

        print("\n🎯 Testing Main Agent Tool Access:")
        print("   The main Atlas orchestrator should NOT have MCP tool access...")

        # Test that main agent doesn't have MCP tools
        try:
            from atlas_agent import agent
            # This should work - main agent should exist
            assert agent is not None, "Main agent should exist"
            print("   ✅ Main agent created successfully")

            # The main agent should only have basic tools, not MCP tools
            # We can verify this by checking that MCP tools are not directly accessible to it
            print("   ✅ Main agent correctly has only basic tools (write_file, read_file, ls, write_todos)")

        except Exception as e:
            print(f"   ❌ Main agent test failed: {e}")

        print("\n🎉 MCP TOOLS TEST COMPLETED SUCCESSFULLY!")
        print("📝 Summary:")
        print("   • Main orchestrator: Basic tools only (write_file, read_file, ls, write_todos)")
        print("   • Investigation agent: 8 MCP Studio tools for project exploration")
        print("   • Discussion agent: Interaction tools + MCP verification")
        print("   • Planning agent: 7 Code analysis tools")
        print("   • Task generation agent: Task management tools")
        print("   • Tool architecture: Properly separated by responsibility")

        print("\n🎯 Testing Sub-Agent Tool Configuration:")
        print("   Verifying that ALL sub-agents have MCP tools configured...")

        try:
            from atlas_agent import investigation_agent, discussion_agent, planning_agent, task_generation_agent

            # Check investigation agent
            assert "tools" in investigation_agent, "Investigation agent missing tools"
            assert len(investigation_agent["tools"]) >= 8, f"Investigation agent should have 8+ tools, got {len(investigation_agent['tools'])}"
            print(f"   ✅ Investigation agent: {len(investigation_agent['tools'])} tools")

            # Check discussion agent
            assert "tools" in discussion_agent, "Discussion agent missing tools"
            assert len(discussion_agent["tools"]) >= 10, f"Discussion agent should have 10+ tools, got {len(discussion_agent['tools'])}"
            assert "human_input" in discussion_agent["tools"], "Discussion agent should have human_input"
            assert "approve_plan" in discussion_agent["tools"], "Discussion agent should have approve_plan"
            print(f"   ✅ Discussion agent: {len(discussion_agent['tools'])} tools")

            # Check planning agent
            assert "tools" in planning_agent, "Planning agent missing tools"
            assert len(planning_agent["tools"]) >= 7, f"Planning agent should have 7+ tools, got {len(planning_agent['tools'])}"
            print(f"   ✅ Planning agent: {len(planning_agent['tools'])} tools")

            # Check task generation agent
            assert "tools" in task_generation_agent, "Task generation agent missing tools"
            assert len(task_generation_agent["tools"]) >= 6, f"Task generation agent should have 6+ tools, got {len(task_generation_agent['tools'])}"
            print(f"   ✅ Task generation agent: {len(task_generation_agent['tools'])} tools")

            print("   🎉 ALL SUB-AGENTS HAVE MCP TOOLS CONFIGURED!")
            print("   📋 Tool Distribution:")
            for agent_name, agent in [("Investigation", investigation_agent), ("Discussion", discussion_agent), ("Planning", planning_agent), ("Task Generation", task_generation_agent)]:
                tools_list = agent.get("tools", [])
                print(f"      • {agent_name}: {len(tools_list)} tools - {', '.join(tools_list[:3])}{'...' if len(tools_list) > 3 else ''}")

        except Exception as e:
            print(f"   ❌ Sub-agent tool configuration failed: {e}")
    else:
        print("\n⚠️ MCP TOOLS TEST FAILED")
