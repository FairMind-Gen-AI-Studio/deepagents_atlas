"""FairMind Middleware - Custom middleware for context management and safety.

This module provides enhanced middleware for managing conversation context
and preventing token overflow in deep agent conversations.
"""

from fairmind.middleware.safe_summarization import SafeSummarizationMiddleware

__all__ = [
    "SafeSummarizationMiddleware",
]
