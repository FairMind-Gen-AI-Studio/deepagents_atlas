"""Tool wrapper utilities for ArchQA agent.

Provides validation and error handling for deepagents built-in tools to improve
LLM tool call reliability.
"""

from typing import Callable, Any, Annotated
from langchain_core.tools import tool, InjectedToolCallId
from langchain_core.messages import ToolMessage
from langgraph.types import Command
from langchain.tools.tool_node import InjectedState
from deepagents.state import FilesystemState


def create_safe_write_file_wrapper(original_write_file: Any) -> Callable:
    """
    Creates a validated wrapper around write_file that catches parameter errors
    before Pydantic validation, providing clear error messages for LLM retry.

    Args:
        original_write_file: The original write_file tool from deepagents (unused, we recreate)

    Returns:
        New write_file tool with built-in parameter validation
    """

    # Create a NEW tool with validation logic, instead of wrapping the existing one
    # This avoids issues with LangChain's tool introspection

    @tool(description="""Writes to a file in the local filesystem.

Usage:
- The file_path parameter must be an absolute path, not a relative path
- The content parameter must be a string
- The write_file tool will create a new file.
- Prefer to edit existing files over creating new ones when possible.

IMPORTANT: BOTH parameters are required. Calling with only file_path will cause an error.""")
    def write_file(
        file_path: str,
        content: str,
        state: Annotated[FilesystemState, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ) -> Command:
        """Write content to a file. BOTH file_path AND content are required."""

        # Validate file_path
        if not file_path or not isinstance(file_path, str) or file_path.strip() == "":
            raise ValueError(
                "🚨 write_file VALIDATION ERROR: 'file_path' is required and cannot be empty.\n"
                "\n"
                "✅ CORRECT USAGE:\n"
                "write_file(\n"
                "    file_path='/report.md',\n"
                "    content='# Report Title\\n\\nYour content here...'\n"
                ")\n"
                "\n"
                "❌ WRONG: write_file(file_path='')  # Empty path!\n"
                "\n"
                "Please retry with a valid file_path."
            )

        # Validate content (it's okay if empty string, but must be provided)
        if content is None:
            raise ValueError(
                "🚨 write_file VALIDATION ERROR: 'content' parameter is REQUIRED.\n"
                "\n"
                "You called write_file with only file_path, but the content parameter is mandatory.\n"
                "\n"
                "✅ CORRECT USAGE:\n"
                "write_file(\n"
                "    file_path='/report.md',\n"
                "    content='# Report Title\\n\\nYour complete content here...'\n"
                ")\n"
                "\n"
                "❌ WRONG: write_file(file_path='/report.md')  # Missing content!\n"
                "\n"
                "📝 TIP: Compose your full file content first, then call write_file with BOTH parameters.\n"
                "\n"
                "Please retry with both file_path AND content parameters."
            )

        # Validation passed - execute the write operation
        files = state.get("files", {})
        files[file_path] = content

        return Command(
            update={
                "files": files,
                "messages": [
                    ToolMessage(f"Updated file {file_path}", tool_call_id=tool_call_id)
                ],
            }
        )

    return write_file


def wrap_filesystem_tools(tools: list) -> list:
    """
    Wraps filesystem tools from deepagents with validation.

    Currently wraps:
    - write_file: Adds parameter validation for file_path and content

    Args:
        tools: List of tools from deepagents (typically imported from deepagents.tools)

    Returns:
        List of tools with wrapped versions replacing originals
    """
    wrapped_tools = []

    for tool in tools:
        # Check if this is the write_file tool
        tool_name = getattr(tool, 'name', None) or getattr(tool, '__name__', None)

        if tool_name == 'write_file':
            # Wrap write_file with validation
            wrapped_tool = create_safe_write_file_wrapper(tool)
            # Preserve LangChain tool attributes
            if hasattr(tool, 'name'):
                wrapped_tool.name = tool.name
            if hasattr(tool, 'description'):
                wrapped_tool.description = tool.description
            wrapped_tools.append(wrapped_tool)
        else:
            # Keep other tools unchanged
            wrapped_tools.append(tool)

    return wrapped_tools
