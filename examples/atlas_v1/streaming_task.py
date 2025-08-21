"""
Atlas V1 Streaming Task Tool
Provides streaming version of the task tool to show intermediate subagent messages in UI
"""

import logging
from typing import List, Dict, Any
from langchain_core.tools import BaseTool, tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import create_react_agent, InjectedState
from langgraph.types import Command
from typing_extensions import Annotated
from langchain.chat_models import init_chat_model

from deepagents.state import DeepAgentState
from deepagents.sub_agent import SubAgent
from deepagents.prompts import TASK_DESCRIPTION_PREFIX, TASK_DESCRIPTION_SUFFIX

logger = logging.getLogger(__name__)

def create_streaming_task_tool(tools, instructions, subagents: List[SubAgent], model, state_schema):
    """
    Create a streaming version of the task tool that shows intermediate subagent messages.
    
    This is a modified version of deepagents.sub_agent._create_task_tool that uses astream
    instead of ainvoke to capture intermediate messages for better UI feedback.
    
    Args:
        tools: List of tools available to subagents
        instructions: Instructions for the general-purpose agent
        subagents: List of subagent configurations
        model: Language model to use
        state_schema: State schema (usually DeepAgentState)
    
    Returns:
        task: The streaming task tool function
    """
    
    # Create agents dictionary (same logic as original _create_task_tool)
    agents = {
        "general-purpose": create_react_agent(model, prompt=instructions, tools=tools)
    }
    
    tools_by_name = {}
    for tool_ in tools:
        if not isinstance(tool_, BaseTool):
            from langchain_core.tools import tool as tool_decorator
            tool_ = tool_decorator(tool_)
        tools_by_name[tool_.name] = tool_
    
    # Essential builtin tools for virtual filesystem handover - always available
    essential_builtins = {'write_file', 'read_file', 'ls', 'write_todos'}
    
    for _agent in subagents:
        if "tools" in _agent:
            # Get specified tools
            _tools = [tools_by_name[t] for t in _agent["tools"] if t in tools_by_name]
            
            # Add essential builtins that aren't already specified
            for tool_obj in tools:
                if isinstance(tool_obj, BaseTool) and tool_obj.name in essential_builtins:
                    if tool_obj.name not in _agent["tools"]:
                        _tools.append(tool_obj)
        else:
            # No specific tools = inherit all tools
            _tools = tools
        
        # Resolve per-subagent model if specified, else fallback to main model
        if "model_settings" in _agent:
            model_config = _agent["model_settings"]
            # Always use get_default_model to ensure all settings are applied
            sub_model = init_chat_model(**model_config)
        else:
            sub_model = model
        
        agents[_agent["name"]] = create_react_agent(
            sub_model, prompt=_agent["prompt"], tools=_tools, state_schema=state_schema
        )

    other_agents_string = [
        f"- {_agent['name']}: {_agent['description']}" for _agent in subagents
    ]

    @tool(
        description=TASK_DESCRIPTION_PREFIX.format(other_agents=other_agents_string)
        + TASK_DESCRIPTION_SUFFIX
    )
    async def task(
        description: str,
        subagent_type: str,
        state: Annotated[DeepAgentState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        """
        Enhanced task tool with streaming support for better UI feedback.
        
        This version uses astream instead of ainvoke to capture intermediate messages
        from subagents and provide real-time feedback to the UI.
        """
        
        if subagent_type not in agents:
            return f"Error: invoked agent of type {subagent_type}, the only allowed types are {[f'`{k}`' for k in agents]}"
        
        sub_agent = agents[subagent_type]
        state["messages"] = [{"role": "user", "content": description}]
        
        # Collect all messages during streaming execution
        intermediate_messages = []
        final_state = None
        
        try:
            logger.info(f"Starting streaming execution of subagent: {subagent_type}")
            
            # Use astream to get intermediate messages instead of ainvoke
            async for chunk in sub_agent.astream(state):
                # Collect messages from each streaming chunk
                if "messages" in chunk:
                    for msg in chunk["messages"]:
                        # Only collect AI messages with actual content
                        if hasattr(msg, 'content') and msg.content and msg.content.strip():
                            # Skip tool call messages and empty messages
                            if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                                intermediate_messages.append(msg.content)
                                logger.debug(f"Collected message from {subagent_type}: {msg.content[:100]}...")
                
                # Keep track of the final state for files and other data
                final_state = chunk
            
            # Prepare the response content
            if intermediate_messages:
                # Join all messages with separators for better readability in UI
                feedback_content = "\n\n---\n\n".join(intermediate_messages)
                logger.info(f"Streaming completed: collected {len(intermediate_messages)} messages from {subagent_type}")
            else:
                # Fallback to the last message if no intermediate messages were captured
                if final_state and "messages" in final_state and final_state["messages"]:
                    feedback_content = final_state["messages"][-1].content
                else:
                    feedback_content = f"{subagent_type} agent completed the task."
                logger.warning(f"No intermediate messages captured from {subagent_type}, using fallback")
            
            # Handle USER_QUESTION pattern (for interactive discussion agents)
            if "USER_QUESTION:" in feedback_content:
                # Extract the question and display it to the user, preserving conversational flow
                question = feedback_content.replace("USER_QUESTION:", "").strip()
                return Command(
                    update={
                        "files": final_state.get("files", {}) if final_state else {},
                        "messages": [
                            ToolMessage(question, tool_call_id=tool_call_id)
                        ],
                    }
                )
            else:
                return Command(
                    update={
                        "files": final_state.get("files", {}) if final_state else {},
                        "messages": [
                            ToolMessage(feedback_content, tool_call_id=tool_call_id)
                        ],
                    }
                )
        
        except Exception as e:
            logger.error(f"Error in streaming task execution for {subagent_type}: {e}")
            logger.info(f"Falling back to standard ainvoke for {subagent_type}")
            
            # Fallback to standard ainvoke if streaming fails
            try:
                result = await sub_agent.ainvoke(state)
                
                # Check if the last message contains a user question that needs to be surfaced
                last_message = result["messages"][-1].content
                if "USER_QUESTION:" in last_message:
                    # Extract the question and display it to the user, preserving the conversational flow
                    question = last_message.replace("USER_QUESTION:", "").strip()
                    return Command(
                        update={
                            "files": result.get("files", {}),
                            "messages": [
                                ToolMessage(question, tool_call_id=tool_call_id)
                            ],
                        }
                    )
                else:
                    return Command(
                        update={
                            "files": result.get("files", {}),
                            "messages": [
                                ToolMessage(
                                    result["messages"][-1].content, tool_call_id=tool_call_id
                                )
                            ],
                        }
                    )
            except Exception as fallback_error:
                logger.error(f"Fallback execution also failed for {subagent_type}: {fallback_error}")
                return Command(
                    update={
                        "messages": [
                            ToolMessage(
                                f"Error executing {subagent_type}: {str(e)}", 
                                tool_call_id=tool_call_id
                            )
                        ],
                    }
                )

    return task