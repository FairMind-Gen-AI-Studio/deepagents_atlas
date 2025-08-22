# Managing Agent State

Agent state in deepagents is a mechanism for maintaining persistent data across interaction turns, serving as a "memory" that allows agents to collaborate and build on previous work.

## Key Concepts

Agent state functions as the persistent memory layer that enables agents to:
- Maintain context across multiple interactions
- Share information between different agents
- Build incrementally on previous work
- Coordinate complex multi-step tasks

## State Structure

The default state schema consists of two main components:

### 1. Todos
A list of task items with content and status tracking:

```python
class DeepAgentState(AgentState):
    todos: NotRequired[list[Todo]]
    files: Annotated[NotRequired[dict[str, str]], file_reducer]
```

### 2. Files
A virtual file system implemented as a dictionary mapping file names to their content, with a custom reducer for proper state management.

## State Reducers

State reducers determine how updates are merged when multiple agents modify the same state. The `file_reducer` ensures file changes are combined properly:

```python
def file_reducer(l, r):
    if l is None:
        return r
    elif r is None:
        return l
    else:
        return {**l, **r}
```

This reducer:
- Returns the right operand if left is None
- Returns the left operand if right is None
- Merges both dictionaries, with right operand taking precedence for duplicate keys

## Built-in State Management Tools

### Todo Management
The `write_todos` tool allows creating and updating todos:
- Accepts a list of todo items with content and status
- Returns a `Command` object specifying state updates
- Enables task planning and progress tracking

### File Operations
The framework provides several file system tools:
- `ls`: List all files in the virtual filesystem
- `read_file`: Read content of a specific file
- `write_file`: Create new files or update existing ones
- `edit_file`: Modify specific portions of files

All file operations work on the virtual filesystem stored in agent state.

## State Sharing Between Agents

The `task` tool enables state sharing by:

1. **Creating a state copy**: Current state is copied for the subagent
2. **Invoking subagents**: Subagents work with their own state copy
3. **Propagating updates**: Changes are merged back to the main agent state

This pattern allows for:
- Parallel agent execution
- Isolated agent workspaces
- Controlled state synchronization

## Best Practices

### 1. Keep State Focused
Design state schemas that contain only essential information needed across interactions.

### 2. Use Appropriate Data Structures
Choose data structures that match your use case:
- Lists for ordered collections
- Dictionaries for key-value mappings
- Custom classes for complex structured data

### 3. Implement Custom Reducers
When using custom state fields, implement reducers that handle merging logic appropriately for your data type.

### 4. Plan for State Sharing
Consider how state will be shared and modified when designing multi-agent workflows.

### 5. Use Files for Persistence
Leverage the virtual file system for storing:
- Large content that shouldn't be in memory
- Structured documents
- Intermediate results
- Shareable artifacts

## Custom State Schemas

The framework allows custom state schemas by extending `DeepAgentState`:

```python
class CustomAgentState(DeepAgentState):
    custom_field: NotRequired[YourDataType]
    another_field: Annotated[NotRequired[dict], custom_reducer]
```

Specify your custom state when creating agents to enable domain-specific state management while maintaining compatibility with the core framework.

## Implementation Details

State management in deepagents is built on LangGraph's state management system, providing:
- Automatic state persistence across turns
- Thread-safe state updates
- Efficient state serialization
- Integration with agent tools and workflows

The state acts as both a coordination mechanism between agents and a persistent workspace for complex tasks requiring multiple interaction rounds.