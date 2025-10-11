"""
Async-safe wrapper for OpenPipe ART to prevent blocking I/O errors.

This module provides an async-compatible wrapper around ART's LoggingLLM
to handle file I/O operations without blocking the event loop.
"""

import asyncio
from typing import Any, Dict, Optional, List
from langchain_core.messages import BaseMessage
from langchain_core.language_models import BaseChatModel
from langchain_core.outputs import ChatResult
from pydantic import Field
import logging

logger = logging.getLogger(__name__)


class AsyncSafeARTModel(BaseChatModel):
    """
    Async-safe wrapper for ART model that prevents blocking I/O.
    
    This wrapper delegates actual model calls to the wrapped model
    but ensures any synchronous I/O operations are handled in a
    separate thread to prevent blocking the event loop.
    """
    
    # Declare the wrapped_model field for Pydantic
    wrapped_model: Any = Field(default=None, exclude=True)
    
    def __init__(self, wrapped_model: Any, **kwargs):
        """
        Initialize with an ART-wrapped model.
        
        Args:
            wrapped_model: The ART LoggingLLM model to wrap
        """
        super().__init__(**kwargs)
        self.wrapped_model = wrapped_model
        
    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> ChatResult:
        """
        Generate a response asynchronously without blocking.
        
        Uses asyncio.to_thread to run the potentially blocking
        ART model in a separate thread.
        """
        # Run the synchronous model in a thread to avoid blocking
        try:
            # Check if the wrapped model has async support
            if hasattr(self.wrapped_model, 'ainvoke'):
                # Use native async if available
                result = await self.wrapped_model.ainvoke(messages, **kwargs)
                # Convert to ChatResult if needed
                if not isinstance(result, ChatResult):
                    # Wrap single message in ChatResult
                    from langchain_core.outputs import ChatGeneration
                    generation = ChatGeneration(message=result)
                    return ChatResult(generations=[generation])
                return result
            else:
                # Fallback to thread for sync models
                def sync_call():
                    return self.wrapped_model.invoke(messages, **kwargs)
                
                result = await asyncio.to_thread(sync_call)
                
                # Convert to ChatResult if needed
                if not isinstance(result, ChatResult):
                    from langchain_core.outputs import ChatGeneration
                    generation = ChatGeneration(message=result)
                    return ChatResult(generations=[generation])
                return result
                
        except Exception as e:
            logger.error(f"Error in async-safe ART wrapper: {e}")
            raise
    
    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[Any] = None,
        **kwargs: Any
    ) -> ChatResult:
        """
        Synchronous generation (fallback).
        """
        try:
            result = self.wrapped_model.invoke(messages, **kwargs)
            
            # Convert to ChatResult if needed
            if not isinstance(result, ChatResult):
                from langchain_core.outputs import ChatGeneration
                generation = ChatGeneration(message=result)
                return ChatResult(generations=[generation])
            return result
        except Exception as e:
            logger.error(f"Error in sync generation: {e}")
            raise
    
    @property
    def _llm_type(self) -> str:
        """Return type of LLM."""
        return "async-safe-art"
    
    def bind_tools(self, tools, **kwargs):
        """
        Delegate bind_tools to the wrapped model.
        """
        # The wrapped model should handle tool binding
        bound_model = self.wrapped_model.bind_tools(tools, **kwargs)
        # Return a new wrapped instance with the bound model
        return AsyncSafeARTModel(bound_model)
    
    def with_structured_output(self, schema, **kwargs):
        """
        Delegate structured output to the wrapped model.
        """
        structured_model = self.wrapped_model.with_structured_output(schema, **kwargs)
        return AsyncSafeARTModel(structured_model)
    
    def __getattr__(self, name):
        """
        Delegate any other attributes to the wrapped model.
        """
        return getattr(self.wrapped_model, name)


def make_async_safe(model: Any) -> AsyncSafeARTModel:
    """
    Wrap an ART model to make it async-safe.
    
    Args:
        model: The ART-wrapped model
        
    Returns:
        An async-safe wrapper around the model
    """
    return AsyncSafeARTModel(model)