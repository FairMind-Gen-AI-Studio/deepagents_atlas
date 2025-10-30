"""
Example: Streaming Agent Wrapper for Router Graph

This demonstrates the correct pattern for propagating subgraph events
through a parent router graph to SSE streams.
"""

def create_streaming_agent_wrapper(agent_name: str, compiled_agent):
    """
    Create a streaming wrapper that propagates subgraph state updates in real-time.

    Key differences from blocking wrapper:
    1. Uses astream() instead of ainvoke()
    2. Yields state chunks as they arrive
    3. Preserves context fields in every chunk
    4. Allows parent graph SSE to capture intermediate updates

    Args:
        agent_name: Display name for logging
        compiled_agent: Pre-compiled LangGraph agent graph

    Returns:
        Async generator function compatible with LangGraph nodes
    """
    async def wrapper(state: RouterState):
        import time
        import asyncio
        from typing import AsyncIterator

        start_time = time.time()

        # CRITICAL: Preserve active_agent and project_id from input state
        # Subagents use DeepAgentState (no active_agent/project_id fields), so they won't return them.
        # We must preserve them here to maintain session continuity across the router graph.
        active_agent = state.get('active_agent')
        project_id = state.get('project_id')
        user_api_key = state.get('user_api_key')

        print(f"🎯 Streaming {agent_name} agent...")
        print(f"   Input state: messages={len(state.get('messages', []))}, "
              f"todos={len(state.get('todos', []))}, "
              f"files={len(state.get('files', {}))}, "
              f"active_agent={active_agent}, "
              f"project_id={project_id}")

        # LAZY INITIALIZATION: Check MCP tools cache and initialize if needed
        mcp_tools_cache = state.get('mcp_tools_cache')

        if not mcp_tools_cache:
            # Cache miss - initialize MCP tools with user credentials in thread pool
            # Using asyncio.to_thread() to avoid blocking the event loop (ASGI requirement)
            logger.info(f"🔧 [{agent_name}] MCP tools cache miss - initializing with user credentials (async thread)")

            try:
                # Run blocking MCP initialization in thread pool to avoid blocking event loop
                # This is necessary because langchain_mcp_adapters uses sync I/O internally
                mcp_tools = await asyncio.to_thread(
                    _initialize_mcp_tools_blocking,
                    user_api_key
                )

                if mcp_tools:
                    logger.info(f"✅ [{agent_name}] MCP tools initialized: {len(mcp_tools)} tools available")
                    # Cache for reuse in this conversation thread
                    mcp_tools_cache = mcp_tools
                else:
                    logger.warning(f"⚠️  [{agent_name}] MCP initialization returned None - agent will run without MCP tools")
                    mcp_tools_cache = {}  # Empty dict to indicate "tried and failed"

            except Exception as e:
                logger.error(f"❌ [{agent_name}] Failed to initialize MCP tools: {e}")
                logger.info(f"   [{agent_name}] Agent will run with limited capabilities (no MCP tools)")
                mcp_tools_cache = {}  # Empty dict to indicate failure
        else:
            # Cache hit - reuse existing tools (no blocking!)
            tool_count = len(mcp_tools_cache) if isinstance(mcp_tools_cache, dict) else 0
            logger.info(f"♻️  [{agent_name}] MCP tools cache hit - reusing {tool_count} cached tools (no blocking)")

        # Update state with cached tools (for agent's internal use)
        state = {**state, 'mcp_tools_cache': mcp_tools_cache}

        # CRITICAL FIX: Inject project_id as a visible SystemMessage so LLM sees the actual value
        enriched_state = state
        if project_id:
            from langchain_core.messages import SystemMessage

            project_context_msg = SystemMessage(
                content=f"""🎯 CURRENT PROJECT CONTEXT

Project ID: {project_id}

CRITICAL INSTRUCTIONS:
- Use this EXACT project_id for ALL MCP tool calls
- Code_list_repositories(project="{project_id}")
- Code_search(project="{project_id}", repository, query)
- Code_cat(project="{project_id}", repository, file)
- General_rag_retrieve_documents(query, project_id="{project_id}", k)
- Studio_list_user_stories_by_project(project_id="{project_id}")

DO NOT:
- Call General_list_projects and iterate through projects
- Use any project_id other than: {project_id}

This is a MONO-PROJECT query. Only analyze this project."""
            )

            enriched_state = state.copy()
            messages = list(enriched_state.get("messages", []))
            messages.insert(0, project_context_msg)
            enriched_state["messages"] = messages
            print(f"   🎯 Injected project context message with project_id: {project_id}")

        try:
            # ✅ KEY CHANGE: Use astream() to get state chunks as they update
            # Each chunk contains partial state updates (todos, files, messages)
            # Yielding these chunks allows parent graph's SSE stream to capture them

            last_chunk = None
            chunk_count = 0

            async for chunk in compiled_agent.astream(enriched_state):
                chunk_count += 1

                # CRITICAL: Preserve context fields in every chunk
                # Without this, active_agent/project_id/mcp_tools_cache would be lost
                if active_agent and 'active_agent' not in chunk:
                    chunk['active_agent'] = active_agent

                if project_id and 'project_id' not in chunk:
                    chunk['project_id'] = project_id

                if mcp_tools_cache and 'mcp_tools_cache' not in chunk:
                    chunk['mcp_tools_cache'] = mcp_tools_cache

                # Log streaming progress
                if chunk.get('todos') or chunk.get('files') or chunk.get('messages'):
                    print(f"  📤 Chunk {chunk_count}: "
                          f"todos={len(chunk.get('todos', []))}, "
                          f"files={len(chunk.get('files', {}))}, "
                          f"messages={len(chunk.get('messages', []))}")

                # Yield chunk - parent graph will propagate via SSE
                # This is THE KEY to real-time streaming
                yield chunk

                last_chunk = chunk

            elapsed = time.time() - start_time
            print(f"✅ {agent_name} agent completed in {elapsed:.1f}s")
            print(f"   Streamed {chunk_count} state updates")

            if last_chunk:
                print(f"   Final state: "
                      f"todos={len(last_chunk.get('todos', []))}, "
                      f"files={len(last_chunk.get('files', {}))}, "
                      f"messages={len(last_chunk.get('messages', []))}")

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


def create_router_graph_with_streaming():
    """
    Create router graph with streaming-enabled agent wrappers.

    Key changes from blocking version:
    1. Agent nodes use streaming wrappers
    2. Aggregator removed (redundant with streaming)
    3. Agents route directly to END
    """
    print("🔨 Building router graph with streaming support...")

    router_graph = StateGraph(RouterState)

    # Add nodes (same as before)
    router_graph.add_node("extract_user_context", extract_user_context)
    router_graph.add_node("resume_or_route", resume_or_route_node)
    router_graph.add_node("router", router_node)
    router_graph.add_node("agent_continuation", agent_continuation_node)

    # ✅ KEY CHANGE: Use streaming wrappers instead of blocking wrappers
    router_graph.add_node(
        "docgen_agent",
        create_streaming_agent_wrapper("DocGen", docgen_agent)
    )
    router_graph.add_node(
        "archqa_agent",
        create_streaming_agent_wrapper("ArchQA", archqa_agent)
    )

    # ✅ KEY CHANGE: Remove aggregator, route agents directly to END
    # With streaming, state updates propagate automatically via SSE
    # No need for aggregator to "re-emit" state

    print("✅ Nodes added with streaming wrappers (no aggregator)")

    # Add edges (same conditional routing as before)
    router_graph.add_conditional_edges(
        "resume_or_route",
        lambda state: state.get("route_decision"),
        {
            "new": "router",
            "resume": "agent_continuation"
        }
    )

    router_graph.add_conditional_edges(
        "router",
        lambda state: state.get("next_agent", "docgen"),
        {
            "docgen": "docgen_agent",
            "archqa": "archqa_agent"
        }
    )

    router_graph.add_conditional_edges(
        "agent_continuation",
        lambda state: state.get("active_agent", "docgen"),
        {
            "docgen": "docgen_agent",
            "archqa": "archqa_agent"
        }
    )

    # ✅ KEY CHANGE: Agents route directly to END (no aggregator)
    router_graph.add_edge("docgen_agent", END)
    router_graph.add_edge("archqa_agent", END)

    # Entry point
    router_graph.add_edge(START, "extract_user_context")
    router_graph.add_edge("extract_user_context", "resume_or_route")

    print("✅ Router graph compiled with streaming support")
    print("")
    print("📊 Streaming Architecture:")
    print("  - Agent nodes use astream() for real-time state propagation")
    print("  - Each state chunk (todos/files/messages) emitted immediately")
    print("  - No aggregator needed - SSE captures chunks directly")
    print("  - Frontend receives updates during execution (not just at end)")
    print("")

    return router_graph.compile()


# Example: Invoking with streaming at server level
async def invoke_router_with_streaming(input_state: dict, config: dict):
    """
    Example of invoking the router with streaming enabled.

    This shows how to consume the streaming events at the API level.
    """
    agent = create_router_graph_with_streaming()

    # Use astream to get chunks
    async for chunk in agent.astream(input_state, config=config):
        # chunk is a dict with node name as key
        node_name = list(chunk.keys())[0]
        node_output = chunk[node_name]

        print(f"📦 Received chunk from node: {node_name}")

        # Extract state updates
        if 'todos' in node_output:
            print(f"   - Todos: {len(node_output['todos'])} items")
        if 'files' in node_output:
            print(f"   - Files: {len(node_output['files'])} files")
        if 'messages' in node_output:
            print(f"   - Messages: {len(node_output['messages'])} messages")

        # Yield to SSE stream
        yield chunk


# Example: SSE endpoint with streaming
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import json

app = FastAPI()

@app.post("/chat/stream")
async def stream_chat(request: dict):
    """
    Example SSE endpoint that streams router events to frontend.
    """
    async def generate():
        config = {
            "configurable": {
                "thread_id": request.get("thread_id", "default"),
                "x-fairmind-api-key": request.get("api_key"),
                "x-project-id": request.get("project_id"),
            }
        }

        input_state = {"messages": request.get("messages", [])}

        # Stream events
        async for chunk in invoke_router_with_streaming(input_state, config):
            # Convert to SSE format
            event_data = {
                "type": "state_update",
                "data": chunk
            }
            yield f"data: {json.dumps(event_data)}\n\n"

        # Send completion marker
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )
