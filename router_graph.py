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
from typing import Literal, NotRequired
from typing_extensions import Annotated
from langgraph.graph import StateGraph, START, END
from deepagents.state import DeepAgentState
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

# Project root
_project_root = Path(__file__).parent


# Reducer for active_agent channel
def active_agent_reducer(current, update):
    """
    Reducer for active_agent channel that preserves values across checkpoints.

    Args:
        current: Current value from checkpoint (or None if not set)
        update: New value being applied (or None if not in update dict)

    Returns:
        The merged value following these rules:
        - If update is provided and not None, use it (allows setting/changing agent)
        - If update is None but current exists, keep current (preserves across updates)
        - Otherwise None (initial state or explicit clear)
    """
    print(f"🔧 REDUCER CALLED: current={current}, update={update}")
    result = None
    if update is not None:
        result = update
        print(f"   → Using update value: {result}")
    elif current is not None:
        result = current
        print(f"   → Preserving current value: {result}")
    else:
        result = None
        print(f"   → No value, returning None")
    return result


# Router State Schema
# Extends DeepAgentState with active_agent field for session continuity
class RouterState(DeepAgentState):
    """
    Router state schema extending DeepAgentState with session tracking.

    The active_agent field tracks which agent is currently handling the conversation,
    enabling session continuity across multiple user messages. This field is persisted
    in LangGraph checkpoints as a proper channel (via Annotated with reducer).

    Fields:
        active_agent: Name of the currently active agent ("atlas", "docgen", "archqa", or "research")
                     None when no agent session is active (initial message or after workflow completion)
                     Uses active_agent_reducer that preserves the value across checkpoint saves/loads.
    """
    # CRITICAL: Use Annotated[NotRequired[str], reducer] pattern (same as files in DeepAgentState)
    # This creates a LangGraph channel that persists to checkpoints.
    # NotRequired handles the optional nature; the reducer handles None values.
    # Using str (not str | None) matches the proven pattern from DeepAgentState.files.
    active_agent: Annotated[NotRequired[str], active_agent_reducer]


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
    1. Checks if an agent session is active (preserves workflow continuity)
    2. If no active session, extracts user query and classifies intent
    3. Returns routing decision as state update

    The routing decision is stored in the "next_agent" field which is used
    by the conditional edge to determine which agent subgraph to invoke.

    Session Continuity:
    - Once an agent starts working, all subsequent messages go to that agent
    - Agent can signal completion by including [WORKFLOW_COMPLETE] in response
    - User can override with explicit commands like "switch to [agent]"

    Args:
        state: Current graph state with messages

    Returns:
        State update dict with "next_agent" field set to route destination
    """
    # Extract user message
    if not state.get("messages"):
        print("⚠️  No messages in state, defaulting to Atlas V1")
        return {"next_agent": "atlas", "active_agent": "atlas"}

    # DEBUG: Log router input state
    active_agent_in_input = state.get("active_agent")
    print(f"🔍 DEBUG: router_node INPUT active_agent = {active_agent_in_input}")
    print(f"🔍 DEBUG: router_node INPUT state keys = {list(state.keys())}")

    # Get last user message content
    last_message = state["messages"][-1]
    user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)

    # Check for active session continuity
    active_agent = state.get("active_agent")

    # Check if previous agent signaled completion
    if len(state["messages"]) >= 2:
        prev_message = state["messages"][-2]
        prev_content = prev_message.content if hasattr(prev_message, 'content') else str(prev_message)
        if "[WORKFLOW_COMPLETE]" in prev_content:
            print("📋 Agent workflow completed, clearing active session")
            active_agent = None

    # Check for explicit user override (e.g., "switch to atlas")
    override_patterns = {
        "switch to atlas": "atlas",
        "switch to docgen": "docgen",
        "switch to archqa": "archqa",
        "switch to research": "research",
        "use atlas": "atlas",
        "use docgen": "docgen",
        "use archqa": "archqa",
        "use research": "research"
    }

    user_lower = user_message.lower()
    explicit_override = None
    for pattern, agent in override_patterns.items():
        if pattern in user_lower:
            explicit_override = agent
            print(f"🔄 User explicitly requested {agent.upper()}")
            break

    # If explicit override, clear active session and use the requested agent
    if explicit_override:
        next_agent = explicit_override
        active_agent = explicit_override
    # If active session exists, continue with same agent
    elif active_agent:
        print("=" * 60)
        print("🔗 CONTINUING ACTIVE SESSION")
        print("=" * 60)
        print(f"Active agent: {active_agent.upper()}")
        print(f"User message: {user_message[:100]}...")
        print(f"Routing to: {active_agent.upper()} (session continuity)")
        print("=" * 60)
        # CRITICAL: Must include active_agent in return to preserve it through the graph
        return {"next_agent": active_agent, "active_agent": active_agent}
    else:
        # New session - classify intent
        next_agent = classify_intent(user_message)
        active_agent = next_agent

    # Log routing decision for debugging and monitoring
    print("=" * 60)
    print("🔀 ROUTER DECISION")
    print("=" * 60)
    print(f"Query: {user_message[:100]}...")
    print(f"Routed to: {next_agent.upper()}")
    if active_agent:
        print(f"Starting new session: {active_agent.upper()}")
    print("=" * 60)

    # DEBUG: Log router output state
    print(f"🔍 DEBUG: router_node OUTPUT next_agent = {next_agent}")
    print(f"🔍 DEBUG: router_node OUTPUT active_agent = {active_agent}")

    # Return state update with routing decision and active session
    return {"next_agent": next_agent, "active_agent": active_agent}


def aggregator_node(state: RouterState) -> RouterState:
    """
    Aggregator node - re-emits the complete state after subagent execution.

    This node is crucial for SSE state propagation. When a subagent (compiled graph)
    executes as a subgraph node, its internal state updates may not automatically
    propagate via SSE to the frontend. This aggregator node explicitly returns
    the full state (todos, files, messages, active_agent) so the SSE stream captures it.

    IMPORTANT: This node MUST propagate active_agent to maintain session continuity.
    Without it, the active agent session would be lost after each agent execution.

    Args:
        state: Current graph state after subagent execution

    Returns:
        Complete state dict for SSE propagation including active_agent
    """
    todos = state.get('todos', [])
    files = state.get('files', {})
    messages = state.get('messages', [])
    active_agent = state.get('active_agent')

    print("📤 Aggregator: Re-emitting state for SSE propagation")
    print(f"   - Todos: {len(todos)} items")
    print(f"   - Files: {len(files)} files")
    print(f"   - Messages: {len(messages)} messages")
    print(f"   - Active agent: {active_agent}")

    # Debug: Print actual todos content
    if todos:
        print(f"   - First todo: {todos[0]}")

    # IMPORTANT: We must return the state to force LangGraph to emit an SSE update
    # Even though the values are the same, returning them from this node creates
    # a new state update event that the SSE stream will capture
    #
    # CRITICAL: Must include active_agent to maintain session continuity!
    result = {
        "messages": messages,
        "todos": todos,
        "files": files,
        "active_agent": active_agent,  # Preserve session state
    }

    print(f"📤 Aggregator: Returning state update with {len(todos)} todos, active_agent={active_agent}")
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
    async def wrapper(state: RouterState) -> RouterState:
        import time
        start_time = time.time()

        # CRITICAL: Preserve active_agent from input state
        # Subagents use DeepAgentState (no active_agent field), so they won't return it.
        # We must preserve it here to maintain session continuity across the router graph.
        active_agent = state.get('active_agent')
        print(f"🎯 Executing {agent_name} agent...")
        print(f"   Input state: messages={len(state.get('messages', []))}, todos={len(state.get('todos', []))}, files={len(state.get('files', {}))}, active_agent={active_agent}")

        try:
            # Use ainvoke - the subgraph will stream its internal updates automatically
            result = await compiled_agent.ainvoke(state)
            elapsed = time.time() - start_time

            print(f"✅ {agent_name} agent completed in {elapsed:.1f}s")
            print(f"   - Todos in result: {len(result.get('todos', []))}")
            print(f"   - Files in result: {len(result.get('files', {}))}")
            print(f"   - Messages in result: {len(result.get('messages', []))}")
            print(f"   - Active agent in result: {result.get('active_agent')}")

            # Debug: Print first todo if exists
            if result.get('todos'):
                print(f"   - First todo: {result['todos'][0]}")

            # CRITICAL FIX: Subagent doesn't have active_agent in its state schema,
            # so we must add it back to the result to preserve session continuity.
            # Without this, active_agent gets lost when subagent returns, breaking
            # the session continuity mechanism.
            if active_agent and 'active_agent' not in result:
                result['active_agent'] = active_agent
                print(f"   ⚠️  Subagent didn't return active_agent, preserving from input: {active_agent}")

            return result
        except Exception as e:
            from langgraph.errors import NodeInterrupt

            # Check if this is a NodeInterrupt (not a real error - expected for human_input)
            if isinstance(e, NodeInterrupt):
                elapsed = time.time() - start_time
                print(f"⏸️  {agent_name} agent paused for human input after {elapsed:.1f}s")
                interrupt_value = e.value if hasattr(e, 'value') else []
                if interrupt_value and isinstance(interrupt_value, list) and len(interrupt_value) > 0:
                    action = interrupt_value[0].get('action_request', {}).get('action', 'unknown') if isinstance(interrupt_value[0], dict) else 'unknown'
                    print(f"   - NodeInterrupt action: {action}")
                # Re-raise so LangGraph can handle it properly
                raise
            else:
                # This is a real error
                elapsed = time.time() - start_time
                print(f"❌ {agent_name} agent failed after {elapsed:.1f}s: {e}")
                raise
    return wrapper


def resume_or_route_node(state: RouterState) -> dict:
    """
    First decision point: resume active session or classify new intent.

    This node prevents the router from re-executing on checkpoint resume,
    which would cause incorrect intent re-classification and routing.

    On resume after human_input interrupt:
    - If active_agent exists and no [WORKFLOW_COMPLETE] signal → resume (bypass router)
    - If [WORKFLOW_COMPLETE] signal → clear session and route to new
    - If explicit user override → clear session and route to new
    - Otherwise → route to new (normal classification)

    Args:
        state: Current router state with messages and active_agent

    Returns:
        State update with route_decision ("new" or "resume") and routing info
    """
    active_agent = state.get("active_agent")
    messages = state.get("messages", [])

    # Check if workflow was completed in previous message
    if len(messages) >= 2:
        prev_message = messages[-2]
        prev_content = prev_message.content if hasattr(prev_message, 'content') else str(prev_message)
        if "[WORKFLOW_COMPLETE]" in prev_content:
            print("✅ Workflow completed, clearing active session")
            active_agent = None

    # Check for explicit user override (e.g., "switch to atlas")
    override_patterns = {
        "switch to atlas": "atlas",
        "switch to docgen": "docgen",
        "switch to archqa": "archqa",
        "switch to research": "research",
        "use atlas": "atlas",
        "use docgen": "docgen",
        "use archqa": "archqa",
        "use research": "research"
    }

    if messages:
        last_message = messages[-1]
        user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)
        user_lower = user_message.lower()

        for pattern, agent in override_patterns.items():
            if pattern in user_lower:
                print(f"🔄 User requested switch to {agent.upper()}, routing to classifier")
                return {
                    "route_decision": "new",
                    "active_agent": None  # Clear session for re-classification
                }

    # Decision logic
    if active_agent:
        print("=" * 60)
        print("🔗 RESUMING ACTIVE SESSION")
        print("=" * 60)
        print(f"Active agent: {active_agent.upper()}")
        print(f"Decision: Bypass router, route directly to {active_agent.upper()}")
        print("=" * 60)
        return {
            "route_decision": "resume",
            "next_agent": active_agent,
            "active_agent": active_agent
        }
    else:
        print("🆕 New session detected, routing to intent classifier")
        return {
            "route_decision": "new"
        }


def agent_continuation_node(state: RouterState) -> dict:
    """
    Pass-through node for resuming active sessions.

    This node exists in the graph structure to support the conditional
    edge routing from resume_or_route. When a session resumes, we bypass
    the router entirely by coming through this node.

    The actual routing decision is made by the conditional edge using
    the next_agent value set by resume_or_route_node.

    Args:
        state: Current router state (already has next_agent set)

    Returns:
        Empty dict (no state changes needed)
    """
    next_agent = state.get("next_agent", "atlas")
    active_agent = state.get("active_agent")

    print(f"→ agent_continuation_node executing...")
    print(f"   - next_agent from state: {next_agent}")
    print(f"   - active_agent from state: {active_agent}")
    print(f"   - All state keys: {list(state.keys())}")
    print(f"→ Routing to {next_agent.upper()} (active session resumed, bypassed router)")

    return {}


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

    # Create parent router graph using RouterState schema (extends DeepAgentState)
    # RouterState adds active_agent field for session continuity
    # All agents use DeepAgentState, which is compatible via inheritance
    router_graph = StateGraph(RouterState)

    # Add resume_or_route node (NEW: decision node for session continuity)
    # This node checks for active_agent BEFORE the router, preventing re-classification on resume
    router_graph.add_node("resume_or_route", resume_or_route_node)

    # Add router node (intent classification)
    # This now only executes for NEW sessions (not for resume)
    router_graph.add_node("router", router_node)

    # Add agent_continuation node (NEW: pass-through for resume path)
    # This node supports the conditional edge from resume_or_route
    router_graph.add_node("agent_continuation", agent_continuation_node)

    # Add agent subgraphs as wrapped nodes
    # Wrapping is necessary so the parent graph can route to aggregator after agent execution
    router_graph.add_node("atlas_agent", create_agent_wrapper("Atlas V1", atlas_agent))
    router_graph.add_node("docgen_agent", create_agent_wrapper("DocGen", docgen_agent))
    router_graph.add_node("archqa_agent", create_agent_wrapper("ArchQA", archqa_agent))
    router_graph.add_node("research_agent", create_agent_wrapper("Research", research_agent))

    # Add aggregator node to re-emit state for SSE propagation
    # This ensures todos, files, and messages are visible to the frontend
    router_graph.add_node("aggregator", aggregator_node)

    print("✅ Nodes added: resume_or_route, router, agent_continuation, atlas_agent, docgen_agent, archqa_agent, research_agent, aggregator")

    # NEW: Add conditional routing from resume_or_route
    # This is the NEW entry point decision that prevents router re-execution on resume
    router_graph.add_conditional_edges(
        "resume_or_route",  # Source node (NEW entry point)
        lambda state: state.get("route_decision"),  # Decision function
        {
            "new": "router",              # New session → classify intent via router
            "resume": "agent_continuation" # Resume session → bypass router
        }
    )

    # Add conditional routing based on intent classification (for NEW sessions)
    # The lambda extracts the "next_agent" field set by router_node
    # Maps classification result to the appropriate agent node
    router_graph.add_conditional_edges(
        "router",  # Source node (only for NEW sessions)
        lambda state: state.get("next_agent", "atlas"),  # Decision function
        {
            "atlas": "atlas_agent",      # If classification = "atlas", route to atlas_agent
            "docgen": "docgen_agent",    # If classification = "docgen", route to docgen_agent
            "archqa": "archqa_agent",    # If classification = "archqa", route to archqa_agent
            "research": "research_agent" # If classification = "research", route to research_agent
        }
    )

    # NEW: Add conditional routing from agent_continuation (for RESUME sessions)
    # This routes resumed sessions directly to the appropriate agent, bypassing router
    def debug_continuation_routing(state):
        """Debug function to log routing decisions from agent_continuation"""
        # Use active_agent (persisted) instead of next_agent (ephemeral)
        # On resume, active_agent contains the correct agent to continue with
        next_agent = state.get("active_agent", "atlas")
        print(f"🔍 DEBUG: agent_continuation conditional edge deciding...")
        print(f"   - active_agent value: {next_agent}")
        print(f"   - state keys: {list(state.keys())}")
        print(f"   - Decision: routing to {next_agent}_agent")
        return next_agent

    router_graph.add_conditional_edges(
        "agent_continuation",  # Source node (for resumed sessions)
        debug_continuation_routing,  # Decision function with debug logging
        {
            "atlas": "atlas_agent",      # Route to atlas_agent
            "docgen": "docgen_agent",    # Route to docgen_agent
            "archqa": "archqa_agent",    # Route to archqa_agent
            "research": "research_agent" # Route to research_agent
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

    # NEW: Set entry point - graph starts at resume_or_route (not router)
    # This prevents router re-execution on checkpoint resume
    router_graph.add_edge(START, "resume_or_route")

    print("✅ Router graph compiled successfully")
    print("")
    print("📊 Graph Architecture (with session continuity fix):")
    print("  - START → resume_or_route (NEW entry point)")
    print("  - resume_or_route → router (NEW sessions) OR agent_continuation (RESUME)")
    print("  - router/agent_continuation → agents (conditional routing)")
    print("  - agents → aggregator → END")
    print("")
    print("Available Routes:")
    print("  - Atlas V1: Planning, implementation, task generation, user story analysis")
    print("  - DocGen: Documentation generation, repository documentation")
    print("  - ArchQA: Architectural questions, technical debt analysis, code quality assessment")
    print("  - Research: Web search, information gathering, best practices research")
    print("")
    print("Session Continuity:")
    print("  - Active sessions bypass router on resume (prevents re-classification)")
    print("  - Workflow completes when agent returns [WORKFLOW_COMPLETE]")
    print("  - Explicit 'switch to X' command clears session and re-routes")
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
