# Hierarchical Teams Pattern: Router Graph with Subgraphs

**Pattern Type**: LangGraph Native Multi-Agent Routing
**Date**: 2025-10-09
**Status**: Technical Analysis & Implementation Guide

---

## Overview

The Hierarchical Teams pattern implements multi-agent routing as a **single unified LangGraph graph** where specialized agent graphs become **subgraph nodes** within a parent router graph. This creates a tree-like structure where routing decisions are made at the graph level through conditional edges.

### Core Concept

```
┌─────────────────────────────────────────────────────┐
│ Main Router Graph (Single LangGraph StateGraph)     │
│                                                      │
│  START                                               │
│    ↓                                                 │
│  [Router Node]                                       │
│    ├─ Receives user query                           │
│    ├─ Classifies intent                             │
│    └─ Returns routing decision                      │
│    ↓                                                 │
│  Conditional Edge (based on intent)                 │
│  ├─→ [Atlas V1 Subgraph] ──→ END                    │
│  ├─→ [DocGen Subgraph] ──→ END                      │
│  └─→ [Research Subgraph] ──→ END                    │
│                                                      │
└─────────────────────────────────────────────────────┘
```

**Key Insight**: Each specialized agent (Atlas V1, DocGen, Research) is a compiled `CompiledStateGraph` that gets added as a **node** in the parent graph. LangGraph treats these subgraphs as opaque nodes - state flows in, execution happens, updated state flows out.

---

## Technical Foundation

### LangGraph Subgraph Support

LangGraph explicitly supports this pattern through:

1. **`StateGraph.add_node(name, runnable)`**
   - Accepts any `Runnable` including `CompiledStateGraph`
   - Compiled agent graphs are valid node implementations

2. **`create_deep_agent(name="agent_name")`**
   - The `name` parameter is "particularly useful for building multi-agent systems"
   - "Will be automatically used when adding the agent graph to another graph as a subgraph node"

3. **State Propagation**
   - Parent graph state flows into subgraph
   - Subgraph execution produces updated state
   - LangGraph automatically merges updates back to parent state

### State Schema Compatibility

All deepagents agents use `DeepAgentState`:

```python
class DeepAgentState(TypedDict):
    messages: list[BaseMessage]
    files: dict[str, str]  # Virtual filesystem
    todos: list[dict]
    archived_context: list[dict]
```

Since all agents share this schema, state flows naturally between parent and subgraphs without transformation.

---

## Implementation Architecture

### Complete Implementation

```python
# router_graph.py - Hierarchical Teams implementation

from typing import Literal, Optional
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage
from deepagents.state import DeepAgentState

# Import existing agent factories
from examples.atlas_v1.atlas_agent import create_langgraph_agent as create_atlas
from examples.docgen.docgen_agent import create_docgen_agent
from examples.research.research_agent import agent as research_agent


# ============================================================================
# STEP 1: Intent Classification Function
# ============================================================================

def classify_intent(user_query: str) -> Literal["atlas", "docgen", "research"]:
    """Classify user intent using keyword matching.

    This can be replaced with LLM-based classification for more sophistication.

    Args:
        user_query: User's question/request

    Returns:
        Agent name to route to
    """
    query_lower = user_query.lower()

    # Planning keywords
    planning_keywords = ["plan", "implement", "task", "user story", "us-",
                        "feature", "requirement", "sprint"]
    if any(word in query_lower for word in planning_keywords):
        return "atlas"

    # Documentation keywords
    doc_keywords = ["document", "explain", "analyze code", "repository",
                   "api doc", "readme", "architecture"]
    if any(word in query_lower for word in doc_keywords):
        return "docgen"

    # Research keywords
    research_keywords = ["research", "search", "find information", "look up",
                        "what is", "how to"]
    if any(word in query_lower for word in research_keywords):
        return "research"

    # Default to atlas
    return "atlas"


# ============================================================================
# STEP 2: Router Node Implementation
# ============================================================================

def router_node(state: DeepAgentState) -> dict:
    """Router node - performs intent classification.

    This node:
    1. Extracts user query from messages
    2. Classifies intent
    3. Returns routing decision in state update

    Args:
        state: Current graph state with messages

    Returns:
        State update with routing decision
    """
    # Extract user message
    if not state.get("messages"):
        return {"next_agent": "atlas"}  # Default if no messages

    # Get last user message
    user_message = state["messages"][-1].content

    # Classify intent
    next_agent = classify_intent(user_message)

    # Log routing decision (helpful for debugging)
    print(f"🔀 Router Decision: {next_agent}")
    print(f"   Query: {user_message[:80]}...")

    # Return state update with routing decision
    return {"next_agent": next_agent}


# ============================================================================
# STEP 3: Router Graph Construction
# ============================================================================

def create_router_graph():
    """Create router graph with agent subgraphs.

    Architecture:
    - Router node classifies intent
    - Conditional edge routes to appropriate agent subgraph
    - Agent executes completely
    - State flows back to parent graph
    - End

    Returns:
        Compiled router graph ready for invocation
    """
    print("📦 Creating specialized agent graphs...")

    # Create specialized agents (these return CompiledStateGraph)
    atlas_graph = create_atlas()
    docgen_graph = create_docgen_agent()
    # research_agent is already compiled

    print("✅ All agent graphs compiled")

    # Create parent router graph
    print("🔨 Building router graph...")
    router_graph = StateGraph(DeepAgentState)

    # Add router node (intent classification)
    router_graph.add_node("router", router_node)

    # Add agent subgraphs as nodes
    # These are compiled LangGraph graphs treated as opaque nodes
    router_graph.add_node("atlas_agent", atlas_graph)
    router_graph.add_node("docgen_agent", docgen_graph)
    router_graph.add_node("research_agent", research_agent)

    print("✅ All nodes added to graph")

    # Add conditional routing based on intent classification
    # The lambda extracts the "next_agent" field set by router_node
    router_graph.add_conditional_edges(
        "router",  # Source node
        lambda state: state.get("next_agent", "atlas"),  # Decision function
        {
            "atlas": "atlas_agent",      # If intent is "atlas", go to atlas_agent
            "docgen": "docgen_agent",    # If intent is "docgen", go to docgen_agent
            "research": "research_agent" # If intent is "research", go to research_agent
        }
    )

    # All agents route to END after execution
    for agent_name in ["atlas_agent", "docgen_agent", "research_agent"]:
        router_graph.add_edge(agent_name, END)

    # Set entry point to router
    router_graph.set_entry_point("router")

    print("✅ Router graph compiled successfully")

    # Compile and return
    return router_graph.compile()


# ============================================================================
# STEP 4: Usage Example
# ============================================================================

def main():
    """Example usage of router graph"""

    # Create router graph
    router = create_router_graph()

    # Example 1: Planning request (routes to Atlas V1)
    print("\n" + "="*60)
    print("Example 1: Planning Request")
    print("="*60)

    result = router.invoke({
        "messages": [HumanMessage(content="Create implementation plan for user story US-123")]
    })

    print("\n📝 Agent Response:")
    print(result["messages"][-1].content)
    print("\n📁 Files Created:")
    for filename in result.get("files", {}).keys():
        print(f"  - {filename}")


    # Example 2: Documentation request (routes to DocGen)
    print("\n" + "="*60)
    print("Example 2: Documentation Request")
    print("="*60)

    result = router.invoke({
        "messages": [HumanMessage(content="Document the authentication API endpoints")]
    })

    print("\n📝 Agent Response:")
    print(result["messages"][-1].content)
    print("\n📁 Files Created:")
    for filename in result.get("files", {}).keys():
        print(f"  - {filename}")


    # Example 3: Research request (routes to Research)
    print("\n" + "="*60)
    print("Example 3: Research Request")
    print("="*60)

    result = router.invoke({
        "messages": [HumanMessage(content="Research best practices for API authentication")]
    })

    print("\n📝 Agent Response:")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
```

---

## State Management Deep Dive

### How State Flows Through Subgraphs

```
Initial Invoke
─────────────────────────────────────────────────────────────
router.invoke({
    "messages": [HumanMessage("Create plan for US-123")]
})

↓ LangGraph initializes state

State: {
    "messages": [HumanMessage("Create plan for US-123")],
    "files": {},
    "todos": [],
    "archived_context": []
}

↓ Router node executes

router_node(state) returns: {"next_agent": "atlas"}

↓ State merges update

State: {
    "messages": [HumanMessage("Create plan for US-123")],
    "files": {},
    "todos": [],
    "archived_context": [],
    "next_agent": "atlas"  ← Added by router_node
}

↓ Conditional edge evaluates: state["next_agent"] = "atlas"
↓ Routes to atlas_agent subgraph node

Atlas V1 Subgraph Executes
─────────────────────────────────────────────────────────────
Input State (same as parent): {
    "messages": [HumanMessage("Create plan for US-123")],
    "files": {},
    "todos": [],
    "archived_context": [],
    "next_agent": "atlas"
}

Atlas V1 executes its 4 phases:
  - Investigation phase
  - Discussion phase
  - Planning phase
  - Task generation phase

Each phase adds to virtual filesystem:
  - investigation_findings.md
  - planning_summary.md
  - tasks.json

Output State: {
    "messages": [
        HumanMessage("Create plan for US-123"),
        AIMessage("Investigation complete..."),
        AIMessage("Planning complete..."),
        AIMessage("I've created implementation plan for US-123...")
    ],
    "files": {
        "investigation_findings.md": "...",
        "planning_summary.md": "...",
        "tasks.json": "..."
    },
    "todos": [
        {"content": "Investigation", "status": "completed"},
        {"content": "Planning", "status": "completed"}
    ],
    "archived_context": [...],
    "next_agent": "atlas"
}

↓ LangGraph merges subgraph output into parent state

Parent Graph State After Subgraph
─────────────────────────────────────────────────────────────
State: {
    "messages": [...all messages from Atlas...],
    "files": {...all files created by Atlas...},
    "todos": [...all todos from Atlas...],
    "archived_context": [...],
    "next_agent": "atlas"
}

↓ Edge to END

Final Result
─────────────────────────────────────────────────────────────
router.invoke() returns this final state
```

### State Merge Strategy

LangGraph automatically merges state using **reducer functions** defined in `DeepAgentState`:

```python
# Implicit reducers for DeepAgentState fields:
messages: list  → append new messages
files: dict     → merge/update (last write wins for same key)
todos: list     → append new todos
archived_context: list → append new context

# Custom fields added at runtime (like "next_agent"):
next_agent: str → replace (last write wins)
```

This means:
- **Files created by Atlas V1** persist in parent state
- **Next invocation** (e.g., DocGen) will see those files
- **Cross-agent collaboration** works through shared state.files

---

## Cross-Agent Collaboration Example

### Scenario: DocGen Uses Atlas Investigation Results

```python
def create_router_graph_with_state_sharing():
    """Router graph demonstrating cross-agent collaboration"""

    router_graph = StateGraph(DeepAgentState)

    # Create agents
    atlas_graph = create_atlas()
    docgen_graph = create_docgen_agent()

    # Add nodes
    router_graph.add_node("router", router_node)
    router_graph.add_node("atlas_agent", atlas_graph)
    router_graph.add_node("docgen_agent", docgen_graph)

    # Routing logic (same as before)
    router_graph.add_conditional_edges(
        "router",
        lambda state: state.get("next_agent", "atlas"),
        {"atlas": "atlas_agent", "docgen": "docgen_agent"}
    )

    router_graph.add_edge("atlas_agent", END)
    router_graph.add_edge("docgen_agent", END)
    router_graph.set_entry_point("router")

    return router_graph.compile()


# Usage: Sequential invocations share state
router = create_router_graph_with_state_sharing()

# Step 1: Atlas investigates project
result_1 = router.invoke({
    "messages": [HumanMessage("Investigate user story US-123")]
})

# Atlas creates: investigation_findings.md
print("Atlas created:", list(result_1["files"].keys()))
# Output: ['investigation_findings.md', 'project_context.md']

# Step 2: DocGen uses Atlas results
# Pass previous state.files to next invocation
result_2 = router.invoke({
    "messages": [HumanMessage("Document the API based on investigation")],
    "files": result_1["files"]  # ← Share files from previous invocation
})

# DocGen can now read investigation_findings.md
# DocGen creates: api_documentation.md (informed by Atlas findings)
print("DocGen created:", list(result_2["files"].keys()))
# Output: ['investigation_findings.md', 'project_context.md', 'api_documentation.md']
```

**Key Insight**: State sharing requires **explicit passing** between separate invocations, OR using a stateful checkpointer (LangGraph persistence feature).

---

## Advanced: LLM-Based Intent Classification

For more sophisticated routing, replace keyword matching with LLM classification:

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.pydantic_v1 import BaseModel, Field

# Define structured output for classification
class IntentClassification(BaseModel):
    agent: Literal["atlas", "docgen", "research"] = Field(
        description="Which specialist agent should handle this request"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for this classification"
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was chosen"
    )


def llm_classify_intent(user_query: str) -> str:
    """LLM-based intent classification with structured output"""

    llm = ChatAnthropic(model="claude-3-haiku-20240307", temperature=0)

    prompt = f"""Classify this user request into one category:

Categories:
- atlas: Implementation planning, task generation, user story analysis, feature breakdown
- docgen: Code documentation, API docs, architecture explanation, repository analysis
- research: Web search, information gathering, best practices lookup, external knowledge

User request: {user_query}

Analyze the request and determine which specialist agent is most appropriate.
Provide your classification with confidence score and reasoning."""

    result = llm.with_structured_output(IntentClassification).invoke(prompt)

    # Log decision with confidence
    print(f"🤖 LLM Classification: {result.agent} (confidence: {result.confidence:.2f})")
    print(f"   Reasoning: {result.reasoning}")

    # Handle low confidence
    if result.confidence < 0.7:
        print(f"⚠️  Low confidence - defaulting to atlas")
        return "atlas"

    return result.agent


# Use in router node
def router_node_with_llm(state: DeepAgentState) -> dict:
    """Router node using LLM classification"""

    if not state.get("messages"):
        return {"next_agent": "atlas"}

    user_message = state["messages"][-1].content

    # Use LLM instead of keywords
    next_agent = llm_classify_intent(user_message)

    return {"next_agent": next_agent}
```

**When to use LLM classification:**
- More than 5 specialized agents (keyword matching becomes unwieldy)
- Complex or ambiguous user queries
- Need for confidence scores and reasoning
- Multi-intent queries requiring disambiguation

**Tradeoff:**
- ➕ More accurate routing for complex queries
- ➕ Handles novel query patterns better
- ➖ Adds latency (~500ms for Haiku call)
- ➖ Adds cost (small but non-zero)

---

## State Schema Extension

If you need router-specific metadata, extend `DeepAgentState`:

```python
from typing import Optional
from deepagents.state import DeepAgentState

class RouterState(DeepAgentState):
    """Extended state schema for router graph"""

    # Routing decision
    next_agent: Optional[str] = None

    # Classification metadata
    classification_confidence: Optional[float] = None
    classification_reasoning: Optional[str] = None

    # Routing history (for multi-turn conversations)
    routing_history: list[dict] = []  # List of past routing decisions


def router_node_extended(state: RouterState) -> dict:
    """Router node with extended state"""

    user_message = state["messages"][-1].content

    # LLM classification
    classification = llm_classify_intent(user_message)

    # Build routing history entry
    routing_entry = {
        "agent": classification.agent,
        "confidence": classification.confidence,
        "reasoning": classification.reasoning,
        "query": user_message[:100]
    }

    return {
        "next_agent": classification.agent,
        "classification_confidence": classification.confidence,
        "classification_reasoning": classification.reasoning,
        "routing_history": state.get("routing_history", []) + [routing_entry]
    }
```

---

## LangGraph Studio Integration

The router graph works seamlessly with LangGraph Studio:

### 1. Create `langgraph.json`

```json
{
  "graphs": {
    "router_graph": "./router_graph.py:create_router_graph"
  },
  "env": ".env"
}
```

### 2. Launch Studio

```bash
cd /path/to/router_graph/
langgraph dev
```

### 3. Visualize Execution

LangGraph Studio will show:
- Router node execution with classification decision
- Conditional edge branching to selected agent
- Complete subgraph execution (Atlas V1's 4 phases, DocGen's 5 phases, etc.)
- State evolution at each step
- Unified trace tree showing entire execution

**Benefits:**
- **Single trace**: See routing decision + agent execution in one tree
- **State inspection**: View state.files at any point to see cross-agent artifacts
- **Debugging**: Step through router node, conditional edge, and subgraph execution
- **Performance**: Identify bottlenecks in routing or agent execution

---

## Error Handling

Subgraphs can fail - the parent graph must handle errors:

```python
def safe_router_node(state: DeepAgentState) -> dict:
    """Router node with error handling"""

    try:
        user_message = state["messages"][-1].content
        next_agent = classify_intent(user_message)
        return {"next_agent": next_agent}

    except Exception as e:
        print(f"❌ Router node failed: {e}")
        # Default to atlas on error
        return {"next_agent": "atlas"}


def create_router_graph_with_error_handling():
    """Router graph with error recovery"""

    router_graph = StateGraph(DeepAgentState)

    # Wrap agents with error handling
    def safe_atlas(state: DeepAgentState) -> dict:
        try:
            return atlas_graph.invoke(state)
        except Exception as e:
            print(f"❌ Atlas V1 failed: {e}")
            # Return error state
            return {
                "messages": state["messages"] + [
                    AIMessage(content=f"Atlas V1 encountered an error: {str(e)}")
                ]
            }

    router_graph.add_node("router", safe_router_node)
    router_graph.add_node("atlas_agent", safe_atlas)
    # Add other agents similarly...

    # ... rest of graph construction
```

---

## Testing Strategy

### Unit Tests: Test Router Node in Isolation

```python
import pytest
from router_graph import router_node, classify_intent

def test_router_node_planning_query():
    """Test router classifies planning queries correctly"""

    state = {
        "messages": [{"role": "user", "content": "Create implementation plan for US-123"}],
        "files": {}
    }

    result = router_node(state)

    assert result["next_agent"] == "atlas"


def test_router_node_documentation_query():
    """Test router classifies documentation queries correctly"""

    state = {
        "messages": [{"role": "user", "content": "Document the API endpoints"}],
        "files": {}
    }

    result = router_node(state)

    assert result["next_agent"] == "docgen"


def test_classify_intent_edge_cases():
    """Test classification handles edge cases"""

    # Ambiguous query
    assert classify_intent("Help me with the project") == "atlas"  # Default

    # Multi-keyword query (planning wins)
    assert classify_intent("Document the implementation plan") == "atlas"
```

### Integration Tests: Test Full Router Graph

```python
def test_router_graph_end_to_end():
    """Test router graph routes correctly and agents execute"""

    router = create_router_graph()

    # Planning request
    result = router.invoke({
        "messages": [{"role": "user", "content": "Create plan for US-123"}]
    })

    # Verify Atlas V1 executed
    assert "investigation_findings.md" in result["files"]
    assert "planning_summary.md" in result["files"]

    # Verify response
    assert len(result["messages"]) > 1
    assert result["messages"][-1].type == "ai"


def test_cross_agent_state_sharing():
    """Test state sharing between agents"""

    router = create_router_graph()

    # First invocation: Atlas creates files
    result_1 = router.invoke({
        "messages": [{"role": "user", "content": "Investigate US-123"}]
    })

    # Second invocation: DocGen should see Atlas files
    result_2 = router.invoke({
        "messages": [{"role": "user", "content": "Document the findings"}],
        "files": result_1["files"]  # Pass files forward
    })

    # Verify DocGen saw Atlas files
    assert "investigation_findings.md" in result_2["files"]
    assert "api_documentation.md" in result_2["files"]
```

---

## Performance Considerations

### Memory Footprint

**All agents are compiled at startup:**
```python
# These create and compile graphs immediately
atlas_graph = create_atlas()      # ~50MB
docgen_graph = create_docgen_agent()  # ~50MB
research_agent = ...              # ~30MB

# Total: ~130MB in memory before first request
```

**Optimization**: Lazy compilation if memory is constrained:

```python
class LazyAgentNode:
    """Lazy-load agent graph on first use"""

    def __init__(self, factory_fn):
        self.factory_fn = factory_fn
        self._graph = None

    def __call__(self, state):
        if self._graph is None:
            print(f"📦 Compiling agent graph...")
            self._graph = self.factory_fn()
        return self._graph.invoke(state)


# Use in graph construction
router_graph.add_node("atlas_agent", LazyAgentNode(create_atlas))
```

### Execution Latency

```
Total latency = Classification + Agent Execution

Classification:
- Keyword-based: ~1ms
- LLM-based (Haiku): ~300-500ms

Agent Execution:
- Atlas V1: ~15-30s (4 phases, MCP calls)
- DocGen: ~10-20s (5 phases, MCP calls)
- Research: ~5-10s (web search)
```

**Optimization**: None needed for classification - agent execution dominates latency.

---

## Migration from Existing Agents

Existing agents created with `create_deep_agent()` work as-is:

```python
# Existing agent code (no changes needed)
from deepagents import create_deep_agent

def create_atlas_agent():
    return create_deep_agent(
        name="atlas-v1",  # Important: set name for subgraph usage
        instructions="You are Atlas V1...",
        subagents=[...],
        tools=[...]
    )


# New router graph (uses existing agent)
router_graph = StateGraph(DeepAgentState)
router_graph.add_node("atlas", create_atlas_agent())  # ← Just works!
```

**Only requirement**: Ensure agent factory returns `CompiledStateGraph` (which `create_deep_agent()` already does).

---

## Summary

The Hierarchical Teams pattern provides:

✅ **Native LangGraph integration** - everything is a graph
✅ **Clean subgraph composition** - existing agents slot in as nodes
✅ **Automatic state propagation** - LangGraph handles merging
✅ **Unified observability** - single trace tree in LangSmith
✅ **Simple routing logic** - conditional edges based on classification
✅ **Cross-agent collaboration** - shared state.files enables artifact passing

**Implementation is straightforward:**
1. Create router node (intent classification)
2. Add compiled agent graphs as nodes
3. Add conditional edges for routing
4. LangGraph handles the rest

**Next Steps:**
- Implement `router_graph.py` following the code examples above
- Test with existing agents (Atlas V1, DocGen, Research)
- Add LangGraph Studio configuration for visualization
- Deploy as single unified graph endpoint
