"""
Hierarchical Teams Router Pattern Implementation
Routes user requests to Atlas V1, DocGen, or Research agents based on intent classification.

This implements the pattern from HIERARCHICAL_TEAMS_PATTERN.md as a single unified LangGraph
graph where specialized agent graphs become subgraph nodes within a parent router graph.
"""

import sys
import os
import importlib.util
from pathlib import Path
from typing import Literal
from langgraph.graph import StateGraph, START, END
from deepagents.state import DeepAgentState
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Project root
_project_root = Path(__file__).parent

# Load environment variables from .env file
load_dotenv(_project_root / ".env")
print(f"📝 Environment loaded from {_project_root / '.env'}")

print("📦 Importing agent graphs using importlib...")

# Helper function to load agent module directly from file
def load_agent_from_file(agent_name: str, file_path: Path):
    """Load an agent module directly from file to avoid sys.path conflicts."""
    spec = importlib.util.spec_from_file_location(agent_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {agent_name} from {file_path}")

    module = importlib.util.module_from_spec(spec)

    # Save current sys.path and sys.modules state
    agent_dir = str(file_path.parent)
    old_path = sys.path.copy()
    old_modules = set(sys.modules.keys())

    # Add the agent's directory to sys.path temporarily for its dependencies
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)

    try:
        spec.loader.exec_module(module)
        agent_instance = module.agent

        # Clean up sys.modules - remove modules that were added during this import
        # except the ones we explicitly want to keep
        new_modules = set(sys.modules.keys()) - old_modules
        # Keep the agent module itself and core dependencies
        keep_modules = {agent_name, 'langgraph', 'langchain', 'deepagents'}
        for mod_name in new_modules:
            if not any(mod_name.startswith(keep) for keep in keep_modules):
                # Remove conflicting modules like 'agents', 'subagents', etc.
                if mod_name in ['agents', 'subagents', 'prompts', 'mcp_tools', 'mcp_client']:
                    sys.modules.pop(mod_name, None)

        return agent_instance
    finally:
        # Restore sys.path to avoid pollution
        sys.path = old_path

# Import Atlas V1 agent
atlas_agent = load_agent_from_file(
    "atlas_agent_module",
    _project_root / "examples" / "atlas_v1" / "atlas_agent.py"
)
print("  ✅ Atlas V1 loaded")

# Import DocGen agent
docgen_agent = load_agent_from_file(
    "docgen_agent_module",
    _project_root / "examples" / "docgen" / "docgen_agent.py"
)
print("  ✅ DocGen loaded")

# Import Research agent
research_agent = load_agent_from_file(
    "research_agent_module",
    _project_root / "examples" / "research" / "research_agent.py"
)
print("  ✅ Research loaded")

print("✅ All agents imported successfully")


def classify_intent(user_query: str) -> Literal["atlas", "docgen", "research"]:
    """
    Classify user intent using keyword matching.

    This is a simple POC implementation using keyword-based classification.
    Can be replaced with LLM-based classification for more sophisticated routing.

    Args:
        user_query: User's question/request

    Returns:
        Agent name to route to ("atlas", "docgen", or "research")
    """
    query_lower = user_query.lower()

    # Atlas V1: Planning, implementation, tasks, user stories
    atlas_keywords = [
        "plan", "implement", "task", "user story", "us-",
        "feature", "requirement", "sprint", "backlog",
        "analyze user story", "create plan", "implementation",
        "planning", "sviluppo", "sviluppare"
    ]
    if any(word in query_lower for word in atlas_keywords):
        return "atlas"

    # DocGen: Documentation, code analysis, explanation
    docgen_keywords = [
        "document", "explain", "analyze code", "repository",
        "api doc", "readme", "architecture", "generate docs",
        "code explanation", "codebase", "documenta", "documentazione"
    ]
    if any(word in query_lower for word in docgen_keywords):
        return "docgen"

    # Research: Web search, information gathering
    research_keywords = [
        "research", "search", "find information", "look up",
        "what is", "how to", "best practices", "investigate",
        "web search", "cerca", "ricerca"
    ]
    if any(word in query_lower for word in research_keywords):
        return "research"

    # Default to Atlas (most general purpose agent)
    return "atlas"


def router_node(state: DeepAgentState) -> dict:
    """
    Router node - performs intent classification and returns routing decision.

    This node:
    1. Extracts user query from messages in state
    2. Classifies intent using keyword matching
    3. Returns routing decision as state update

    The routing decision is stored in the "next_agent" field which is used
    by the conditional edge to determine which agent subgraph to invoke.

    Args:
        state: Current graph state with messages

    Returns:
        State update dict with "next_agent" field set to route destination
    """
    # Extract user message
    if not state.get("messages"):
        print("⚠️  No messages in state, defaulting to Atlas V1")
        return {"next_agent": "atlas"}

    # Get last user message content
    last_message = state["messages"][-1]
    user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # Classify intent
    next_agent = classify_intent(user_message)

    # Log routing decision for debugging and monitoring
    print("=" * 60)
    print("🔀 ROUTER DECISION")
    print("=" * 60)
    print(f"Query: {user_message[:100]}...")
    print(f"Routed to: {next_agent.upper()}")
    print("=" * 60)

    # Return state update with routing decision
    # The conditional edge will use this to route to the appropriate agent
    return {"next_agent": next_agent}


def create_router_graph():
    """
    Create and compile the hierarchical router graph with agent subgraphs.

    Architecture:
    - Router node performs intent classification
    - Conditional edge routes to appropriate agent subgraph based on classification
    - Agent subgraph executes completely (all phases)
    - Updated state (messages, files, todos) flows back to parent graph
    - Graph terminates

    The agents are compiled LangGraph graphs that become opaque subgraph nodes.
    State flows in, subgraph executes, updated state flows out. LangGraph handles
    all state merging automatically.

    Returns:
        Compiled router graph (CompiledStateGraph) ready for invocation
    """
    print("🔨 Building router graph...")

    # Create parent router graph using shared DeepAgentState schema
    # All agents use this same schema so state flows naturally
    router_graph = StateGraph(DeepAgentState)

    # Add router node (intent classification)
    router_graph.add_node("router", router_node)

    # Add agent subgraphs as nodes
    # These are compiled LangGraph graphs treated as opaque nodes
    # Each agent receives full DeepAgentState and returns updated state
    router_graph.add_node("atlas_agent", atlas_agent)
    router_graph.add_node("docgen_agent", docgen_agent)
    router_graph.add_node("research_agent", research_agent)

    print("✅ Nodes added: router, atlas_agent, docgen_agent, research_agent")

    # Add conditional routing based on intent classification
    # The lambda extracts the "next_agent" field set by router_node
    # Maps classification result to the appropriate agent node
    router_graph.add_conditional_edges(
        "router",  # Source node
        lambda state: state.get("next_agent", "atlas"),  # Decision function
        {
            "atlas": "atlas_agent",      # If classification = "atlas", route to atlas_agent
            "docgen": "docgen_agent",    # If classification = "docgen", route to docgen_agent
            "research": "research_agent" # If classification = "research", route to research_agent
        }
    )

    # All agent subgraphs route to END after execution
    # No further processing needed after agent completes
    router_graph.add_edge("atlas_agent", END)
    router_graph.add_edge("docgen_agent", END)
    router_graph.add_edge("research_agent", END)

    # Set entry point - graph starts at router node
    router_graph.add_edge(START, "router")

    print("✅ Router graph compiled successfully")
    print("")
    print("Available Routes:")
    print("  - Atlas V1: Planning, implementation, task generation, user story analysis")
    print("  - DocGen: Documentation generation, code analysis, repository documentation")
    print("  - Research: Web search, information gathering, best practices research")
    print("")

    # Compile and return the graph
    # The compiled graph can be invoked with state and will execute the routing logic
    return router_graph.compile()


# Export compiled agent for LangGraph
# This is what langgraph.json references as "./router_graph.py:agent"
agent = create_router_graph()


# Example usage and testing
if __name__ == "__main__":
    print("🧪 Testing router graph...")
    print("")

    # Test 1: Atlas routing - Planning request
    print("=" * 60)
    print("TEST 1: Planning Request → Should route to Atlas V1")
    print("=" * 60)
    result = agent.invoke({
        "messages": [HumanMessage(content="Create implementation plan for user story US-123")]
    })
    print(f"✅ Test 1 complete")
    print(f"Files created: {list(result.get('files', {}).keys())}")
    print(f"Response preview: {result['messages'][-1].content[:200] if result.get('messages') else 'No response'}...")
    print("")

    # Test 2: DocGen routing - Documentation request
    print("=" * 60)
    print("TEST 2: Documentation Request → Should route to DocGen")
    print("=" * 60)
    result = agent.invoke({
        "messages": [HumanMessage(content="Document the authentication API endpoints")]
    })
    print(f"✅ Test 2 complete")
    print(f"Files created: {list(result.get('files', {}).keys())}")
    print(f"Response preview: {result['messages'][-1].content[:200] if result.get('messages') else 'No response'}...")
    print("")

    # Test 3: Research routing - Web search request
    print("=" * 60)
    print("TEST 3: Research Request → Should route to Research")
    print("=" * 60)
    result = agent.invoke({
        "messages": [HumanMessage(content="Research best practices for API authentication")]
    })
    print(f"✅ Test 3 complete")
    print(f"Files created: {list(result.get('files', {}).keys())}")
    print(f"Response preview: {result['messages'][-1].content[:200] if result.get('messages') else 'No response'}...")
    print("")

    print("✅ All router classification tests completed!")
    print("")
    print("Next steps:")
    print("1. Run 'langgraph dev' to start the unified backend server")
    print("2. Update UI .env.local with NEXT_PUBLIC_AGENT_ID='router'")
    print("3. Test routing through the UI chat interface")
