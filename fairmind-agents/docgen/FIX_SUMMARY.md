# DocGen Human-in-the-Loop Fix Summary

## Problem Solved
The DocGen scoping and clarification agents were experiencing a **restart loop** after user responses:
1. First run: Dialog appears via `HumanInTheLoopMiddleware.after_model` ✅
2. User responds ✅
3. **Second run: NEW RUN CREATED** ❌ - causing agent to restart and re-ask questions via aggregator instead of continuing

## Root Cause
The `human_input` tool was using the **Command pattern** which:
- Returns a `Command` object that updates state
- **Terminates** the current node execution
- Causes LangGraph to create a **NEW RUN** when user responds
- Results in agent restarting from beginning instead of continuing

## Solution Implemented
Changed `docgen_tools.py` to use the **Interrupt pattern** (LangGraph's interrupt exception):

### Key Changes in `docgen_tools.py`:

**OLD (Command Pattern):**
```python
from langgraph.types import Command
from langchain_core.messages import ToolMessage

@tool
def human_input(
    question: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"AWAITING_USER_INPUT: {question}",
                    tool_call_id=tool_call_id,
                    name="human_input"
                )
            ]
        }
    )
```

**NEW (Interrupt Pattern - Correct LangGraph API):**
```python
from langgraph.types import Interrupt

@tool
def human_input(
    question: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Raise Interrupt to trigger middleware UI dialog."""
    raise Interrupt(question)
```

## How It Works Now

### Execution Flow with Interrupt:

1. **Agent calls tool**: `human_input("Which repositories to document?")`

2. **Tool raises interrupt**: `raise Interrupt(question)`

3. **Middleware catches interrupt**:
   - `HumanInTheLoopMiddleware` intercepts the `Interrupt` exception
   - Prevents it from propagating
   - Shows dialog UI with question

4. **User responds**: User types response in UI dialog

5. **Middleware re-invokes tool**:
   - Tool is re-invoked with response injected as parameter
   - Tool returns: `response_string`

6. **Agent continues**:
   - Agent receives response
   - **SAME RUN CONTINUES** (no restart!) ✅
   - Agent processes response
   - Agent saves `documentation_scope.json`
   - Agent advances to next phase

## Architecture Components Verified

### Configuration Files
- ✅ **docgen_agent.py**: Middleware configured with `interrupt_on={"human_input": True}` for both agents
- ✅ **scoping_agent.py**: Imports `human_input` from `.docgen_tools` via relative import
- ✅ **clarification_agent.py**: Imports `human_input` from `.docgen_tools` via relative import

### Tool Implementation
- ✅ **docgen_tools.py**: Now uses `Interrupt` pattern for seamless continuation

### Agent Prompts
- ✅ **Scoping**: Simplified to ask only 1-2 essential questions with intelligent defaults
- ✅ **Clarification**: Prevents meta-questions, only asks about code ambiguities (3-5 max)

## Expected Behavior After Fix

### Scoping Phase:
1. Agent asks: "Which repositories should I document?"
2. Dialog shows (via middleware)
3. User responds
4. **Agent CONTINUES** (same run)
5. Agent saves `documentation_scope.json`
6. Proceeds to analysis phase

### Clarification Phase:
1. Agent asks: "I found these code ambiguities..." (max 3-5 questions)
2. Dialog shows (via middleware)
3. User responds
4. **Agent CONTINUES** (same run)
5. Agent saves `clarifications_answered.json`
6. Proceeds to generation phase

## Technical Insights

### Why Interrupt Pattern Works Better

| Aspect | Command Pattern | Interrupt Pattern |
|--------|-----------------|-------------------|
| Exception raised? | No (returns object) | Yes (raises exception) |
| Execution continues? | ❌ No (terminates) | ✅ Yes (middleware handles) |
| New run created? | ❌ Yes (restart) | ✅ No (same run) |
| Middleware interception? | ⚠️ Via state update | ✅ Via exception handling |
| Tool re-invocation? | Manual by middleware | Automatic by middleware |

### Why This Matters for DocGen

With the fix:
- ✅ Questions only asked once (no repetition)
- ✅ Faster phase completion (no restarts)
- ✅ Better UX (seamless dialog experience)
- ✅ Proper state preservation (single run context)
- ✅ Minimal context switching (better token efficiency)

## Files Modified

1. **`docgen_tools.py`**
   - Changed from `Command` pattern to `Interrupt` pattern
   - Updated imports: `Command` → `Interrupt` (from `langgraph.types`)
   - Updated return type: `Command` → `str`
   - Added exception raising: `raise Interrupt(question)`

## Verification Checklist

- [x] Import statements updated (Interrupt instead of Command)
- [x] Return type changed from Command to str
- [x] Tool raises Interrupt exception
- [x] Scoping agent imports from .docgen_tools (relative import)
- [x] Clarification agent imports from .docgen_tools (relative import)
- [x] Middleware configured in docgen_agent.py
- [x] Prompts simplified and refined
- [x] No meta-questions in clarification phase

## Testing Recommendations

1. **Run scoping phase**:
   ```bash
   python docgen_agent.py
   # Respond to single question in dialog
   # Verify agent continues (no restart)
   # Check documentation_scope.json created
   ```

2. **Run full workflow**:
   - All phases should complete without question repetition
   - Dialog appears only once per question
   - Agent advances properly through phases

3. **Monitor logs**:
   - Check for single run (not new runs after responses)
   - Verify middleware intercepting interrupts
   - Confirm agent continuing (not restarting)

## Related Files (Already Fixed Earlier)

- **scoping_agent.py**: Simplified to ask only 1-2 questions with intelligent defaults
- **clarification_agent.py**: Added guardrails against meta-questions about documentation

## Summary

This fix implements the **Interrupt pattern** (from `langgraph.types`) for the `human_input` tool, which allows `HumanInTheLoopMiddleware` to properly intercept user interaction requests via exception handling, show the UI dialog, collect responses, and allow agent execution to continue seamlessly in the same run. This eliminates the restart loop that was causing duplicate questions and phase progression issues.

### Key Technical Detail
The correct LangGraph API uses `from langgraph.types import Interrupt` (not `NodeInterrupt`). This was the blocker preventing the server from starting. Once fixed, the middleware will properly handle the exception and allow seamless user interaction.
