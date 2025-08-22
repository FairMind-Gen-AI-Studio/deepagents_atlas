# Implementing Custom Tools

## Overview

Custom tools are a powerful way to extend deepagents' capabilities, allowing agents to interact with external systems, process data, and perform specialized tasks. The tools are built on LangChain's tool system using the `@tool` decorator.

## Basic Tool Structure

There are two main tool categories:

### a) Simple tools
Return information without modifying state

### b) State-modifying tools
Return a `Command` object to update agent state

## Creating Custom Tools

### Simple Tool Example

```python
@tool(description="Calculates the square of a number")
def calculate_square(number: int) -> int:
    """Calculate the square of the given number."""
    return number * number
```

### State-Modifying Tool Example

```python
@tool(description="Add a note to the agent's memory")
def add_note(
    note: str,
    state: Annotated[DeepAgentState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    notes = state.get("notes", [])
    notes.append(note)
    return Command(
        update={
            "notes": notes,
            "messages": [
                ToolMessage(f"Added note: {note}", tool_call_id=tool_call_id)
            ],
        }
    )
```

## Best Practices for Custom Tools

- **Provide clear descriptions**: Make tool purposes obvious to the agent
- **Include comprehensive docstrings**: Help agents understand tool functionality
- **Use type annotations**: Enable proper validation and error handling
- **Implement robust error handling**: Handle edge cases gracefully
- **Safely modify state**: Use Command objects for state changes
- **Maintain focused functionality**: Keep tools single-purpose and specific
- **Return meaningful responses**: Provide useful feedback to agents

## Integrating Tools with Agents

Use the `create_deep_agent` function to add custom tools to an agent's workflow.

## Conclusion

Custom tools enable developers to extend agent capabilities by creating specialized functions for interacting with external systems and processing data within the deepagents framework.