from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain.tools.tool_node import InjectedState
from typing import Annotated, Union
from deepagents.state import Todo, FilesystemState
from deepagents.prompts import (
    WRITE_TODOS_TOOL_DESCRIPTION,
    LIST_FILES_TOOL_DESCRIPTION,
    READ_FILE_TOOL_DESCRIPTION,
    WRITE_FILE_TOOL_DESCRIPTION,
    EDIT_FILE_TOOL_DESCRIPTION,
)


@tool(description=WRITE_TODOS_TOOL_DESCRIPTION)
def write_todos(
    todos: list[Todo], tool_call_id: Annotated[str, InjectedToolCallId]
) -> Command:
    return Command(
        update={
            "todos": todos,
            "messages": [
                ToolMessage(f"Updated todo list to {todos}", tool_call_id=tool_call_id)
            ],
        }
    )


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


@tool(description=LIST_FILES_TOOL_DESCRIPTION)
def ls(state: Annotated[FilesystemState, InjectedState]) -> list[str]:
    """List all files"""
    return list(state.get("files", {}).keys())


@tool(description=READ_FILE_TOOL_DESCRIPTION)
def read_file(
    file_path: str,
    state: Annotated[FilesystemState, InjectedState],
    offset: int = 0,
    limit: int = 2000,
) -> str:
    mock_filesystem = state.get("files", {})
    if file_path not in mock_filesystem:
        return f"Error: File '{file_path}' not found"

    # Get file content
    content = mock_filesystem[file_path]

    # Handle empty file
    if not content or content.strip() == "":
        return "System reminder: File exists but has empty contents"

    # Split content into lines
    lines = content.splitlines()

    # Apply line offset and limit
    start_idx = offset
    end_idx = min(start_idx + limit, len(lines))

    # Handle case where offset is beyond file length
    if start_idx >= len(lines):
        return f"Error: Line offset {offset} exceeds file length ({len(lines)} lines)"

    # Format output with line numbers (cat -n format)
    result_lines = []
    for i in range(start_idx, end_idx):
        line_content = lines[i]

        # Truncate lines longer than 2000 characters
        if len(line_content) > 2000:
            line_content = line_content[:2000]

        # Line numbers start at 1, so add 1 to the index
        line_number = i + 1
        result_lines.append(f"{line_number:6d}\t{line_content}")

    return "\n".join(result_lines)


@tool(description=WRITE_FILE_TOOL_DESCRIPTION)
def write_file(
    file_path: str,
    content: str,
    state: Annotated[FilesystemState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
) -> Command:
    # Enhanced validation to prevent infinite loops
    if not file_path or not isinstance(file_path, str):
        return Command(
            update={
                "messages": [
                    ToolMessage(f"Error: file_path is required and must be a string, got: {type(file_path)}", tool_call_id=tool_call_id)
                ]
            }
        )

    if content is None:
        return Command(
            update={
                "messages": [
                    ToolMessage(f"Error: content is required, got None", tool_call_id=tool_call_id)
                ]
            }
        )

    # Convert content to string if needed
    if not isinstance(content, str):
        content = str(content)

    files = state.get("files", {})
    files[file_path] = content

    # INTERRUPT PROTECTION: Also store in global cache for recovery during interrupts
    # This ensures files survive even if Command updates are lost during GraphInterrupt
    global _interrupt_file_cache
    if '_interrupt_file_cache' not in globals():
        _interrupt_file_cache = {}
    _interrupt_file_cache[file_path] = content
    print(f"💾 INTERRUPT CACHE: Stored {file_path} ({len(content)} chars) - cache now has {len(_interrupt_file_cache)} files")

    return Command(
        update={
            "files": files,
            "messages": [
                ToolMessage(f"Updated file {file_path}", tool_call_id=tool_call_id)
            ],
        }
    )


@tool(description=EDIT_FILE_TOOL_DESCRIPTION)
def edit_file(
    file_path: str,
    old_string: str,
    new_string: str,
    state: Annotated[FilesystemState, InjectedState],
    tool_call_id: Annotated[str, InjectedToolCallId],
    replace_all: bool = False,
) -> Union[Command, str]:
    """Write to a file."""
    mock_filesystem = state.get("files", {})
    # Check if file exists in mock filesystem
    if file_path not in mock_filesystem:
        return f"Error: File '{file_path}' not found"

    # Get current file content
    content = mock_filesystem[file_path]

    # Check if old_string exists in the file
    if old_string not in content:
        return f"Error: String not found in file: '{old_string}'"

    # If not replace_all, check for uniqueness
    if not replace_all:
        occurrences = content.count(old_string)
        if occurrences > 1:
            return f"Error: String '{old_string}' appears {occurrences} times in file. Use replace_all=True to replace all instances, or provide a more specific string with surrounding context."
        elif occurrences == 0:
            return f"Error: String not found in file: '{old_string}'"

    # Perform the replacement
    if replace_all:
        new_content = content.replace(old_string, new_string)
        replacement_count = content.count(old_string)
        result_msg = f"Successfully replaced {replacement_count} instance(s) of the string in '{file_path}'"
    else:
        new_content = content.replace(
            old_string, new_string, 1
        )  # Replace only first occurrence
        result_msg = f"Successfully replaced string in '{file_path}'"

    # Update the mock filesystem
    mock_filesystem[file_path] = new_content

    # INTERRUPT PROTECTION: Also store in global cache for recovery during interrupts
    # This ensures edited files survive even if Command updates are lost during GraphInterrupt
    global _interrupt_file_cache
    if '_interrupt_file_cache' not in globals():
        _interrupt_file_cache = {}
    _interrupt_file_cache[file_path] = new_content
    print(f"💾 INTERRUPT CACHE: Updated {file_path} ({len(new_content)} chars) - cache now has {len(_interrupt_file_cache)} files")

    return Command(
        update={
            "files": mock_filesystem,
            "messages": [ToolMessage(result_msg, tool_call_id=tool_call_id)],
        }
    )


@tool(description="Request user approval for plans, requirements, or important decisions. Use this for requirements approval, technical plan approval, or any decision that needs explicit user confirmation.")
def approve_plan(plan_content: str, tool_call_id: Annotated[str, InjectedToolCallId]) -> Command:
    """
    Request user approval for plans, requirements, or important decisions.

    This tool is specifically designed for approval requests where the user should have
    the option to approve, edit, or provide alternative feedback. Unlike human_input,
    this will show appropriate approval UI with buttons in the frontend.

    Use this for:
    - Requirements approval (discussion phase)
    - Technical plan approval (planning phase)
    - Any decision that needs explicit user confirmation

    Args:
        plan_content: The plan, requirements, or decision to be approved
        tool_call_id: Injected tool call ID for state tracking

    Returns:
        Command object that triggers the interrupt workflow with approval UI
    """
    # Use the interrupt system to request approval
    # The frontend will recognize this is NOT human_input and show full approval UI
    return Command(
        update={
            "messages": [
                ToolMessage(
                    content=f"APPROVAL_REQUEST: {plan_content}",
                    tool_call_id=tool_call_id
                )
            ]
        }
    )
