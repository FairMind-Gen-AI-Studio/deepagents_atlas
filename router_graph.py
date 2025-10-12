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

# Helper function to clean up conflicting modules before loading next agent
def cleanup_conflicting_modules():
    """Remove conflicting module prefixes from sys.modules to prevent import resolution issues."""
    # Generic conflict prefixes (shared between agents)
    conflict_prefixes = ['agents', 'subagents', 'prompts', 'mcp_tools', 'mcp_client']

    # Agent-specific prefixes that should also be cleaned up
    agent_specific_prefixes = [
        'atlas_coordinator', 'atlas_tools', 'model_config', 'state_store',
        'mcp_client', 'docgen_', 'archqa_', 'research_'
    ]

    all_prefixes = conflict_prefixes + agent_specific_prefixes

    modules_to_remove = []
    for mod_name in sys.modules.keys():
        # Check if module matches any conflict prefix
        for prefix in all_prefixes:
            if mod_name == prefix or mod_name.startswith(prefix + '.'):
                modules_to_remove.append(mod_name)
                break

    # Remove the identified modules
    for mod_name in modules_to_remove:
        sys.modules.pop(mod_name, None)

    # Clear importlib finder cache to ensure fresh import resolution
    importlib.invalidate_caches()

    if modules_to_remove:
        print(f"  🧹 Cleaned up {len(modules_to_remove)} conflicting modules + invalidated import cache")

# Helper function to load agent module directly from file
def load_agent_from_file(agent_name: str, file_path: Path):
    """Load an agent module directly from file to avoid sys.path conflicts."""
    # Clean up conflicting modules BEFORE loading to prevent import resolution issues
    cleanup_conflicting_modules()

    spec = importlib.util.spec_from_file_location(agent_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load spec for {agent_name} from {file_path}")

    module = importlib.util.module_from_spec(spec)

    # Add the agent's directory to sys.path temporarily for its dependencies
    agent_dir = str(file_path.parent)
    added_to_path = False
    if agent_dir not in sys.path:
        sys.path.insert(0, agent_dir)
        added_to_path = True

    # DEBUG: Log sys.modules and sys.path state before loading
    print(f"  🔍 Loading {agent_name} from {file_path.name}")
    agents_in_modules = [m for m in sys.modules.keys() if 'agents' in m.lower()]
    print(f"  🔍 Modules with 'agents': {agents_in_modules[:5]}")  # Show first 5
    atlas_in_path = [p for p in sys.path[:10] if 'atlas_v1' in p or 'archqa' in p]
    print(f"  🔍 Agent dirs in sys.path: {atlas_in_path}")

    try:
        spec.loader.exec_module(module)
        agent_instance = module.agent
        return agent_instance
    finally:
        # Aggressively remove ALL agent directories from sys.path
        # This is needed because agent loading might add directories back
        agent_paths_to_remove = [
            p for p in sys.path
            if isinstance(p, str) and ('atlas_v1' in p or 'docgen' in p or 'archqa' in p or 'research' in p)
            and 'fairmind-agents' in p
        ]
        for path in agent_paths_to_remove:
            while path in sys.path:  # Remove all occurrences
                sys.path.remove(path)

        print(f"  🧹 Removed {len(agent_paths_to_remove)} agent paths from sys.path")

# Import Atlas V1 agent
atlas_agent = load_agent_from_file(
    "atlas_agent_module",
    _project_root / "fairmind-agents" / "atlas_v1" / "atlas_agent.py"
)
print("  ✅ Atlas V1 loaded")

# Import DocGen agent
docgen_agent = load_agent_from_file(
    "docgen_agent_module",
    _project_root / "fairmind-agents" / "docgen" / "docgen_agent.py"
)
print("  ✅ DocGen loaded")

# Import ArchQA agent
archqa_agent = load_agent_from_file(
    "archqa_agent_module",
    _project_root / "fairmind-agents" / "archqa" / "archqa_agent.py"
)
print("  ✅ ArchQA loaded")

# Import Research agent
research_agent = load_agent_from_file(
    "research_agent_module",
    _project_root / "fairmind-agents" / "research" / "research_agent.py"
)
print("  ✅ Research loaded")

print("✅ All agents imported successfully")


def classify_intent(user_query: str) -> Literal["atlas", "docgen", "archqa", "research"]:
    """
    Classify user intent using keyword matching.

    This is a simple POC implementation using keyword-based classification.
    Can be replaced with LLM-based classification for more sophisticated routing.

    Args:
        user_query: User's question/request

    Returns:
        Agent name to route to ("atlas", "docgen", "archqa", or "research")
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

    # DocGen: Documentation generation, code analysis, explanation
    docgen_keywords = [
        "document", "generate docs", "api doc", "readme",
        "documentation", "documenta", "documentazione",
        "create documentation"
    ]
    if any(word in query_lower for word in docgen_keywords):
        return "docgen"

    # ArchQA: Architectural questions, technical debt, code quality
    archqa_keywords = [
        "architecture", "architectural", "technical debt",
        "code quality", "design pattern", "how does", "how is",
        "explain code", "analyze code", "code structure",
        "why does", "what is the purpose"
    ]
    if any(word in query_lower for word in archqa_keywords):
        return "archqa"

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


def aggregator_node(state: DeepAgentState) -> DeepAgentState:
    """
    Aggregator node - re-emits the complete state after subagent execution.

    This node is crucial for SSE state propagation. When a subagent (compiled graph)
    executes as a subgraph node, its internal state updates may not automatically
    propagate via SSE to the frontend. This aggregator node explicitly returns
    the full state (todos, files, messages) so the SSE stream captures it.

    Args:
        state: Current graph state after subagent execution

    Returns:
        Complete state dict for SSE propagation
    """
    todos = state.get('todos', [])
    files = state.get('files', {})
    messages = state.get('messages', [])

    print("📤 Aggregator: Re-emitting state for SSE propagation")
    print(f"   - Todos: {len(todos)} items")
    print(f"   - Files: {len(files)} files")
    print(f"   - Messages: {len(messages)} messages")

    # Debug: Print actual todos content
    if todos:
        print(f"   - First todo: {todos[0]}")

    # IMPORTANT: We must return the state to force LangGraph to emit an SSE update
    # Even though the values are the same, returning them from this node creates
    # a new state update event that the SSE stream will capture
    result = {
        "messages": messages,
        "todos": todos,
        "files": files,
    }

    print(f"📤 Aggregator: Returning state update with {len(todos)} todos")
    return result


def create_agent_wrapper(agent_name: str, compiled_agent):
    """
    Wrap a compiled agent graph in an async node function.

    This wrapper allows the parent graph to:
    1. Execute the subagent and wait for completion
    2. Route to subsequent nodes (aggregator) after completion
    3. Log execution progress for debugging

    The wrapper uses ainvoke() which will automatically stream updates
    from the subgraph through the parent graph's SSE connection.
    """
    async def wrapper(state: DeepAgentState) -> DeepAgentState:
        import time
        start_time = time.time()

        print(f"🎯 Executing {agent_name} agent...")
        print(f"   Input state: messages={len(state.get('messages', []))}, todos={len(state.get('todos', []))}, files={len(state.get('files', {}))}")

        try:
            # Use ainvoke - the subgraph will stream its internal updates automatically
            result = await compiled_agent.ainvoke(state)
            elapsed = time.time() - start_time

            print(f"✅ {agent_name} agent completed in {elapsed:.1f}s")
            print(f"   - Todos in result: {len(result.get('todos', []))}")
            print(f"   - Files in result: {len(result.get('files', {}))}")
            print(f"   - Messages in result: {len(result.get('messages', []))}")

            # Debug: Print first todo if exists
            if result.get('todos'):
                print(f"   - First todo: {result['todos'][0]}")

            return result
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"❌ {agent_name} agent failed after {elapsed:.1f}s: {e}")
            raise
    return wrapper


def create_router_graph():
    """
    Create and compile the hierarchical router graph with agent subgraphs.

    Architecture:
    - Router node performs intent classification
    - Conditional edge routes to appropriate agent subgraph based on classification
    - Agent subgraph executes completely (all phases)
    - Updated state (messages, files, todos) flows back to parent graph
    - Aggregator node re-emits state for SSE propagation
    - Graph terminates

    The agents are compiled LangGraph graphs wrapped in node functions.
    This ensures the parent graph can continue routing after agent execution.

    Returns:
        Compiled router graph (CompiledStateGraph) ready for invocation
    """
    print("🔨 Building router graph...")

    # Create parent router graph using shared DeepAgentState schema
    # All agents use this same schema so state flows naturally
    router_graph = StateGraph(DeepAgentState)

    # Add router node (intent classification)
    router_graph.add_node("router", router_node)

    # Add agent subgraphs as wrapped nodes
    # Wrapping is necessary so the parent graph can route to aggregator after agent execution
    router_graph.add_node("atlas_agent", create_agent_wrapper("Atlas V1", atlas_agent))
    router_graph.add_node("docgen_agent", create_agent_wrapper("DocGen", docgen_agent))
    router_graph.add_node("archqa_agent", create_agent_wrapper("ArchQA", archqa_agent))
    router_graph.add_node("research_agent", create_agent_wrapper("Research", research_agent))

    # Add aggregator node to re-emit state for SSE propagation
    # This ensures todos, files, and messages are visible to the frontend
    router_graph.add_node("aggregator", aggregator_node)

    print("✅ Nodes added: router, atlas_agent, docgen_agent, archqa_agent, research_agent, aggregator")

    # Add conditional routing based on intent classification
    # The lambda extracts the "next_agent" field set by router_node
    # Maps classification result to the appropriate agent node
    router_graph.add_conditional_edges(
        "router",  # Source node
        lambda state: state.get("next_agent", "atlas"),  # Decision function
        {
            "atlas": "atlas_agent",      # If classification = "atlas", route to atlas_agent
            "docgen": "docgen_agent",    # If classification = "docgen", route to docgen_agent
            "archqa": "archqa_agent",    # If classification = "archqa", route to archqa_agent
            "research": "research_agent" # If classification = "research", route to research_agent
        }
    )

    # All agent subgraphs route to aggregator node
    # The aggregator re-emits the complete state so SSE can capture todos/files/messages
    router_graph.add_edge("atlas_agent", "aggregator")
    router_graph.add_edge("docgen_agent", "aggregator")
    router_graph.add_edge("archqa_agent", "aggregator")
    router_graph.add_edge("research_agent", "aggregator")

    # Aggregator routes to END after re-emitting state
    router_graph.add_edge("aggregator", END)

    # Set entry point - graph starts at router node
    router_graph.add_edge(START, "router")

    print("✅ Router graph compiled successfully")
    print("")
    print("Available Routes:")
    print("  - Atlas V1: Planning, implementation, task generation, user story analysis")
    print("  - DocGen: Documentation generation, repository documentation")
    print("  - ArchQA: Architectural questions, technical debt analysis, code quality assessment")
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
