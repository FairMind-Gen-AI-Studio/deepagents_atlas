"""
Atlas V1 Custom Tools
Enhanced tool implementations for Atlas V1 that override deepagents defaults
with LangGraph Studio-compatible interrupt functionality.
"""

from langchain_core.tools import tool
from typing import Optional
import logging

# Try to import interrupt - it might not be available in all environments
try:
    from langgraph.types import interrupt
    INTERRUPT_AVAILABLE = True
except ImportError:
    INTERRUPT_AVAILABLE = False
    interrupt = None  # Define as None for fallback

logger = logging.getLogger(__name__)


@tool  # Name is inferred from function name
def human_input(question: str) -> str:
    """
    Ask the user a question and wait for their response.
    
    This is an Atlas V1 enhanced version that uses LangGraph interrupt
    for proper blocking behavior in LangGraph Studio. Falls back gracefully
    in environments where interrupt is not available.
    
    Args:
        question: The question to ask the user
        
    Returns:
        The user's response as a string
    """
    logger.debug(f"[human_input] Called with question: {question}")
    logger.debug(f"[human_input] INTERRUPT_AVAILABLE: {INTERRUPT_AVAILABLE}, interrupt object: {interrupt}")
    
    # Try to use interrupt if available (LangGraph Studio environment)
    if INTERRUPT_AVAILABLE and interrupt:
        try:
            # Import GraphInterrupt for proper exception handling
            from langgraph.errors import GraphInterrupt
            
            logger.debug("[human_input] Using LangGraph interrupt for real blocking")
            
            # CRITICAL: Call interrupt - this will raise GraphInterrupt
            response = interrupt(question)
            
            # This line is only reached AFTER user responds (when graph resumes)
            logger.info(f"[human_input] User responded: {response}")
            
            if response is not None:
                # Convert response to string and return it
                response_str = str(response)
                return response_str
            else:
                logger.warning("[human_input] Interrupt returned None/empty response")
                return "No response provided"
                
        except GraphInterrupt:
            # This is EXPECTED - GraphInterrupt is how LangGraph pauses execution
            # CRITICAL: We MUST re-raise this exception for LangGraph to handle it properly
            logger.debug("[human_input] GraphInterrupt raised - pausing execution for user input")
            raise  # <-- MUST RE-RAISE for interrupt to work!
            
        except Exception as e:
            # Only catch other unexpected errors
            logger.error(f"[human_input] Unexpected error (not GraphInterrupt): {e}")
            import traceback
            logger.error(traceback.format_exc())
            # Fall through to fallback behavior
    else:
        logger.warning(f"[human_input] Interrupt not available - using fallback mode")
    
    # Fallback behavior for non-Studio environments
    logger.warning(f"[human_input] Using fallback mode - interrupt not available")
    logger.warning(f"[human_input] Question that needs answer: {question}")
    
    # In fallback mode, we return a marker that indicates input is needed
    # This allows the agent to continue but marks where interaction was requested
    fallback_response = f"[AWAITING_USER_INPUT: {question}]"
    logger.debug(f"[human_input] Returning fallback response: {fallback_response}")
    return fallback_response


@tool
def human_confirm(message: str, default: bool = False) -> bool:
    """
    Ask user for yes/no confirmation.
    
    Enhanced confirmation tool for Atlas V1 that uses interrupt when available.
    
    Args:
        message: The confirmation message to show the user
        default: Default value if no response (default: False)
        
    Returns:
        True for yes/approved, False for no/rejected
    """
    logger.info(f"[human_confirm] Asking for confirmation: {message}")
    
    if INTERRUPT_AVAILABLE and interrupt:
        try:
            from langgraph.errors import GraphInterrupt
            
            logger.debug("[human_confirm] Using LangGraph interrupt for confirmation")
            response = interrupt(f"{message} (yes/no)")
            
            # This line is only reached after user responds
            if response is not None:
                response_str = str(response).lower().strip()
                logger.info(f"[human_confirm] User response: {response_str}")
                
                # Accept various affirmative responses
                affirmative = ['yes', 'y', 'si', 'ok', 'okay', 'sure', 'confirm', 'approve', 'true', '1']
                result = response_str in affirmative
                
                logger.info(f"[human_confirm] Interpreted as: {'approved' if result else 'rejected'}")
                return result
            else:
                logger.warning(f"[human_confirm] No response, using default: {default}")
                return default
                
        except GraphInterrupt:
            # Re-raise GraphInterrupt for LangGraph to handle
            logger.debug("[human_confirm] GraphInterrupt raised - pausing for confirmation")
            raise
            
        except Exception as e:
            logger.error(f"[human_confirm] Unexpected error: {e}")
    
    # Fallback behavior
    logger.warning(f"[human_confirm] Interrupt not available, using default: {default}")
    return default


@tool
def human_input_multiline(question: str, placeholder: Optional[str] = None) -> str:
    """
    Ask the user for potentially multi-line input.
    
    Useful for collecting longer responses like requirements, descriptions, or code.
    
    Args:
        question: The question or prompt for the user
        placeholder: Optional placeholder text to show as example
        
    Returns:
        The user's multi-line response as a string
    """
    logger.info(f"[human_input_multiline] Requesting multi-line input: {question}")
    
    if placeholder:
        full_prompt = f"{question}\n(Example: {placeholder})"
    else:
        full_prompt = question
    
    if INTERRUPT_AVAILABLE and interrupt:
        try:
            from langgraph.errors import GraphInterrupt
            
            logger.debug("[human_input_multiline] Using interrupt for multi-line input")
            response = interrupt(full_prompt)
            
            # This line is only reached after user responds
            if response is not None:
                response_str = str(response)
                lines = response_str.count('\n') + 1
                logger.info(f"[human_input_multiline] Received {lines} lines of input")
                return response_str
            else:
                logger.warning("[human_input_multiline] No response provided")
                return "No response provided"
                
        except GraphInterrupt:
            # Re-raise GraphInterrupt for LangGraph to handle
            logger.debug("[human_input_multiline] GraphInterrupt raised - pausing for multi-line input")
            raise
            
        except Exception as e:
            logger.error(f"[human_input_multiline] Unexpected error: {e}")
    
    # Fallback
    logger.warning(f"[human_input_multiline] Using fallback for: {question}")
    return f"[AWAITING_MULTILINE_INPUT: {question}]"


# Export the tools for easy import
__all__ = ['human_input', 'human_confirm', 'human_input_multiline']


# Log initialization status
if INTERRUPT_AVAILABLE:
    logger.info("Atlas tools initialized with LangGraph interrupt support ✓")
else:
    logger.warning("Atlas tools initialized without interrupt support (fallback mode)")