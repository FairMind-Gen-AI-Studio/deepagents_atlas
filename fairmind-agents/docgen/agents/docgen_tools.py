# DocGen Interactive Tools
# Tools that work correctly with HumanInTheLoopMiddleware for UI interrupts

from langchain_core.tools import tool, InjectedToolCallId
from langgraph.errors import NodeInterrupt
from typing import Annotated


@tool
def human_input(
    question: str,
    tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """
    Ask the user a question via HumanInTheLoopMiddleware dialog.

    This tool raises an Interrupt that allows HumanInTheLoopMiddleware to:
    1. Intercept the interrupt
    2. Show a dialog UI with the question
    3. Collect the user's response via the UI
    4. Resume execution with the response injected

    Using Interrupt instead of Command ensures execution continues
    seamlessly without creating a new run.

    Args:
        question: The question to ask the user
        tool_call_id: Tool call ID for state tracking

    Returns:
        The user's response to the question (provided when tool is re-invoked)

    Raises:
        NodeInterrupt: To trigger middleware UI dialog collection
    """
    # Raise NodeInterrupt to trigger middleware UI
    # The middleware will:
    # 1. Catch the NodeInterrupt exception
    # 2. Show a dialog UI with the question
    # 3. Collect the user's response from the dialog
    # 4. Resume execution and re-invoke this tool with the response
    # 5. This tool then returns the response, allowing execution to continue

    raise NodeInterrupt(question)


__all__ = ["human_input"]
