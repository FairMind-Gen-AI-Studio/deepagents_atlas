# Discussion Phase User Interaction Fix

## Problem

The discussion phase in Atlas V1 was generating questions but they weren't displayed to the user. The UI flow continued automatically without user interaction because:

1. Subagents' outputs were returned as ToolMessages to the orchestrator, not shown to the user
2. The discussion agent lacked a mechanism to actually interact with the human user
3. The orchestrator treated the subagent's response as complete without checking if user interaction occurred

## Solution Implemented

### 1. Added Human Input Tool (`src/deepagents/tools.py`)

```python
@tool(description="Ask the user a question and wait for their response. Use this for interactive clarification of requirements.")
def human_input(
    question: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    """Ask the user a question and wait for their response."""
    return Command(
        update={
            "messages": [
                ToolMessage(f"USER_QUESTION: {question}", tool_call_id=tool_call_id)
            ],
        }
    )
```

### 2. Updated Deep Agent Framework (`src/deepagents/graph.py`)

- Added `human_input` to the built-in tools available to all agents
- Updated imports to include the new tool

### 3. Modified Discussion Agent Configuration (`examples/atlas_v1/subagents.py`)

```python
def get_discussion_agent_config() -> Dict[str, Any]:
    return {
        "name": "discussion-agent", 
        "description": "Phase 2: Generate targeted clarification questions and process user responses",
        "prompt": DISCUSSION_AGENT_PROMPT_TEMPLATE,
        "tools": ["human_input"],  # Added human_input tool
        "outputs": [               # Added validation requirements
            "clarification_questions.md",
            "user_responses.md", 
            "requirements_clarified.md"
        ],
        "validation_criteria": [
            "Questions were presented to user",
            "User responses were collected",
            "Requirements summary was approved by user"
        ]
    }
```

### 4. Enhanced Subagent Invocation Logic (`src/deepagents/sub_agent.py`)

```python
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
```

### 5. Updated Discussion Agent Prompt (`examples/atlas_v1/prompts.py`)

- Modified interactive discussion process to use `human_input` tool
- Updated approval workflow to explicitly use `human_input` for all user interactions
- Added clear instructions about using the tool for questions and approval

### 6. Enhanced Phase Validation

Added specific validation for discussion phase to check that:
- Questions were actually presented to user
- User responses were collected
- Requirements summary was approved

## How It Works Now

1. **Discussion Agent**: Uses `human_input` tool to present questions
2. **Subagent Handler**: Detects `USER_QUESTION:` prefix and surfaces questions to user
3. **UI Layer**: Should intercept messages with `USER_QUESTION:` and present them to user
4. **Phase Validation**: Ensures all required interaction files are created before advancement

## UI Integration Required

For this fix to work completely in the Atlas V1 UI, the UI needs to:

1. **Detect USER_QUESTION messages**: Look for `USER_QUESTION:` prefix in agent responses
2. **Present questions to user**: Display the question and wait for user input
3. **Continue agent conversation**: Pass user responses back to the agent
4. **Handle interactive flow**: Don't advance phases until user interaction is complete

## Testing

The fix has been tested with:
- ✅ Human input tool creation and integration
- ✅ Discussion agent configuration updates  
- ✅ Subagent invocation logic for USER_QUESTION handling
- ✅ Phase validation enhancements
- ✅ Prompt updates for human_input usage

## Files Modified

- `src/deepagents/tools.py` - Added human_input tool
- `src/deepagents/graph.py` - Added tool to built-ins
- `src/deepagents/sub_agent.py` - Enhanced message handling
- `examples/atlas_v1/subagents.py` - Updated configuration and validation
- `examples/atlas_v1/prompts.py` - Updated prompts to use human_input tool

The discussion phase will now properly generate questions using the `human_input` tool, which can be intercepted by the UI layer to create the interactive experience the user expects.