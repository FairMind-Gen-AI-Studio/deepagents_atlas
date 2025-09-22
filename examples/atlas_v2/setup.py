#!/usr/bin/env python3
"""
Setup script for Atlas V2
Helps configure the environment and test the installation
"""

import os
import sys

def check_requirements():
    """Check if required packages are installed."""
    print("🔍 Checking requirements...")

    try:
        import deepagents
        print("   ✅ deepagents installed")
    except ImportError:
        print("   ❌ deepagents not installed")
        print("   Run: pip install -r requirements.txt")
        return False

    try:
        import langgraph
        print("   ✅ langgraph installed")
    except ImportError:
        print("   ❌ langgraph not installed")
        print("   Run: pip install -r requirements.txt")
        return False

    return True

def check_env_file():
    """Check if .env file exists and has required configuration."""
    print("🔍 Checking environment configuration...")

    env_file = '.env'
    config_file = 'config.env'

    if not os.path.exists(config_file):
        print("   ❌ config.env not found")
        return False

    if os.path.exists(env_file):
        print("   ✅ .env file exists")
    else:
        print("   ⚠️ .env file not found")
        print("   Run: cp config.env .env")
        print("   Then edit .env with your API keys")
        return False

    # Check for required API key
    try:
        with open(env_file, 'r') as f:
            content = f.read()

        if 'ANTHROPIC_API_KEY=sk-ant' in content:
            print("   ⚠️ ANTHROPIC_API_KEY not configured")
            print("   Please edit .env and set your actual API key")
        elif 'ANTHROPIC_API_KEY=' in content:
            print("   ✅ ANTHROPIC_API_KEY configured")
        else:
            print("   ❌ ANTHROPIC_API_KEY not found in .env")

        # Check for MCP FairMind token
        if 'MCP_FAIRMIND_TOKEN=' in content and 'your-fairmind-mcp-token-here' not in content:
            print("   ✅ MCP_FAIRMIND_TOKEN configured")
        else:
            print("   ⚠️ MCP_FAIRMIND_TOKEN not configured")
            print("   Please edit .env and set your FairMind MCP token")
    except Exception as e:
        print(f"   ❌ Error reading .env: {e}")
        return False

    return True

def test_imports():
    """Test that Atlas V2 can be imported correctly."""
    print("🔍 Testing imports...")

    try:
        from atlas_agent import agent, investigation_agent, discussion_agent, planning_agent, task_generation_agent
        print("   ✅ All agents imported successfully")

        # Test agent methods
        assert hasattr(agent, 'invoke'), "Agent should have invoke method"
        assert hasattr(agent, 'stream'), "Agent should have stream method"
        print("   ✅ Agent has required methods")

        # Test that MCP tools are available for sub-agents
        from atlas_agent import MCP_FAIRMIND_TOOLS
        assert len(MCP_FAIRMIND_TOOLS) == 23, f"Expected 23 MCP tools, got {len(MCP_FAIRMIND_TOOLS)}"
        print(f"   ✅ {len(MCP_FAIRMIND_TOOLS)} MCP FairMind tools available for sub-agents")

        # Test that main agent does NOT have MCP tools (should raise ImportError)
        try:
            from atlas_agent import atlas_instructions
            # Check that main agent instructions mention no MCP access
            assert "You do NOT have access to MCP FairMind tools" in atlas_instructions, "Main agent should not have MCP access"
            print("   ✅ Main agent correctly has no MCP tools access")

            # Test that all sub-agents have their tools configured
            from atlas_agent import investigation_agent, discussion_agent, planning_agent, task_generation_agent

            # Check investigation agent tools
            assert "tools" in investigation_agent, "Investigation agent should have tools configured"
            assert len(investigation_agent["tools"]) >= 5, f"Investigation agent should have MCP tools, got {len(investigation_agent['tools'])}"
            assert "studio_list_projects" in investigation_agent["tools"], "Investigation agent should have studio_list_projects"
            print("   ✅ Investigation agent configured with MCP tools")

            # Check discussion agent tools
            assert "tools" in discussion_agent, "Discussion agent should have tools configured"
            assert "human_input" in discussion_agent["tools"], "Discussion agent should have human_input"
            assert "approve_plan" in discussion_agent["tools"], "Discussion agent should have approve_plan"
            print("   ✅ Discussion agent configured with human_input, approve_plan and MCP verification tools")

            # Check planning agent tools
            assert "tools" in planning_agent, "Planning agent should have tools configured"
            assert len(planning_agent["tools"]) >= 5, f"Planning agent should have code tools, got {len(planning_agent['tools'])}"
            assert "code_get_directory_structure" in planning_agent["tools"], "Planning agent should have code tools"
            print("   ✅ Planning agent configured with code analysis tools")

            # Check task generation agent tools
            assert "tools" in task_generation_agent, "Task generation agent should have tools configured"
            assert len(task_generation_agent["tools"]) >= 2, f"Task generation agent should have task tools, got {len(task_generation_agent['tools'])}"
            assert "write_todos" in task_generation_agent["tools"], "Task generation agent should have write_todos"
            print("   ✅ Task generation agent configured with task management tools")
        except Exception as e:
            print(f"   ❌ Main agent test failed: {e}")
            raise

        return True

    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        return False

def show_next_steps():
    """Show what to do next."""
    print("\n🎯 Next Steps:")
    print("1. Edit .env file with your actual API keys")
    print("2. Run: langgraph dev")
    print("3. Open LangGraph Studio in your browser")
    print("4. Start using Atlas V2!")

if __name__ == "__main__":
    print("🚀 ATLAS V2 SETUP")
    print("=" * 50)

    success = True

    # Check requirements
    if not check_requirements():
        success = False

    print()

    # Check environment
    if not check_env_file():
        success = False

    print()

    # Test imports
    if not test_imports():
        success = False

    print("\n" + "=" * 50)

    if success:
        print("🎉 ATLAS V2 SETUP COMPLETED SUCCESSFULLY!")
        print("✅ All checks passed")
        show_next_steps()
    else:
        print("⚠️ ATLAS V2 SETUP NEEDS ATTENTION")
        print("🔧 Please fix the issues above before running Atlas V2")

    print("\n📖 For detailed configuration, see README.md")
    print("🐛 For troubleshooting, see the Troubleshooting section in README.md")
