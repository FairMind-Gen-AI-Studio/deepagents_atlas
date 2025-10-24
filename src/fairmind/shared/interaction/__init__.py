"""
User interaction tools for Fairmind agents.

Provides LangGraph-compatible interrupt tools for human-in-the-loop workflows:
- human_input: Ask open-ended questions
- human_confirm: Yes/no confirmations
- human_input_multiline: Multi-line text input
- approve_plan: Full approval UI with edit capability

These tools use LangGraph's Command and ToolMessage pattern to trigger interrupts,
allowing agents to pause execution and wait for user input.

Usage:
    from fairmind.shared.interaction import human_input, approve_plan

    # Ask user for input
    response = human_input("Which project should I analyze?")

    # Request approval
    approved = approve_plan(plan_content)

Originally extracted from Atlas V1 agent for reuse across all Fairmind agents.
"""

from .tools import (
    human_input,
    human_confirm,
    human_input_multiline,
    approve_plan,
)

__all__ = [
    'human_input',
    'human_confirm',
    'human_input_multiline',
    'approve_plan',
]

__version__ = "0.1.0"
