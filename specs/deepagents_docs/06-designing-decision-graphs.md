# Designing Decision Graphs

## Overview
Decision graphs are the backbone of intelligent agent systems in the deepagents framework. They define how agents think, make decisions, and process information through a structured workflow.

## Core Components of a Decision Graph

### 1. Main Agent
The main agent coordinates the decision graph, responsible for:
- Processing user inputs
- Planning high-level actions
- Delegating tasks to subagents
- Managing overall workflow

Example creation:
```python
agent = create_deep_agent(
    tools=[my_tool1, my_tool2],
    instructions="You are an expert at solving complex tasks...",
    subagents=[subagent1, subagent2],
)
```

### 2. Subagents
Specialized agents handling specific tasks, defined by:
- Name
- Description
- Prompt
- Optional tools

Example subagent:
```python
subagent = {
    "name": "research-agent",
    "description": "Used to research complex questions in depth",
    "prompt": "You are a dedicated researcher...",
    "tools": ["internet_search", "read_file"] # Optional
}
```

### 3. State Management
Represents shared context between agents, typically including:
- Messages
- Todos
- Files

### 4. Tools
Enable agents to interact with external world, used for:
- Reading/writing files
- Internet searching
- Managing todos
- Invoking subagents

## Designing Your Decision Graph

### Steps:
1. Define problem space
2. Design main agent
3. Create specialized subagents
4. Define information flow

## Best Practices
- Establish clear responsibility boundaries
- Create effective communication patterns
- Manage state thoughtfully
- Balance agent autonomy and guidance

## Example: Research Agent Decision Graph
A complete example demonstrating a research agent that can:
- Break down research questions
- Conduct detailed research
- Critique and improve reports

## Conclusion
Decision graphs provide a powerful framework for designing complex, reasoning-based agent systems by decomposing problems and leveraging specialized knowledge.