# deepagents: Advanced LLM-Powered Agents

## Overview

**deepagents** is a Python package designed to create sophisticated LLM-powered agents capable of handling complex, multi-step tasks. Inspired by advanced systems like Claude Code and Deep Research, it elevates agent functionality beyond simple "call tools in a loop" approaches.

## Key Capabilities

| Capability | Purpose | Implementation |
|------------|---------|----------------|
| **Planning** | Break down complex tasks | Built-in `write_todos` tool |
| **Sub Agents** | Delegate and quarantine contexts | Hierarchical agent structure |
| **File System** | Provide external memory | Virtual file system tools |
| **Detailed Prompting** | Guide agent behavior | Comprehensive system prompts |

## Core Architecture

Built on [LangGraph](https://github.com/langchain-ai/langgraph), deepagents uses:
- Anthropic's Claude Sonnet 4 model (default)
- Custom model support
- `DeepAgentState` for managing todos and virtual files

## When to Use deepagents

Ideal for:
- Complex research tasks
- Multi-step workflows
- Content creation with state maintenance
- Problem-solving involving multiple tools

## Getting Started

```python
from deepagents import create_deep_agent

# Define tools the agent can use
tools = [your_custom_tool1, your_custom_tool2]

# Create instructions for the agent
instructions = "You are an expert researcher. Your job is to..."

# Create the agent
agent = create_deep_agent(tools, instructions)

# Invoke the agent
result = agent.invoke({"messages": [{"role": "user", "content": "your task"}]})
```

## Next Steps
1. Follow the Quick Start guide
2. Review the Installation Guide
3. Create your first agent tutorial