# Working with Prompts in DeepAgents

## Overview
Prompts are critical in agent-based systems, serving to:
- Provide instructions to agents
- Define tool behavior
- Guide agent decision-making
- Establish interaction patterns

## Prompt Types

### 1. Tool Description Prompts
Provide detailed instructions for using specific tools, including:
- Tool purpose
- Usage guidelines
- Examples
- Formatting requirements

Example:
```python
WRITE_TODOS_DESCRIPTION = """Use this tool to create and manage a structured task list for your current work session..."""
```

### 2. Task Management Prompts
Help agents manage complex tasks by defining:
- Task states (pending, in_progress, completed)
- Tracking mechanisms
- Completion requirements

### 3. Subagent Prompts
Facilitate task delegation to specialized agents, defining:
- Agent types
- Available tools
- Specialized task handling

## Prompt Flow in the System
Prompts move through the system via:
1. User request
2. Main agent loads base prompts
3. Combine custom instructions with base prompts
4. Send to language model
5. Potential subagent delegation

## Customizing Prompts

### Adding Custom Instructions
```python
my_instructions = """You are a specialized coding assistant focused on Python development.
When helping users, prioritize code clarity, PEP 8 compliance, and best practices.
Always suggest unit tests when providing code solutions."""

agent = create_deep_agent(
    tools=[],
    instructions=my_instructions
)
```

### Creating Custom Subagents
```python
data_analysis_agent = SubAgent(
    name="data-analyzer",
    description="Use this agent for complex data analysis tasks",
    prompt="""You are a specialized data analysis agent. Your primary focus is helping users with:
 1. Statistical analysis of datasets
 2. Data visualization recommendations
 3. Interpreting trends and patterns in data""",
    tools=["read_file", "write_file", "python"]
)
```

## Prompt Engineering Best Practices
- Be specific and detailed
- Provide clear examples
- Structure prompts logically
- Test and iterate
- Manage context